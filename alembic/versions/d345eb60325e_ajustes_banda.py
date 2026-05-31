"""ajustes_banda

Revision ID: d345eb60325e
Revises: 2ac87e227536
Create Date: 2024-05-30 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd345eb60325e'
down_revision: Union[str, None] = '2ac87e227536'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Crear tabla de auditoria_banda
    op.create_table('auditoria_banda',
        sa.Column('id_auditoria', sa.Integer(), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=True),
        sa.Column('hora', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('id_usuario', sa.Integer(), nullable=False),
        sa.Column('nombre_usuario', sa.String(length=200), nullable=False),
        sa.Column('modulo_origen', sa.String(length=100), nullable=False),
        sa.Column('tipo_accion', sa.String(length=100), nullable=False),
        sa.Column('entidad_afectada', sa.String(length=300), nullable=False),
        sa.Column('valor_anterior', sa.String(length=200), nullable=True),
        sa.Column('valor_nuevo', sa.String(length=200), nullable=True),
        sa.Column('resultado', sa.String(length=50), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id_auditoria')
    )
    op.create_index(op.f('ix_auditoria_banda_id_auditoria'), 'auditoria_banda', ['id_auditoria'], unique=False)

    # 2. Modificar inventario_instrumento
    op.add_column('inventario_instrumento', sa.Column('codigo', sa.Integer(), nullable=True))
    op.add_column('inventario_instrumento', sa.Column('cantidad_total', sa.Integer(), server_default='1', nullable=False))
    op.add_column('inventario_instrumento', sa.Column('cantidad_disponible', sa.Integer(), server_default='1', nullable=False))
    op.add_column('inventario_instrumento', sa.Column('estado', sa.String(length=50), server_default='Activo', nullable=False))
    op.create_unique_constraint('uq_inventario_codigo', 'inventario_instrumento', ['codigo'])
    op.drop_column('inventario_instrumento', 'disponible')

    # 3. Modificar prestamo_instrumento
    op.add_column('prestamo_instrumento', sa.Column('estado_al_devolver', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Revertir prestamo_instrumento
    op.drop_column('prestamo_instrumento', 'estado_al_devolver')

    # Revertir inventario_instrumento
    op.add_column('inventario_instrumento', sa.Column('disponible', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_constraint('uq_inventario_codigo', 'inventario_instrumento', type_='unique')
    op.drop_column('inventario_instrumento', 'estado')
    op.drop_column('inventario_instrumento', 'cantidad_disponible')
    op.drop_column('inventario_instrumento', 'cantidad_total')
    op.drop_column('inventario_instrumento', 'codigo')

    # Revertir auditoria_banda
    op.drop_index(op.f('ix_auditoria_banda_id_auditoria'), table_name='auditoria_banda')
    op.drop_table('auditoria_banda')