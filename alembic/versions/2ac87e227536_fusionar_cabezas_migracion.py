"""fusionar_cabezas_migracion

Revision ID: 2ac87e227536
Revises: 397a33327c66, e8f933781a2f
Create Date: 2026-05-30 23:22:13.492663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ac87e227536'
down_revision: Union[str, None] = ('397a33327c66', 'e8f933781a2f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
