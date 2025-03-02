from pydantic import BaseModel


class UserLoginForm(BaseModel):
    username: str
    password: str


class UserCreateForm(BaseModel):
    username: str
    password: str
    base_dir: str = "/"


class UserUpdateForm(BaseModel):
    username: str
    password: str = None
    base_dir: str = "/"


class UserDeleteForm(BaseModel):
    username: str


class FileWriteForm(BaseModel):
    path: str
    content: str
    encoding: str = "utf-8"


class FilePermissionForm(BaseModel):
    path: str
    mode: int
    group: int
    owner: int


class FileMoveForm(BaseModel):
    source: str
    destination: str


class FileDeleteForm(BaseModel):
    path: str
