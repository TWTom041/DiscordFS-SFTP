# from discord import SyncWebhook
# import discord
import requests
import os
from io import BytesIO
from pymongo import MongoClient
import pymongo
from hashlib import md5
from zlib import crc32
import time
import threading
import array
import fs.path


chunk_size = 24 * 1024 * 1024  # MB


class HookTool:
    def __init__(self, hooks):
        self.hooks = hooks
        self.index = 0

    def get_hook(self):
        self.index += 1
        return self.hooks[self.index % len(self.hooks)]
    
    def send(self, *args, **kwargs):
        resp = requests.post(self.get_hook(), *args, **kwargs)
        if resp.status_code != 200:
            msg_json = resp.json()
            if resp.status_code == 429:
                retry_after = msg_json["retry_after"]
                time.sleep(retry_after + 0.1)
                return self.send(*args, **kwargs)
            else:
                raise Exception(f"Error sending data : {resp.text}")
        return resp
    
    def get(self, *args, **kwargs):
        resp = requests.get(*args, **kwargs)
        if resp.status_code != 200:
            msg_json = resp.json()
            if resp.status_code == 429:
                retry_after = msg_json["retry_after"]
                time.sleep(retry_after + 0.1)
                return self.get(*args, **kwargs)
            else:
                raise Exception(f"Error sending data : {resp.text}")
        if len(resp.content) == 0:
            time.sleep(0.1)
            return self.get(*args, **kwargs)
        return resp


class DSFile(BytesIO):
    def __init__(self, url, path, dsdrive, mode="r"):
        super().__init__()
        self.url:str = url
        self.dsdrive: DSdriveApi = dsdrive
        self.path:str = path
        self.mode:str = mode
        self._read:bool = False
        self._write:bool = False
        if "r" in mode:
            self._read = True
            self._write = True
            self.dsdrive.download_file(self.path, self)
            if "+" not in mode:
                self._write = False
            self.seek(0)
        if "w" in mode or "x" in mode or "a" in mode:
            self._write = True

    def readable(self) -> bool:
        return self._read
    
    def writable(self) -> bool:
        return self._write
    
    def read(self, size=-1) -> bytes:
        if not self._read:
            raise OSError("File not readable")
        return super().read(size)
    
    def write(self, b: bytes) -> int:
        if not self._write:
            raise OSError("File not writable")
        return super().write(b)

    def close(self):
        if self._write:
            # print("Sending file", self.path)
            # Update the URL in the database when the BytesIO is closed
            self.seek(0)
            self._read = True
            self.dsdrive.send_file(self.path, self)
            self._read = False
        
        super().close()


