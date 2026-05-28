"""add estado_fisico to inventario_libro

Revision ID: 22e732c2e318
Revises: 5d315bc2cc20
Create Date: 2026-05-24 12:00:51.715885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22e732c2e318'
down_revision: Union[str, None] = '5d315bc2cc20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "inventario_libro",
        sa.Column("estado_fisico", sa.String(50), nullable=True)
    )

def downgrade():
    op.drop_column("inventario_libro", "estado_fisico")