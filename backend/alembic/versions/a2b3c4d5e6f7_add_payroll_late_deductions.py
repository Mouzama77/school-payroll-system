"""add late_deductions column to payrolls

Req 12.7 — payroll snapshot must store total late deductions.

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-07-01 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "payrolls",
        sa.Column(
            "late_deductions",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    # Remove server_default so application controls the value going forward
    op.alter_column("payrolls", "late_deductions", server_default=None)


def downgrade() -> None:
    op.drop_column("payrolls", "late_deductions")
