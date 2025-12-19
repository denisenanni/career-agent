"""add_user_jobs_table

Revision ID: 51a810a2b2d8
Revises: 17474fd54e48
Create Date: 2025-12-19 14:52:06.499001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51a810a2b2d8'
down_revision: Union[str, None] = '17474fd54e48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_jobs table for user-submitted job postings
    op.create_table(
        'user_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('source', sa.String(length=50), server_default='user_submitted', nullable=False),

        # Extracted fields (same as scraped jobs)
        sa.Column('tags', sa.JSON(), server_default='[]', nullable=True),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('salary_currency', sa.String(length=10), server_default='USD', nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('remote_type', sa.String(length=50), nullable=True),
        sa.Column('job_type', sa.String(length=50), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'company', 'title', name='uq_user_jobs_user_company_title'),
    )

    # Create indexes
    op.create_index('idx_user_jobs_user_id', 'user_jobs', ['user_id'])
    op.create_index('idx_user_jobs_created_at', 'user_jobs', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_user_jobs_created_at', table_name='user_jobs')
    op.drop_index('idx_user_jobs_user_id', table_name='user_jobs')
    op.drop_table('user_jobs')
