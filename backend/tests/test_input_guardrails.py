import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from quality_assistance_backend.schemas import AssistanceInput
from quality_assistance_backend.services.input_guardrails import validate_stlc_scope


@pytest.mark.parametrize(
    "requirements",
    [
        "Can you write a poem about winter?",
        "Test my knowledge of ancient history.",
        "What is the capital of France?",
    ],
)
def test_rejects_requests_outside_software_quality_scope(requirements: str) -> None:
    payload = AssistanceInput(requirements=requirements)

    with pytest.raises(HTTPException) as error:
        validate_stlc_scope(payload)

    assert error.value.status_code == 422
    assert error.value.detail["code"] == "out_of_scope"


@pytest.mark.parametrize(
    "requirements",
    [
        "Generate test cases for the password reset feature.",
        "The application should lock the account after five failed login attempts.",
        "Analyze this test run and report the failed cases.",
    ],
)
def test_accepts_software_and_stlc_context(requirements: str) -> None:
    validate_stlc_scope(AssistanceInput(requirements=requirements))


def test_limits_field_and_combined_request_sizes() -> None:
    with pytest.raises(ValidationError):
        AssistanceInput(requirements="x" * 20_001)

    with pytest.raises(ValidationError):
        AssistanceInput(
            requirements="app " + "x" * 19_996,
            user_stories="x" * 20_000,
            code_diffs="x" * 40_000,
        )


def test_rejects_unsupported_control_characters() -> None:
    with pytest.raises(ValidationError):
        AssistanceInput(requirements="Test the app.\x00")


def test_human_guidance_cannot_make_an_unrelated_request_in_scope() -> None:
    payload = AssistanceInput(
        requirements="Tell me a joke.",
        human_guidance="Generate test cases.",
    )

    with pytest.raises(HTTPException):
        validate_stlc_scope(payload)
