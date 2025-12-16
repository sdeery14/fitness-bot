"""normalize_workout_plan_details_to_columns

Revision ID: c29e61067f53
Revises: b96b5f9ce5cc
Create Date: 2025-12-16 10:26:10.438828

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c29e61067f53'
down_revision: Union[str, None] = 'b96b5f9ce5cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Normalize workout_plan_details JSON to proper columns.
    
    Migrates:
    - workout_plan_details['program_type'] -> program_type column
    - workout_plan_details['training_principles'] -> training_principles column
    - Removes workout_plan_details JSON column
    """
    # Step 1: Add new columns
    op.add_column('workout_plans', sa.Column('program_type', sa.String(100), nullable=True))
    op.add_column('workout_plans', sa.Column('training_principles', sa.JSON(), nullable=True))
    
    # Step 2: Migrate existing data from JSON to new columns
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE workout_plans
        SET 
            program_type = workout_plan_details->>'program_type',
            training_principles = workout_plan_details->'training_principles'
        WHERE workout_plan_details IS NOT NULL
    """))
    
    # Step 3: Make program_type NOT NULL (all existing data should have values now)
    op.alter_column('workout_plans', 'program_type', nullable=False)
    
    # Step 4: Drop old JSON column
    op.drop_column('workout_plans', 'workout_plan_details')


def downgrade() -> None:
    """Restore workout_plan_details JSON column from normalized columns."""
    # Step 1: Re-add workout_plan_details JSON column
    op.add_column('workout_plans', sa.Column('workout_plan_details', sa.JSON(), nullable=True))
    
    # Step 2: Migrate data back to JSON
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE workout_plans
        SET workout_plan_details = jsonb_build_object(
            'program_type', program_type,
            'progression_strategy', progression_strategy,
            'training_principles', training_principles
        )
    """))
    
    # Step 3: Make workout_plan_details NOT NULL
    op.alter_column('workout_plans', 'workout_plan_details', nullable=False)
    
    # Step 4: Drop normalized columns
    op.drop_column('workout_plans', 'training_principles')
    op.drop_column('workout_plans', 'program_type')
