"""add pre score

Revision ID: fba143dfbf04
Revises: 4d2ef3d081d5
Create Date: 2025-04-23 18:09:39.886540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fba143dfbf04'
down_revision: Union[str, None] = '4d2ef3d081d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the `pre_grade` column to the `answers` table
    op.add_column('answers', sa.Column('pre_grade', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove the `pre_grade` column from the `answers` table
    op.drop_column('answers', 'pre_grade')
