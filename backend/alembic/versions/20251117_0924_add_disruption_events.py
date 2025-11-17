"""Add DisruptionEvent model for User Story 3 - schedule disruptions

Revision ID: 20251117_0924
Revises: 8c87f613d348
Create Date: 2025-11-17 09:24:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251117_0924'
down_revision: Union[str, None] = '8c87f613d348'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create disruption_events table
    # The ENUM types will be created automatically by SQLAlchemy when the table is created
    op.create_table('disruption_events',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('fitness_plan_id', sa.UUID(), nullable=False),
        sa.Column('disruption_type', postgresql.ENUM('illness', 'injury', 'travel', 'schedule_conflict', 'other', name='disruption_type'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', postgresql.ENUM('minor', 'moderate', 'severe', name='disruption_severity'), nullable=False, server_default='moderate'),
        sa.Column('workouts_affected', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('meals_affected', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('resolution_strategy', postgresql.ENUM('reschedule', 'skip', 'extend_timeline', 'reassess', name='resolution_strategy'), nullable=False),
        sa.Column('timeline_extension_days', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('resolution_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', postgresql.ENUM('reported', 'processing', 'resolved', name='disruption_status'), nullable=False, server_default='reported'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['fitness_plan_id'], ['fitness_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('idx_disruption_events_user', 'disruption_events', ['user_id'], unique=False)
    op.create_index('idx_disruption_events_fitness_plan', 'disruption_events', ['fitness_plan_id'], unique=False)
    op.create_index('idx_disruption_events_conversation', 'disruption_events', ['conversation_id'], unique=False)
    op.create_index('idx_disruption_events_status', 'disruption_events', ['status'], unique=False)
    op.create_index('idx_disruption_events_start_date', 'disruption_events', ['start_date'], unique=False)
    op.create_index('idx_disruption_events_user_plan', 'disruption_events', ['user_id', 'fitness_plan_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_disruption_events_user_plan', table_name='disruption_events')
    op.drop_index('idx_disruption_events_start_date', table_name='disruption_events')
    op.drop_index('idx_disruption_events_status', table_name='disruption_events')
    op.drop_index('idx_disruption_events_conversation', table_name='disruption_events')
    op.drop_index('idx_disruption_events_fitness_plan', table_name='disruption_events')
    op.drop_index('idx_disruption_events_user', table_name='disruption_events')

    # Drop table (will also drop the enum types if not used elsewhere)
    op.drop_table('disruption_events')

    # Explicitly drop enum types
    sa.Enum(name='disruption_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='resolution_strategy').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='disruption_severity').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='disruption_type').drop(op.get_bind(), checkfirst=True)
