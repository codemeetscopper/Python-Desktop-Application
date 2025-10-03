import json
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

class AESCipher:
    def __init__(self, key: bytes):
        self.key = key  # must be 16, 24, or 32 bytes

    def encrypt(self, data: dict) -> str:
        return self.encrypt_string(json.dumps(data))

    def decrypt(self, enc_data: str) -> dict:
        return json.loads(self.decrypt_string(enc_data))

    def encrypt_string(self, data: str) -> str:
        plaintext = data.encode("utf-8")
        nonce = get_random_bytes(12)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        return json.dumps({
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "tag": base64.b64encode(tag).decode()
        })

    def decrypt_string(self, enc_data: str) -> str:
        enc = json.loads(enc_data)
        nonce = base64.b64decode(enc["nonce"])
        ciphertext = base64.b64decode(enc["ciphertext"])
        tag = base64.b64decode(enc["tag"])
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode("utf-8")
