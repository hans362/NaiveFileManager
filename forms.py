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
