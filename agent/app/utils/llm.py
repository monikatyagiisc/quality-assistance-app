from google.adk.models.lite_llm import LiteLlm

from app.config.settings import settings


def resolve_model():
    """Return an ADK model.

    - gemini: native Gemini model string
    - litellm / bedrock / ollama: LiteLLM wrapper
    """
    if settings.agent_backend in ("litellm", "bedrock", "ollama"):
        return LiteLlm(model=settings.resolved_model)
    return settings.agent_model
