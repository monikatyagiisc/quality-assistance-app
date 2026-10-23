import unittest

from cryptography.fernet import Fernet
from pydantic import ValidationError

from quality_assistance_backend.config import Settings


class ProductionSettingsTests(unittest.TestCase):
    def valid_production_settings(self, **overrides: object) -> Settings:
        values: dict[str, object] = {
            "APP_ENV": "production",
            "JWT_SECRET": "a" * 64,
            "ENCRYPTION_KEY": Fernet.generate_key().decode(),
            "cors_origins": "https://app.example.com",
            "DB_HOST": "db.example.com",
            "DB_PASSWORD": "unique-production-db-password",
            "DB_SSL": True,
        }
        values.update(overrides)
        return Settings(_env_file=None, **values)

    def test_accepts_secure_production_configuration(self) -> None:
        settings = self.valid_production_settings()
        self.assertEqual(settings.cors_origin_list, ["https://app.example.com"])

    def test_rejects_default_jwt_secret(self) -> None:
        with self.assertRaises(ValidationError):
            self.valid_production_settings(JWT_SECRET="docker-dev-jwt-secret-change-me")

    def test_rejects_missing_encryption_key(self) -> None:
        with self.assertRaises(ValidationError):
            self.valid_production_settings(ENCRYPTION_KEY=None)

    def test_rejects_insecure_production_database_or_origin(self) -> None:
        with self.assertRaises(ValidationError):
            self.valid_production_settings(DB_SSL=False)
        with self.assertRaises(ValidationError):
            self.valid_production_settings(cors_origins="http://app.example.com")
        with self.assertRaises(ValidationError):
            self.valid_production_settings(DB_PASSWORD="quality_assistance")
        with self.assertRaises(ValidationError):
            self.valid_production_settings(DB_HOST="localhost")


if __name__ == "__main__":
    unittest.main()
