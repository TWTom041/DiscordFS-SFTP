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


# Example usage
key = b''
cipher = AESCipher(key)

data_to_encrypt = b'This is some binary data.' * 50000000

atime = time.time()
encrypted_data = cipher.encrypt(data_to_encrypt)
print("Time taken to encrypt: ", time.time() - atime)  # 7.8s on my machine
print("size of data: ", sizeof_fmt(len(data_to_encrypt)))  # 1.2GiB
# print("Encrypted:", encrypted_data)

atime = time.time()
decrypted_data = cipher.decrypt(encrypted_data)
print("Time taken to encrypt: ", time.time() - atime)  # 6.6s on my machine
print("size of data: ", sizeof_fmt(len(decrypted_data)))  # 1.2GiB
# print("Decrypted:", decrypted_data)