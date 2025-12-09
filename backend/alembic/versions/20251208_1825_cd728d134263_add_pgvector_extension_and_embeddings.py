"""add_pgvector_extension_and_embeddings

Revision ID: cd728d134263
Revises: 20251207_1320_add_timezone
Create Date: 2025-12-08 18:25:34.423809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'cd728d134263'
down_revision: Union[str, None] = '20251207_1320_add_timezone'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Add embedding vector column to exercises table (384 dimensions for sentence-transformers/all-MiniLM-L6-v2)
    op.add_column('exercises', sa.Column('embedding', Vector(384), nullable=True))
    
    # Create index for fast vector similarity search using cosine distance
    op.execute('CREATE INDEX IF NOT EXISTS idx_exercises_embedding ON exercises USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')


def downgrade() -> None:
    # Drop the index
    op.execute('DROP INDEX IF EXISTS idx_exercises_embedding')
    
    # Drop the embedding column
    op.drop_column('exercises', 'embedding')
    
    # Drop pgvector extension (optional - may affect other tables)
    # op.execute('DROP EXTENSION IF EXISTS vector')
