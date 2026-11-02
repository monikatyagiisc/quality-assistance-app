"""add human review guidance to assistance requests

Revision ID: f1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2026-11-03 10:30:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "assistance_requests",
        sa.Column("human_guidance", sa.Text(), nullable=True),
    )
    op.add_column(
        "assistance_requests",
        sa.Column("target_agent", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("assistance_requests", "target_agent")
    op.drop_column("assistance_requests", "human_guidance")
