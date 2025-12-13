"""add_performance_indexes

Revision ID: 79d767eb5024
Revises: 5b6fab1826e2
Create Date: 2025-12-13 14:07:25.004671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79d767eb5024'
down_revision: Union[str, None] = '5b6fab1826e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add performance-optimizing indexes for common query patterns.

    - Composite index on (source, scraped_at) for efficient source filtering with time ordering
    - Composite index on (remote_type, scraped_at) for remote job queries
    - Index on scraped_at for general time-based queries

    Note: The unique constraint on (source, source_id) from migration 054a4f72cc3b
    already provides an index for ON CONFLICT operations.
    """

    # Composite index for source-based queries ordered by time
    # Supports queries like: WHERE source = ? ORDER BY scraped_at DESC
    op.create_index(
        'idx_jobs_source_scraped_at',
        'jobs',
        ['source', 'scraped_at'],
        unique=False
    )

    # Composite index for remote job queries
    # Supports queries like: WHERE remote_type = 'full' ORDER BY scraped_at DESC
    op.create_index(
        'idx_jobs_remote_type_scraped_at',
        'jobs',
        ['remote_type', 'scraped_at'],
        unique=False
    )

    # Standalone index on scraped_at for general ordering
    # Supports queries like: ORDER BY scraped_at DESC LIMIT 50
    op.create_index(
        'idx_jobs_scraped_at',
        'jobs',
        ['scraped_at'],
        unique=False
    )

    # Composite index for job type filtering
    # Supports queries like: WHERE job_type = ? ORDER BY scraped_at DESC
    op.create_index(
        'idx_jobs_job_type_scraped_at',
        'jobs',
        ['job_type', 'scraped_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove performance indexes"""
    op.drop_index('idx_jobs_job_type_scraped_at', table_name='jobs')
    op.drop_index('idx_jobs_scraped_at', table_name='jobs')
    op.drop_index('idx_jobs_remote_type_scraped_at', table_name='jobs')
    op.drop_index('idx_jobs_source_scraped_at', table_name='jobs')
