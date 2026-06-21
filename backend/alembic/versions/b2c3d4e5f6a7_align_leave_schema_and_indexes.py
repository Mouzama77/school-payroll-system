"""align leave schema and indexes

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-21 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


leave_type_enum = postgresql.ENUM(
    "CASUAL",
    "SICK",
    "PAID",
    "UNPAID",
    name="leave_type",
    create_type=False,
)
leave_status_enum = postgresql.ENUM(
    "PENDING",
    "APPROVED",
    "REJECTED",
    name="leave_status",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    leave_type_enum.create(bind, checkfirst=True)
    leave_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "leaves",
        sa.Column(
            "leave_type",
            leave_type_enum,
            nullable=False,
            server_default="CASUAL",
        ),
    )
    op.alter_column("leaves", "leave_type", server_default=None)

    op.alter_column(
        "leaves",
        "status",
        existing_type=sa.String(length=20),
        type_=leave_status_enum,
        existing_nullable=False,
        server_default="PENDING",
        postgresql_using="upper(status)::leave_status",
    )
    op.alter_column("leaves", "status", server_default=None)

    op.add_column(
        "leaves",
        sa.Column("approved_by", sa.UUID(), nullable=True),
    )
    op.add_column(
        "leaves",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column(
        "leaves",
        "created_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        server_default=sa.text("now()"),
    )
    op.create_foreign_key(
        "fk_leaves_approved_by_users",
        "leaves",
        "users",
        ["approved_by"],
        ["id"],
    )
    op.create_index(op.f("ix_leaves_employee_id"), "leaves", ["employee_id"])
    op.create_index(op.f("ix_leaves_status"), "leaves", ["status"])
    op.create_index(op.f("ix_payrolls_employee_id"), "payrolls", ["employee_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_payrolls_employee_id"), table_name="payrolls")
    op.drop_index(op.f("ix_leaves_status"), table_name="leaves")
    op.drop_index(op.f("ix_leaves_employee_id"), table_name="leaves")
    op.drop_constraint("fk_leaves_approved_by_users", "leaves", type_="foreignkey")
    op.alter_column(
        "leaves",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
        server_default=None,
    )
    op.drop_column("leaves", "updated_at")
    op.drop_column("leaves", "approved_by")
    op.alter_column(
        "leaves",
        "status",
        existing_type=leave_status_enum,
        type_=sa.String(length=20),
        existing_nullable=False,
        postgresql_using="status::text",
    )
    op.drop_column("leaves", "leave_type")
    leave_status_enum.drop(op.get_bind(), checkfirst=True)
    leave_type_enum.drop(op.get_bind(), checkfirst=True)
