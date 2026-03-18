"""
Alembic 迁移 — std_clause 表添加 embedding 向量列 + HNSW 索引

前置条件：已在 PostgreSQL 中执行 CREATE EXTENSION IF NOT EXISTS vector;
"""
from alembic import op
import sqlalchemy as sa

revision = "a2b3c4d5e6f7"
down_revision = "c4b1c5249d34"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 确保 pgvector 扩展已安装
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 添加 embedding 向量列（1536 维，对应 Gemini text-embedding-004）
    op.add_column(
        "std_clause",
        sa.Column("embedding", sa.dialects.postgresql.ARRAY(sa.Float), nullable=True,
                  comment="文本嵌入向量(1536维)")
    )

    # 使用原生 SQL 创建真正的 vector 列和 HNSW 索引
    # 先改列类型为 vector(1536)
    op.execute("ALTER TABLE std_clause ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)")

    # 创建 HNSW 索引，加速余弦相似度检索
    op.execute(
        "CREATE INDEX ix_std_clause_embedding ON std_clause "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_std_clause_embedding")
    op.drop_column("std_clause", "embedding")
