"""add_fulltext_search_index

Revision ID: b9152b597093
Revises: 79d767eb5024
Create Date: 2025-12-16 18:54:23.349508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9152b597093'
down_revision: Union[str, None] = '79d767eb5024'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tsvector column for full-text search
    op.execute("""
        ALTER TABLE jobs ADD COLUMN search_vector tsvector;
    """)

    # Create trigger function to automatically update search_vector
    op.execute("""
        CREATE FUNCTION jobs_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.company, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'C');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger to call the function on INSERT or UPDATE
    op.execute("""
        CREATE TRIGGER jobs_search_vector_trigger
        BEFORE INSERT OR UPDATE ON jobs
        FOR EACH ROW EXECUTE FUNCTION jobs_search_vector_update();
    """)

    # Update existing rows with search_vector
    op.execute("""
        UPDATE jobs SET search_vector =
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(company, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'C');
    """)

    # Create GIN index for fast full-text search
    op.execute("""
        CREATE INDEX idx_jobs_search_vector ON jobs USING GIN(search_vector);
    """)


def downgrade() -> None:
    # Remove index
    op.execute("DROP INDEX IF EXISTS idx_jobs_search_vector;")

    # Remove trigger
    op.execute("DROP TRIGGER IF EXISTS jobs_search_vector_trigger ON jobs;")

    # Remove trigger function
    op.execute("DROP FUNCTION IF EXISTS jobs_search_vector_update();")

    # Remove column
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS search_vector;")
