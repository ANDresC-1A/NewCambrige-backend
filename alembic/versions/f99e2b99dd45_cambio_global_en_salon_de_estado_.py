"""cambio global en salon de estado boolean a string

Revision ID: f99e2b99dd45
Revises: d87d118ac979
Create Date: 2026-05-24 13:43:40.935865
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'f99e2b99dd45'
down_revision: Union[str, None] = '10cbe4088f45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def convertir_estado(tabla, nullable=True):
    bind = op.get_bind()
    inspector = inspect(bind)

    columnas = inspector.get_columns(tabla)

    estado_col = next((c for c in columnas if c["name"] == "estado"), None)

    if not estado_col:
        return

    tipo_actual = str(estado_col["type"]).lower()

    if "boolean" in tipo_actual:
        op.alter_column(
            tabla,
            "estado",
            existing_type=sa.Boolean(),
            type_=sa.String(20),
            postgresql_using="""
                CASE
                    WHEN estado = true THEN 'Activo'
                    ELSE 'Pendiente'
                END
            """,
            nullable=nullable
        )

    else:
        op.alter_column(
            tabla,
            "estado",
            existing_type=estado_col["type"],
            type_=sa.String(20),
            existing_nullable=nullable
        )


def upgrade():

    convertir_estado("prestamo_libro", nullable=False)
    convertir_estado("prueba", nullable=True)
    convertir_estado("pupitres", nullable=True)


def downgrade():

    op.alter_column(
        "prestamo_libro",
        "estado",
        existing_type=sa.String(20),
        type_=sa.Boolean(),
        nullable=True
    )

    op.alter_column(
        "prueba",
        "estado",
        existing_type=sa.String(20),
        type_=sa.Boolean(),
        nullable=True
    )

    op.alter_column(
        "pupitres",
        "estado",
        existing_type=sa.String(20),
        type_=sa.Boolean(),
        nullable=True
    )