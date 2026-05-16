import os

from asgi_correlation_id import CorrelationIdMiddleware
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.callbacks.helpers import truncate
from app.config.logging_config import get_logger, setup_logging
from app.errors import classify_agent_error
from app.config.settings import settings
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.schemas import AssistRequest, AssistResponse
from app.services.runner_service import runner_service

load_dotenv()
setup_logging()

logger = get_logger(__name__)

if settings.google_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)
if settings.openai_api_key:
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

app = FastAPI(
    title="Quality Assistance Agent",
    description="Google ADK agent service for quality engineering assistance.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent"}


@app.post("/assist", response_model=AssistResponse)
async def assist(request: AssistRequest) -> AssistResponse:
    config_error = settings.validate_model_credentials()
    if config_error:
        logger.warning("assist.config_error detail=%s", config_error)
        raise HTTPException(
            status_code=503,
            detail={
                "message": config_error,
                "code": "invalid_api_key",
            },
        )

    logger.info(
        "assist.start user_id=%s session_id=%s message_len=%s",
        request.user_id,
        request.session_id or "<new>",
        len(request.message),
    )
    logger.debug("assist.input message=%s", truncate(request.message))

    try:
        session_id, response = await runner_service.run(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
        )
        logger.info(
            "assist.success user_id=%s session_id=%s response_len=%s",
            request.user_id,
            session_id,
            len(response),
        )
        logger.debug("assist.output response=%s", truncate(response))
        return AssistResponse(session_id=session_id, response=response)
    except Exception as exc:
        logger.exception(
            "assist.failure user_id=%s session_id=%s",
            request.user_id,
            request.session_id or "<new>",
        )
        user_error = classify_agent_error(exc)
        raise HTTPException(
            status_code=user_error.status_code,
            detail={"message": user_error.message, "code": user_error.code},
        ) from exc
