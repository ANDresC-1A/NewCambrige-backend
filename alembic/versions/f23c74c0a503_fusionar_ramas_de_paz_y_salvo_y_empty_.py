"""fusionar ramas de paz_y_salvo y empty_message

Revision ID: f23c74c0a503
Revises: 397a33327c66, e8f933781a2f
Create Date: 2026-05-28 09:01:58.773315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f23c74c0a503'
down_revision: Union[str, None] = ('397a33327c66', 'e8f933781a2f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
