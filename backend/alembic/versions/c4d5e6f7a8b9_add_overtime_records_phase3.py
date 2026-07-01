"""add overtime_records table

Phase 3 — Req 19.1

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-07-01 14:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "overtime_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("hours", sa.Double(), nullable=False),
        sa.Column(
            "rate_multiplier",
            sa.Double(),
            nullable=False,
            server_default="1.5",
        ),
    )
    op.create_index(
        "ix_overtime_records_employee_id",
        "overtime_records",
        ["employee_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_overtime_records_employee_id", table_name="overtime_records")
    op.drop_table("overtime_records")
