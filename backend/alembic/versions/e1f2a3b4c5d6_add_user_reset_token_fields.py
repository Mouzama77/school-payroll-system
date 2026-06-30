"""add user reset token fields

Adds reset_token_hash and reset_token_expires_at columns to the users table.
These are used by the password-reset flow in AuthService.

Revision ID: e1f2a3b4c5d6
Revises: 67aa4e2bdcdc
Create Date: 2026-06-30 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "67aa4e2bdcdc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("reset_token_hash", sa.String(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("reset_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "reset_token_expires_at")
    op.drop_column("users", "reset_token_hash")
