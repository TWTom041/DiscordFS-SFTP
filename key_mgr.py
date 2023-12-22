import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

class AESCipher(object):
    def __init__(self, key):
        self.bs = AES.block_size
        if isinstance(key, str):
            key = key.encode("utf-8")
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
    
def gen_key(passphrase, path=None, validatepath=None):
    validator = b"successful"
    key = get_random_bytes(32)
    cipher = AESCipher(passphrase)
    encrypted_key = cipher.encrypt(key)
    validator = cipher.encrypt(validator)
    if path is not None:
        with open(path, "wb") as f:
            f.write(encrypted_key)
    if validatepath is not None:
        with open(validatepath, "wb") as f:
            f.write(validator)
    return encrypted_key, validator

def get_key(passphrase, path, validation=None, validation_mode="bytes"):
    try:
        with open(path, "rb") as f:
            encrypted_key = f.read()
    except FileNotFoundError:
        return 1, None
    cipher = AESCipher(passphrase)
    key = cipher.decrypt(encrypted_key)
    
    if validation is not None:
        if validation_mode == "bytes":
            if cipher.decrypt(validation) != b"successful":
                return 2, key
        elif validation_mode == "file":
            try:
                with open(validation, "rb") as f:
                    if cipher.decrypt(f.read()) != b"successful":
                        return 2, key
            except FileNotFoundError:
                return 1, key
        else:
            return 3, key  # validation mode not supported
    
    return 0, key


    
def _tester():
    key, validator = gen_key("test", "key.bin", "validator.bin")
    print(key)
    print(validator)
    print(get_key("test", "key.bin", "validator.bin", "file"))
    print(get_key("test", "key.bin", "validator.bin", "invalid"))
    print(get_key("test", "key.bin", "invalid.bin", "file"))
    print(get_key("test", "invalid.bin", "validator.bin", "file"))
    print(get_key("test", "invalid.bin", "invalid.bin", "file"))
    print(get_key("test", "key.bin", "validator.bin", "invalid"))
    print(get_key("test", "key.bin", validator, "bytes"))
    

if __name__ == "__main__":
    _tester()