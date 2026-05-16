from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AgentBackend = Literal["gemini", "litellm"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    agent_backend: AgentBackend = Field(default="gemini", validation_alias="AGENT_BACKEND")
    agent_model: str = Field(default="gemini-2.0-flash", validation_alias="AGENT_MODEL")

    google_api_key: str | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")

    agent_host: str = "0.0.0.0"
    agent_port: int = 8001
    app_name: str = "quality_assistance_agent"
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    def validate_model_credentials(self) -> str | None:
        if self.agent_backend == "gemini":
            if not self.google_api_key:
                return "GOOGLE_API_KEY is required when AGENT_BACKEND=gemini"
            return None

        if self.agent_backend == "litellm":
            if self.agent_model.lower().startswith("openai/") and not self.openai_api_key:
                return "OPENAI_API_KEY is required for OpenAI models (e.g. openai/gpt-4o-mini)"
            return None

        return f"Unsupported AGENT_BACKEND: {self.agent_backend}"


settings = Settings()
