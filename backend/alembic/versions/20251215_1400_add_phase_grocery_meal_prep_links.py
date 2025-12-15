"""Add phase links to grocery trips and meal prep sessions

Revision ID: add_phase_links
Revises: 
Create Date: 2025-12-13

This migration adds foreign key links from grocery_shopping_trips and 
meal_prep_sessions to phases, and adds schedule metadata fields to support
recurring events without plan_snapshot.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'add_phase_links_2025'
down_revision = 'a1b2c3d4e5f6'  # 20251213_1200_add_grocery_meal_prep_tables
branch_labels = None
depends_on = None


def upgrade():
    """Add phase links and schedule metadata."""
    
    # Add phase_id to grocery_shopping_trips
    op.add_column(
        'grocery_shopping_trips',
        sa.Column('phase_id', UUID(as_uuid=True), sa.ForeignKey('phases.id', ondelete='CASCADE'), nullable=True, index=True)
    )
    
    # Add schedule metadata to grocery_shopping_trips
    op.add_column('grocery_shopping_trips', sa.Column('target_day_name', sa.String(20), nullable=True))
    op.add_column('grocery_shopping_trips', sa.Column('time', sa.Time, nullable=True))
    op.add_column('grocery_shopping_trips', sa.Column('repeats_every', sa.Integer, nullable=True))
    
    # Add phase_id to meal_prep_sessions
    op.add_column(
        'meal_prep_sessions',
        sa.Column('phase_id', UUID(as_uuid=True), sa.ForeignKey('phases.id', ondelete='CASCADE'), nullable=True, index=True)
    )
    
    # Add schedule metadata to meal_prep_sessions
    op.add_column('meal_prep_sessions', sa.Column('target_day_name', sa.String(20), nullable=True))
    op.add_column('meal_prep_sessions', sa.Column('time', sa.Time, nullable=True))
    op.add_column('meal_prep_sessions', sa.Column('repeats_every', sa.Integer, nullable=True))
    
    # Make plan_snapshot nullable (step toward removing it)
    op.alter_column('fitness_plans', 'plan_snapshot', nullable=True)


def downgrade():
    """Remove phase links and schedule metadata."""
    
    # Remove columns from grocery_shopping_trips
    op.drop_column('grocery_shopping_trips', 'repeats_every')
    op.drop_column('grocery_shopping_trips', 'time')
    op.drop_column('grocery_shopping_trips', 'target_day_name')
    op.drop_column('grocery_shopping_trips', 'phase_id')
    
    # Remove columns from meal_prep_sessions
    op.drop_column('meal_prep_sessions', 'repeats_every')
    op.drop_column('meal_prep_sessions', 'time')
    op.drop_column('meal_prep_sessions', 'target_day_name')
    op.drop_column('meal_prep_sessions', 'phase_id')
    
    # Make plan_snapshot required again
    op.alter_column('fitness_plans', 'plan_snapshot', nullable=False)
