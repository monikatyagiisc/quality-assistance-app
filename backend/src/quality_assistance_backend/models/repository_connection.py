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


class RepositoryConnection(Base):
    """Per-user Git provider credentials and default repository."""

    __tablename__ = "repository_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), default="github")
    owner: Mapped[str] = mapped_column(String(255))
    repo: Mapped[str] = mapped_column(String(255))
    default_branch: Mapped[str] = mapped_column(String(128), default="main")
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="repository_connection")