class DSdriveApi:
    def __init__(self, url, hook) -> None:
        client = MongoClient(url)
        self.db = client["dsdrive"]
        self.hook: HookTool = hook
        root = self.db["tree"].find_one({"name": "", "parent": None})
        if not root:
            root = self.db["tree"].insert_one(
                {
                    "name": "",
                    "parent": None,
                    "type": "folder",
                    "access": {
                        "group": "staff",
                        "permissions": [
                            "g_r",
                            "g_w",
                            "g_x",
                            "u_r",
                            "u_w",
                            "u_x",
                            "o_r",
                            "o_w",
                            "o_x",
                        ],
                        "user": "root",
                    },
                    "details": {
                        "accessed": time.time(),
                        "created": time.time(),
                        "metadata_changed": time.time(),
                        "modified": time.time(),
                        "size": 0,
                        "type": 1,  # Folder
                    },
                }
            )
            self.root_id = root.inserted_id
        else:
            self.root_id = root["_id"]
        
        self.db["tree"].create_index("parent")

    def clear(self):
        root = self.db["tree"].find_one({"name": "", "parent": None})
        self.db["tree"].drop()
        self.db["tree"].insert_one(root)


    def path_splitter(self, path):
        paths = fs.path.relpath(fs.path.normpath(path)).split("/")
        return paths

    def makedirs(self, paths, allow_many=False, exist_ok=False):
        parent_id = self.root_id
        already_exist_counter = 0
        resource_not_found_counter = 0
        for i in paths:
            fs = self.db["tree"].find_one(
                {"name": i, "parent": parent_id, "type": "folder"}
            )
            if fs:
                parent_id = fs["_id"]
                resource_not_found_counter += 1
            else:
                if not allow_many and len(paths) - resource_not_found_counter > 1:
                    return 1  # Only one directory allowed, resource not found
                o = self.db["tree"].insert_one(
                    {
                        "name": i,
                        "parent": parent_id,
                        "type": "folder",
                        "access": {
                            "group": "staff",
                            "permissions": [
                                "g_r",
                                "g_w",
                                "g_x",
                                "u_r",
                                "u_w",
                                "u_x",
                                "o_r",
                                "o_w",
                                "o_x",
                            ],
                            "user": "root",
                        },
                        "details": {
                            "accessed": time.time(),
                            "created": time.time(),
                            "metadata_changed": time.time(),
                            "modified": time.time(),
                            "size": 0,
                            "type": 1,  # Folder
                        },
                    }
                )
                parent_id = o.inserted_id
                already_exist_counter += 1
        if (not exist_ok) and already_exist_counter == 0:
            return 2  # No directories created, already exists
        return parent_id

    def find(self, paths, return_obj=False):
        # paths = os.path.normpath(path).split(os.sep)
        parent_id = self.root_id
        for i, j in zip(paths, range(len(paths), 0, -1)):
            fs = self.db["tree"].find_one({"name": i, "parent": parent_id})
            if fs:
                parent_id = fs["_id"]
                continue
            else:
                if j == 1:
                    return 1, None  # Path not found, but at the end
                return 2, None  # Path not found, and not at the end
        if paths == []:  # Root directory
            fs = self.db["tree"].find_one({"_id": self.root_id})
            parent_id = self.root_id
        if return_obj:
            return 0, fs
        return 0, parent_id

    def send_file(self, path, file_obj=None):
        # with open(path, "rb") as file:

        if file_obj is None:
            file = open(path, "rb")
            size = os.path.getsize(path)
        else:
            if isinstance(file_obj, BytesIO) or isinstance(file_obj, DSFile):
                file = file_obj
                size = file_obj.getbuffer().nbytes
            elif isinstance(file_obj, str):
                file = open(file_obj, "rb")
                size = os.path.getsize(file_obj)
            else:
                raise TypeError("file_obj must be a BytesIO or str")

        chunk = file.read(chunk_size)
        serial = 0
        
        paths = self.path_splitter(path)
        parent_id = self.makedirs(paths[:-1], allow_many=True, exist_ok=True)
        urls = []
        chunk_sizes = []

        while chunk or serial == 0:
            with BytesIO(chunk) as buffer:
                fname = (
                    md5(chunk).hexdigest() + "-" + crc32(chunk).to_bytes(4, "big").hex()
                )
                resp = self.hook.send(
                    files={"file": (fname, buffer)}
                )
                urls.append(resp.json()["attachments"][0]["url"])
                chunk_sizes.append(len(chunk))
                
            chunk = file.read(chunk_size)
            serial += 1
        try:
            # dirname = os.path.dirname(path)

            finder = self.db["tree"].find_one(
                {"name": paths[-1], "parent": parent_id}
            )
            if finder:
                if finder["type"] == "file":
                    # print(resp.json())
                    self.db["tree"].update_one(
                        {"_id": finder["_id"]},
                        {"$set": {"urls": urls, "chunk_sizes": chunk_sizes}},
                    )
                else:
                    print("File already exists, and is a folder, skipping")
            else:
                info = {
                    "name": paths[-1],
                    "type": "file",
                    # "hashes": fname,
                    "urls": urls,
                    "parent": parent_id,
                    "chunk_sizes": chunk_sizes,
                }
                info["access"] = {
                    "group": "staff",
                    "permissions": [
                        "g_r",
                        "g_w",
                        "g_x",
                        "u_r",
                        "u_w",
                        "u_x",
                        "o_r",
                        "o_w",
                        "o_x",
                    ],
                    "user": "root",
                }
                info["details"] = {
                    "accessed": time.time(),
                    "created": time.time(),
                    "metadata_changed": time.time(),
                    "modified": time.time(),
                    "size": size,
                    "type": 2,  # File
                }
                self.db["tree"].insert_one(info)
        except Exception as e:
            print("Error sending file")
            print(e)
            print(resp.text)

        if file_obj is None:
            file.close()

    def open_binary(self, path, mode):
        # check if the file size is 0
        stat, fn = self.find(self.path_splitter(path), return_obj=True)
        if stat == 0:
            if fn["type"] == "folder":
                raise OSError("Path is a folder")
            if fn["details"]["size"] == 0:
                return DSFile([], path, self, mode)
        return DSFile(self.get_file_urls(path), path, self, mode)

    def get_file_urls(self, path):
        paths = self.path_splitter(path)

        stat, fn = self.find(paths, return_obj=True)
        if stat != 0:
            return None
        if fn:
            urls = fn["urls"]
            # print(urls)
            return urls
        else:
            return None

    def download_file(self, path_src, path_dst=None):
        if path_dst is None:
            path_dst = path_src
        urls = self.get_file_urls(path_src)
        # print(urls)
        if isinstance(path_dst, str):
            if not os.path.exists(path_dst):
                with open(path_dst, "x") as file:
                    pass
            with open(path_dst, "wb") as file:
                for i, url in enumerate(urls):
                    resp = self.hook.get(url)
                    file.write(resp.content)
        elif isinstance(path_dst, BytesIO) or isinstance(path_dst, DSFile):
            for i, url in enumerate(urls):
                resp = self.hook.get(url)
                path_dst.write(resp.content)

    def list_dir(self, path):
        paths = self.path_splitter(path)
        if paths == []:  # Root directory
            return True, self.db["tree"].find({"parent": self.root_id})
        stat, parent = self.find(paths, return_obj=True)
        if stat != 0:
            return None, 1  # Path not found
        if parent["type"] == "file":
            return None, 2  # Path is a file

        fn = self.db["tree"].find({"parent": parent["_id"]})
        return True, fn

    def remove_file(self, path):
        paths = self.path_splitter(path)
        stat, fn = self.find(paths, return_obj=True)
        if stat != 0:
            return 1  # Path not found
        if fn["type"] != "file":
            return 2  # Path is not a file
        self.db["tree"].delete_one({"_id": fn["_id"]})
        return 0

    def remove_dir(self, path):
        paths = self.path_splitter(path)
        if len(paths) == 0:
            return 4  # Root directory cannot be deleted
        stat, parent_id = self.find(paths[:-1])
        if stat != 0:
            return 1  # Path not found
        fn = self.db["tree"].find_one(
            {"name": paths[-1], "parent": parent_id}
        )
        if not fn:
            return 1  # Path not found
        # check if is folder
        if fn["type"] != "folder":
            return 2  # Path is not a folder
        if self.db["tree"].find_one({"parent": fn["_id"]}):
            return 3  # Folder not empty
        self.db["tree"].delete_one({"_id": fn["_id"]})

    def remove_tree(self, path):
        paths = self.path_splitter(path)
        if len(paths) == 0:
            return 4  # Root directory cannot be deleted
        stat, parent_id = self.find(paths[:-1])
        if stat != 0:
            return 1
        fn = self.db["tree"].find_one(
            {"name": paths[-1], "parent": parent_id}
        )

    def get_info(self, path):
        paths = self.path_splitter(path)
        if paths == []:  # Root directory
            fn = self.db["tree"].find_one({"_id": self.root_id})
            return 0, {
                "access": fn["access"],
                "basic": {"name": fn["name"], "is_dir": True},
                "details": fn["details"],
            }

        stat, fn = self.find(paths, return_obj=True)
        if stat != 0:
            return 1, None  # Path not found
        raw_info = {
            "access": fn["access"],
            "basic": {
                "name": fn["name"],
                "is_dir": True if fn["type"] == "folder" else False,
            },
            "details": fn["details"],
        }
        return 0, raw_info

    def set_info(self, path, info):
        paths = self.path_splitter(path)
        if paths == []:  # Root directory
            fn = self.db["tree"].find_one({"_id": self.root_id})
        else:
            stat, parent_id = self.find(paths[:-1])
            if stat != 0:
                return 1

            fn = self.db["tree"].find_one(
                {"name": paths[-1], "parent": parent_id}
            )
            if not fn:
                return 1
        if "access" in info:
            self.db["tree"].update_one(
                {"_id": fn["_id"]},
                {"$set": {"access": {**fn["access"], **info["access"]}}},
            )
        if "details" in info:
            self.db["tree"].update_one(
                {"_id": fn["_id"]},
                {"$set": {"details": {**fn["access"], **info["details"]}}},
            )
        if "basic" in info:
            if "name" in info["basic"]:
                self.db["tree"].update_one(
                    {"_id": fn["_id"]}, {"$set": {"name": info["basic"]["name"]}}
                )
            if "is_dir" in info["basic"]:
                if info["basic"]["is_dir"]:
                    self.db["tree"].update_one(
                        {"_id": fn["_id"]}, {"$set": {"type": "folder"}}
                    )
                else:
                    self.db["tree"].update_one(
                        {"_id": fn["_id"]}, {"$set": {"type": "file"}}
                    )
        return 0


if __name__ == "__main__":
    with open("webhooks.txt", "r") as file:
        webhook_urls = [i for i in file.read().split("\n") if i]

    hook = HookTool(webhook_urls)
    dsdrive_api = DSdriveApi("mongodb://localhost:27017/", hook)
    dsdrive_api.path_splitter("./test/aaa.txt")
    # a = dsdrive_api.open_binary("test/aaa.txt", "w")
    # a.write(b"hello world")
    # a.seek(0)
    # a._read = True
    # print(a.read())
    # a._read = False
    # a.close()

    # dsdrive_api.send_file("test/test_3mb.mp4")
    # dsdrive_api.send_file("test/testfile.txt")
    # dsdrive_api.send_file("test/tta/t112.mp4")
    # # urls = get_file_urls("test/test_3mb.mp4")
    # dsdrive_api.download_file("test/test_3mb.mp4", "test/test_3mb2.mp4")
    # print(list(dsdrive_api.list_dir("test")[1]))
