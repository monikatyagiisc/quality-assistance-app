import httpx
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from quality_assistance_backend.config import settings
from quality_assistance_backend.db import engine
from quality_assistance_backend.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="backend")


@router.get("/ready", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.agent_service_url.rstrip('/')}/health")
            response.raise_for_status()
    except (httpx.HTTPError, SQLAlchemyError, OSError) as exc:
        raise HTTPException(status_code=503, detail="Service dependencies are not ready") from exc
    return HealthResponse(status="ok", service="backend")
