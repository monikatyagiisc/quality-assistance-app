import uuid
from collections.abc import AsyncIterator

from google.adk.runners import InMemoryRunner
from google.genai import types

from quality_assistance_agent.agent import root_agent
from quality_assistance_agent.settings import settings


class AgentRunnerService:
    def __init__(self) -> None:
        self._runner = InMemoryRunner(
            agent=root_agent,
            app_name=settings.app_name,
        )

    async def run(self, *, user_id: str, session_id: str | None, message: str) -> tuple[str, str]:
        session_id = session_id or str(uuid.uuid4())
        user_message = types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )

        final_text: list[str] = []
        async for event in self._runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text.append(part.text)

        response = "\n".join(final_text).strip() or "No response generated."
        return session_id, response


runner_service = AgentRunnerService()
