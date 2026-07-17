"""add password_reset_otps table

Creates the password_reset_otps table used by the OTP-based forgot-password
flow. Stores only a bcrypt hash of the 6-digit OTP with a 10-minute expiry,
attempt counter, verification/consumption flags, and a short-lived post-
verification reset token hash.

Revision ID: f0a1b2c3d4e5
Revises: d5e6f7a8b9c0
Create Date: 2026-07-16 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_otps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("otp_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "attempts", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "verified",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "consumed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("reset_token_hash", sa.String(), nullable=True),
        sa.Column(
            "reset_token_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_password_reset_otps_user_id",
        "password_reset_otps",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_password_reset_otps_user_id", table_name="password_reset_otps"
    )
    op.drop_table("password_reset_otps")
