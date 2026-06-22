"""merge leave and attendance heads

Revision ID: 67b419aadb77
Revises: b2c3d4e5f6a7, c1d2e3f4a5b6
Create Date: 2026-06-22 22:20:54.739605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67b419aadb77'
down_revision: Union[str, Sequence[str], None] = ('b2c3d4e5f6a7', 'c1d2e3f4a5b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
