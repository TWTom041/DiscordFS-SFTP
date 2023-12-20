import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

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
key = b'SomeSecretKey'
cipher = AESCipher(key)

data_to_encrypt = b'This is some binary data.'
encrypted_data = cipher.encrypt(data_to_encrypt)
print("Encrypted:", encrypted_data)

decrypted_data = cipher.decrypt(encrypted_data)
print("Decrypted:", decrypted_data)