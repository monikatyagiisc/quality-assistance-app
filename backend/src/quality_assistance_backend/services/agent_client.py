import httpx

from quality_assistance_backend.config import settings
from quality_assistance_backend.services.agent_errors import (
    AgentServiceError,
    map_connection_error,
    parse_agent_http_error,
)


class AgentClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.agent_service_url).rstrip("/")

    async def assist(
        self,
        *,
        message: str,
        user_id: str,
        session_id: str | None,
    ) -> dict[str, str]:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/assist",
                    json={
                        "message": message,
                        "user_id": user_id,
                        "session_id": session_id,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise parse_agent_http_error(exc) from exc
        except httpx.RequestError as exc:
            raise map_connection_error(exc) from exc


agent_client = AgentClient()
