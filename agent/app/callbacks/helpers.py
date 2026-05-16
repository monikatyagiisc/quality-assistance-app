import json
from typing import Any

from google.adk.agents.context import Context
from google.genai import types

MAX_LOG_CHARS = 4000


def truncate(value: str, limit: int = MAX_LOG_CHARS) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}... [{len(value) - limit} chars truncated]"


def safe_json(data: Any, *, limit: int = MAX_LOG_CHARS) -> str:
    try:
        text = json.dumps(data, default=str, ensure_ascii=False)
    except TypeError:
        text = str(data)
    return truncate(text, limit)


def content_to_text(content: types.Content | None) -> str:
    if content is None:
        return ""
    parts: list[str] = []
    for part in content.parts or []:
        if part.text:
            parts.append(part.text)
        elif part.function_call:
            parts.append(
                f"<function_call name={part.function_call.name!r} "
                f"args={safe_json(part.function_call.args, limit=800)}>"
            )
        elif part.function_response:
            parts.append(
                f"<function_response name={part.function_response.name!r} "
                f"response={safe_json(part.function_response.response, limit=800)}>"
            )
    return truncate("\n".join(parts))


def context_fields(ctx: Context) -> dict[str, str]:
    return {
        "agent": ctx.agent_name,
        "user_id": ctx.user_id,
        "invocation_id": ctx.invocation_id,
        "session_id": ctx.session.id,
    }
