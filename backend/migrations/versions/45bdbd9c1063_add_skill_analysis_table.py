"""add skill_analysis table

Revision ID: 45bdbd9c1063
Revises: 054a4f72cc3b
Create Date: 2025-12-13 09:13:41.827204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45bdbd9c1063'
down_revision: Union[str, None] = '054a4f72cc3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'skill_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('analysis_date', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('market_skills', sa.JSON(), nullable=True),
        sa.Column('user_skills', sa.JSON(), nullable=True),
        sa.Column('skill_gaps', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('jobs_analyzed', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_skill_analysis_id'), 'skill_analysis', ['id'], unique=False)
    op.create_index(op.f('ix_skill_analysis_user_id'), 'skill_analysis', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_skill_analysis_user_id'), table_name='skill_analysis')
    op.drop_index(op.f('ix_skill_analysis_id'), table_name='skill_analysis')
    op.drop_table('skill_analysis')
