"""add unique constraint on match user_id job_id

Revision ID: h1a2b3c4d5e6
Revises: g9a3d4e5f6c7
Create Date: 2025-12-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h1a2b3c4d5e6'
down_revision: Union[str, None] = 'g9a3d4e5f6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First, remove any duplicate matches (keep the most recent one)
    # This is necessary before adding the unique constraint
    op.execute("""
        DELETE FROM matches m1
        USING matches m2
        WHERE m1.user_id = m2.user_id
        AND m1.job_id = m2.job_id
        AND m1.id < m2.id
    """)

    # Add unique constraint on (user_id, job_id)
    op.create_unique_constraint(
        'uq_match_user_job',
        'matches',
        ['user_id', 'job_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_match_user_job', 'matches', type_='unique')
