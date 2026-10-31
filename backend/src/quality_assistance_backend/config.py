import hashlib
from base64 import urlsafe_b64encode
from urllib.parse import quote_plus
from uuid import UUID

from cryptography.fernet import Fernet
from pydantic import AliasChoices, Field, SecretStr, computed_field, model_validator
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
    jira_client_id: str | None = Field(default=None, validation_alias=AliasChoices("JIRA_CLIENT_ID"))
    jira_client_secret: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("JIRA_CLIENT_SECRET"),
    )
    jira_redirect_uri: str | None = Field(
        default=None,
        validation_alias=AliasChoices("JIRA_REDIRECT_URI"),
    )
    jira_frontend_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("JIRA_FRONTEND_URL"),
    )
    entra_tenant_id: str | None = Field(default=None, validation_alias=AliasChoices("ENTRA_TENANT_ID"))
    entra_client_id: str | None = Field(default=None, validation_alias=AliasChoices("ENTRA_CLIENT_ID"))
    entra_client_secret: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("ENTRA_CLIENT_SECRET"),
    )
    entra_redirect_uri: str | None = Field(default=None, validation_alias=AliasChoices("ENTRA_REDIRECT_URI"))
    entra_frontend_url: str | None = Field(default=None, validation_alias=AliasChoices("ENTRA_FRONTEND_URL"))

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        jira_oauth_values = (
            self.jira_client_id,
            self.jira_client_secret.get_secret_value() if self.jira_client_secret else None,
            self.jira_redirect_uri,
        )
        if any(jira_oauth_values) and not all(jira_oauth_values):
            raise ValueError(
                "JIRA_CLIENT_ID, JIRA_CLIENT_SECRET, and JIRA_REDIRECT_URI must be configured together."
            )

        entra_values = (
            self.entra_tenant_id,
            self.entra_client_id,
            self.entra_client_secret.get_secret_value() if self.entra_client_secret else None,
            self.entra_redirect_uri,
            self.entra_frontend_url,
        )
        if any(entra_values) and not all(entra_values):
            raise ValueError(
                "ENTRA_TENANT_ID, ENTRA_CLIENT_ID, ENTRA_CLIENT_SECRET, "
                "ENTRA_REDIRECT_URI, and ENTRA_FRONTEND_URL must be configured together."
            )
        if all(entra_values):
            try:
                self.entra_tenant_id = str(UUID(self.entra_tenant_id or ""))
            except ValueError as exc:
                raise ValueError("ENTRA_TENANT_ID must be the Microsoft Entra tenant GUID.") from exc

        if self.app_env.lower() != "production":
            return self

        if self.jira_oauth_enabled and (
            not self.jira_redirect_uri.startswith("https://")
            or (
                self.jira_frontend_url
                and not self.jira_frontend_url.startswith("https://")
            )
        ):
            raise ValueError("Production Jira OAuth redirect URLs must use HTTPS.")
        if self.entra_sso_enabled and (
            not self.entra_redirect_uri.startswith("https://")
            or not self.entra_frontend_url.startswith("https://")
        ):
            raise ValueError("Production Microsoft Entra SSO redirect URLs must use HTTPS.")
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

    @property
    def jira_oauth_enabled(self) -> bool:
        return bool(
            self.jira_client_id
            and self.jira_client_secret
            and self.jira_client_secret.get_secret_value()
            and self.jira_redirect_uri
        )

    @property
    def entra_sso_enabled(self) -> bool:
        return bool(
            self.entra_tenant_id
            and self.entra_client_id
            and self.entra_client_secret
            and self.entra_client_secret.get_secret_value()
            and self.entra_redirect_uri
            and self.entra_frontend_url
        )


settings = Settings()
