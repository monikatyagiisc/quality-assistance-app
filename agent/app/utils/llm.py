from google.adk.models.lite_llm import LiteLlm

from app.config.settings import settings


def resolve_model():
    """Return an ADK model.

    - gemini: native Gemini model string
    - litellm / bedrock: LiteLLM wrapper (Bedrock model ids get a 'bedrock/' prefix)
    """
    if settings.agent_backend in ("litellm", "bedrock"):
        return LiteLlm(model=settings.resolved_model)
    return settings.agent_model
