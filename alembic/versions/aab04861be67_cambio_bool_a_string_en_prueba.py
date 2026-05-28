"""cambio bool a string en prueba

Revision ID: aab04861be67
Revises: f99e2b99dd45
Create Date: 2026-05-24 ...

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'aab04861be67'
down_revision: Union[str, None] = 'f99e2b99dd45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE prueba
        SET estado = 'Pendiente'
        WHERE estado IS NULL;
    """)


def downgrade() -> None:
    pass