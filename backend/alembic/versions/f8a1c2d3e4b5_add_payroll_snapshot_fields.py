"""add payroll snapshot fields

Revision ID: f8a1c2d3e4b5
Revises: 0ab52f8637a6
Create Date: 2026-06-20 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a1c2d3e4b5'
down_revision: Union[str, Sequence[str], None] = '0ab52f8637a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'payrolls',
        sa.Column('total_absent', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'payrolls',
        sa.Column('total_half_days', sa.Integer(), nullable=False, server_default='0'),
    )
    op.alter_column('payrolls', 'total_absent', server_default=None)
    op.alter_column('payrolls', 'total_half_days', server_default=None)
    op.create_unique_constraint(
        'uq_payroll_employee_month',
        'payrolls',
        ['employee_id', 'month'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_payroll_employee_month', 'payrolls', type_='unique')
    op.drop_column('payrolls', 'total_half_days')
    op.drop_column('payrolls', 'total_absent')
