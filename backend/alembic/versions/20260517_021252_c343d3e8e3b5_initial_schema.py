"""initial_schema

Revision ID: c343d3e8e3b5
Revises:
Create Date: 2026-05-17 02:12:52.849432

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "c343d3e8e3b5"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    bind = op.get_bind()
    return set(inspect(bind).get_table_names())


def _column_names(table: str) -> set[str]:
    bind = op.get_bind()
    return {column["name"] for column in inspect(bind).get_columns(table)}


def upgrade() -> None:
    tables = _table_names()

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    if "assistance_requests" not in tables:
        op.create_table(
            "assistance_requests",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("owner_id", sa.UUID(), nullable=False),
            sa.Column("session_id", sa.String(length=128), nullable=True),
            sa.Column("requirements", sa.Text(), nullable=False),
            sa.Column("user_stories", sa.Text(), nullable=True),
            sa.Column("code_diffs", sa.Text(), nullable=True),
            sa.Column("agent_response", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
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
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_assistance_requests_owner_id"),
            "assistance_requests",
            ["owner_id"],
            unique=False,
        )
        return

    columns = _column_names("assistance_requests")

    if "owner_id" not in columns:
        op.add_column("assistance_requests", sa.Column("owner_id", sa.UUID(), nullable=True))
        op.execute(
            """
            UPDATE assistance_requests
            SET owner_id = (
                SELECT id FROM users ORDER BY created_at ASC LIMIT 1
            )
            WHERE owner_id IS NULL
            """
        )
        op.alter_column("assistance_requests", "owner_id", nullable=False)

    if "ix_assistance_requests_owner_id" not in {
        index["name"] for index in inspect(op.get_bind()).get_indexes("assistance_requests")
    }:
        op.create_index(
            op.f("ix_assistance_requests_owner_id"),
            "assistance_requests",
            ["owner_id"],
            unique=False,
        )

    foreign_keys = inspect(op.get_bind()).get_foreign_keys("assistance_requests")
    has_owner_fk = any("owner_id" in (fk.get("constrained_columns") or []) for fk in foreign_keys)
    if not has_owner_fk:
        op.create_foreign_key(
            "fk_assistance_requests_owner_id_users",
            "assistance_requests",
            "users",
            ["owner_id"],
            ["id"],
        )

    if "user_id" in columns:
        op.drop_column("assistance_requests", "user_id")


def downgrade() -> None:
    tables = _table_names()

    if "assistance_requests" in tables:
        op.drop_index(op.f("ix_assistance_requests_owner_id"), table_name="assistance_requests")
        op.drop_table("assistance_requests")

    if "users" in tables:
        op.drop_index(op.f("ix_users_email"), table_name="users")
        op.drop_table("users")
