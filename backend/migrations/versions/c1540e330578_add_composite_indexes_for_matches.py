"""add_composite_indexes_for_matches

Revision ID: c1540e330578
Revises: b9152b597093
Create Date: 2025-12-17 15:42:37.553388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1540e330578'
down_revision: Union[str, None] = 'b9152b597093'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add composite indexes for common match queries
    # These significantly improve query performance when filtering matches

    # Index for: SELECT * FROM matches WHERE user_id = ? AND score >= ? ORDER BY score DESC
    op.create_index(
        'idx_matches_user_score',
        'matches',
        ['user_id', 'score'],
        unique=False
    )

    # Index for: SELECT * FROM matches WHERE user_id = ? AND status = ?
    op.create_index(
        'idx_matches_user_status',
        'matches',
        ['user_id', 'status'],
        unique=False
    )

    # Index for: SELECT * FROM matches WHERE user_id = ? AND status = ? AND score >= ?
    op.create_index(
        'idx_matches_user_status_score',
        'matches',
        ['user_id', 'status', 'score'],
        unique=False
    )


def downgrade() -> None:
    # Remove composite indexes
    op.drop_index('idx_matches_user_status_score', table_name='matches')
    op.drop_index('idx_matches_user_status', table_name='matches')
    op.drop_index('idx_matches_user_score', table_name='matches')
