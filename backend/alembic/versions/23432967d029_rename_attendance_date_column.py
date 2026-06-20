"""rename_attendance_date_column

Revision ID: 23432967d029
Revises: 3fd4d5f0b210
Create Date: 2026-06-20 12:07:18.011559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23432967d029'
down_revision: Union[str, Sequence[str], None] = '3fd4d5f0b210'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
