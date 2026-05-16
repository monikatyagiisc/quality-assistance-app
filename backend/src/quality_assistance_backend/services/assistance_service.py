from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from quality_assistance_backend.models import AssistanceRequest, User
from quality_assistance_backend.schemas import AssistanceInput, AssistanceOutput
from quality_assistance_backend.services.agent_client import agent_client


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


async def run_assistance(
    *,
    db: AsyncSession,
    current_user: User,
    payload: AssistanceInput,
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
