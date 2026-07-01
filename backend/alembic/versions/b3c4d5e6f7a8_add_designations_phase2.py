"""add designations table and employee designation_id FK

Phase 2 — Req 13.1, 13.4

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-07-01 13:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create designations table (Req 13.1)
    op.create_table(
        "designations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
    )

    # Add nullable designation_id FK to employees (Req 13.4)
    op.add_column(
        "employees",
        sa.Column(
            "designation_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_employees_designation_id",
        "employees",
        "designations",
        ["designation_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_employees_designation_id", "employees", type_="foreignkey")
    op.drop_column("employees", "designation_id")
    op.drop_table("designations")
