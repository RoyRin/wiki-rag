import pytest
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from wiki_rag.encryption import encrypt_message, decrypt_message


class TestEncryption:
    def setup_method(self):
        # Generate a test key for AES-256
        self.key = AESGCM.generate_key(bit_length=256)
        self.key_base64 = base64.b64encode(self.key).decode()
    
    def test_encrypt_decrypt_roundtrip(self):
        original_message = "This is a secret message!"
        
        # Encrypt the message
        encrypted = encrypt_message(original_message, self.key_base64)
        
        # Verify the encrypted message is different from original
        assert encrypted != original_message
        assert isinstance(encrypted, str)
        
        # Decrypt the message
        decrypted = decrypt_message(encrypted, self.key_base64)
        
        # Verify we get the original message back
        assert decrypted == original_message
    
    def test_encrypt_different_nonces(self):
        message = "Test message"
        
        # Encrypt the same message twice
        encrypted1 = encrypt_message(message, self.key_base64)
        encrypted2 = encrypt_message(message, self.key_base64)
        
        # Due to different nonces, encrypted messages should be different
        assert encrypted1 != encrypted2
        
        # But both should decrypt to the same message
        assert decrypt_message(encrypted1, self.key_base64) == message
        assert decrypt_message(encrypted2, self.key_base64) == message
    
    def test_empty_message(self):
        empty_message = ""
        
        encrypted = encrypt_message(empty_message, self.key_base64)
        decrypted = decrypt_message(encrypted, self.key_base64)
        
        assert decrypted == empty_message
    
    def test_unicode_message(self):
        unicode_message = "Hello 世界! 🚀 Special çhäracters"
        
        encrypted = encrypt_message(unicode_message, self.key_base64)
        decrypted = decrypt_message(encrypted, self.key_base64)
        
        assert decrypted == unicode_message
    
    def test_long_message(self):
        long_message = "A" * 10000  # 10KB message
        
        encrypted = encrypt_message(long_message, self.key_base64)
        decrypted = decrypt_message(encrypted, self.key_base64)
        
        assert decrypted == long_message
    
    def test_invalid_key_format(self):
        message = "Test message"
        invalid_key = "not-a-valid-base64-key"
        
        with pytest.raises(Exception):  # Will raise base64 decode error
            encrypt_message(message, invalid_key)
    
    def test_decrypt_with_wrong_key(self):
        message = "Secret message"
        wrong_key = base64.b64encode(AESGCM.generate_key(bit_length=256)).decode()
        
        encrypted = encrypt_message(message, self.key_base64)
        
        # Decrypting with wrong key should fail
        with pytest.raises(Exception):  # Will raise authentication error
            decrypt_message(encrypted, wrong_key)
    
    def test_decrypt_tampered_message(self):
        message = "Original message"
        encrypted = encrypt_message(message, self.key_base64)
        
        # Tamper with the encrypted message
        encrypted_bytes = base64.b64decode(encrypted)
        tampered_bytes = encrypted_bytes[:-1] + b'X'  # Change last byte
        tampered_encrypted = base64.b64encode(tampered_bytes).decode()
        
        # Decrypting tampered message should fail
        with pytest.raises(Exception):  # Will raise authentication error
            decrypt_message(tampered_encrypted, self.key_base64)
    
    def test_message_format(self):
        message = "Test"
        encrypted = encrypt_message(message, self.key_base64)
        
        # Verify encrypted message is base64 encoded
        try:
            decoded = base64.b64decode(encrypted)
            assert len(decoded) > 0
        except:
            pytest.fail("Encrypted message is not valid base64")