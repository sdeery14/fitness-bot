"""add_exercise_catalog_table

Revision ID: b82aa00151aa
Revises: cd728d134263
Create Date: 2025-12-09 21:37:16.380881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'b82aa00151aa'
down_revision: Union[str, None] = 'cd728d134263'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create exercise_catalog table for curated exercise database
    op.create_table(
        'exercise_catalog',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('exercise_type', sa.String(length=100), nullable=False),
        sa.Column('target_muscle_groups', sa.JSON(), nullable=False),
        sa.Column('equipment_required', sa.JSON(), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('form_cues', sa.JSON(), nullable=True),
        sa.Column('alternatives', sa.JSON(), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id', name='exercise_catalog_id_key')
    )
    
    # Create indexes
    op.create_index('ix_exercise_catalog_name', 'exercise_catalog', ['name'])
    op.create_index('ix_exercise_catalog_difficulty', 'exercise_catalog', ['difficulty'])
    op.create_index('ix_exercise_catalog_exercise_type', 'exercise_catalog', ['exercise_type'])
    
    # Create pgvector index for semantic search
    op.execute("""
        CREATE INDEX idx_exercise_catalog_embedding 
        ON exercise_catalog 
        USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100)
    """)


def downgrade() -> None:
    op.drop_index('idx_exercise_catalog_embedding', table_name='exercise_catalog')
    op.drop_index('ix_exercise_catalog_exercise_type', table_name='exercise_catalog')
    op.drop_index('ix_exercise_catalog_difficulty', table_name='exercise_catalog')
    op.drop_index('ix_exercise_catalog_name', table_name='exercise_catalog')
    op.drop_table('exercise_catalog')
