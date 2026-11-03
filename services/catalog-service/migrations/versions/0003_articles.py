"""Tables `articles`, `article_photos` et `price_history` (contrats.md §4.1).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("shop_id", sa.Uuid(), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("category_id", sa.Uuid(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("shipping_fee", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "rejection_reasons",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("price > 0", name="ck_articles_price_positive"),
        sa.CheckConstraint("shipping_fee >= 0", name="ck_articles_shipping_fee_non_negative"),
        sa.CheckConstraint("status IN ('PUBLISHED', 'REJECTED')", name="ck_articles_status"),
    )
    op.create_index(
        "ix_articles_catalog", "articles", ["status", "category_id", sa.text("created_at DESC")]
    )
    op.create_index("ix_articles_shop_id", "articles", ["shop_id"])
    op.create_table(
        "article_photos",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("article_id", sa.Uuid(), sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.UniqueConstraint("article_id", "position", name="uq_article_photos_position"),
    )
    op.create_index("ix_article_photos_article_id", "article_photos", ["article_id"])
    op.create_table(
        "price_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("article_id", sa.Uuid(), sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("old_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("new_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("changed_by", sa.String(128), nullable=False),
        sa.Column(
            "changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_price_history_article_id", "price_history", ["article_id"])


def downgrade() -> None:
    op.drop_table("price_history")
    op.drop_table("article_photos")
    op.drop_table("articles")
