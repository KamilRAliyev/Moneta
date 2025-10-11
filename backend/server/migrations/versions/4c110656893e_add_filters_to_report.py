"""add_filters_to_report

Revision ID: 4c110656893e
Revises: 9cd4361681c3
Create Date: 2025-10-11 08:48:45.189659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c110656893e'
down_revision: Union[str, Sequence[str], None] = '9cd4361681c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add filters column to reports table
    op.add_column('reports', sa.Column('filters', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove filters column from reports table
    op.drop_column('reports', 'filters')
