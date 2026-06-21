from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AgentBackend = Literal["gemini", "litellm", "bedrock", "ollama"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    agent_backend: AgentBackend = Field(default="gemini", validation_alias="AGENT_BACKEND")
    agent_model: str = Field(default="gemini-2.0-flash", validation_alias="AGENT_MODEL")

    google_api_key: str | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")

    # AWS Bedrock (when AGENT_BACKEND=bedrock)
    aws_access_key_id: str | None = Field(default=None, validation_alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(
        default=None, validation_alias="AWS_SECRET_ACCESS_KEY"
    )
    aws_session_token: str | None = Field(default=None, validation_alias="AWS_SESSION_TOKEN")
    aws_region: str = Field(default="us-east-1", validation_alias="AWS_REGION_NAME")

    # Ollama (when AGENT_BACKEND=ollama) — local, no API key required
    ollama_api_base: str = Field(
        default="http://localhost:11434", validation_alias="OLLAMA_API_BASE"
    )

    agent_host: str = "0.0.0.0"
    agent_port: int = 8001
    app_name: str = "quality_assistance_agent"
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @property
    def resolved_model(self) -> str:
        """LiteLLM-compatible model id with provider prefix when needed."""
        if self.agent_backend == "bedrock" and not self.agent_model.startswith("bedrock/"):
            return f"bedrock/{self.agent_model}"
        if self.agent_backend == "ollama" and not self.agent_model.startswith("ollama/"):
            return f"ollama/{self.agent_model}"
        return self.agent_model

    def validate_model_credentials(self) -> str | None:
        if self.agent_backend == "gemini":
            if not self.google_api_key:
                return "GOOGLE_API_KEY is required when AGENT_BACKEND=gemini"
            return None

        if self.agent_backend == "litellm":
            if self.agent_model.lower().startswith("openai/") and not self.openai_api_key:
                return "OPENAI_API_KEY is required for OpenAI models (e.g. openai/gpt-4o-mini)"
            return None

        if self.agent_backend == "bedrock":
            using_explicit_keys = bool(self.aws_access_key_id and self.aws_secret_access_key)
            if not using_explicit_keys and not self.aws_session_token:
                return (
                    "AWS credentials are required when AGENT_BACKEND=bedrock. "
                    "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY (or use an IAM role) "
                    "in agent/.env."
                )
            return None

        if self.agent_backend == "ollama":
            return None

        return f"Unsupported AGENT_BACKEND: {self.agent_backend}"


settings = Settings()
