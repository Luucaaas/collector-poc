"""Modèles SQLAlchemy de notification_db (contrats.md §4.2).

`user_id` est le `sub` Keycloak et `category_id` un identifiant du catalogue : ce sont des
identifiants opaques, sans clé étrangère (une base par service).
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from notification.db import Base

NEW_ARTICLE = "NEW_ARTICLE"
PRICE_CHANGED = "PRICE_CHANGED"


def now() -> datetime:
    return datetime.now(UTC)


class Interest(Base):
    __tablename__ = "interests"

    # La clé primaire (user_id, category_id) ne sert pas la recherche des destinataires par
    # catégorie : index dédié, déclaré aussi dans la migration 0001.
    __table_args__ = (Index("ix_interests_category_id", "category_id"),)

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    category_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )


class Preference(Base):
    __tablename__ = "preferences"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    new_article: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    price_changed: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        # RM-09 : un même événement ne produit qu'une notification par acheteur.
        UniqueConstraint("user_id", "source_event_id", name="uq_notifications_user_event"),
        CheckConstraint("type IN ('NEW_ARTICLE', 'PRICE_CHANGED')", name="ck_notifications_type"),
        Index("ix_notifications_user_created", "user_id", text("created_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(20))
    article_id: Mapped[uuid.UUID]
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    source_event_id: Mapped[uuid.UUID]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
