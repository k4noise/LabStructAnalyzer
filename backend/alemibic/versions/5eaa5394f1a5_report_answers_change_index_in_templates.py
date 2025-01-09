"""report+answers, change index in templates

Revision ID: 5eaa5394f1a5
Revises: 34ce7b2ec09e
Create Date: 2025-01-08 17:25:07.423793

"""
from typing import Sequence, Union

import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5eaa5394f1a5'
down_revision: Union[str, None] = '34ce7b2ec09e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reports',
    sa.Column('report_id', sa.Uuid(), nullable=False),
    sa.Column('template_id', sa.Uuid(), nullable=False),
    sa.Column('author_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('grader_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['template_id'], ['templates.template_id'], ),
    sa.PrimaryKeyConstraint('report_id')
    )
    op.create_index('reports_author_id_template_id_created_at_idx', 'reports', ['author_id', 'template_id', 'created_at'], unique=False)
    op.create_index('reports_template_id_updated_at_idx', 'reports', ['template_id', 'updated_at'], unique=False)
    op.create_table('answers',
    sa.Column('answer_id', sa.Uuid(), nullable=False),
    sa.Column('report_id', sa.Uuid(), nullable=False),
    sa.Column('element_id', sa.Uuid(), nullable=False),
    sa.Column('data', sa.JSON(), nullable=True),
    sa.Column('score', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['report_id'], ['reports.report_id'], ),
    sa.PrimaryKeyConstraint('answer_id')
    )
    op.create_index(op.f('ix_answers_report_id'), 'answers', ['report_id'], unique=False)
    op.drop_index('templates_template_id_is_draft_idx', table_name='templates')
    op.create_index('templates_course_id_is_draft_idx', 'templates', ['course_id', 'is_draft'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('templates_course_id_is_draft_idx', table_name='templates')
    op.create_index('templates_template_id_is_draft_idx', 'templates', ['template_id', 'is_draft'], unique=False)
    op.drop_index(op.f('ix_answers_report_id'), table_name='answers')
    op.drop_table('answers')
    op.drop_index('reports_template_id_updated_at_idx', table_name='reports')
    op.drop_index('reports_author_id_template_id_created_at_idx', table_name='reports')
    op.drop_table('reports')
    # ### end Alembic commands ###