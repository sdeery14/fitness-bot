"""drop plan_snapshot column

Revision ID: drop_plan_snapshot
Revises: a1b2c3d4e5f6
Create Date: 2025-12-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'drop_plan_snapshot'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop plan_snapshot column from fitness_plans table (if exists)
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='fitness_plans' AND column_name='plan_snapshot'"
    ))
    if result.fetchone():
        op.drop_column('fitness_plans', 'plan_snapshot')


def downgrade() -> None:
    # Re-add plan_snapshot column if we need to rollback
    op.add_column('fitness_plans', 
        sa.Column('plan_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )
