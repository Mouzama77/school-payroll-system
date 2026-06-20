"""add_attendance_constraints

Revision ID: 0ab52f8637a6
Revises: 23432967d029
Create Date: 2026-06-20 18:10:39.314413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ab52f8637a6'
down_revision: Union[str, Sequence[str], None] = '23432967d029'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'attendance',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE attendance SET updated_at = created_at WHERE updated_at IS NULL"
    )
    op.alter_column('attendance', 'updated_at', nullable=False)
    op.create_unique_constraint(
        'uq_attendance_employee_date',
        'attendance',
        ['employee_id', 'date'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'uq_attendance_employee_date',
        'attendance',
        type_='unique',
    )
    op.drop_column('attendance', 'updated_at')
