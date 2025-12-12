"""make_conversation_title_non_nullable

Revision ID: a28154bf3f90
Revises: 21a1135198bf
Create Date: 2025-12-12 12:41:21.900036

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a28154bf3f90'
down_revision: Union[str, None] = '21a1135198bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First, update any existing NULL titles to a default value
    op.execute("UPDATE conversations SET title = 'New Conversation' WHERE title IS NULL")
    
    # Now make the column non-nullable
    op.alter_column('conversations', 'title',
               existing_type=sa.String(length=255),
               nullable=False)


def downgrade() -> None:
    # Allow NULL values again
    op.alter_column('conversations', 'title',
               existing_type=sa.String(length=255),
               nullable=True)
