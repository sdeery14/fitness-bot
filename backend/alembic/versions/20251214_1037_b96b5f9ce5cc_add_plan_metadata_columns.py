"""add_plan_metadata_columns

Revision ID: b96b5f9ce5cc
Revises: cec6978bd6bd
Create Date: 2025-12-14 10:37:02.665085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b96b5f9ce5cc'
down_revision: Union[str, None] = 'cec6978bd6bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add metadata columns to fitness_plans table
    op.add_column('fitness_plans', sa.Column('key_principles', sa.JSON(), nullable=True))
    op.add_column('fitness_plans', sa.Column('success_metrics', sa.JSON(), nullable=True))
    op.add_column('fitness_plans', sa.Column('important_notes', sa.Text(), nullable=True))
    
    # Add metadata columns to workout_plans table
    op.add_column('workout_plans', sa.Column('phase_progression_notes', sa.Text(), nullable=True))
    op.add_column('workout_plans', sa.Column('equipment_used', sa.JSON(), nullable=True))
    
    # Add metadata columns to meal_plans table
    op.add_column('meal_plans', sa.Column('dietary_approach', sa.String(500), nullable=True))
    op.add_column('meal_plans', sa.Column('macro_strategy', sa.String(500), nullable=True))
    op.add_column('meal_plans', sa.Column('meal_timing', sa.String(500), nullable=True))
    op.add_column('meal_plans', sa.Column('hydration_guidance', sa.String(500), nullable=True))
    op.add_column('meal_plans', sa.Column('phase_nutrition_notes', sa.String(1000), nullable=True))


def downgrade() -> None:
    # Remove metadata columns from meal_plans table
    op.drop_column('meal_plans', 'phase_nutrition_notes')
    op.drop_column('meal_plans', 'hydration_guidance')
    op.drop_column('meal_plans', 'meal_timing')
    op.drop_column('meal_plans', 'macro_strategy')
    op.drop_column('meal_plans', 'dietary_approach')
    
    # Remove metadata columns from workout_plans table
    op.drop_column('workout_plans', 'equipment_used')
    op.drop_column('workout_plans', 'phase_progression_notes')
    
    # Remove metadata columns from fitness_plans table
    op.drop_column('fitness_plans', 'important_notes')
    op.drop_column('fitness_plans', 'success_metrics')
    op.drop_column('fitness_plans', 'key_principles')
