"""Événements consommés (contrats.md §3.3 à §3.5) : validation, contenu et destinataires.

Ce module ne dépend ni de RabbitMQ ni de FastAPI : la validation et la construction du contenu
sont des fonctions pures. Le service n'appelle jamais `catalog-service` : l'événement transporte
tout ce qu'il faut (catégorie, vendeur, titre, prix).
"""

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    field_validator,
)
from sqlalchemy import select, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from notification.models import NEW_ARTICLE, PRICE_CHANGED, Interest, Notification, Preference

ARTICLE_PUBLISHED = "article.published"
ARTICLE_PRICE_CHANGED = "article.price_changed"
PRODUCER = "catalog-service"

# Deux décimales, pas de prix nul (RM-01) ; les frais de port peuvent être nuls.
Price = Annotated[str, StringConstraints(pattern=r"^(?!0+\.00$)[0-9]{1,7}\.[0-9]{2}$")]
Amount = Annotated[str, StringConstraints(pattern=r"^[0-9]{1,7}\.[0-9]{2}$")]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Title = Annotated[str, StringConstraints(min_length=5, max_length=120)]
UserId = Annotated[str, StringConstraints(min_length=1, max_length=128)]


class InvalidEvent(Exception):
    """Message qui ne respecte pas le contrat : inutile de le relivrer."""


class _Envelope(BaseModel):
    # Lecteur tolérant (contrats.md §3.3) : les champs inconnus sont ignorés, les champs connus
    # restent exigés avec leur type. Les schémas stricts du contrat décrivent le producteur.
    model_config = ConfigDict(extra="ignore")

    event_id: uuid.UUID
    schema_version: StrictInt  # entier strict : `true` ou `"1"` ne sont pas la version 1
    occurred_at: Annotated[datetime, Field(strict=True)]
    producer: Literal["catalog-service"]
    correlation_id: Annotated[str, StringConstraints(min_length=1, max_length=128)]

    @field_validator("schema_version")
    @classmethod
    def _known_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError("schema_version inconnue")
        return value


class _Data(BaseModel):
    # Champs inconnus ignorés (évolution §3.3). Le moteur `re` de Python est nécessaire : le motif
    # du prix exclut zéro par anticipation (`(?!…)`), que le moteur par défaut ne gère pas.
    model_config = ConfigDict(extra="ignore", regex_engine="python-re")


class PublishedData(_Data):
    article_id: uuid.UUID
    shop_id: uuid.UUID
    seller_id: UserId
    category_id: uuid.UUID
    title: Title
    price: Price
    shipping_fee: Amount
    currency: Currency


class PriceChangedData(_Data):
    article_id: uuid.UUID
    seller_id: UserId
    category_id: uuid.UUID
    title: Title
    old_price: Price
    new_price: Price
    currency: Currency
    changed_by: UserId


class PublishedEvent(_Envelope):
    event_type: Literal["article.published"]
    data: PublishedData


class PriceChangedEvent(_Envelope):
    event_type: Literal["article.price_changed"]
    data: PriceChangedData


class UnknownTypeEvent(_Envelope):
    """Enveloppe valide d'un type que ce service ne connaît pas : acquittée sans traitement."""

    @field_validator("schema_version")
    @classmethod
    def _known_version(cls, value: int) -> int:  # toute version, mais entière
        return value

    producer: str  # type:ignore[assignment]
    event_type: str
    data: dict[str, Any]


Event = PublishedEvent | PriceChangedEvent
_MODELS: dict[str, type[PublishedEvent] | type[PriceChangedEvent]] = {
    ARTICLE_PUBLISHED: PublishedEvent,
    ARTICLE_PRICE_CHANGED: PriceChangedEvent,
}
_RAW: TypeAdapter[Any] = TypeAdapter(Any)


def parse_event(body: bytes) -> Event | UnknownTypeEvent:
    """Valide un corps de message.

    - type connu : validation complète (champs requis et types) ; champs inconnus ignorés ;
    - type inconnu, enveloppe valide : `UnknownTypeEvent` (à acquitter sans traitement) ;
    - JSON invalide, champ requis absent ou mal typé, version inconnue : `InvalidEvent`, sans
      recopier le contenu reçu.
    """
    try:
        raw = _RAW.validate_json(body)
        if not isinstance(raw, dict):
            raise InvalidEvent("body")
        model = _MODELS.get(str(raw.get("event_type")))
        if model is None:
            return UnknownTypeEvent.model_validate_json(body)
        # `model_validate_json` reste strict sur les types JSON (un nombre n'est pas une chaîne).
        return model.model_validate_json(body)
    except ValidationError as error:
        fields = sorted(
            {".".join(str(part) for part in e["loc"]) or "body" for e in error.errors()}
        )
        raise InvalidEvent(",".join(fields)) from error


def notification_type(event: Event) -> str:
    return NEW_ARTICLE if isinstance(event, PublishedEvent) else PRICE_CHANGED


def build_content(event: Event) -> dict[str, Any]:
    """Contenu exploitable par le front, sans autre appel : titre et prix (montants en chaîne)."""
    data = event.data
    if isinstance(data, PublishedData):
        return {"title": data.title, "price": data.price, "currency": data.currency}
    return {
        "title": data.title,
        "old_price": data.old_price,
        "new_price": data.new_price,
        "currency": data.currency,
    }


async def find_recipients(session: AsyncSession, event: Event) -> list[str]:
    """Destinataires en une requête (RM-08) : acheteurs intéressés par la catégorie, dont la
    préférence du type concerné est active (vraie si aucune préférence enregistrée), sauf le
    vendeur de l'article."""
    preference = (
        Preference.new_article if isinstance(event, PublishedEvent) else Preference.price_changed
    )
    statement = (
        select(Interest.user_id)
        .outerjoin(Preference, Preference.user_id == Interest.user_id)
        .where(
            Interest.category_id == event.data.category_id,
            Interest.user_id != event.data.seller_id,
            func.coalesce(preference, true()),
        )
        .order_by(Interest.user_id)
    )
    return list((await session.scalars(statement)).all())


async def create_notifications(session: AsyncSession, event: Event) -> list[str]:
    """Crée les notifications d'un événement dans la transaction de `session` (sans commit).

    `ON CONFLICT DO NOTHING` sur `(user_id, source_event_id)` : un événement relivré ne crée rien
    de plus (RM-09). Renvoie les acheteurs réellement notifiés par cet appel."""
    recipients = await find_recipients(session, event)
    if not recipients:
        return []
    content = build_content(event)
    type_ = notification_type(event)
    statement = (
        insert(Notification)
        .values(
            [
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "type": type_,
                    "article_id": event.data.article_id,
                    "content": content,
                    "source_event_id": event.event_id,
                }
                for user_id in recipients
            ]
        )
        .on_conflict_do_nothing(index_elements=["user_id", "source_event_id"])
        .returning(Notification.user_id)
    )
    return list((await session.scalars(statement)).all())
