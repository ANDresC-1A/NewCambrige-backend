"""Agregar fecha_pago a tabla pupitres

Revision ID: 893592e6ba36
Revises: aab04861be67
Create Date: 2026-05-26 13:53:12.096996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '893592e6ba36'
down_revision: Union[str, None] = 'aab04861be67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pupitres', sa.Column('fecha_pago', sa.Date(), nullable=True))

def downgrade() -> None:
    op.drop_column('pupitres', 'fecha_pago')