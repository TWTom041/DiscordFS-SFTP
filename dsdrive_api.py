# from discord import SyncWebhook
# import discord
import requests
import os
from io import BytesIO
from pymongo import MongoClient
import pymongo
from hashlib import md5
from zlib import crc32


chunk_size = 24 * 1024 * 1024  # MB


# webhook = SyncWebhook.from_url(webhook_url)
# webhook.send("Hello World")

class HookIter:
    def __init__(self, hooks):
        self.hooks = hooks
        self.index = 0

    def get_hook(self):
        self.index += 1
        return self.hooks[self.index % len(self.hooks)]


class DSdriveApi:
    def __init__(self, url, hook) -> None:
        client = MongoClient(url)
        self.db = client["dsdrive"]
        self.hook = hook

    def makedirs(self, paths, allow_many=False):
        parent_id = "/"
        counter = 0
        for i in paths:
            fs = self.db["tree"].find_one({"name": i, "parent": parent_id, "type": "folder"})
            path_now = os.path.join(parent_id, i)
            if fs:
                parent_id = fs["_id"]
            else:
                if not allow_many and counter > 0:
                    return 1  # Only one directory allowed, resource not found
                hashes = md5(path_now.encode()).hexdigest() + "-" + crc32(path_now.encode()).to_bytes(4, "big").hex()
                o = self.db["tree"].insert_one({"name": i, "parent": parent_id, "type": "folder", "hashes": hashes, "serial": 0})
                parent_id = o.inserted_id
                counter += 1
        if counter == 0:
            return 2  # No directories created, already exists
        return parent_id


    def finddirs(self, paths):
        # paths = os.path.normpath(path).split(os.sep)
        parent_id = "/"
        for i in paths:
            fs = self.db["tree"].find_one({"name": i, "parent": parent_id, "type": "folder"})
            path_now = os.path.join(parent_id, i)
            if fs:
                parent_id = fs["_id"]
                continue
            else:
                return None
        return parent_id


    def send_file(self, path):
        with open(path, "rb") as file:
            chunk = file.read(chunk_size)
            serial = 0
            paths = os.path.normpath(path).split(os.sep)
            paths = list(filter(None, paths))
            parent_id = self.makedirs(paths[:-1])
            while chunk:
                with BytesIO(chunk) as buffer:
                    fname = md5(chunk).hexdigest() + "-" + crc32(chunk).to_bytes(4, "big").hex()
                    resp = requests.post(self.hook.get_hook(), files={"file": (fname, buffer)})
                    try:
                        # dirname = os.path.dirname(path)

                        finder = self.db["tree"].find_one({"name": paths[-1], "parent": parent_id, "serial": serial})
                        if finder:
                            if finder["type"] == "file":
                                print(resp.json())
                                self.db["tree"].update_one({"_id": finder["_id"]}, {"$set": {"url": resp.json()["attachments"][0]["url"]}})
                            else:
                                print("File already exists, and is a folder, skipping")
                        else:
                            self.db["tree"].insert_one({"name": paths[-1], "type": "file", "hashes": fname, "url": resp.json()["attachments"][0]["url"], "parent": parent_id, "serial": serial})
                    except Exception as e:
                        print("Error sending file")
                        print(e)
                        print(resp.text)

                serial += 1
                chunk = file.read(chunk_size)
            
            # clear all the things that are greater than serial
            self.db["tree"].delete_many({"parent": parent_id, "serial": {"$gte": serial}})


    def get_file_urls(self, path):
        paths = os.path.normpath(path).split(os.sep)
        paths = list(filter(None, paths))
        parent_id = self.finddirs(paths[:-1])
        if not parent_id:
            return None
        fn = self.db["tree"].find({"name": paths[-1], "parent": parent_id, "type": "file"}).sort("serial", pymongo.ASCENDING)
        if fn:
            return [i["url"] for i in fn]
        else:
            return None
        

    def download_file(self, path_src, path_dst=None):
        if path_dst is None:
            path_dst = path_src
        urls = self.get_file_urls(path_src)
        print(urls)
        if isinstance(path_dst, str):    
            if not os.path.exists(path_dst):
                with open(path_dst, "x") as file:
                    pass
            with open(path_dst, "wb") as file:
                for i, url in enumerate(urls):
                    resp = requests.get(url)
                    file.write(resp.content)
        elif isinstance(path_dst, BytesIO):
            for i, url in enumerate(urls):
                resp = requests.get(url)
                path_dst.write(resp.content)


    def list_dir(self, path):
        paths = os.path.normpath(path).split(os.sep)
        paths = list(filter(None, paths))
        parent_id = self.finddirs(paths)
        if not parent_id:
            return None, 1  # Path not found
        if self.db["tree"].find_one({"name": paths[-1], "parent": parent_id, "type": "file"}):
            return None, 2  # Path is a file
        
        fn = self.db["tree"].find({"parent": parent_id, "serial": 0})
        return True, fn
    
    def remove_file(self, path):
        paths = os.path.normpath(path).split(os.sep)
        paths = list(filter(None, paths))
        parent_id = self.finddirs(paths[:-1])
        if not parent_id:
            return 1  # Path not found
        fn = self.db["tree"].find({"name": paths[-1], "parent": parent_id, "type": "file"})
        if not fn:
            return 2  # File not found
        self.db["tree"].delete_many({"name": paths[-1], "parent": parent_id, "type": "file"})
        return 0
    
    def remove_dir(self, path):
        paths = os.path.normpath(path).split(os.sep)
        paths = list(filter(None, paths))
        if len(paths) == 0:
            return 4  # Root directory cannot be deleted
        parent_id = self.finddirs(paths[:-1])
        if not parent_id:
            return 1  # Path not found
        fn = self.db["tree"].find_one({"name": paths[-1], "parent": parent_id, "serial": 0})
        if not fn:
            return 1  # Path not found
        # check if is folder
        if fn["type"] != "folder":
            return 2  # Path is not a folder
        if self.db["tree"].find_one({"parent": fn["_id"]}):
            return 3  # Folder not empty
        self.db["tree"].delete_one({"_id": fn["_id"]})

    def remove_tree(self, path):
        paths = os.path.normpath(path).split(os.sep)
        paths = list(filter(None, paths))
        if len(paths) == 0:
            return 4  # Root directory cannot be deleted
        parent_id = self.finddirs(paths[:-1])
        if not parent_id:
            return 1
        fn = self.db["tree"].find_one({"name": paths[-1], "parent": parent_id, "serial": 0})
        


with open("webhooks.txt", "r") as file:
    webhook_urls = [i for i in file.read().split("\n") if i]

hook = HookIter(webhook_urls)
dsdrive_api = DSdriveApi("mongodb://localhost:27017/", hook)

dsdrive_api.send_file("test/test_3mb.mp4")
# urls = get_file_urls("test/test_3mb.mp4")
dsdrive_api.download_file("test/test_3mb.mp4", "test/test_3mb2.mp4")

print(list(dsdrive_api.list_dir("test")))


