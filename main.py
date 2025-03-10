import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from forms import (
    FileCreateForm,
    FileDeleteForm,
    FileMoveForm,
    FilePermissionForm,
    FileUploadForm,
    FileWriteForm,
    UserCreateForm,
    UserDeleteForm,
    UserLoginForm,
    UserPasswordForm,
    UserUpdateForm,
)
from models import AbstractModel, User
from utils import (
    audit_log,
    change_file_permission,
    create_file,
    delete_file,
    generate_sm2_keypair,
    get_groups_list,
    get_users_list,
    list_files,
    list_logs,
    move_file,
    read_file,
    sanitize_path,
    sha256,
    sm2_decrypt,
    upload_file,
    validate_password,
    write_file,
)

if not os.path.exists(os.path.join(os.getcwd(), "data")):
    os.makedirs(os.path.join(os.getcwd(), "data"))

for cls in AbstractModel.__subclasses__():
    if not os.path.exists(cls.get_data_dir()):
        os.makedirs(cls.get_data_dir())

if not os.path.exists(os.path.join(os.getcwd(), "data/logs")):
    os.makedirs(os.path.join(os.getcwd(), "data/logs"))

if not os.path.exists("data/.secretkey"):
    open("data/.secretkey", "wb").write(os.urandom(32))

if not os.path.exists("data/.privatekey") or not os.path.exists("data/.publickey"):
    private_key, public_key = generate_sm2_keypair()
    open("data/.privatekey", "w").write(private_key)
    open("data/.publickey", "w").write(public_key)

public_key = open("data/.publickey").read()
private_key = open("data/.privatekey").read()

log_handler = TimedRotatingFileHandler(
    os.path.join(os.getcwd(), "data/logs/app.log"), when="midnight", backupCount=60
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_handler.suffix = "%Y-%m-%d"
log_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

app = FastAPI()
api = FastAPI()
app.mount("/api", api)

app.add_middleware(
    SessionMiddleware,
    secret_key=open("data/.secretkey", "rb").read(),
    max_age=24 * 60 * 60,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    try:
        User.is_authenticated(request)
        return RedirectResponse("/files")
    except Exception:
        return RedirectResponse("/login")


@app.get("/login")
def login(request: Request):
    try:
        User.is_authenticated(request)
        return RedirectResponse("/files")
    except Exception:
        return templates.TemplateResponse(
            "login.html", {"request": request, "public_key": public_key}
        )


@app.get("/files")
def files(request: Request):
    try:
        User.is_authenticated(request)
        return templates.TemplateResponse(
            "files.html",
            {
                "request": request,
                "user": User.load(request.session.get("uid")),
                "public_key": public_key,
            },
        )
    except Exception:
        return RedirectResponse("/")


@app.get("/users")
def users(request: Request):
    try:
        User.is_authenticated(request)
        User.is_admin(request)
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "user": User.load(request.session.get("uid")),
                "public_key": public_key,
            },
        )
    except Exception:
        return RedirectResponse("/")


@app.get("/logs")
def logs(request: Request):
    try:
        User.is_authenticated(request)
        User.is_admin(request)
        return templates.TemplateResponse(
            "logs.html",
            {
                "request": request,
                "user": User.load(request.session.get("uid")),
                "public_key": public_key,
            },
        )
    except Exception:
        return RedirectResponse("/")


@api.get("/")
def status():
    return {"status": "success", "message": "NaiveFileManager API 运行正常"}


@api.post("/user/login")
def user_login(request: Request, data: Annotated[UserLoginForm, Form()]):
    user = User.load(sha256(data.username))
    data.password = sm2_decrypt(private_key, bytes.fromhex(data.password))
    if user and User.verify_password(data.password, user.password):
        request.session["uid"] = user.id
        audit_log(logger, "用户登录", user.username)
        return {"status": "success", "message": "登录成功"}
    return {"status": "failed", "message": "用户名或密码错误"}


@api.post("/user/logout", dependencies=[Depends(User.is_authenticated)])
def user_logout(request: Request):
    audit_log(logger, "用户登出", User.load(request.session.get("uid")).username)
    request.session.clear()
    return {"status": "success", "message": "退出登录成功"}


