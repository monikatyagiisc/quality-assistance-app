from pydantic import BaseModel, Field


class AssistRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt for the quality assistant.")
    user_id: str = Field(default="default_user")
    session_id: str | None = Field(default=None, description="Reuse a session for multi-turn context.")


class AssistResponse(BaseModel):
    session_id: str
    response: str
