"""add repository_connections

Revision ID: a1b2c3d4e5f6
Revises: c343d3e8e3b5
Create Date: 2026-05-17 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "8dbea417dddd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    bind = op.get_bind()
    return set(inspect(bind).get_table_names())


def upgrade() -> None:
    if "repository_connections" in _table_names():
        return

    op.create_table(
        "repository_connections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("repo", sa.String(length=255), nullable=False),
        sa.Column("default_branch", sa.String(length=128), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_repository_connections_user_id"),
        "repository_connections",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    if "repository_connections" not in _table_names():
        return
    op.drop_index(op.f("ix_repository_connections_user_id"), table_name="repository_connections")
    op.drop_table("repository_connections")
