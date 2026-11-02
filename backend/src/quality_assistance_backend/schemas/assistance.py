import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


AssistanceAgent = Literal[
    "test_case_generation",
    "test_data_generation",
    "test_script_automation",
    "test_execution",
    "self_healing_test_scripts",
    "change_impact_analysis",
    "bug_report_generation",
    "test_summary_reporting",
    "release_readiness_evaluation",
]


class AssistanceInput(BaseModel):
    requirements: str = Field(..., min_length=1, max_length=20_000)
    user_stories: str | None = Field(default=None, max_length=20_000)
    code_diffs: str | None = Field(default=None, max_length=50_000)
    session_id: str | None = Field(default=None, max_length=128)
    human_guidance: str | None = Field(default=None, max_length=5000)
    target_agent: AssistanceAgent | None = None

    @field_validator("requirements", "user_stories", "code_diffs", "human_guidance")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if any(ord(char) < 32 and char not in "\t\n\r" for char in normalized):
            raise ValueError("Text contains unsupported control characters.")
        return normalized or None

    @field_validator("requirements")
    @classmethod
    def require_nonempty_requirements(cls, value: str) -> str:
        if not value:
            raise ValueError("Provide software requirements or context.")
        return value

    @model_validator(mode="after")
    def limit_total_input_size(self) -> "AssistanceInput":
        total_size = sum(
            len(value or "")
            for value in (
                self.requirements,
                self.user_stories,
                self.code_diffs,
                self.human_guidance,
            )
        )
        if total_size > 70_000:
            raise ValueError("The combined input is too long. Shorten it and try again.")
        return self


class AssistanceOutput(BaseModel):
    id: uuid.UUID
    session_id: str
    response: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
