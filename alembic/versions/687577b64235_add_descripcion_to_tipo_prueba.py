from alembic import op
import sqlalchemy as sa

revision = "xxxx"  # el que te generó alembic
down_revision = "8598fe908090"  # tu head anterior (IMPORTANTE)
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "tipo_prueba",
        sa.Column("descripcion", sa.Text(), nullable=True)
    )

def downgrade():
    op.drop_column("tipo_prueba", "descripcion")