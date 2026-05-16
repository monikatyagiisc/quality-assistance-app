import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from quality_assistance_backend.config import settings
from quality_assistance_backend.db import engine, get_db
from quality_assistance_backend.migrations import run_migrations
from quality_assistance_backend.deps import get_current_user
from quality_assistance_backend.models import AssistanceRequest, User
from quality_assistance_backend.routers import auth
from quality_assistance_backend.schemas import AssistanceInput, AssistanceOutput, HealthResponse
from quality_assistance_backend.services.agent_client import agent_client

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await run_migrations()
    yield
    await engine.dispose()


app = FastAPI(
    title="Quality Assistance API",
    description="Backend API for the quality assistance web application.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def build_agent_message(payload: AssistanceInput) -> str:
    sections = [f"## Requirements\n{payload.requirements}"]
    if payload.user_stories:
        sections.append(f"## User Stories\n{payload.user_stories}")
    if payload.code_diffs:
        sections.append(f"## Code Diffs\n{payload.code_diffs}")
    sections.append(
        "\nProvide: (1) prioritized test cases, (2) suggested test data, "
        "(3) automation notes, (4) release risks."
    )
    return "\n\n".join(sections)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="backend")


@app.post("/api/assist", response_model=AssistanceOutput)
async def assist(
    payload: AssistanceInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssistanceOutput:
    record = AssistanceRequest(
        owner_id=current_user.id,
        session_id=payload.session_id,
        requirements=payload.requirements,
        user_stories=payload.user_stories,
        code_diffs=payload.code_diffs,
        status="processing",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    try:
        agent_result = await agent_client.assist(
            message=build_agent_message(payload),
            user_id=str(current_user.id),
            session_id=payload.session_id,
        )
        record.session_id = agent_result["session_id"]
        record.agent_response = agent_result["response"]
        record.status = "completed"
    except Exception as exc:
        record.status = "failed"
        record.agent_response = str(exc)
        await db.commit()
        raise HTTPException(status_code=502, detail=f"Agent service error: {exc}") from exc

    await db.commit()
    await db.refresh(record)

    return AssistanceOutput(
        id=record.id,
        session_id=record.session_id or "",
        response=record.agent_response or "",
        status=record.status,
        created_at=record.created_at,
    )
