from quality_assistance_backend.schemas.assistance import AssistanceInput
from quality_assistance_backend.services.assistance_service import build_agent_message


def test_build_agent_message_includes_review_guidance_and_selected_specialist() -> None:
    payload = AssistanceInput(
        requirements="Users can reset their passwords.",
        user_stories="As a user, I want to reset my password.",
        human_guidance="Include expired-token cases and prioritize high-risk paths.",
        target_agent="test_case_generation",
    )

    message = build_agent_message(payload)

    assert "## Requirements\nUsers can reset their passwords." in message
    assert "## User Stories\nAs a user, I want to reset my password." in message
    assert "Include expired-token cases and prioritize high-risk paths." in message
    assert "Test Case Generation specialist" in message
    assert "do not delegate to other specialists" in message
    assert "suggested test data" not in message


def test_build_agent_message_keeps_full_review_default() -> None:
    message = build_agent_message(AssistanceInput(requirements="Test sign-in."))

    assert "prioritized test cases" in message
    assert "suggested test data" in message
    assert "automation notes" in message
    assert "release risks" in message
