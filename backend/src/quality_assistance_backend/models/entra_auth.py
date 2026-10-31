from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from quality_assistance_backend.db import Base


class EntraOAuthState(Base):
    __tablename__ = "entra_oauth_states"

    state_digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    nonce_digest: Mapped[str] = mapped_column(String(64))
    code_verifier: Mapped[str] = mapped_column(Text)
    user_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    flow: Mapped[str] = mapped_column(String(16), default="login")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EntraLoginTicket(Base):
    __tablename__ = "entra_login_tickets"

    ticket_digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