@api.get(
    "/user/list", dependencies=[Depends(User.is_authenticated), Depends(User.is_admin)]
)
def user_list(request: Request, page: int = 1, per_page: int = 15):
    data = User.list(page, per_page)
    audit_log(logger, "查看用户列表", User.load(request.session.get("uid")).username)
    return {
        "status": "success",
        "data": {
            "items": [
                {
                    "username": user.username,
                    "base_dir": user.base_dir,
                    "role": user.role,
                    "is_current_user": user.id == request.session.get("uid"),
                }
                for user in data["items"]
            ],
            "total": data["total"],
            "page": data["page"],
            "per_page": data["per_page"],
        },
    }


@api.put(
    "/user/create",
    dependencies=[Depends(User.is_authenticated), Depends(User.is_admin)],
)
def user_create(request: Request, data: Annotated[UserCreateForm, Form()]):
    user = User.load(sha256(data.username))
    if user:
        audit_log(
            logger,
            "创建用户",
            User.load(request.session.get("uid")).username,
            f"创建新用户 {data.username}",
            False,
        )
        return {"status": "failed", "message": "用户已存在"}
    data.password = sm2_decrypt(private_key, bytes.fromhex(data.password))
    validation = validate_password(data.password)
    if validation is not True:
        audit_log(
            logger,
            "创建用户",
            User.load(request.session.get("uid")).username,
            f"创建新用户 {data.username}",
            False,
        )
        return {"status": "failed", "message": validation}
    User(
        data.username, User.hash_password(data.password), data.base_dir, data.role
    ).save()
    audit_log(
        logger,
        "创建用户",
        User.load(request.session.get("uid")).username,
        f"创建新用户 {data.username}",
    )
    return {"status": "success", "message": "用户创建成功"}


@api.patch(
    "/user/update",
    dependencies=[Depends(User.is_authenticated), Depends(User.is_admin)],
)
def user_update(request: Request, data: Annotated[UserUpdateForm, Form()]):
    user = User.load(sha256(data.username))
    if not user:
        audit_log(
            logger,
            "更新用户",
            User.load(request.session.get("uid")).username,
            f"更新用户 {data.username}",
            False,
        )
        return {"status": "failed", "message": "用户不存在"}
    if data.password:
        data.password = sm2_decrypt(private_key, bytes.fromhex(data.password))
        validation = validate_password(data.password)
        if validation is not True:
            audit_log(
                logger,
                "更新用户",
                User.load(request.session.get("uid")).username,
                f"更新用户 {data.username}",
                False,
            )
            return {"status": "failed", "message": validation}
        user.password = User.hash_password(data.password)
    user.base_dir = data.base_dir
    user.role = data.role
    user.save()
    audit_log(
        logger,
        "更新用户",
        User.load(request.session.get("uid")).username,
        f"更新用户 {data.username}",
    )
    return {"status": "success", "message": "用户更新成功"}


@api.delete(
    "/user/delete",
    dependencies=[Depends(User.is_authenticated), Depends(User.is_admin)],
)
def user_delete(request: Request, data: Annotated[UserDeleteForm, Form()]):
    user = User.load(sha256(data.username))
    if not user:
        audit_log(
            logger,
            "删除用户",
            User.load(request.session.get("uid")).username,
            f"删除用户 {data.username}",
            False,
        )
        return {"status": "failed", "message": "用户不存在"}
    if user.id == request.session.get("uid"):
        audit_log(
            logger,
            "删除用户",
            User.load(request.session.get("uid")).username,
            f"删除用户 {data.username}",
            False,
        )
        return {"status": "failed", "message": "不能删除当前用户"}
    user.delete()
    audit_log(
        logger,
        "删除用户",
        User.load(request.session.get("uid")).username,
        f"删除用户 {data.username}",
    )
    return {"status": "success", "message": "用户删除成功"}


