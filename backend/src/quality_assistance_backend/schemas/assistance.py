import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AssistanceInput(BaseModel):
    requirements: str = Field(..., min_length=1)
    user_stories: str | None = None
    code_diffs: str | None = None
    session_id: str | None = None


class AssistanceOutput(BaseModel):
    id: uuid.UUID
    session_id: str
    response: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
