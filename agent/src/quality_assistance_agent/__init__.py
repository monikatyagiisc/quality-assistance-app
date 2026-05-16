import uvicorn

from quality_assistance_agent.settings import settings


def main() -> None:
    uvicorn.run(
        "quality_assistance_agent.server:app",
        host=settings.agent_host,
        port=settings.agent_port,
        reload=True,
    )
