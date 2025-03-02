import os
from typing import Annotated

from fastapi import FastAPI, Form
from fastapi.responses import FileResponse

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
from models import User
from utils import (
    change_file_permission,
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
    if not os.path.exists("data/users"):
        os.makedirs("data/users")
    yield


app = FastAPI(root_path="/api", lifespan=lifespan)


@app.get("/")
def status():
    return {"status": "success", "message": "NaiveFileManager is running."}


@app.post("/user/login")
def user_login(data: Annotated[UserLoginForm, Form()]):
    user = User.load(sha256(data.username))
    if user and User.verify_password(data.password, user.password):
        return {"status": "success", "message": "Login success."}
    return {"status": "failed", "message": "Login failed."}


@app.get("/user/list")
def user_list(page: int = 1, per_page: int = 10):
    return {
        "status": "success",
        "data": [
            {"username": user.username, "base_dir": user.base_dir}
            for user in User.list(page, per_page)
        ],
    }


@app.put("/user/create")
def user_create(data: Annotated[UserCreateForm, Form()]):
    user = User.load(sha256(data.username))
    if user:
        return {"status": "failed", "message": "User already exists."}
    User(data.username, User.hash_password(data.password), data.base_dir).save()
    return {"status": "success", "message": "User created."}


@app.patch("/user/update")
def user_update(data: Annotated[UserUpdateForm, Form()]):
    user = User.load(sha256(data.username))
    if not user:
        return {"status": "failed", "message": "User does not exist."}
    if data.password:
        user.password = User.hash_password(data.password)
    user.base_dir = data.base_dir
    user.save()
    return {"status": "success", "message": "User updated."}


@app.delete("/user/delete")
def user_delete(data: Annotated[UserDeleteForm, Form()]):
    user = User.load(sha256(data.username))
    if not user:
        return {"status": "failed", "message": "User does not exist."}
    user.delete()
    return {"status": "success", "message": "User deleted."}


@app.get("/file/list")
def file_list(path: str, page: int = 1, per_page: int = 10):
    base_dir = "/"
    return {"status": "success", "data": list_files(path, base_dir, page, per_page)}


@app.get("/file/download")
def file_download(path: str):
    base_dir = "/"
    path = sanitize_path(path, base_dir)
    return FileResponse(path)


@app.get("/file/read")
def file_read(path: str, encoding: str = "utf-8"):
    base_dir = "/"
    content = read_file(path, base_dir, encoding)
    if content is None:
        return {"status": "failed", "message": "Read failed."}
    return {"status": "success", "data": content}


@app.patch("/file/write")
def file_write(data: Annotated[FileWriteForm, Form()]):
    base_dir = "/"
    if write_file(data.path, data.content, base_dir, data.encoding):
        return {"status": "success", "message": "Write success."}
    return {"status": "failed", "message": "Write failed."}


@app.patch("/file/permission")
def file_permission(data: Annotated[FilePermissionForm, Form()]):
    base_dir = "/"
    if change_file_permission(data.path, data.mode, data.group, data.owner, base_dir):
        return {"status": "success", "message": "Permission updated."}
    return {"status": "failed", "message": "Permission update failed."}


@app.patch("/file/move")
def file_move(data: Annotated[FileMoveForm, Form()]):
    base_dir = "/"
    if move_file(data.source, data.destination, base_dir):
        return {"status": "success", "message": "Move success."}
    return {"status": "failed", "message": "Move failed."}


@app.delete("/file/delete")
def file_delete(data: Annotated[FileDeleteForm, Form()]):
    base_dir = "/"
    if delete_file(data.path, base_dir):
        return {"status": "success", "message": "Delete success."}
    return {"status": "failed", "message": "Delete failed."}


@app.get("/system/group/list")
def system_group_list():
    return {"status": "success", "data": get_groups_list()}


@app.get("/system/user/list")
def system_user_list():
    return {"status": "success", "data": get_users_list()}
