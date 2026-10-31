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

    def test_requires_all_jira_oauth_settings_together(self) -> None:
        with self.assertRaises(ValidationError):
            self.valid_production_settings(JIRA_CLIENT_ID="client-id")

    def test_requires_complete_secure_entra_sso_configuration(self) -> None:
        with self.assertRaises(ValidationError):
            self.valid_production_settings(ENTRA_CLIENT_ID="client-id")

        valid = self.valid_production_settings(
            ENTRA_TENANT_ID="12345678-1234-5678-1234-567812345678",
            ENTRA_CLIENT_ID="client-id",
            ENTRA_CLIENT_SECRET="client-secret",
            ENTRA_REDIRECT_URI="https://app.example.com/api/auth/entra/callback",
            ENTRA_FRONTEND_URL="https://app.example.com/login",
        )
        self.assertTrue(valid.entra_sso_enabled)

        with self.assertRaises(ValidationError):
            self.valid_production_settings(
                ENTRA_TENANT_ID="12345678-1234-5678-1234-567812345678",
                ENTRA_CLIENT_ID="client-id",
                ENTRA_CLIENT_SECRET="client-secret",
                ENTRA_REDIRECT_URI="http://app.example.com/api/auth/entra/callback",
                ENTRA_FRONTEND_URL="https://app.example.com/login",
            )


if __name__ == "__main__":
    unittest.main()
