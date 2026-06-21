import re
from typing import NamedTuple

from app.config.settings import settings

# Shared markers across Gemini, OpenAI (LiteLLM), Anthropic, etc.
_QUOTA_MARKERS = (
    "RESOURCE_EXHAUSTED",
    "429",
    "QUOTA",
    "RATE LIMIT",
    "RATE_LIMIT",
    "RATE_LIMIT_EXCEEDED",
    "TOO MANY REQUESTS",
    "INSUFFICIENT_QUOTA",
    "BILLING_HARD_LIMIT",
    "EXCEEDED YOUR CURRENT QUOTA",
)

_AUTH_MARKERS = (
    "INVALID_API_KEY",
    "INCORRECT_API_KEY",
    "UNAUTHENTICATED",
    "PERMISSION_DENIED",
    "AUTHENTICATIONERROR",
    "INVALID AUTHENTICATION",
    "API KEY NOT VALID",
)

_CONTEXT_MARKERS = (
    "CONTEXT_LENGTH",
    "MAXIMUM CONTEXT",
    "TOKEN LIMIT",
    "TOO MANY TOKENS",
    "MAX_TOKENS",
)

_MODEL_MARKERS = (
    "MODEL_NOT_FOUND",
    "DOES NOT EXIST",
    "UNKNOWN MODEL",
)


class UserFacingError(NamedTuple):
    status_code: int
    message: str
    code: str


def classify_agent_error(exc: BaseException) -> UserFacingError:
    text = str(exc)
    upper = text.upper()

    if _matches_any(upper, _QUOTA_MARKERS):
        return UserFacingError(429, _quota_message(text), "quota_exceeded")

    if _matches_any(upper, _AUTH_MARKERS) or _matches_api_key_error(upper):
        return UserFacingError(503, _invalid_api_key_message(), "invalid_api_key")

    if _matches_any(upper, _CONTEXT_MARKERS):
        return UserFacingError(
            400,
            "The prompt is too long for the selected model. Shorten your input and try again.",
            "context_length_exceeded",
        )

    if _matches_any(upper, _MODEL_MARKERS):
        return UserFacingError(
            400,
            f"The configured model ({settings.agent_model}) is not available. "
            "Check AGENT_MODEL in agent/.env.",
            "model_not_found",
        )

    if "TIMEOUT" in upper or "TIMED OUT" in upper:
        return UserFacingError(
            504,
            "The AI request timed out. Try again with a shorter prompt.",
            "timeout",
        )

    if "SESSION NOT FOUND" in upper:
        return UserFacingError(
            400,
            "Your conversation session expired. Start a new session and try again.",
            "session_not_found",
        )

    if settings.agent_backend == "ollama" and (
        "CONNECTION REFUSED" in upper
        or "CONNECT ERROR" in upper
        or "FAILED TO ESTABLISH" in upper
        or "OLLAMA" in upper and "NOT FOUND" in upper
    ):
        return UserFacingError(
            503,
            _invalid_api_key_message(),
            "ollama_unavailable",
        )

    return UserFacingError(
        500,
        "We could not generate quality assistance right now. Please try again in a few minutes.",
        "agent_internal_error",
    )


def _matches_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _matches_api_key_error(upper_text: str) -> bool:
    return "API KEY" in upper_text and any(
        word in upper_text for word in ("INVALID", "MISSING", "INCORRECT", "REQUIRED")
    )


def _provider_label() -> str:
    if settings.agent_backend == "bedrock":
        return "Amazon Bedrock"
    if settings.agent_backend == "ollama":
        return "Ollama"
    if settings.agent_backend == "litellm":
        model = settings.agent_model.lower()
        if model.startswith("openai/"):
            return "OpenAI"
        if model.startswith("anthropic/"):
            return "Anthropic"
        if model.startswith("azure/"):
            return "Azure OpenAI"
        if model.startswith("bedrock/"):
            return "Amazon Bedrock"
        if model.startswith("ollama/"):
            return "Ollama"
        return "your model provider"
    return "Gemini"


def _billing_hint() -> str:
    provider = _provider_label()
    if settings.agent_backend == "bedrock":
        return (
            "If this keeps happening, check your Amazon Bedrock model access and "
            "service quotas in the AWS console."
        )
    if settings.agent_backend == "ollama":
        return (
            "If this keeps happening, confirm Ollama is running "
            f"({settings.ollama_api_base}) and the model is pulled: "
            f"ollama pull {settings.agent_model.removeprefix('ollama/')}"
        )
    if settings.agent_backend == "litellm":
        return f"If this keeps happening, check {provider} usage limits and billing."
    return "If this keeps happening, check your Gemini API plan and billing."


def _invalid_api_key_message() -> str:
    if settings.agent_backend == "bedrock":
        return (
            "AWS credentials are missing or invalid for Amazon Bedrock. "
            "Check AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_REGION_NAME in agent/.env, "
            "and confirm the model is enabled in Bedrock model access."
        )
    if settings.agent_backend == "ollama":
        return (
            f"Could not reach Ollama at {settings.ollama_api_base}. "
            "Start Ollama (ollama serve) and pull the model "
            f"(ollama pull {settings.agent_model.removeprefix('ollama/')})."
        )
    if settings.agent_backend == "litellm":
        model = settings.agent_model.lower()
        if model.startswith("openai/"):
            return (
                "The OpenAI API key is missing or invalid. "
                "Check OPENAI_API_KEY in agent/.env."
            )
        if model.startswith("bedrock/"):
            return (
                "AWS credentials are missing or invalid for Amazon Bedrock. "
                "Check AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_REGION_NAME in agent/.env."
            )
        return (
            "The AI API key is missing or invalid for the configured model. "
            "Check agent/.env credentials for AGENT_BACKEND=litellm."
        )
    return (
        "The Gemini API key is missing or invalid. "
        "Check GOOGLE_API_KEY in agent/.env."
    )


def _quota_message(raw: str) -> str:
    retry_hint = _extract_retry_seconds(raw)
    message = (
        f"The {_provider_label()} rate limit or quota was exceeded. "
        "Please wait a moment and try again."
    )
    if retry_hint:
        message += f" Suggested wait: about {retry_hint} seconds."
    message += f" {_billing_hint()}"
    return message


def _extract_retry_seconds(text: str) -> int | None:
    for pattern in (
        r"retry in (\d+(?:\.\d+)?)s",
        r"retry after (\d+(?:\.\d+)?) second",
        r"try again in (\d+(?:\.\d+)?)s",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return max(1, int(float(match.group(1))))
    return None
