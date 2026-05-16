import uvicorn

from quality_assistance_backend.config import settings


def main() -> None:
    uvicorn.run(
        "quality_assistance_backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
