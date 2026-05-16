"""widen_password_hash_column

Revision ID: 8dbea417dddd
Revises: c343d3e8e3b5
Create Date: 2026-05-17 03:18:38.292629

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8dbea417dddd"
down_revision: Union[str, Sequence[str], None] = "c343d3e8e3b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        type_=sa.String(length=512),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=512),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
