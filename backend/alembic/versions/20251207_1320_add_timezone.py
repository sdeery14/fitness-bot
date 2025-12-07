"""add timezone field to users table

Revision ID: 20251207_1320_add_timezone
Revises: 635c1b9ac835
Create Date: 2025-12-07 13:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251207_1320_add_timezone'
down_revision = '635c1b9ac835'  # References the performance indexes migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add timezone field to users table."""
    # Add timezone column with default 'UTC'
    op.add_column('users', sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'))


def downgrade() -> None:
    """Remove timezone field from users table."""
    op.drop_column('users', 'timezone')
