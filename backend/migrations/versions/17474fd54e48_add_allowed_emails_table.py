"""add_allowed_emails_table

Revision ID: 17474fd54e48
Revises: a246a7dfd293
Create Date: 2025-12-19 08:17:19.293179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17474fd54e48'
down_revision: Union[str, None] = 'a246a7dfd293'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create allowed_emails table for admin-managed registration allowlist
    op.create_table(
        'allowed_emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('added_by', sa.Integer(), nullable=True),  # User ID who added this email
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_allowed_emails_email'),
        sa.ForeignKeyConstraint(['added_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_allowed_emails_email', 'allowed_emails', ['email'])


def downgrade() -> None:
    op.drop_index('idx_allowed_emails_email', table_name='allowed_emails')
    op.drop_table('allowed_emails')
