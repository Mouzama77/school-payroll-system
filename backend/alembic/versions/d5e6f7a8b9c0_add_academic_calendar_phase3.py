"""add academic_calendar table

Phase 3 — Req 15.1

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-07-01 15:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "academic_calendar",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False, unique=True),
        sa.Column("day_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_academic_calendar_date",
        "academic_calendar",
        ["date"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_academic_calendar_date", table_name="academic_calendar")
    op.drop_table("academic_calendar")
