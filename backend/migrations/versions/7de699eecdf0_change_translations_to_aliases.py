"""change translations to aliases

Revision ID: 7de699eecdf0
Revises: b7bac9e63bee
Create Date: 2026-08-09 03:43:18.108796
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7de699eecdf0'
down_revision: Union[str, Sequence[str], None] = 'b7bac9e63bee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    op.add_column('albums', sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False))
    op.add_column('artists', sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False))
    op.add_column('franchises', sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False))
    op.add_column('tracks', sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False))

    op.execute("UPDATE albums SET aliases = jsonb_build_array(title_translated) WHERE title_translated IS NOT NULL AND btrim(title_translated) <> ''")
    op.execute("UPDATE artists SET aliases = jsonb_build_array(name_translated) WHERE name_translated IS NOT NULL AND btrim(name_translated) <> ''")
    op.execute("UPDATE franchises SET aliases = jsonb_build_array(name_translated) WHERE name_translated IS NOT NULL AND btrim(name_translated) <> ''")
    op.execute("UPDATE tracks SET aliases = jsonb_build_array(title_translated) WHERE title_translated IS NOT NULL AND btrim(title_translated) <> ''")

    op.execute("CREATE INDEX IF NOT EXISTS idx_albums_aliases_trgm ON albums USING gin ((aliases::text) gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_artists_aliases_trgm ON artists USING gin ((aliases::text) gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_franchises_aliases_trgm ON franchises USING gin ((aliases::text) gin_trgm_ops)")

    op.drop_column('albums', 'title_translated')
    op.drop_column('artists', 'name_translated')
    op.drop_column('franchises', 'name_translated')
    op.drop_column('tracks', 'title_translated')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('tracks', sa.Column('title_translated', sa.VARCHAR(length=512), autoincrement=False, nullable=True))
    op.add_column('franchises', sa.Column('name_translated', sa.VARCHAR(length=512), autoincrement=False, nullable=True))
    op.add_column('artists', sa.Column('name_translated', sa.VARCHAR(length=512), autoincrement=False, nullable=True))
    op.add_column('albums', sa.Column('title_translated', sa.VARCHAR(length=512), autoincrement=False, nullable=True))

    op.execute("UPDATE tracks SET title_translated = aliases->>0 WHERE jsonb_typeof(aliases) = 'array' AND jsonb_array_length(aliases) > 0")
    op.execute("UPDATE franchises SET name_translated = aliases->>0 WHERE jsonb_typeof(aliases) = 'array' AND jsonb_array_length(aliases) > 0")
    op.execute("UPDATE artists SET name_translated = aliases->>0 WHERE jsonb_typeof(aliases) = 'array' AND jsonb_array_length(aliases) > 0")
    op.execute("UPDATE albums SET title_translated = aliases->>0 WHERE jsonb_typeof(aliases) = 'array' AND jsonb_array_length(aliases) > 0")

    op.execute("DROP INDEX IF EXISTS idx_franchises_aliases_trgm")
    op.execute("DROP INDEX IF EXISTS idx_artists_aliases_trgm")
    op.execute("DROP INDEX IF EXISTS idx_albums_aliases_trgm")

    op.drop_column('tracks', 'aliases')
    op.drop_column('franchises', 'aliases')
    op.drop_column('artists', 'aliases')
    op.drop_column('albums', 'aliases')