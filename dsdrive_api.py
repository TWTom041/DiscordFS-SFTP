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
    """
    A tool to send data to multiple webhooks

    Attributes:
        hooks (list): A list of webhook URLs
        index (int): The index of the current webhook URL
    
    Methods:
        get_hook: Get the current webhook URL
        send: Send data to the current webhook URL
        get: Send a GET request to a URL, handling rate limits and nothing
    """
    def __init__(self, hooks):
        self.hooks = hooks
        self.index = 0

    def get_hook(self):
        """
        Get the current webhook URL
        """
        self.index += 1
        return self.hooks[self.index % len(self.hooks)]
    
    def send(self, *args, **kwargs):
        """
        Send data to the current webhook URL, handling rate limits

        Args:
            *args: Arguments to be passed to requests.post
            **kwargs: Keyword arguments to be passed to requests.post
        
        Returns:
            requests.Response: The response of the request
        """
        kwargs["timeout"] = 10
        try:
            resp = requests.post(self.get_hook(), *args, **kwargs)
        except requests.exceptions.Timeout:
            raise OSError("Connection timed out")
        
        if resp.status_code != 200:
            msg_json = resp.json()
            if resp.status_code == 429:
                retry_after = msg_json["retry_after"]
                time.sleep(retry_after + 0.03)
                return self.send(*args, **kwargs)
            else:
                raise Exception(f"Error sending data : {resp.text}")
        return resp
    
    def get(self, *args, **kwargs):
        """
        Send a GET request to a URL, handling rate limits and nothing

        Args:
            *args: Arguments to be passed to requests.get
            **kwargs: Keyword arguments to be passed to requests.get
        
        Returns:
            requests.Response: The response of the request
        """

        kwargs["timeout"] = 10
        try:
            resp = requests.get(*args, **kwargs)
        except requests.exceptions.Timeout:
            raise OSError("Connection timed out")
        
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
    """
    A file-like object that can be used to read and write files on DSdrive

    Attributes:
        path (str): The path of the file
        dsdrive (DSdriveApi): The DSdriveApi object
        mode (str): The mode of the file
        _read (bool): Whether the file is readable
        _write (bool): Whether the file is writable
    
    Methods:
        readable: Whether the file is readable
        writable: Whether the file is writable
        read: Read the file
        write: Write to the file
        close: Close the file
    """
    def __init__(self, path, dsdrive, mode="r", zero_size=False):
        """
        Create a DSFile object

        Args:
            path (str): The path of the file
            dsdrive (DSdriveApi): The DSdriveApi object
            mode (str): The mode of the file
            zero_size (bool): Whether the file is empty
        """
        super().__init__()
        self.dsdrive: DSdriveApi = dsdrive
        self.path:str = path
        self.mode:str = mode
        self._read:bool = False
        self._write:bool = False
        if "t" in mode:
            raise ValueError("text mode not supported")
        if "r" in mode or "a" in mode:
            self._read = True
            self._write = True
            if not zero_size:
                self.dsdrive.download_file(self.path, self)
            if "+" not in mode:
                self._write = False
            if "r" in mode:
                self.seek(0)
        if "w" in mode or "x" in mode or "a" in mode:
            self._write = True
        if "b" not in mode:
            self.mode += "b"
        # self.seek(0)

    def readable(self) -> bool:
        return self._read
    
    def writable(self) -> bool:
        return self._write
    
    def read(self, size=-1) -> bytes:
        """
        Read the file
        
        Args:
            size (int): The number of bytes to read. If -1, read the whole file
            
        Returns:
            bytes: The bytes read
            
        Raises:
            OSError: If the file is not readable
        """
        if not self._read:
            raise OSError("File not readable")
        return super().read(size)
    
    def write(self, b: bytes) -> int:
        """
        Read the file
        
        Args:
            b (bytes): The bytes to write
            
        Returns:
            int: The number of bytes written
            
        Raises:
            OSError: If the file is not writable
        """
        if not self._write:
            raise OSError("File not writable")
        return super().write(b)

    def truncate(self, size=None):
        original_pos = self.tell()
        if size is None:
            size = self.tell()
        elif size < 0:
            raise ValueError(f"negative size value {size}")

        current_size = self.getbuffer().nbytes

        if size < current_size:
            # If size is smaller than the current size, truncate the buffer
            super().truncate(size)
        elif size > current_size:
            # If size is larger than the current size, extend with null bytes
            super().write(b'\0' * (size - current_size))
        self.seek(original_pos)
        return size

    def close(self):
        """
        Close the file, and send the file to DSdrive if the file is writable
        """
        if self._write:
            # print("Sending file", self.path)
            # Update the URL in the database when the BytesIO is closed
            self.seek(0)
            self._read = True
            self.dsdrive.send_file(self.path, self)
            self._read = False
        
        super().close()


