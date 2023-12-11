# from discord import SyncWebhook
# import discord
import requests
import os
from io import BytesIO
from pymongo import MongoClient
from hashlib import md5
from zlib import crc32


chunk_size = 24 * 1024 * 1024  # MB
webhook_url = input("Enter the webhook url: ") or None
client = MongoClient("mongodb://localhost:27017/")

db = client["dsdrive"]

# webhook = SyncWebhook.from_url(webhook_url)
# webhook.send("Hello World")

def makedirs(paths):
    parent_id = "/"
    for i in paths:
        fs = db["tree"].find_one({"name": i, "parent": parent_id, "type": "folder"})
        path_now = os.path.join(parent_id, i)
        if fs:
            parent_id = fs["id"]
        else:
            id = md5(path_now.encode()).hexdigest() + "-" + crc32(path_now.encode()).to_bytes(4, "big").hex()
            db["tree"].insert_one({"name": i, "parent": parent_id, "type": "folder", "id": id})
            parent_id = id            
    return parent_id


def finddirs(paths):
    # paths = os.path.normpath(path).split(os.sep)
    parent_id = "/"
    for i in paths:
        fs = db["tree"].find_one({"name": i, "parent": parent_id, "type": "folder"})
        path_now = os.path.join(parent_id, i)
        if fs:
            parent_id = fs["id"]
            continue
        else:
            return None
    return parent_id


def send_file(url, path):
    with open(path, "rb") as file:
        chunk = file.read(chunk_size)
        while chunk:
            with BytesIO(chunk) as buffer:
                fname = md5(chunk).hexdigest() + "-" + crc32(chunk).to_bytes(4, "big").hex()
                print(fname)
                resp = requests.post(url, files={"file": (fname, buffer)})
                print(resp.json())
                # dirname = os.path.dirname(path)

                paths = os.path.normpath(path).split(os.sep)
                print(paths)
                parent_id = makedirs(paths[:-1])

                finder = db["tree"].find_one({"name": paths[-1], "type": "file", "parent": parent_id})
                if finder:
                    print(1)
                    db["tree"].update_one({"id": finder["id"]}, {"$set": {"url": resp.json()["attachments"][0]["url"]}})
                else:
                    db["tree"].insert_one({"name": paths[-1], "type": "file", "id": fname, "url": resp.json()["attachments"][0]["url"], "parent": parent_id})
            chunk = file.read(chunk_size)


def get_file(path):
    paths = os.path.normpath(path).split(os.sep)
    parent_id = finddirs(paths[:-1])
    if not parent_id:
        return None
    fn = db["tree"].find_one({"name": paths[-1], "type": "file", "parent": parent_id})
    if fn:
        return fn["url"]
    else:
        return None


send_file(webhook_url, "test/testfile.txt")

print(get_file("test/testfile.txt"))





        
    