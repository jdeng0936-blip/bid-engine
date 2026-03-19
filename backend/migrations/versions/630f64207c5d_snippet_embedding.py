"""chapter_snippet 添加 embedding 列 + HNSW 索引

Revision ID: 630f64207c5d
Revises: 4b2bc153ee5c
"""
from alembic import op
import sqlalchemy as sa

revision = "630f64207c5d"
down_revision = "4b2bc153ee5c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE chapter_snippet ADD COLUMN IF NOT EXISTS embedding vector(1536)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_snippet_embedding ON chapter_snippet USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_snippet_embedding")
    op.execute("ALTER TABLE chapter_snippet DROP COLUMN IF EXISTS embedding")
