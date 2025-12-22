"""set devdenise as admin

Revision ID: g9a3d4e5f6c7
Revises: f8a2c3d4e5b6
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'g9a3d4e5f6c7'
down_revision: Union[str, None] = 'f8a2c3d4e5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Set info@devdenise.com as admin (idempotent - safe to run multiple times)
    op.execute("UPDATE users SET is_admin = true WHERE email = 'info@devdenise.com'")


def downgrade() -> None:
    op.execute("UPDATE users SET is_admin = false WHERE email = 'info@devdenise.com'")