@api.patch(
    "/user/password",
    dependencies=[Depends(User.is_authenticated)],
)
def user_password(request: Request, data: Annotated[UserPasswordForm, Form()]):
    user = User.load(request.session.get("uid"))
    if not user:
        return {"status": "failed", "message": "用户不存在"}
    data.old_password = sm2_decrypt(private_key, bytes.fromhex(data.old_password))
    if not User.verify_password(data.old_password, user.password):
        audit_log(
            logger,
            "修改密码",
            user.username,
            False,
        )
        return {"status": "failed", "message": "当前密码错误"}
    data.new_password = sm2_decrypt(private_key, bytes.fromhex(data.new_password))
    validation = validate_password(data.new_password)
    if validation is not True:
        audit_log(
            logger,
            "修改密码",
            user.username,
            False,
        )
        return {"status": "failed", "message": validation}
    user.password = User.hash_password(data.new_password)
    user.save()
    audit_log(
        logger,
        "修改密码",
        user.username,
    )
    return {"status": "success", "message": "密码修改成功"}


@api.get("/file/list", dependencies=[Depends(User.is_authenticated)])
def file_list(
    request: Request,
    path: str,
    search: str = "",
    page: int = 1,
    per_page: int = 15,
    admin: bool = False,
):
    if admin and User.load(request.session.get("uid")).role == "admin":
        base_dir = "/"
    else:
        base_dir = User.load(request.session.get("uid")).base_dir
    try:
        audit_log(
            logger,
            "查看文件列表",
            User.load(request.session.get("uid")).username,
            f"查看 {sanitize_path(path, base_dir)}",
        )
        return {
            "status": "success",
            "data": list_files(path, base_dir, search, page, per_page),
        }
    except Exception:
        audit_log(
            logger,
            "查看文件列表",
            User.load(request.session.get("uid")).username,
            f"查看 {sanitize_path(path, base_dir)}",
            False,
        )
        return {"status": "failed", "message": "文件列表获取失败"}


@api.get("/file/download", dependencies=[Depends(User.is_authenticated)])
def file_download(request: Request, path: str):
    base_dir = User.load(request.session.get("uid")).base_dir
    path = sanitize_path(path, base_dir)
    if not os.path.exists(path) or os.path.isdir(path):
        audit_log(
            logger,
            "下载文件",
            User.load(request.session.get("uid")).username,
            f"下载 {sanitize_path(path, base_dir)}",
            False,
        )
        raise HTTPException(status_code=404, detail="Not Found")
    audit_log(
        logger,
        "下载文件",
        User.load(request.session.get("uid")).username,
        f"下载 {sanitize_path(path, base_dir)}",
    )
    return FileResponse(path)


@api.get("/file/read", dependencies=[Depends(User.is_authenticated)])
def file_read(request: Request, path: str, encoding: str = "utf-8"):
    base_dir = User.load(request.session.get("uid")).base_dir
    content = read_file(path, base_dir, encoding)
    if content is None:
        audit_log(
            logger,
            "读取文件",
            User.load(request.session.get("uid")).username,
            f"读取 {sanitize_path(path, base_dir)}",
            False,
        )
        return {"status": "failed", "message": "文件读取失败"}
    audit_log(
        logger,
        "读取文件",
        User.load(request.session.get("uid")).username,
        f"读取 {sanitize_path(path, base_dir)}",
    )
    return {"status": "success", "data": content}


@api.patch("/file/write", dependencies=[Depends(User.is_authenticated)])
def file_write(request: Request, data: Annotated[FileWriteForm, Form()]):
    base_dir = User.load(request.session.get("uid")).base_dir
    if write_file(data.path, data.content, base_dir, data.encoding):
        audit_log(
            logger,
            "写入文件",
            User.load(request.session.get("uid")).username,
            f"写入 {sanitize_path(data.path, base_dir)}",
        )
        return {"status": "success", "message": "文件保存成功"}
    audit_log(
        logger,
        "写入文件",
        User.load(request.session.get("uid")).username,
        f"写入 {sanitize_path(data.path, base_dir)}",
        False,
    )
    return {"status": "failed", "message": "文件保存失败"}


@api.patch("/file/permission", dependencies=[Depends(User.is_authenticated)])
def file_permission(request: Request, data: Annotated[FilePermissionForm, Form()]):
    base_dir = User.load(request.session.get("uid")).base_dir
    if change_file_permission(data.path, data.mode, data.group, data.owner, base_dir):
        audit_log(
            logger,
            "修改文件权限",
            User.load(request.session.get("uid")).username,
            f"修改 {sanitize_path(data.path, base_dir)} 的权限",
        )
        return {"status": "success", "message": "权限修改成功"}
    audit_log(
        logger,
        "修改文件权限",
        User.load(request.session.get("uid")).username,
        f"修改 {sanitize_path(data.path, base_dir)} 的权限",
        False,
    )
    return {"status": "failed", "message": "权限修改失败"}


