import base64

from cryptography.fernet import Fernet
from django.conf import settings


class Crypto:
    """
    A class to handle encryption and decryption of sensitive data.
    """

    def __init__(self):
        self.key = settings.ENCRYPTION_KEY.encode()
        # Ensure key is URL-safe base64-encoded and 32 bytes long
        if len(base64.urlsafe_b64decode(
          self.key + b'=' * (-len(self.key) % 4)
          )) != 32:
            raise ValueError("Encryption key must be 32 bytes long after"
                             " base64 decoding")
        self.cipher = Fernet(self.key)

    def encrypt(self, value: str) -> str:
        """
        Encrypt a string
        """
        if not value:
            return value
        encrypted = self.cipher.encrypt(value.encode())
        return encrypted.decode()

    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt an encrypted value
        """
        if not encrypted_value:
            return encrypted_value
        decrypted = self.cipher.decrypt(encrypted_value.encode())
        return decrypted.decode()
