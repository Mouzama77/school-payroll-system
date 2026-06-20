"""align attendance table with model

Revision ID: 3fd4d5f0b210
Revises: af2802d72050
Create Date: 2026-06-20 11:35:40.821267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3fd4d5f0b210'
down_revision: Union[str, Sequence[str], None] = 'af2802d72050'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

attendance_status_enum = postgresql.ENUM(
    'PRESENT',
    'ABSENT',
    'HALF_DAY',
    name='attendance_status',
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('attendance', 'check_in')
    op.drop_column('attendance', 'check_out')

    attendance_status_enum.create(op.get_bind(), checkfirst=True)
    op.alter_column(
        'attendance',
        'status',
        existing_type=sa.String(length=20),
        type_=attendance_status_enum,
        existing_nullable=False,
        postgresql_using='status::attendance_status',
    )

    op.create_index(
        op.f('ix_attendance_employee_id'),
        'attendance',
        ['employee_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_attendance_date'),
        'attendance',
        ['date'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_attendance_date'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_employee_id'), table_name='attendance')

    op.alter_column(
        'attendance',
        'status',
        existing_type=attendance_status_enum,
        type_=sa.String(length=20),
        existing_nullable=False,
        postgresql_using='status::text',
    )
    attendance_status_enum.drop(op.get_bind(), checkfirst=True)

    op.add_column('attendance', sa.Column('check_in', sa.Time(), nullable=True))
    op.add_column('attendance', sa.Column('check_out', sa.Time(), nullable=True))
