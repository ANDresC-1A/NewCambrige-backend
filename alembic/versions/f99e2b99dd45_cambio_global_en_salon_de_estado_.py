"""cambio global en salon de estado boolean a string

Revision ID: f99e2b99dd45
Revises: d87d118ac979
Create Date: 2026-05-24 13:43:40.935865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f99e2b99dd45'
down_revision: Union[str, None] = '10cbe4088f45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():

    # PRESTAMO LIBRO - primero cambiar tipo, luego actualizar
    op.alter_column(
        "prestamo_libro", "estado",
        existing_type=sa.Boolean(),
        type_=sa.String(20),
        postgresql_using="CASE WHEN estado THEN 'Activo' ELSE 'Pendiente' END",
        nullable=False
    )

    # PRUEBA
    op.alter_column(
        "prueba", "estado",
        existing_type=sa.Boolean(),
        type_=sa.String(20),
        postgresql_using="CASE WHEN estado THEN 'Activo' ELSE 'Pendiente' END",
        nullable=True
    )

    # PUPITRES
    op.alter_column(
        "pupitres", "estado",
        existing_type=sa.Boolean(),
        type_=sa.String(20),
        postgresql_using="CASE WHEN estado THEN 'Activo' ELSE 'Pendiente' END",
        nullable=True
    )
def downgrade():
    op.alter_column("prestamo_libro", "estado",
        existing_type=sa.String(20),
        type_=sa.Boolean(),
        nullable=True
    )
    op.alter_column("prueba", "estado",
        existing_type=sa.String(20),
        type_=sa.Boolean(),
        nullable=True
    )
    op.alter_column("pupitres", "estado",
        existing_type=sa.String(20),
        type_=sa.Boolean(),
        nullable=True
    )