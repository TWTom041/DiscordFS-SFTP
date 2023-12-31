import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import time

def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

class AESCipher(object):

    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(raw)
        return base64.b64encode(iv + encrypted)

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(enc[AES.block_size:])
        return AESCipher._unpad(decrypted)

    def _pad(self, s):
        padding = self.bs - len(s) % self.bs
        return s + bytes([padding] * padding)

    @staticmethod
    def _unpad(s):
        return s[:-s[-1]]

def permission_to_list(permission):
    # permission is a octal number
    if not 0o0 <= permission <= 0o777:
        raise ValueError("Permission must be an octal number between 0 and 777")
    # Convert each digit to a list of permissions
    permission_list = ["o_r", "o_w", "o_x", "g_r", "g_w", "g_x", "u_r", "u_w", "u_x"]
    permission_list = [d for i, d in enumerate(permission_list[::-1]) if permission & (1 << i)]
    return permission_list


import requests
import io

url = "https://discord.com/api/webhooks/1185590612725088297/_-k_sRmBv-eM_kzuGBroCkD8fOiyhbGU6l0d7GgOs3UhbMonxBPe69X2cJI33P6XOHhq" #webhook url, from here: https://i.imgur.com/f9XnAew.png

#for all params, see https://discordapp.com/developers/docs/resources/webhook#execute-webhook

result = requests.post(url, files={"file": io.BytesIO(b"test")})

try:
    print(result.json())
    result.raise_for_status()
except requests.exceptions.HTTPError as err:
    print(err)
else:
    print("Payload delivered successfully, code {}.".format(result.status_code))

import discord
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('Logged in as:', client.user)

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    if message.content == 'ping':
        message = await message.channel.fetch_message(1190645814863872102)
        print(message.attachments)

client.run('MTE5MDY3MzE1MjkzNDY5NDk4Mg.GWv41t.27lW4aF-HR70WcYMxRg2H-r1nNIDjVLCiBKnMY')



# # Example usage
# key = b''
# cipher = AESCipher(key)

# data_to_encrypt = b'This is some binary data.' * 50000000

# atime = time.time()
# encrypted_data = cipher.encrypt(data_to_encrypt)
# print("Time taken to encrypt: ", time.time() - atime)  # 7.8s on my machine
# print("size of data: ", sizeof_fmt(len(data_to_encrypt)))  # 1.2GiB
# # print("Encrypted:", encrypted_data)

# atime = time.time()
# decrypted_data = cipher.decrypt(encrypted_data)
# print("Time taken to encrypt: ", time.time() - atime)  # 6.6s on my machine
# print("size of data: ", sizeof_fmt(len(decrypted_data)))  # 1.2GiB
# # print("Decrypted:", decrypted_data)