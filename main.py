import os
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from forms import (
    FileDeleteForm,
    FileMoveForm,
    FilePermissionForm,
    FileWriteForm,
    UserCreateForm,
    UserDeleteForm,
    UserLoginForm,
    UserUpdateForm,
)
from models import AbstractModel, User
from utils import (
    change_file_permission,
    create_file,
    delete_file,
    get_groups_list,
    get_users_list,
    list_files,
    move_file,
    read_file,
    sanitize_path,
    sha256,
    write_file,
)


def lifespan(app: FastAPI):
    for cls in AbstractModel.__subclasses__():
        if not os.path.exists(f"data/{cls.__name__.lower()}"):
            os.makedirs(f"data/{cls.__name__.lower()}")
    yield


app = FastAPI(root_path="/api", lifespan=lifespan)

if not os.path.exists("data/.secretkey"):
    open("data/.secretkey", "wb").write(os.urandom(32))
app.add_middleware(
    SessionMiddleware,
    secret_key=open("data/.secretkey", "rb").read(),
    max_age=24 * 60 * 60,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def status():
    return {"status": "success", "message": "NaiveFileManager is running."}


@app.post("/user/login")
def user_login(request: Request, data: Annotated[UserLoginForm, Form()]):
    user = User.load(sha256(data.username))
    if user and User.verify_password(data.password, user.password):
        request.session["uid"] = user.id
        return {"status": "success", "message": "Login success."}
    return {"status": "failed", "message": "Login failed."}


@app.post("/user/logout", dependencies=[Depends(User.is_authenticated)])
def user_logout(request: Request):
    request.session.clear()
    return {"status": "success", "message": "Logout success."}


@app.get(
    "/user/list", dependencies=[Depends(User.is_authenticated), Depends(User.is_admin)]
)
def user_list(page: int = 1, per_page: int = 10):
    data = User.list(page, per_page)
    return {
        "status": "success",
        "data": {
            "items": [
                {"username": user.username, "base_dir": user.base_dir}
                for user in data["items"]
            ],
            "total": data["total"],
            "page": data["page"],
            "per_page": data["per_page"],
        },
    }


@app.put(
    "/user/create",
    dependencies=[Depends(User.is_authenticated), Depends(User.is_admin)],
)
def user_create(data: Annotated[UserCreateForm, Form()]):
    user = User.load(sha256(data.username))
    if user:
        return {"status": "failed", "message": "User already exists."}
    User(
        data.username, User.hash_password(data.password), data.base_dir, data.role
    ).save()
    return {"status": "success", "message": "User created."}


@app.patch(
    "/user/update",
    dependencies=[Depends(User.is_authenticated), Depends(User.is_admin)],
)
def user_update(data: Annotated[UserUpdateForm, Form()]):
    user = User.load(sha256(data.username))
    if not user:
        return {"status": "failed", "message": "User does not exist."}
    if data.password:
        user.password = User.hash_password(data.password)
    user.base_dir = data.base_dir
    user.role = data.role
    user.save()
    return {"status": "success", "message": "User updated."}


@app.delete(
    "/user/delete",
    dependencies=[Depends(User.is_authenticated), Depends(User.is_admin)],
)
def user_delete(data: Annotated[UserDeleteForm, Form()]):
    user = User.load(sha256(data.username))
    if not user:
        return {"status": "failed", "message": "User does not exist."}
    user.delete()
    return {"status": "success", "message": "User deleted."}


@app.get("/file/list", dependencies=[Depends(User.is_authenticated)])
def file_list(request: Request, path: str, page: int = 1, per_page: int = 10):
    base_dir = User.load(request.session.get("uid")).base_dir
    return {"status": "success", "data": list_files(path, base_dir, page, per_page)}


@app.get("/file/download", dependencies=[Depends(User.is_authenticated)])
def file_download(request: Request, path: str):
    base_dir = User.load(request.session.get("uid")).base_dir
    path = sanitize_path(path, base_dir)
    if not os.path.exists(path) or os.path.isdir(path):
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(path)


@app.get("/file/read", dependencies=[Depends(User.is_authenticated)])
def file_read(request: Request, path: str, encoding: str = "utf-8"):
    base_dir = User.load(request.session.get("uid")).base_dir
    content = read_file(path, base_dir, encoding)
    if content is None:
        return {"status": "failed", "message": "Read failed."}
    return {"status": "success", "data": content}


@app.patch("/file/write", dependencies=[Depends(User.is_authenticated)])
def file_write(request: Request, data: Annotated[FileWriteForm, Form()]):
    base_dir = User.load(request.session.get("uid")).base_dir
    if write_file(data.path, data.content, base_dir, data.encoding):
        return {"status": "success", "message": "Write success."}
    return {"status": "failed", "message": "Write failed."}


@app.patch("/file/permission", dependencies=[Depends(User.is_authenticated)])
def file_permission(request: Request, data: Annotated[FilePermissionForm, Form()]):
    base_dir = User.load(request.session.get("uid")).base_dir
    if change_file_permission(data.path, data.mode, data.group, data.owner, base_dir):
        return {"status": "success", "message": "Permission updated."}
    return {"status": "failed", "message": "Permission update failed."}


@app.patch("/file/move", dependencies=[Depends(User.is_authenticated)])
def file_move(request: Request, data: Annotated[FileMoveForm, Form()]):
    base_dir = User.load(request.session.get("uid")).base_dir
    if move_file(data.source, data.destination, base_dir):
        return {"status": "success", "message": "Move success."}
    return {"status": "failed", "message": "Move failed."}


@app.delete("/file/delete", dependencies=[Depends(User.is_authenticated)])
def file_delete(request: Request, data: Annotated[FileDeleteForm, Form()]):
    base_dir = User.load(request.session.get("uid")).base_dir
    if delete_file(data.path, base_dir):
        return {"status": "success", "message": "Delete success."}
    return {"status": "failed", "message": "Delete failed."}


@app.post("/file/create", dependencies=[Depends(User.is_authenticated)])
def file_create(request: Request, path: str, type: str):
    base_dir = User.load(request.session.get("uid")).base_dir
    if create_file(path, type, base_dir):
        return {"status": "success", "message": "Create success."}
    return {"status": "failed", "message": "Create failed."}


@app.get("/system/group/list", dependencies=[Depends(User.is_authenticated)])
def system_group_list():
    return {"status": "success", "data": get_groups_list()}


@app.get("/system/user/list", dependencies=[Depends(User.is_authenticated)])
def system_user_list():
    return {"status": "success", "data": get_users_list()}
