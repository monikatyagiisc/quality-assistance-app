import hashlib
from base64 import urlsafe_b64encode
from urllib.parse import quote_plus

from cryptography.fernet import Fernet
from pydantic import AliasChoices, Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", validation_alias=AliasChoices("APP_ENV"))
    db_host: str = Field(default="localhost", validation_alias=AliasChoices("DB_HOST"))
    db_port: int = Field(default=5432, validation_alias=AliasChoices("DB_PORT"))
    db_user: str = Field(default="quality_assistance", validation_alias=AliasChoices("DB_USER"))
    db_password: str = Field(
        default="quality_assistance",
        validation_alias=AliasChoices("DB_PASSWORD", "DBPASSWORD"),
    )
    db_ssl: bool = Field(default=False, validation_alias=AliasChoices("DB_SSL"))
    db_name: str = Field(
        default="quality_assistance",
        validation_alias=AliasChoices("DB_NAME", "DBNAME"),
    )
    # Optional full URL override (takes precedence when set)
    database_url_override: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL"),
    )

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    agent_service_url: str = "http://localhost:8001"
    jwt_secret: str = Field(default="change-me-in-production", validation_alias=AliasChoices("JWT_SECRET"))
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(
        default=60 * 24 * 7,
        validation_alias=AliasChoices("JWT_EXPIRE_MINUTES"),
    )
    encryption_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ENCRYPTION_KEY"),
    )
    api_docs_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("API_DOCS_ENABLED"),
    )
    run_migrations: bool = Field(
        default=True,
        validation_alias=AliasChoices("RUN_MIGRATIONS"),
    )

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env.lower() != "production":
            return self

        if (
            self.jwt_secret in {"change-me-in-production", "docker-dev-jwt-secret-change-me"}
            or len(self.jwt_secret) < 32
        ):
            raise ValueError("Production requires a unique JWT_SECRET of at least 32 characters.")
        if not self.encryption_key:
            raise ValueError("Production requires a Fernet ENCRYPTION_KEY.")
        try:
            Fernet(self.encryption_key.encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise ValueError("ENCRYPTION_KEY must be a valid Fernet key in production.") from exc
        if not self.cors_origin_list or "*" in self.cors_origin_list:
            raise ValueError("Production CORS_ORIGINS must contain explicit trusted origins.")
        if any(not origin.startswith("https://") for origin in self.cors_origin_list):
            raise ValueError("Production CORS_ORIGINS must use HTTPS.")
        if not self.db_ssl:
            raise ValueError("Production database connections must enable DB_SSL.")
        if self.db_host.lower() in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Production DB_HOST must identify the managed database endpoint.")
        if not self.db_password or self.db_password == "quality_assistance":
            raise ValueError("Production requires a non-default DB_PASSWORD.")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_encryption_key(self) -> str:
        if self.encryption_key:
            return self.encryption_key
        digest = hashlib.sha256(self.jwt_secret.encode("utf-8")).digest()
        return urlsafe_b64encode(digest).decode("utf-8")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        password = quote_plus(self.db_password)
        return (
            f"postgresql+asyncpg://{self.db_user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
