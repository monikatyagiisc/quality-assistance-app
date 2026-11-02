import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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
    requirements: str = Field(..., min_length=1)
    user_stories: str | None = None
    code_diffs: str | None = None
    session_id: str | None = None
    human_guidance: str | None = Field(default=None, max_length=5000)
    target_agent: AssistanceAgent | None = None


class AssistanceOutput(BaseModel):
    id: uuid.UUID
    session_id: str
    response: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
