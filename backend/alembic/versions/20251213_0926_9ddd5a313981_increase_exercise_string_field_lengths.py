"""increase_exercise_string_field_lengths

Revision ID: 9ddd5a313981
Revises: 83adbc68b3fa
Create Date: 2025-12-13 09:26:17.866557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ddd5a313981'
down_revision: Union[str, None] = '83adbc68b3fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Increase VARCHAR length for reps and tempo columns in exercises table
    # These fields can contain descriptive text like "8-12 reps with 2 RIR" or detailed tempo patterns
    op.alter_column('exercises', 'reps',
                    existing_type=sa.String(50),
                    type_=sa.String(200),
                    existing_nullable=True)
    
    op.alter_column('exercises', 'tempo',
                    existing_type=sa.String(50),
                    type_=sa.String(200),
                    existing_nullable=True)


def downgrade() -> None:
    # Revert to original VARCHAR(50) lengths
    op.alter_column('exercises', 'tempo',
                    existing_type=sa.String(200),
                    type_=sa.String(50),
                    existing_nullable=True)
    
    op.alter_column('exercises', 'reps',
                    existing_type=sa.String(200),
                    type_=sa.String(50),
                    existing_nullable=True)
