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
client = MongoClient("mongodb://localhost:27017/")

db = client["dsdrive"]

# webhook = SyncWebhook.from_url(webhook_url)
# webhook.send("Hello World")

class HookIter:
    def __init__(self, hooks):
        self.hooks = hooks
        self.index = 0

    def get_hook(self):
        self.index += 1
        return self.hooks[self.index % len(self.hooks)]


def makedirs(paths):
    parent_id = "/"
    for i in paths:
        fs = db["tree"].find_one({"name": i, "parent": parent_id, "type": "folder"})
        path_now = os.path.join(parent_id, i)
        if fs:
            parent_id = fs["_id"]
        else:
            hashes = md5(path_now.encode()).hexdigest() + "-" + crc32(path_now.encode()).to_bytes(4, "big").hex()
            o = db["tree"].insert_one({"name": i, "parent": parent_id, "type": "folder", "hashes": hashes, "serial": 0})
            parent_id = o.inserted_id          
    return parent_id


def finddirs(paths):
    # paths = os.path.normpath(path).split(os.sep)
    parent_id = "/"
    for i in paths:
        fs = db["tree"].find_one({"name": i, "parent": parent_id, "type": "folder"})
        path_now = os.path.join(parent_id, i)
        if fs:
            parent_id = fs["_id"]
            continue
        else:
            return None
    return parent_id


def send_file(hook, path):
    with open(path, "rb") as file:
        chunk = file.read(chunk_size)
        serial = 0
        paths = os.path.normpath(path).split(os.sep)
        print(paths)
        parent_id = makedirs(paths[:-1])
        while chunk:
            with BytesIO(chunk) as buffer:
                fname = md5(chunk).hexdigest() + "-" + crc32(chunk).to_bytes(4, "big").hex()
                resp = requests.post(hook.get_hook(), files={"file": (fname, buffer)})
                try:
                    # dirname = os.path.dirname(path)

                    finder = db["tree"].find_one({"name": paths[-1], "parent": parent_id, "serial": serial})
                    if finder:
                        if finder["type"] == "file":
                            print(resp.json())
                            db["tree"].update_one({"_id": finder["_id"]}, {"$set": {"url": resp.json()["attachments"][0]["url"]}})
                        else:
                            print("File already exists, and is a folder, skipping")
                    else:
                        db["tree"].insert_one({"name": paths[-1], "type": "file", "hashes": fname, "url": resp.json()["attachments"][0]["url"], "parent": parent_id, "serial": serial})
                except Exception as e:
                    print("Error sending file")
                    print(e)
                    print(resp.text)

            
            serial += 1
            chunk = file.read(chunk_size)
        
        # clear all the things that are greater than serial
        db["tree"].delete_many({"parent": parent_id, "serial": {"$gte": serial}})


def get_files_url(path):
    paths = os.path.normpath(path).split(os.sep)
    parent_id = finddirs(paths[:-1])
    if not parent_id:
        return None
    fn = db["tree"].find({"name": paths[-1], "parent": parent_id, "type": "file"}).sort("serial", pymongo.ASCENDING)
    if fn:
        return [i["url"] for i in fn]
    else:
        return None
    

def download_file(urls, path):
    if isinstance(path, str):    
        if not os.path.exists(path):
            with open(path, "x") as file:
                pass
        with open(path, "wb") as file:
            for i, url in enumerate(urls):
                resp = requests.get(url)
                file.write(resp.content)
    elif isinstance(path, BytesIO):
        for i, url in enumerate(urls):
            resp = requests.get(url)
            path.write(resp.content)


def list_dir(path):
    paths = os.path.normpath(path).split(os.sep)
    parent_id = finddirs(paths)
    if not parent_id:
        return None
    fn = db["tree"].find({"parent": parent_id, "serial": 0})
    return fn


with open("webhooks.txt", "r") as file:
    webhook_urls = [i for i in file.read().split("\n") if i]

hook = HookIter(webhook_urls)

send_file(hook, "test/test_3mb.mp4")
urls = get_files_url("test/test_3mb.mp4")
download_file(urls, "test/test_3mb2.mp4")

print(list(list_dir("test")))


