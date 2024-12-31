"""template: add nesting element support + index

Revision ID: 34ce7b2ec09e
Revises: e28c48d06652
Create Date: 2024-12-30 21:17:54.949996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34ce7b2ec09e'
down_revision: Union[str, None] = 'e28c48d06652'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('template_elements', sa.Column('parent_element_id', sa.Uuid(), nullable=True))
    op.create_index('templates_template_id_is_draft_idx', 'templates', ['template_id', 'is_draft'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('templates_template_id_is_draft_idx', table_name='templates')
    op.drop_column('template_elements', 'parent_element_id')
    # ### end Alembic commands ###
