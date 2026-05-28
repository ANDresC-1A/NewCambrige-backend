"""add fecha_pago to prueba

Revision ID: 5d315bc2cc20
Revises: xxxx
Create Date: 2026-05-23 22:52:45.342084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d315bc2cc20'
down_revision: Union[str, None] = 'xxxx'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "prueba",
        sa.Column("fecha_pago", sa.Date(), nullable=True)
    )


def downgrade():
    op.drop_column("prueba", "fecha_pago")