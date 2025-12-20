"""add is_admin field to users

Revision ID: f8a2c3d4e5b6
Revises: 51a810a2b2d8
Create Date: 2025-12-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a2c3d4e5b6'
down_revision: Union[str, None] = '05069ca43c64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column with default False
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))

    # Make info@devdenise.com an admin
    op.execute("UPDATE users SET is_admin = true WHERE email = 'info@devdenise.com'")


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
