"""add disponible to inventario_libro

Revision ID: 10cbe4088f45
Revises: ea8d29c24875
Create Date: 2026-05-24 12:25:40.387066

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10cbe4088f45'
down_revision: Union[str, None] = 'ea8d29c24875'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='inventario_libro'
                AND column_name='disponible'
            ) THEN
                ALTER TABLE inventario_libro
                ADD COLUMN disponible BOOLEAN DEFAULT true;
            END IF;
        END $$;
    """)

def downgrade():
    op.drop_column("inventario_libro", "disponible")