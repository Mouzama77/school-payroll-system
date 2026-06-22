"""add attendance override fields

Adds ON_LEAVE and LATE values to the attendance_status enum, then adds the
four override audit columns: is_override, override_reason, overridden_by,
and overridden_at.

Revision ID: c1d2e3f4a5b6
Revises: f8a1c2d3e4b5
Create Date: 2026-06-22 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "f8a1c2d3e4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE attendance_status ADD VALUE IF NOT EXISTS 'ON_LEAVE'")
    op.execute("ALTER TYPE attendance_status ADD VALUE IF NOT EXISTS 'LATE'")

    op.add_column(
        "attendance",
        sa.Column(
            "is_override",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Remove the server_default so new rows rely on the ORM default only.
    op.alter_column("attendance", "is_override", server_default=None)

    op.add_column(
        "attendance",
        sa.Column("override_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "attendance",
        sa.Column(
            "overridden_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "attendance",
        sa.Column(
            "overridden_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_attendance_overridden_by_users",
        "attendance",
        "users",
        ["overridden_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_attendance_overridden_by_users", "attendance", type_="foreignkey"
    )
    op.drop_column("attendance", "overridden_at")
    op.drop_column("attendance", "overridden_by")
    op.drop_column("attendance", "override_reason")
    op.drop_column("attendance", "is_override")
    # Note: PostgreSQL does not support removing enum values without
    # recreating the type. ON_LEAVE and LATE are left in the enum on downgrade.
