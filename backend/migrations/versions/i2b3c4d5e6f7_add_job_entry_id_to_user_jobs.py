"""add job_entry_id to user_jobs

Revision ID: i2b3c4d5e6f7
Revises: h1a2b3c4d5e6
Create Date: 2025-12-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i2b3c4d5e6f7'
down_revision: Union[str, None] = 'h1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add job_entry_id column to user_jobs table
    op.add_column(
        'user_jobs',
        sa.Column('job_entry_id', sa.Integer(), nullable=True)
    )

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_user_jobs_job_entry_id',
        'user_jobs',
        'jobs',
        ['job_entry_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Create index for job_entry_id
    op.create_index(
        'ix_user_jobs_job_entry_id',
        'user_jobs',
        ['job_entry_id']
    )


def downgrade() -> None:
    op.drop_index('ix_user_jobs_job_entry_id', table_name='user_jobs')
    op.drop_constraint('fk_user_jobs_job_entry_id', 'user_jobs', type_='foreignkey')
    op.drop_column('user_jobs', 'job_entry_id')