@api.patch("/file/move", dependencies=[Depends(User.is_authenticated)])
def file_move(request: Request, data: Annotated[FileMoveForm, Form()]):
    base_dir = User.load(request.session.get("uid")).base_dir
    if move_file(data.source, data.destination, base_dir):
        audit_log(
            logger,
            "移动文件",
            User.load(request.session.get("uid")).username,
            f"移动 {sanitize_path(data.source, base_dir)} 到 {sanitize_path(data.destination, base_dir)}",
        )
        return {"status": "success", "message": "文件移动成功"}
    audit_log(
        logger,
        "移动文件",
        User.load(request.session.get("uid")).username,
        f"移动 {sanitize_path(data.source, base_dir)} 到 {sanitize_path(data.destination, base_dir)}",
        False,
    )
    return {"status": "failed", "message": "文件移动失败"}


@api.delete("/file/delete", dependencies=[Depends(User.is_authenticated)])
def file_delete(request: Request, data: Annotated[FileDeleteForm, Form()]):
    base_dir = User.load(request.session.get("uid")).base_dir
    if delete_file(data.path, base_dir):
        audit_log(
            logger,
            "删除文件",
            User.load(request.session.get("uid")).username,
            f"删除 {sanitize_path(data.path, base_dir)}",
        )
        return {"status": "success", "message": "文件删除成功"}
    audit_log(
        logger,
        "删除文件",
        User.load(request.session.get("uid")).username,
        f"删除 {sanitize_path(data.path, base_dir)}",
        False,
    )
    return {"status": "failed", "message": "文件删除失败"}


@api.post("/file/create", dependencies=[Depends(User.is_authenticated)])
def file_create(request: Request, data: Annotated[FileCreateForm, Form()]):
    base_dir = User.load(request.session.get("uid")).base_dir
    if create_file(data.path, data.type, base_dir):
        audit_log(
            logger,
            f"创建{'文件夹' if data.type == 'dir' else '文件'}",
            User.load(request.session.get("uid")).username,
            f"创建 {sanitize_path(data.path, base_dir)}",
        )
        return {
            "status": "success",
            "message": f"{'文件夹' if data.type == 'dir' else '文件'}创建成功",
        }
    audit_log(
        logger,
        f"创建{'文件夹' if data.type == 'dir' else '文件'}",
        User.load(request.session.get("uid")).username,
        f"创建 {sanitize_path(data.path, base_dir)}",
        False,
    )
    return {
        "status": "failed",
        "message": f"{'文件夹' if data.type == 'dir' else '文件'}创建失败",
    }


@api.post("/file/upload", dependencies=[Depends(User.is_authenticated)])
def file_upload(request: Request, data: Annotated[FileUploadForm, Form()]):
    base_dir = User.load(request.session.get("uid")).base_dir
    if upload_file(data.path, data.file, base_dir):
        audit_log(
            logger,
            "上传文件",
            User.load(request.session.get("uid")).username,
            f"上传 {sanitize_path(data.path, base_dir)}",
        )
        return {"status": "success", "message": "文件上传成功"}
    audit_log(
        logger,
        "上传文件",
        User.load(request.session.get("uid")).username,
        f"上传 {sanitize_path(data.path, base_dir)}",
        False,
    )
    return {"status": "failed", "message": "文件上传失败"}


@api.get("/system/group/list", dependencies=[Depends(User.is_authenticated)])
def system_group_list():
    return {"status": "success", "data": get_groups_list()}


@api.get("/system/user/list", dependencies=[Depends(User.is_authenticated)])
def system_user_list():
    return {"status": "success", "data": get_users_list()}


@api.get(
    "/system/logs",
    dependencies=[Depends(User.is_authenticated), Depends(User.is_admin)],
)
def system_logs(
    date: str = datetime.now().strftime("%Y-%m-%d"),
    page: int = 1,
    per_page: int = 15,
):
    return {"status": "success", "data": list_logs(date, page, per_page)}
