import time
from typing import Any

from asgi_correlation_id import correlation_id
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.callbacks.helpers import safe_json, truncate
from app.config.logging_config import get_logger

logger = get_logger(__name__)

_SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie"}


def _header_snapshot(request: Request) -> dict[str, str]:
    return {
        key: ("<redacted>" if key.lower() in _SENSITIVE_HEADERS else value)
        for key, value in request.headers.items()
    }


async def _read_body(request: Request) -> bytes:
    body = await request.body()

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": body, "more_body": False}

    request._receive = receive  # noqa: SLF001
    return body


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started = time.perf_counter()
        cid = correlation_id.get() or "-"
        body_bytes = b""
        if request.method in {"POST", "PUT", "PATCH"}:
            body_bytes = await _read_body(request)

        logger.info(
            "http.request method=%s path=%s correlation_id=%s client=%s headers=%s body=%s",
            request.method,
            request.url.path,
            cid,
            request.client.host if request.client else "-",
            safe_json(_header_snapshot(request), limit=1200),
            truncate(body_bytes.decode("utf-8", errors="replace")) if body_bytes else "",
        )

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "http.error method=%s path=%s correlation_id=%s duration_ms=%.1f",
                request.method,
                request.url.path,
                cid,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "http.response method=%s path=%s correlation_id=%s status=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            cid,
            response.status_code,
            elapsed_ms,
        )
        return response
