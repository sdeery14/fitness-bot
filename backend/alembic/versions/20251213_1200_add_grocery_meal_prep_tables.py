"""Add grocery_shopping_trips and meal_prep_sessions tables

Revision ID: 20251213_1200_add_grocery_meal_prep_tables
Revises: 20251213_0926_9ddd5a313981
Create Date: 2025-12-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9ddd5a313981'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create grocery_shopping_trips table
    op.create_table('grocery_shopping_trips',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('items', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create meal_prep_sessions table
    op.create_table('meal_prep_sessions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('session_name', sa.String(length=200), nullable=False),
    sa.Column('recipes', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('batch_size', sa.Integer(), nullable=False),
    sa.Column('instructions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('storage_instructions', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Add new foreign key columns to schedule_entries
    op.add_column('schedule_entries', sa.Column('grocery_trip_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('schedule_entries', sa.Column('meal_prep_session_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create foreign key constraints
    op.create_foreign_key('fk_schedule_entries_grocery_trip', 'schedule_entries', 'grocery_shopping_trips', ['grocery_trip_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_schedule_entries_meal_prep_session', 'schedule_entries', 'meal_prep_sessions', ['meal_prep_session_id'], ['id'], ondelete='SET NULL')
    
    # Create indexes
    op.create_index('idx_schedule_entries_grocery_trip', 'schedule_entries', ['grocery_trip_id'], unique=False)
    op.create_index('idx_schedule_entries_meal_prep', 'schedule_entries', ['meal_prep_session_id'], unique=False)
    
    # Migrate existing data from JSON columns to new tables
    # Note: This migration assumes we'll regenerate schedules, but we preserve the structure
    # If you need to preserve existing data, uncomment and customize the following:
    
    # from sqlalchemy import text
    # conn = op.get_bind()
    # 
    # # Migrate grocery shopping entries
    # result = conn.execute(text("""
    #     SELECT id, grocery_list 
    #     FROM schedule_entries 
    #     WHERE entry_type = 'grocery_shopping' AND grocery_list IS NOT NULL
    # """))
    # 
    # for row in result:
    #     entry_id = row[0]
    #     grocery_data = row[1]
    #     
    #     # Create grocery trip
    #     trip_id = conn.execute(text("""
    #         INSERT INTO grocery_shopping_trips (id, name, items, created_at, updated_at)
    #         VALUES (gen_random_uuid(), 'Weekly Shopping', :items, NOW(), NOW())
    #         RETURNING id
    #     """), {"items": json.dumps(grocery_data)}).scalar()
    #     
    #     # Update schedule entry
    #     conn.execute(text("""
    #         UPDATE schedule_entries 
    #         SET grocery_trip_id = :trip_id 
    #         WHERE id = :entry_id
    #     """), {"trip_id": trip_id, "entry_id": entry_id})
    
    # Drop old check constraint
    op.drop_constraint('valid_entry_reference', 'schedule_entries', type_='check')
    
    # Create new check constraint
    op.create_check_constraint(
        'valid_entry_reference',
        'schedule_entries',
        "(entry_type = 'workout' AND workout_id IS NOT NULL AND meal_id IS NULL AND grocery_trip_id IS NULL AND meal_prep_session_id IS NULL) OR "
        "(entry_type = 'meal' AND meal_id IS NOT NULL AND workout_id IS NULL AND grocery_trip_id IS NULL AND meal_prep_session_id IS NULL) OR "
        "(entry_type = 'grocery_shopping' AND workout_id IS NULL AND meal_id IS NULL AND grocery_trip_id IS NOT NULL AND meal_prep_session_id IS NULL) OR "
        "(entry_type = 'meal_prep' AND workout_id IS NULL AND meal_id IS NULL AND grocery_trip_id IS NULL AND meal_prep_session_id IS NOT NULL)"
    )
    
    # Drop old JSON columns (after data migration if needed)
    op.drop_column('schedule_entries', 'grocery_list')
    op.drop_column('schedule_entries', 'prep_instructions')


def downgrade() -> None:
    # Add back JSON columns
    op.add_column('schedule_entries', sa.Column('prep_instructions', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('schedule_entries', sa.Column('grocery_list', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Drop new check constraint
    op.drop_constraint('valid_entry_reference', 'schedule_entries', type_='check')
    
    # Recreate old check constraint
    op.create_check_constraint(
        'valid_entry_reference',
        'schedule_entries',
        "(entry_type = 'workout' AND workout_id IS NOT NULL AND meal_id IS NULL AND grocery_list IS NULL AND prep_instructions IS NULL) OR "
        "(entry_type = 'meal' AND meal_id IS NOT NULL AND workout_id IS NULL AND grocery_list IS NULL AND prep_instructions IS NULL) OR "
        "(entry_type = 'grocery_shopping' AND workout_id IS NULL AND meal_id IS NULL AND grocery_list IS NOT NULL AND prep_instructions IS NULL) OR "
        "(entry_type = 'meal_prep' AND workout_id IS NULL AND meal_id IS NULL AND grocery_list IS NULL AND prep_instructions IS NOT NULL)"
    )
    
    # Drop indexes
    op.drop_index('idx_schedule_entries_meal_prep', table_name='schedule_entries')
    op.drop_index('idx_schedule_entries_grocery_trip', table_name='schedule_entries')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_schedule_entries_meal_prep_session', 'schedule_entries', type_='foreignkey')
    op.drop_constraint('fk_schedule_entries_grocery_trip', 'schedule_entries', type_='foreignkey')
    
    # Drop columns
    op.drop_column('schedule_entries', 'meal_prep_session_id')
    op.drop_column('schedule_entries', 'grocery_trip_id')
    
    # Drop tables
    op.drop_table('meal_prep_sessions')
    op.drop_table('grocery_shopping_trips')
