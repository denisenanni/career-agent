"""add scrape_logs table

Revision ID: 5b6fab1826e2
Revises: 45bdbd9c1063
Create Date: 2025-12-13 09:21:38.162259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b6fab1826e2'
down_revision: Union[str, None] = '45bdbd9c1063'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'scrape_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('jobs_found', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('jobs_new', sa.Integer(), server_default=sa.text('0'), nullable=True),
        sa.Column('status', sa.String(length=50), server_default=sa.text("'running'"), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scrape_logs_id'), 'scrape_logs', ['id'], unique=False)
    op.create_index(op.f('ix_scrape_logs_source'), 'scrape_logs', ['source'], unique=False)
    op.create_index(op.f('ix_scrape_logs_started_at'), 'scrape_logs', ['started_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scrape_logs_started_at'), table_name='scrape_logs')
    op.drop_index(op.f('ix_scrape_logs_source'), table_name='scrape_logs')
    op.drop_index(op.f('ix_scrape_logs_id'), table_name='scrape_logs')
    op.drop_table('scrape_logs')
