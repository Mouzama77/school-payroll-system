"""align late_penalty_rules schema for Phase 2

Replaces the original late_days_min/deduction_amount columns with
min_late_minutes/max_late_minutes/deduction_type as required by Req 12.1.
Also seeds the four default tier rows.

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-07-01 00:00:00.000000
"""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default tier rows required by Req 12.1 / tasks.md §15.3
_DEFAULT_TIERS = [
    {
        "id": str(uuid.UUID("10000000-0000-0000-0000-000000000001")),
        "min_late_minutes": 0,
        "max_late_minutes": 10,
        "deduction_type": "none",
        "label": "Grace period (0–10 min)",
    },
    {
        "id": str(uuid.UUID("10000000-0000-0000-0000-000000000002")),
        "min_late_minutes": 11,
        "max_late_minutes": 30,
        "deduction_type": "warning",
        "label": "Warning (11–30 min)",
    },
    {
        "id": str(uuid.UUID("10000000-0000-0000-0000-000000000003")),
        "min_late_minutes": 31,
        "max_late_minutes": 60,
        "deduction_type": "half_day",
        "label": "Half-day deduction (31–60 min)",
    },
    {
        "id": str(uuid.UUID("10000000-0000-0000-0000-000000000004")),
        "min_late_minutes": 61,
        "max_late_minutes": None,
        "deduction_type": "full_day",
        "label": "Full-day deduction (>60 min)",
    },
]


def upgrade() -> None:
    # 1. Truncate any existing rows (original schema had different columns)
    op.execute("TRUNCATE TABLE late_penalty_rules")

    # 2. Drop old index and columns (no unique constraint exists in the DB)
    op.drop_index("ix_late_penalty_rules_late_days_min", table_name="late_penalty_rules")
    op.drop_column("late_penalty_rules", "late_days_min")
    op.drop_column("late_penalty_rules", "deduction_amount")

    # 3. Add new columns
    op.add_column(
        "late_penalty_rules",
        sa.Column("min_late_minutes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("late_penalty_rules", "min_late_minutes", server_default=None)

    op.add_column(
        "late_penalty_rules",
        sa.Column("max_late_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "late_penalty_rules",
        sa.Column("deduction_type", sa.String(20), nullable=False, server_default="none"),
    )
    op.alter_column("late_penalty_rules", "deduction_type", server_default=None)

    # 4. Add index on min_late_minutes for fast tier lookup
    op.create_index(
        "ix_late_penalty_rules_min_late_minutes",
        "late_penalty_rules",
        ["min_late_minutes"],
    )

    # 5. Seed the four default tier rows
    table = sa.table(
        "late_penalty_rules",
        sa.column("id", sa.String),
        sa.column("min_late_minutes", sa.Integer),
        sa.column("max_late_minutes", sa.Integer),
        sa.column("deduction_type", sa.String),
        sa.column("label", sa.String),
    )
    op.bulk_insert(table, _DEFAULT_TIERS)


def downgrade() -> None:
    op.drop_index("ix_late_penalty_rules_min_late_minutes", table_name="late_penalty_rules")
    op.execute("TRUNCATE TABLE late_penalty_rules")
    op.drop_column("late_penalty_rules", "deduction_type")
    op.drop_column("late_penalty_rules", "max_late_minutes")
    op.drop_column("late_penalty_rules", "min_late_minutes")
    op.add_column(
        "late_penalty_rules",
        sa.Column("late_days_min", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("late_penalty_rules", "late_days_min", server_default=None)
    op.add_column(
        "late_penalty_rules",
        sa.Column("deduction_amount", sa.Float(), nullable=False, server_default="0"),
    )
    op.alter_column("late_penalty_rules", "deduction_amount", server_default=None)
    op.create_index(
        "ix_late_penalty_rules_late_days_min",
        "late_penalty_rules",
        ["late_days_min"],
    )
