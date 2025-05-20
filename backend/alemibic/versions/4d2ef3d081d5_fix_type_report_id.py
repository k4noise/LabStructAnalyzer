"""fix type report_id

Revision ID: 4d2ef3d081d5
Revises: 0080fa1d9e44
Create Date: 2025-04-08 22:13:59.454758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d2ef3d081d5'
down_revision: Union[str, None] = '0080fa1d9e44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
