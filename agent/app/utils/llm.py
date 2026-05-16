from google.adk.models.lite_llm import LiteLlm

from app.config.settings import settings


def resolve_model():
    """Return an ADK model: Gemini string or LiteLLM wrapper for other providers."""
    if settings.agent_backend == "litellm":
        return LiteLlm(model=settings.agent_model)
    return settings.agent_model
