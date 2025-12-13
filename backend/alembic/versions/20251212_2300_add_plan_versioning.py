"""add plan versioning

Revision ID: 20251212_2300
Revises: 053b0b9e9e70
Create Date: 2025-12-12 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251212_2300'
down_revision: Union[str, None] = '053b0b9e9e70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'replaced' to plan_status enum
    op.execute("ALTER TYPE plan_status ADD VALUE 'replaced'")
    
    # Add versioning columns
    op.add_column('fitness_plans', sa.Column('parent_plan_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('fitness_plans', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('fitness_plans', sa.Column('version_notes', sa.Text(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key('fk_fitness_plans_parent_plan_id', 'fitness_plans', 'fitness_plans', ['parent_plan_id'], ['id'], ondelete='SET NULL')
    
    # Create index on parent_plan_id for faster queries
    op.create_index('ix_fitness_plans_parent_plan_id', 'fitness_plans', ['parent_plan_id'])


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_fitness_plans_parent_plan_id', table_name='fitness_plans')
    
    # Drop foreign key
    op.drop_constraint('fk_fitness_plans_parent_plan_id', 'fitness_plans', type_='foreignkey')
    
    # Drop columns
    op.drop_column('fitness_plans', 'version_notes')
    op.drop_column('fitness_plans', 'version')
    op.drop_column('fitness_plans', 'parent_plan_id')
    
    # Note: PostgreSQL doesn't support removing enum values directly
    # You would need to recreate the enum type if downgrading
