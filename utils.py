import hashlib
import json
import logging
import os
import re
import shutil
from datetime import datetime


def validate_password(password: str) -> str | bool:
    if not password:
        return "密码不能为空"
    if len(password) < 12:
        return "密码长度至少12位"
    if not re.search(r"[A-Z]", password):
        return "密码必须包含大写字母"
    if not re.search(r"[a-z]", password):
        return "密码必须包含小写字母"
    if not re.search(r"\d", password):
        return "密码必须包含数字"
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`\'"\\]', password):
        return "密码必须包含特殊字符"
    return True


def sha256(string: str) -> str:
    return hashlib.sha256(string.encode()).hexdigest()


def get_groups_list() -> list:
    groups = [
        line.split(":")
        for line in open("/etc/group", "r").readlines()
        if not line.strip().startswith("#")
    ]
    return [{"name": group[0], "gid": int(group[2])} for group in groups]


def get_users_list() -> list:
    users = [
        line.split(":")
        for line in open("/etc/passwd", "r").readlines()
        if not line.strip().startswith("#")
    ]
    return [{"name": user[0], "uid": int(user[2])} for user in users]


def list_dir(path: str) -> list:
    dirs = []
    files = []
    for object in os.listdir(path):
        if os.path.isdir(os.path.join(path, object)):
            dirs.append(object)
        else:
            files.append(object)
    dirs.sort()
    files.sort()
    dirs.extend(files)
    return dirs


def sanitize_path(path: str, base_dir: str = "/") -> str:
    if not path.startswith("/"):
        path = "/" + path
    path = os.path.join(base_dir, os.path.normpath(path).lstrip("/"))
    return path


def list_files(
    path: str, base_dir: str = "/", page: int = 1, per_page: int = 15
) -> dict:
    path = sanitize_path(path, base_dir)
    all_files = list_dir(path)
    total = len(all_files)
    files = []

    for file in all_files[(page - 1) * per_page : page * per_page]:
        file = os.path.join(path, file)
        if not os.path.exists(file):
            continue
        try:
            files.append(
                {
                    "name": os.path.basename(file),
                    "size": os.stat(file).st_size,
                    "type": "dir" if os.path.isdir(file) else "file",
                    "target": os.readlink(file) if os.path.islink(file) else None,
                    "permission": oct(os.stat(file).st_mode)[-3:],
                    "gid": os.stat(file).st_gid,
                    "uid": os.stat(file).st_uid,
                    "last_modified": int(os.stat(file).st_mtime),
                }
            )
        except Exception:
            continue

    return {
        "items": files,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def read_file(path: str, base_dir: str = "/", encoding: str = "utf-8") -> str | None:
    path = sanitize_path(path, base_dir)
    if (
        not os.path.exists(path)
        or os.path.isdir(path)
        or os.stat(path).st_size > 5 * 1024 * 1024
    ):
        return None
    try:
        return open(path, "r", encoding=encoding).read()
    except Exception:
        return None


def write_file(
    path: str, content: str, base_dir: str = "/", encoding: str = "utf-8"
) -> bool:
    path = sanitize_path(path, base_dir)
    if not os.path.exists(os.path.dirname(path)) or os.path.isdir(path):
        return False
    try:
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def change_file_permission(
    path: str, mode: int, group: int, owner: int, base_dir: str = "/"
) -> bool:
    path = sanitize_path(path, base_dir)
    if not os.path.exists(path):
        return False
    try:
        os.chmod(path, mode)
        os.chown(path, owner, group)
        return True
    except Exception:
        return False


def move_file(source: str, destination: str, base_dir: str = "/") -> bool:
    source = sanitize_path(source, base_dir)
    destination = sanitize_path(destination, base_dir)
    if not os.path.exists(source):
        return False
    try:
        os.rename(source, destination)
        return True
    except Exception:
        return False


def delete_file(path: str, base_dir: str = "/") -> bool:
    path = sanitize_path(path, base_dir)
    if not os.path.exists(path):
        return False
    try:
        if os.path.islink(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return True
    except Exception:
        return False


def create_file(path: str, type: str, base_dir: str = "/") -> bool:
    path = sanitize_path(path, base_dir)
    if os.path.exists(path):
        return False
    try:
        if type == "file":
            open(path, "w").close()
        elif type == "dir":
            os.makedirs(path)
        return True
    except Exception:
        return False


def audit_log(
    logger: logging.Logger,
    action: str,
    username: str,
    message: str = "",
    success: bool = True,
):
    logger.info(json.dumps([action, username, message, success]))


def list_logs(date: str, page: int = 1, per_page: int = 15) -> list:
    logs = []
    if date == datetime.now().strftime("%Y-%m-%d"):
        date = ""
    else:
        date = "." + date
    if os.path.exists(os.path.join(os.getcwd(), "data/logs", f"app.log{date}")):
        with open(os.path.join(os.getcwd(), "data/logs", f"app.log{date}"), "r") as f:
            lines = f.readlines()[::-1]
            for line in lines[(page - 1) * per_page : page * per_page]:
                line = line.strip().split(" - main - INFO - ")
                audit_log = json.loads(line[1])
                logs.append(
                    {
                        "timestamp": line[0],
                        "action": audit_log[0],
                        "username": audit_log[1],
                        "message": audit_log[2],
                        "success": audit_log[3],
                    }
                )
            return {
                "items": logs,
                "total": len(lines),
                "page": page,
                "per_page": per_page,
            }
    return {
        "items": [],
        "total": 0,
        "page": page,
        "per_page": per_page,
    }


if __name__ == "__main__":
    pass
