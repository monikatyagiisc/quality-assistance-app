import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


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


class HealthResponse(BaseModel):
    status: str
    service: str
