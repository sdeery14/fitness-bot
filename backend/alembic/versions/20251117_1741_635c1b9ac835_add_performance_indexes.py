"""add_performance_indexes

Revision ID: 635c1b9ac835
Revises: 20251117_0924
Create Date: 2025-11-17 17:41:46.914656

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '635c1b9ac835'
down_revision: Union[str, None] = '20251117_0924'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for frequently queried columns."""
    # Users table indexes (skip if exists from earlier migration)
    op.create_index('ix_users_email', 'users', ['email'], unique=False, if_not_exists=True)

    # FitnessPlans table indexes
    op.create_index('ix_fitness_plans_user_id', 'fitness_plans', ['user_id'], unique=False, if_not_exists=True)
    op.create_index('ix_fitness_plans_status', 'fitness_plans', ['status'], unique=False, if_not_exists=True)
    op.create_index('ix_fitness_plans_user_status', 'fitness_plans', ['user_id', 'status'], unique=False, if_not_exists=True)

    # ScheduleEntries table indexes
    op.create_index('ix_schedule_entries_schedule_id', 'schedule_entries', ['schedule_id'], unique=False, if_not_exists=True)
    op.create_index('ix_schedule_entries_entry_date', 'schedule_entries', ['entry_date'], unique=False, if_not_exists=True)
    op.create_index('ix_schedule_entries_completion_status', 'schedule_entries', ['completion_status'], unique=False, if_not_exists=True)
    op.create_index('ix_schedule_entries_user_date', 'schedule_entries', ['schedule_id', 'entry_date'], unique=False, if_not_exists=True)

    # ProgressRecords table indexes
    op.create_index('ix_progress_records_user_id', 'progress_records', ['user_id'], unique=False, if_not_exists=True)
    op.create_index('ix_progress_records_fitness_plan_id', 'progress_records', ['fitness_plan_id'], unique=False, if_not_exists=True)
    op.create_index('ix_progress_records_record_date', 'progress_records', ['record_date'], unique=False, if_not_exists=True)
    op.create_index('ix_progress_records_record_type', 'progress_records', ['record_type'], unique=False, if_not_exists=True)

    # Conversations table indexes
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'], unique=False, if_not_exists=True)
    op.create_index('ix_conversations_status', 'conversations', ['status'], unique=False, if_not_exists=True)

    # Messages table indexes
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'], unique=False, if_not_exists=True)
    op.create_index('ix_messages_created_at', 'messages', ['created_at'], unique=False, if_not_exists=True)

    # DisruptionEvents table indexes
    op.create_index('ix_disruption_events_user_id', 'disruption_events', ['user_id'], unique=False, if_not_exists=True)
    op.create_index('ix_disruption_events_fitness_plan_id', 'disruption_events', ['fitness_plan_id'], unique=False, if_not_exists=True)
    op.create_index('ix_disruption_events_start_date', 'disruption_events', ['start_date'], unique=False, if_not_exists=True)


def downgrade() -> None:
    """Remove performance indexes."""
    # DisruptionEvents indexes
    op.drop_index('ix_disruption_events_start_date', table_name='disruption_events')
    op.drop_index('ix_disruption_events_fitness_plan_id', table_name='disruption_events')
    op.drop_index('ix_disruption_events_user_id', table_name='disruption_events')

    # Messages indexes
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_conversation_id', table_name='messages')

    # Conversations indexes
    op.drop_index('ix_conversations_status', table_name='conversations')
    op.drop_index('ix_conversations_user_id', table_name='conversations')

    # ProgressRecords indexes
    op.drop_index('ix_progress_records_record_type', table_name='progress_records')
    op.drop_index('ix_progress_records_record_date', table_name='progress_records')
    op.drop_index('ix_progress_records_fitness_plan_id', table_name='progress_records')
    op.drop_index('ix_progress_records_user_id', table_name='progress_records')

    # ScheduleEntries indexes
    op.drop_index('ix_schedule_entries_user_date', table_name='schedule_entries')
    op.drop_index('ix_schedule_entries_completion_status', table_name='schedule_entries')
    op.drop_index('ix_schedule_entries_entry_date', table_name='schedule_entries')
    op.drop_index('ix_schedule_entries_schedule_id', table_name='schedule_entries')

    # FitnessPlans indexes
    op.drop_index('ix_fitness_plans_user_status', table_name='fitness_plans')
    op.drop_index('ix_fitness_plans_status', table_name='fitness_plans')
    op.drop_index('ix_fitness_plans_user_id', table_name='fitness_plans')

    # Users indexes
    op.drop_index('ix_users_email', table_name='users')

