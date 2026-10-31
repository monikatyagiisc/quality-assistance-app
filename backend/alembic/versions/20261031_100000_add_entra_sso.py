"""add Microsoft Entra single sign-on

Revision ID: e7f8a9b0c1d2
Revises: d4e5f6a7b8c9
Create Date: 2026-10-31 10:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "password_hash", existing_type=sa.String(length=512), nullable=True)
    op.add_column("users", sa.Column("entra_tenant_id", sa.String(length=36), nullable=True))
    op.add_column("users", sa.Column("entra_object_id", sa.String(length=36), nullable=True))
    op.create_unique_constraint(
        "uq_users_entra_identity",
        "users",
        ["entra_tenant_id", "entra_object_id"],
    )
    op.create_table(
        "entra_oauth_states",
        sa.Column("state_digest", sa.String(length=64), nullable=False),
        sa.Column("nonce_digest", sa.String(length=64), nullable=False),
        sa.Column("code_verifier", sa.Text(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("flow", sa.String(length=16), server_default="login", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("state_digest"),
    )
    op.create_table(
        "entra_login_tickets",
        sa.Column("ticket_digest", sa.String(length=64), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ticket_digest"),
    )
    op.create_index(
        op.f("ix_entra_login_tickets_user_id"),
        "entra_login_tickets",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_entra_login_tickets_user_id"), table_name="entra_login_tickets")
    op.drop_table("entra_login_tickets")
    op.drop_table("entra_oauth_states")
    op.drop_constraint("uq_users_entra_identity", "users", type_="unique")
    op.drop_column("users", "entra_object_id")
    op.drop_column("users", "entra_tenant_id")
    op.alter_column("users", "password_hash", existing_type=sa.String(length=512), nullable=False)
