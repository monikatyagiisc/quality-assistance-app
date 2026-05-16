from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    google_api_key: str | None = None
    agent_host: str = "0.0.0.0"
    agent_port: int = 8001
    app_name: str = "quality_assistance_agent"


settings = Settings()
