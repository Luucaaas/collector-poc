"""Modèles SQLAlchemy de catalog_db (contrats.md §4.1) : catégories, boutiques et articles."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catalog.db import Base


def now() -> datetime:
    return datetime.now(UTC)


class Category(Base):
    __tablename__ = "categories"
    # L'unicité sans tenir compte de la casse est garantie par la base (index fonctionnel).
    __table_args__ = (Index("uq_categories_name_lower", text("lower(name)"), unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(60))
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
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
        DateTime(timezone=True), default=now, server_default=func.now()
    )


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        CheckConstraint("price > 0", name="ck_articles_price_positive"),
        CheckConstraint("shipping_fee >= 0", name="ck_articles_shipping_fee_non_negative"),
        CheckConstraint("status IN ('PUBLISHED', 'REJECTED')", name="ck_articles_status"),
        # Index du catalogue public : filtre sur le statut et la catégorie, tri par date.
        Index("ix_articles_catalog", "status", "category_id", text("created_at DESC")),
        Index("ix_articles_shop_id", "shop_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    shop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shops.id"))
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    shipping_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    status: Mapped[str] = mapped_column(String(20))
    rejection_reasons: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )

    # Chargements par requêtes séparées (`selectin`) : pas de jointure externe, donc compatible
    # avec `SELECT … FOR UPDATE`, et aucun chargement paresseux (interdit en asynchrone).
    shop: Mapped[Shop] = relationship(lazy="selectin")
    photos: Mapped[list["ArticlePhoto"]] = relationship(
        lazy="selectin", order_by="ArticlePhoto.position"
    )


class ArticlePhoto(Base):
    __tablename__ = "article_photos"
    __table_args__ = (
        UniqueConstraint("article_id", "position", name="uq_article_photos_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("articles.id"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    position: Mapped[int] = mapped_column(SmallInteger)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("articles.id"), index=True)
    old_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    new_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    changed_by: Mapped[str] = mapped_column(String(128))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
