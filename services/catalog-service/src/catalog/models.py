"""Modèles SQLAlchemy de catalog_db (contrats.md §4.1) : catégories et boutiques."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from catalog.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Category(Base):
    __tablename__ = "categories"
    # L'unicité sans tenir compte de la casse est garantie par la base (index fonctionnel).
    __table_args__ = (Index("uq_categories_name_lower", text("lower(name)"), unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(60))
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )


class Shop(Base):
    __tablename__ = "shops"
    __table_args__ = (
        Index("uq_shops_name_lower", text("lower(name)"), unique=True),
        CheckConstraint("seller_type = 'INDIVIDUAL'", name="ck_shops_seller_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(60))
    description: Mapped[str | None] = mapped_column(Text)
    seller_type: Mapped[str] = mapped_column(String(20), default="INDIVIDUAL")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )
