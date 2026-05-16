from cryptography.fernet import Fernet, InvalidToken

from quality_assistance_backend.config import settings


class FernetEncryption:
    """Symmetric encryption for sensitive values at rest (e.g. password hashes)."""

    def __init__(self, key: str | None = None) -> None:
        raw_key = (key or settings.resolved_encryption_key).encode("utf-8")
        self._fernet = Fernet(raw_key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, encrypted_value: str) -> str:
        try:
            return self._fernet.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Could not decrypt value") from exc
