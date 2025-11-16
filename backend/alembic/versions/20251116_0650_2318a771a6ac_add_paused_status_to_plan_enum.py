"""add_paused_status_to_plan_enum

Revision ID: 2318a771a6ac
Revises: 370efd33ab6c
Create Date: 2025-11-16 06:50:49.449202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2318a771a6ac'
down_revision: Union[str, None] = '370efd33ab6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'paused' to the plan_status enum
    op.execute("ALTER TYPE plan_status ADD VALUE IF NOT EXISTS 'paused'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type and all dependent columns
    # For now, we'll leave the value in place as it won't cause issues
    pass
