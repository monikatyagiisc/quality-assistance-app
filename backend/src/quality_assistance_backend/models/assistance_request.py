from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quality_assistance_backend.db import Base

if TYPE_CHECKING:
    from quality_assistance_backend.models.user import User


class AssistanceRequest(Base):
    __tablename__ = "assistance_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    requirements: Mapped[str] = mapped_column(Text)
    user_stories: Mapped[str | None] = mapped_column(Text, nullable=True)
    code_diffs: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner: Mapped[User] = relationship(back_populates="assistance_requests")
