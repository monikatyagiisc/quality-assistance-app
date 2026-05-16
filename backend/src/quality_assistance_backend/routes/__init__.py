from fastapi import APIRouter

from quality_assistance_backend.routes import assistance, auth, health, settings

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(assistance.router)
api_router.include_router(settings.router)

__all__ = ["api_router", "assistance", "auth", "health", "settings"]
