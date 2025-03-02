from typing import Annotated

from fastapi import FastAPI, Form
from models import User
from forms import UserLoginForm, UserCreateForm, UserUpdateForm, UserDeleteForm
from utils import sha256, list_files

app = FastAPI(root_path="/api")


@app.get("/")
def status():
    return {"status": "success", "message": "FileManager is running."}


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
    return {"status": "success", "data": list_files(path, page=page, per_page=per_page)}
