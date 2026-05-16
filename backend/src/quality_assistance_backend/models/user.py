from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quality_assistance_backend.db import Base

if TYPE_CHECKING:
    from quality_assistance_backend.models.assistance_request import AssistanceRequest
    from quality_assistance_backend.models.repository_connection import RepositoryConnection


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assistance_requests: Mapped[list[AssistanceRequest]] = relationship(
        back_populates="owner",
    )
    repository_connection: Mapped[RepositoryConnection | None] = relationship(
        back_populates="user",
        uselist=False,
    )
