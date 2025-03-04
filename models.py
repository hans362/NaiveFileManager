import json
import os
from typing import Self

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, Request

from utils import list_dir, sha256


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
    def list(self, page: int = 1, per_page: int = 15) -> dict:
        return {
            "items": [
                self.load(object)
                for object in list_dir(self.get_data_dir())[
                    (page - 1) * per_page : page * per_page
                ]
                if object is not None
            ],
            "total": len(list_dir(self.get_data_dir())),
            "page": page,
            "per_page": per_page,
        }


class User(AbstractModel):
    def __init__(
        self, username: str, password: str, base_dir: str = "/", role: str = "user"
    ) -> None:
        super().__init__()
        self.id = sha256(username)
        self.username = username
        self.password = password
        self.base_dir = base_dir
        self.role = role

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

    @staticmethod
    def is_authenticated(request: Request):
        if not request.session.get("uid") or not User.load(request.session.get("uid")):
            request.session.clear()
            raise HTTPException(status_code=401, detail="Unauthenticated")

    @staticmethod
    def is_admin(request: Request):
        if not User.load(request.session.get("uid")).role == "admin":
            raise HTTPException(status_code=403, detail="Unauthorized")
