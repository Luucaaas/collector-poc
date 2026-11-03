"""Tables `categories` et `shops` (contrats.md §4.1).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("uq_categories_name_lower", "categories", [sa.text("lower(name)")], unique=True)
    op.create_table(
        "shops",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("seller_type", sa.String(20), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("seller_type = 'INDIVIDUAL'", name="ck_shops_seller_type"),
    )
    op.create_index("uq_shops_name_lower", "shops", [sa.text("lower(name)")], unique=True)
    op.create_index("ix_shops_owner_id", "shops", ["owner_id"])


def downgrade() -> None:
    op.drop_table("shops")  # supprime aussi ses index
    op.drop_table("categories")
