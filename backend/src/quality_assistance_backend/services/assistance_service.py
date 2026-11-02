from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from quality_assistance_backend.models import AssistanceRequest, User
from quality_assistance_backend.schemas import AssistanceInput, AssistanceOutput
from quality_assistance_backend.services.agent_client import agent_client
from quality_assistance_backend.services.agent_errors import AgentServiceError

AGENT_LABELS = {
    "test_case_generation": "Test Case Generation",
    "test_data_generation": "Test Data Generation",
    "test_script_automation": "Test Script Automation",
    "test_execution": "Test Execution",
    "self_healing_test_scripts": "Self-Healing Test Scripts",
    "change_impact_analysis": "Change Impact Analysis",
    "bug_report_generation": "Bug Report Generation",
    "test_summary_reporting": "Test Summary Reporting",
    "release_readiness_evaluation": "Release Readiness Evaluation",
}


def build_agent_message(payload: AssistanceInput) -> str:
    sections = [f"## Requirements\n{payload.requirements}"]
    if payload.user_stories:
        sections.append(f"## User Stories\n{payload.user_stories}")
    if payload.code_diffs:
        sections.append(f"## Code Diffs\n{payload.code_diffs}")
    if payload.human_guidance:
        sections.append(
            "## Human review instructions\n"
            "Apply the user's requested refinements to this analysis:\n"
            f"{payload.human_guidance}"
        )
    if payload.target_agent:
        agent_label = AGENT_LABELS[payload.target_agent]
        sections.append(
            "## Requested specialist focus\n"
            f"The user selected the {agent_label} specialist. Route this request to that "
            "specialist only; do not delegate to other specialists. Return a focused response "
            "for this specialty using the supplied context."
        )
    else:
        sections.append(
            "Provide: (1) prioritized test cases, (2) suggested test data, "
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
        human_guidance=payload.human_guidance,
        target_agent=payload.target_agent,
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
    except AgentServiceError as exc:
        record.status = "failed"
        record.agent_response = exc.message
        await db.commit()
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code},
        ) from exc
    except Exception as exc:
        record.status = "failed"
        record.agent_response = str(exc)
        await db.commit()
        raise HTTPException(
            status_code=502,
            detail={
                "message": "We could not generate quality assistance right now. Please try again shortly.",
                "code": "assistance_failed",
            },
        ) from exc

    await db.commit()
    await db.refresh(record)

    return AssistanceOutput(
        id=record.id,
        session_id=record.session_id or "",
        response=record.agent_response or "",
        status=record.status,
        created_at=record.created_at,
    )
