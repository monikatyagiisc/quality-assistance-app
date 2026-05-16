import re
from typing import Any

import httpx

_QUOTA_MARKERS = (
    "RESOURCE_EXHAUSTED",
    "429",
    "QUOTA",
    "RATE LIMIT",
    "RATE_LIMIT",
    "RATE_LIMIT_EXCEEDED",
    "TOO MANY REQUESTS",
    "INSUFFICIENT_QUOTA",
    "EXCEEDED YOUR CURRENT QUOTA",
)

_AUTH_MARKERS = (
    "INVALID_API_KEY",
    "INCORRECT_API_KEY",
    "UNAUTHENTICATED",
    "PERMISSION_DENIED",
    "AUTHENTICATIONERROR",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
)

_CONTEXT_MARKERS = (
    "CONTEXT_LENGTH",
    "TOKEN LIMIT",
    "TOO MANY TOKENS",
    "MAX_TOKENS",
)


class AgentServiceError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        code: str = "agent_error",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def _matches_any(text: str, markers: tuple[str, ...]) -> bool:
    upper = text.upper()
    return any(marker in upper for marker in markers)


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


def _quota_message(raw: str) -> str:
    retry_hint = _extract_retry_seconds(raw)
    message = (
        "The AI provider rate limit or quota was exceeded. "
        "Please wait a moment and try again."
    )
    if retry_hint:
        message += f" Suggested wait: about {retry_hint} seconds."
    message += " If this keeps happening, check your model provider plan and billing."
    return message


def map_raw_agent_error(raw: str, *, http_status: int | None = None) -> AgentServiceError:
    if _matches_any(raw, _QUOTA_MARKERS):
        return AgentServiceError(_quota_message(raw), status_code=429, code="quota_exceeded")

    if _matches_any(raw, _AUTH_MARKERS):
        return AgentServiceError(
            "The AI API key is missing or invalid. Check agent service configuration.",
            status_code=503,
            code="invalid_api_key",
        )

    if _matches_any(raw, _CONTEXT_MARKERS):
        return AgentServiceError(
            "The prompt is too long for the selected model. Shorten your input and try again.",
            status_code=400,
            code="context_length_exceeded",
        )

    if http_status == 503:
        return AgentServiceError(
            raw if len(raw) < 200 else "The quality assistant service is not configured correctly.",
            status_code=503,
            code="agent_unavailable",
        )

    if http_status == 504:
        return AgentServiceError(
            "The AI request timed out. Try again with a shorter prompt.",
            status_code=504,
            code="timeout",
        )

    return AgentServiceError(
        "We could not reach the quality assistant. Please try again shortly.",
        status_code=502,
        code="agent_error",
    )


def _detail_to_text(detail: Any) -> str:
    if detail is None:
        return ""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        return str(detail.get("message") or detail.get("detail") or detail)
    return str(detail)


def parse_agent_http_error(exc: httpx.HTTPStatusError) -> AgentServiceError:
    try:
        body = exc.response.json()
        if isinstance(body, dict):
            detail = body.get("detail")
            if isinstance(detail, dict) and detail.get("message"):
                return AgentServiceError(
                    str(detail["message"]),
                    status_code=exc.response.status_code,
                    code=str(detail.get("code") or "agent_error"),
                )
            raw = _detail_to_text(detail)
        else:
            raw = ""
    except Exception:
        raw = exc.response.text

    if not raw:
        raw = str(exc)

    return map_raw_agent_error(raw, http_status=exc.response.status_code)


def map_connection_error(exc: Exception) -> AgentServiceError:
    return AgentServiceError(
        "The quality assistant service is not running or not reachable. "
        "Start the agent service and try again.",
        status_code=503,
        code="agent_unreachable",
    )
