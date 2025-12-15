"""merge_heads

Revision ID: cec6978bd6bd
Revises: add_phase_links_2025, drop_plan_snapshot
Create Date: 2025-12-14 10:36:53.415746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cec6978bd6bd'
down_revision: Union[str, None] = ('add_phase_links_2025', 'drop_plan_snapshot')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
