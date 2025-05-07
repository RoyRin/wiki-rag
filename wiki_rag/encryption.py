import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM



# 🔒 Decrypt helper
def decrypt_message(enc_b64: str, key: bytes) -> str:
    data = base64.b64decode(enc_b64)
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()


# 🔒 Encrypt helper
def encrypt_message(message: str, key: bytes) -> str:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, message.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()
