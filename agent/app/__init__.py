import uvicorn

from app.config.settings import settings


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host=settings.agent_host,
        port=settings.agent_port,
        reload=True,
        log_level="info",
    )
