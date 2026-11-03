"""Tables `interests`, `preferences` et `notifications` (contrats.md §4.2).

Revision ID: 0001
Revises:
Create Date: 2026-11-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interests",
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("user_id", "category_id"),
    )
    # Recherche des destinataires d'un événement : tous les acheteurs d'une catégorie.
    op.create_index("ix_interests_category_id", "interests", ["category_id"])
    op.create_table(
        "preferences",
        sa.Column("user_id", sa.String(128), primary_key=True),
        sa.Column("new_article", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("price_changed", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("article_id", sa.Uuid(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("source_event_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "source_event_id", name="uq_notifications_user_event"),
        sa.CheckConstraint(
            "type IN ('NEW_ARTICLE', 'PRICE_CHANGED')", name="ck_notifications_type"
        ),
    )
    op.create_index(
        "ix_notifications_user_created", "notifications", ["user_id", sa.text("created_at DESC")]
    )


def downgrade() -> None:
    op.drop_table("notifications")  # supprime aussi ses index
    op.drop_table("preferences")
    op.drop_table("interests")
