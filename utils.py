import os
import hashlib


def sha256(string: str) -> str:
    return hashlib.sha256(string.encode()).hexdigest()


def get_groups_list() -> list:
    groups = [line.split(":") for line in open("/etc/group", "r").readlines()]
    return [{"name": group[0], "gid": int(group[2])} for group in groups]


def get_users_list() -> list:
    users = [line.split(":") for line in open("/etc/passwd", "r").readlines()]
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
        return ""
    path = os.path.join(base_dir, os.path.normpath(path))
    return path


def list_files(
    path: str, base_dir: str = "/", page: int = 1, per_page: int = 10
) -> list:
    path = sanitize_path(path, base_dir)
    files = []
    for file in list_dir(path)[(page - 1) * per_page : page * per_page]:
        file = os.path.join(path, file)
        files.append(
            {
                "name": os.path.basename(file),
                "size": os.stat(file).st_size,
                "type": (
                    "dir"
                    if os.path.isdir(file)
                    else ("link" if os.path.islink(file) else "file")
                ),
                "gid": os.stat(file).st_gid,
                "uid": os.stat(file).st_uid,
                "last_modified": int(os.stat(file).st_mtime),
            }
        )
    return files


def read_file(path: str, base_dir: str = "/") -> str:
    if not path.startswith("/"):
        return ""
    path = os.path.join(base_dir, os.path.normpath(path))
    if not os.path.isfile(path):
        return ""
    return open(path, "r").read()


if __name__ == "__main__":
    print(os.listdir("."))
    print(list_dir("."))
