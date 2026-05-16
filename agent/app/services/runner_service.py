from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent.root_agent import root_agent
from app.callbacks.helpers import truncate
from app.config.logging_config import get_logger
from app.config.settings import settings

logger = get_logger(__name__)


class AgentRunnerService:
    def __init__(self) -> None:
        self._runner = InMemoryRunner(
            agent=root_agent,
            app_name=settings.app_name,
        )
        # Allow new session IDs (and re-create after process restarts) without SessionNotFoundError.
        self._runner.auto_create_session = True

    async def _resolve_session_id(self, *, user_id: str, session_id: str | None) -> str:
        if session_id:
            return session_id
        session = await self._runner.session_service.create_session(
            app_name=self._runner.app_name,
            user_id=user_id,
        )
        return session.id

    async def run(self, *, user_id: str, session_id: str | None, message: str) -> tuple[str, str]:
        session_id = await self._resolve_session_id(user_id=user_id, session_id=session_id)
        logger.info(
            "runner.start user_id=%s session_id=%s message_len=%s",
            user_id,
            session_id,
            len(message),
        )
        logger.debug("runner.input message=%s", truncate(message))

        user_message = types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )

        final_text: list[str] = []
        event_count = 0
        async for event in self._runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            event_count += 1
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text.append(part.text)

        response = "\n".join(final_text).strip() or "No response generated."
        logger.info(
            "runner.end user_id=%s session_id=%s events=%s response_len=%s",
            user_id,
            session_id,
            event_count,
            len(response),
        )
        logger.debug("runner.output response=%s", truncate(response))
        return session_id, response


runner_service = AgentRunnerService()
