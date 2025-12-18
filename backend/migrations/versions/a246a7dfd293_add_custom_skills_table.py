"""add_custom_skills_table

Revision ID: a246a7dfd293
Revises: c1540e330578
Create Date: 2025-12-18 10:07:07.818251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a246a7dfd293'
down_revision: Union[str, None] = 'c1540e330578'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create custom_skills table
    op.create_table(
        'custom_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('skill', sa.String(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_custom_skills_id'), 'custom_skills', ['id'], unique=False)
    op.create_index(op.f('ix_custom_skills_skill'), 'custom_skills', ['skill'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_custom_skills_skill'), table_name='custom_skills')
    op.drop_index(op.f('ix_custom_skills_id'), table_name='custom_skills')
    op.drop_table('custom_skills')