class DSdriveApi:
    """
    A class to interact with Discord's file storage system

    Attributes:
        db (pymongo.database.Database): The database object
        hook (HookTool): The HookTool object
        root_id (bson.objectid.ObjectId): The ID of the root directory
    
    Methods:
        clear: Clear the database
        path_splitter: Split a path into a list of directories
        makedirs: Create directories
        find: Find a path
        send_file: Send a file to DSdrive
        open_binary: Open a file
        get_file_urls: Get the URLs of a file
        download_file: Download a file
        list_dir: List a directory
        remove_file: Remove a file
        remove_dir: Remove a directory
        remove_tree: Remove a tree
        get_info: Get the info of a file or directory
        set_info: Set the info of a file or directory
    """
    def __init__(self, url, hook) -> None:
        """
        Create a DSdriveApi object, creates the root directory if it doesn't exist

        Args:
            url (str): The URL of the MongoDB database
            hook (HookTool): The HookTool object        
        """
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
        """
        Clear the database safely
        """
        root = self.db["tree"].find_one({"name": "", "parent": None})
        self.db["tree"].drop()
        self.db["tree"].insert_one(root)


    def path_splitter(self, path):
        """
        Split a path into a list

        Args:
            path (str): The path to split

        Returns:
            list: The list of directories
        """
        paths = fs.path.relpath(fs.path.normpath(path)).split("/")
        paths = list(filter(None, paths))
        return paths

    def makedirs(self, paths, allow_many=False, exist_ok=False):
        """
        Create directories

        Args:
            paths (list): The list of directories to create
            allow_many (bool): Whether to allow creating multiple directories
            exist_ok (bool): Whether to allow creating directories that already exist
        
        Returns:
            Union[int, ObjectID]: The ID of the last directory created, or an error code
        """
        parent_id = self.root_id
        already_exist_counter = 0
        resource_not_found_counter = 0
        for i in paths:
            fs = self.db["tree"].find_one(
                {"name": i, "parent": parent_id}
            )
            if fs:
                if fs["type"] != "folder":
                    return 3  # Path already exists, but is not a folder
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
        """
        Find a path

        Args:
            paths (list): The list of directories to find
            return_obj (bool): Whether to return the object found
        
        Returns:
            Union[int, ObjectID, dict]: The ID of the last directory found, or a dict representing object found if return_obj is True, or an error code
        """
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
        """
        Send a file to Didcord

        Args:
            path (str): The path to send the file to
            file_obj (Union[str, BytesIO, DSFile]): The file to send
        """

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
        
        paths = self.path_splitter(path)
        parent_id = self.makedirs(paths[:-1], allow_many=True, exist_ok=True)
        urls = []
        chunk_sizes = []

        while chunk:
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
                        {"$set": {"urls": urls, "chunk_sizes": chunk_sizes, "details.modified": time.time(), "details.size": size}},
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
        """
        Open a file

        Args:
            path (str): The path of the file
            mode (str): The mode of the file
        
        Returns:
            DSFile: The file-like object
        """
        # check if the file size is 0
        stat, fn = self.find(self.path_splitter(path), return_obj=True)
        if stat == 0:
            if fn["type"] == "folder":
                raise OSError("Path is a folder")
            if fn["details"]["size"] == 0:
                return DSFile(path, self, mode, zero_size=True)
        else:
            # file does not exist, size is 0
            return DSFile(path, self, mode, zero_size=True)
        return DSFile(path, self, mode)

    def get_file_urls(self, path):
        """
        Get the URLs of a file

        Args:
            path (str): The path of the file
        
        Returns:
            list: The list of URLs of the file
        """
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
        """
        Download a file from Discord to the local filesystem

        Args:
            path_src (str): The path of the file on Discord
            path_dst (str): The path of the file on the local filesystem
        """
        if path_dst is None:
            path_dst = path_src
        urls = self.get_file_urls(path_src)
        if isinstance(path_dst, str):
            if not os.path.exists(path_dst):
                with open(path_dst, "x") as file:
                    pass
            with open(path_dst, "wb") as file:
                for i, url in enumerate(urls):
                    resp = self.hook.get(url)
                    print(resp.content)
                    file.write(resp.content)
        elif isinstance(path_dst, BytesIO) or isinstance(path_dst, DSFile):
            for i, url in enumerate(urls):
                resp = self.hook.get(url)
                # print(resp.content)
                path_dst.write(resp.content)

    def list_dir(self, path):
        """
        List a directory

        Args:
            path (str): The path of the directory

        Returns:
            Union[bool, NoneType]: Whether the path is a directory, or an error code
            Union[list, int]: A list of files and directories, or an error code
        """
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
        """
        Remove a file

        Args:
            path (str): The path of the file

        Returns:
            int: An error code, or 0 if successful
        """
        paths = self.path_splitter(path)
        stat, fn = self.find(paths, return_obj=True)
        if stat != 0:
            return 1  # Path not found
        if fn["type"] != "file":
            return 2  # Path is not a file
        self.db["tree"].delete_one({"_id": fn["_id"]})
        return 0

    def remove_dir(self, path):
        """
        Remove a directory
        
        Args:
            path (str): The path of the directory

        Returns:
            int: An error code, or 0 if successful
        """
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
        """
        Remove a tree, not implemented yet

        Args:
            path (str): The path of the tree

        Returns:
            int: An error code, or 0 if successful
        """
        paths = self.path_splitter(path)
        if len(paths) == 0:
            return 4  # Root directory cannot be deleted
        stat, parent_id = self.find(paths[:-1])
        if stat != 0:
            return 1
        fn = self.db["tree"].find_one(
            {"name": paths[-1], "parent": parent_id}
        )
    
    def rename(self, path_src, path_dst, overwrite=False, create_dirs=False, preserve_timestamps=False):
        """
        Rename a file or directory

        Args:
            path_src (str): The path of the file or directory
            path_dst (str): The new path of the file or directory

        Returns:
            int: An error code, or 0 if successful
        """
        paths_src = self.path_splitter(path_src)
        paths_dst = self.path_splitter(path_dst)
        
        if len(paths_src) == 0 or len(paths_dst) == 0:
            return 2  # Root directory is not a file
        stat, src_fn = self.find(paths_src, return_obj=True)
        if stat != 0:
            return 1  # Path not found
        
        stat, parent_id_dst = self.find(paths_dst[:-1])
        if stat != 0:
            if create_dirs:
                parent_id_dst = self.makedirs(paths_dst[:-1], allow_many=True, exist_ok=True)
            else:
                return 1  # Path not found
        
        if not (src_fn["type"] == "file"):
            return 2  # src is a folder
        
        dst_fn = self.db["tree"].find_one(
            {"name": paths_dst[-1], "parent": parent_id_dst}
        )
        if dst_fn:
            if not overwrite:
                return 3  # Path already exists
            if not (dst_fn["type"] == "file"):
                return 2  # src and dst are not both files
            self.db["tree"].delete_one({"_id": dst_fn["_id"]})
                
        self.db["tree"].update_one(
            {"_id": src_fn["_id"]}, {"$set": {"name": paths_dst[-1], "parent": parent_id_dst}}
        )
        if not preserve_timestamps:
            self.db["tree"].update_one(
                {"_id": src_fn["_id"]}, {"$set": {"details.modified": time.time()}}
            )
        return 0
    

    def copy(self, path_src, path_dst, overwrite=False, create_dirs=False, preserve_timestamps=False):
        """
        Copy a file or directory

        Args:
            path_src (str): The path of the file or directory
            path_dst (str): The new path of the file or directory

        Returns:
            int: An error code, or 0 if successful
        """
        paths_src = self.path_splitter(path_src)
        paths_dst = self.path_splitter(path_dst)
        
        if len(paths_dst) == 0:
            return 2  # Root directory is not a file
        stat, src_fn = self.find(paths_src, return_obj=True)
        if stat != 0:
            return 1  # Path not found
        
        stat, parent_id_dst = self.find(paths_dst[:-1])
        if stat != 0:
            if create_dirs:
                parent_id_dst = self.makedirs(paths_dst[:-1], allow_many=True, exist_ok=True)
            else:
                return 1  # Path not found
        
        if not (src_fn["type"] == "file"):
            return 2  # src is a folder
        
        dst_fn = self.db["tree"].find_one(
            {"name": paths_dst[-1], "parent": parent_id_dst}
        )
        if dst_fn:
            if not overwrite:
                return 3  # Path already exists
            if not (dst_fn["type"] == "file"):
                return 2  # src and dst are not both files
            self.db["tree"].delete_one({"_id": dst_fn["_id"]})

        self.db["tree"].insert_one(
            {
                "name": paths_dst[-1],
                "type": src_fn["type"],
                "urls": src_fn["urls"].copy(),
                "chunk_sizes": src_fn["chunk_sizes"].copy(),
                "access": src_fn["access"],
                "details": src_fn["details"],
                "parent": parent_id_dst,
            }
        )
        if not preserve_timestamps:
            self.db["tree"].update_one(
                {"_id": src_fn["_id"]}, {"$set": {"details.modified": time.time()}}
            )
        return 0


    def get_info(self, path):
        """
        Get the info of a file or directory

        Args:
            path (str): The path of the file or directory

        Returns:
            int: An error code, or 0 if successful
            dict: The info of the file or directory
        """
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
    
    def _set_info_by_fn(self, fn, info):
        out_info = {}
        if "access" in info:
            out_info["access"] = {**fn["access"], **info["access"]}

        if "details" in info:
            out_info["details"] = {**fn["details"], **info["details"]}
        
        if "basic" in info:
            if "name" in info["basic"]:
                out_info["name"] = info["basic"]["name"]

            if "is_dir" in info["basic"]:
                if info["basic"]["is_dir"]:
                    out_info["type"] = "folder"

                else:
                    out_info["type"] = "file"

        self.db["tree"].update_one({"_id": fn["_id"]}, {"$set": out_info})
        return 0

    def set_info(self, path, info):
        """
        Set the info of a file or directory

        Args:
            path (str): The path of the file or directory
            info (dict): The info to set
        
        Returns:
            int: An error code, or 0 if successful
        """

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
        
        return self._set_info_by_fn(fn, info)
        


if __name__ == "__main__":
    with open("webhooks.txt", "r") as file:
        webhook_urls = [i for i in file.read().split("\n") if i]

    hook = HookTool(webhook_urls)
    dsdrive_api = DSdriveApi("mongodb://localhost:27017/", hook)

    with dsdrive_api.open_binary("test/testfile.txt", "w") as file:
        file.write(b"hello world")
    with dsdrive_api.open_binary("test/testfile.txt", "w") as file:
        file.write(b"not hello w")
    with dsdrive_api.open_binary("test/testfile.txt", "r") as file:
        print(file.read())
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
