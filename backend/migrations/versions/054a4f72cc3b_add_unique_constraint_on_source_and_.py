"""Add unique constraint on source and source_id

Revision ID: 054a4f72cc3b
Revises: 6aba7fe40207
Create Date: 2025-12-12 21:53:05.520596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '054a4f72cc3b'
down_revision: Union[str, None] = '6aba7fe40207'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the unique index on source_id alone
    op.drop_index('ix_jobs_source_id', table_name='jobs')

    # Create non-unique index on source_id
    op.create_index('ix_jobs_source_id', 'jobs', ['source_id'], unique=False)

    # Add unique constraint on (source, source_id) combination
    op.create_unique_constraint(
        'uq_jobs_source_source_id',
        'jobs',
        ['source', 'source_id']
    )


def downgrade() -> None:
    # Remove the composite unique constraint
    op.drop_constraint('uq_jobs_source_source_id', 'jobs', type_='unique')

    # Remove non-unique index
    op.drop_index('ix_jobs_source_id', table_name='jobs')

    # Restore the unique index on source_id alone
    op.create_index('ix_jobs_source_id', 'jobs', ['source_id'], unique=True)
