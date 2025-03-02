from typing import Self
from utils import sha256
import os
import json
from utils import list_dir
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class AbstractModel:
    def __init__(self) -> None:
        if not os.path.exists(self.get_data_dir()):
            os.makedirs(self.get_data_dir())

    @classmethod
    def get_data_dir(self) -> str:
        return os.path.join(os.getcwd(), os.path.join("data", self.__name__.lower()))

    @classmethod
    def load(self, id: str) -> Self | None:
        try:
            data = json.load(open(os.path.join(self.get_data_dir(), id), "r"))
            data.pop("id", None)
            return self(**data)
        except FileNotFoundError:
            return None

    def save(self) -> None:
        return json.dump(
            self.__dict__, open(os.path.join(self.get_data_dir(), self.id), "w")
        )

    def delete(self) -> None:
        return os.remove(os.path.join(self.get_data_dir(), self.id))

    @classmethod
    def list_all(self) -> list[Self]:
        return [
            self.load(object)
            for object in list_dir(self.get_data_dir())
            if object is not None
        ]

    @classmethod
    def list(self, page: int = 1, per_page: int = 10) -> list[Self]:
        return [
            self.load(object)
            for object in list_dir(self.get_data_dir())[
                (page - 1) * per_page : page * per_page
            ]
            if object is not None
        ]


class User(AbstractModel):
    def __init__(self, username: str, password: str, base_dir: str = "/") -> None:
        super().__init__()
        self.id = sha256(username)
        self.username = username
        self.password = password
        self.base_dir = base_dir

    @staticmethod
    def hash_password(password: str) -> str:
        return PasswordHasher().hash(password)

    @staticmethod
    def verify_password(password: str, hash: str) -> bool:
        try:
            PasswordHasher().verify(hash, password)
            return True
        except VerifyMismatchError:
            return False
