"""add edit_ratio column to bid_chapter

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bid_chapter",
        sa.Column(
            "edit_ratio",
            sa.Float(),
            nullable=True,
            comment="用户编辑占比(0~1)，由反馈飞轮写入",
        ),
    )


def downgrade() -> None:
    op.drop_column("bid_chapter", "edit_ratio")
