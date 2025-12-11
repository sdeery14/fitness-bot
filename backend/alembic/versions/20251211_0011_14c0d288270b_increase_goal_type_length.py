"""increase_goal_type_length

Revision ID: 14c0d288270b
Revises: b82aa00151aa
Create Date: 2025-12-11 00:11:18.377481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14c0d288270b'
down_revision: Union[str, None] = 'b82aa00151aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Increase goal_type column length from 100 to 500 characters
    op.alter_column('fitness_plans', 'goal_type',
                    type_=sa.String(length=500),
                    existing_type=sa.String(length=100),
                    existing_nullable=False)


def downgrade() -> None:
    # Revert goal_type column length back to 100 characters
    op.alter_column('fitness_plans', 'goal_type',
                    type_=sa.String(length=100),
                    existing_type=sa.String(length=500),
                    existing_nullable=False)
