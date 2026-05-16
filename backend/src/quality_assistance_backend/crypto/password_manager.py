"""
Password storage and verification.

Passwords are never stored in plain text and cannot be retrieved after registration.
Flow:
  1. Hash with bcrypt (one-way)
  2. Encrypt the hash with Fernet before writing to the database
  3. On login, decrypt the stored value, then verify with bcrypt
"""

import bcrypt

from quality_assistance_backend.crypto.fernet_encryption import FernetEncryption


class PasswordManager:
    def __init__(self, encryption: FernetEncryption | None = None) -> None:
        self._encryption = encryption or FernetEncryption()

    def _hash(self, password: str) -> str:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def _verify_hash(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )

    def store_password(self, password: str) -> str:
        """Hash and encrypt a password for database storage."""
        password_hash = self._hash(password)
        return self._encryption.encrypt(password_hash)

    def verify_password(self, password: str, stored_value: str) -> bool:
        """Verify a password against the encrypted value from the database."""
        password_hash = self._unwrap_stored_hash(stored_value)
        return self._verify_hash(password, password_hash)

    def _unwrap_stored_hash(self, stored_value: str) -> str:
        """Support legacy rows that only contain a bcrypt hash (no Fernet envelope)."""
        try:
            return self._encryption.decrypt(stored_value)
        except ValueError:
            return stored_value
