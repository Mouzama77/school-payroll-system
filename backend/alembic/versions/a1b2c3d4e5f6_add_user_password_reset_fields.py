"""add user password reset fields

Revision ID: a1b2c3d4e5f6
Revises: f8a1c2d3e4b5
Create Date: 2026-06-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f8a1c2d3e4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column('users', sa.Column('reset_token_hash', sa.String(), nullable=True))
    op.add_column(
        'users',
        sa.Column('reset_token_expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column('users', 'must_change_password', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'reset_token_expires_at')
    op.drop_column('users', 'reset_token_hash')
    op.drop_column('users', 'must_change_password')
