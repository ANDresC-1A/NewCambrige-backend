"""merge heads

Revision ID: 0616eb0b3d73
Revises: 8438a9245df3, ec893dcc0fe4
Create Date: 2026-06-03 23:04:57.045531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0616eb0b3d73'
down_revision: Union[str, None] = ('8438a9245df3', 'ec893dcc0fe4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
