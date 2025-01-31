"""new column at report

Revision ID: 0080fa1d9e44
Revises: 5eaa5394f1a5
Create Date: 2025-01-09 18:31:17.612432

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0080fa1d9e44'
down_revision: Union[str, None] = '5eaa5394f1a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reports', sa.Column('score', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('reports', 'score')
    # ### end Alembic commands ###
