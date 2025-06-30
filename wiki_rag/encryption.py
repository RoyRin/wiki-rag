import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# 🔒 Decrypt helper
def decrypt_message(enc_b64: str, key: str) -> str:
    key_bytes = base64.b64decode(key)
    data = base64.b64decode(enc_b64)
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key_bytes)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()


# 🔒 Encrypt helper
def encrypt_message(message: str, key: str) -> str:
    key_bytes = base64.b64decode(key)
    aesgcm = AESGCM(key_bytes)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, message.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()
