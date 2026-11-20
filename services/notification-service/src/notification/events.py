"""Consumed events (contrats.md §3.3 to §3.5): validation, content and recipients.

This module depends neither on RabbitMQ nor on FastAPI: validation and content building
are pure functions. The service never calls `catalog-service`: the event carries
everything needed (category, seller, title, price).
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

# Two decimals, no zero price (RM-01); the shipping cost may be zero.
Price = Annotated[str, StringConstraints(pattern=r"^(?!0+\.00$)[0-9]{1,7}\.[0-9]{2}$")]
Amount = Annotated[str, StringConstraints(pattern=r"^[0-9]{1,7}\.[0-9]{2}$")]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Title = Annotated[str, StringConstraints(min_length=5, max_length=120)]
UserId = Annotated[str, StringConstraints(min_length=1, max_length=128)]


class InvalidEvent(Exception):
    """Message that does not follow the contract: no point redelivering it."""


class _Envelope(BaseModel):
    # Tolerant reader (contrats.md §3.3): unknown fields are ignored, known fields
    # stay required with their type. The strict schemas of the contract describe the producer.
    model_config = ConfigDict(extra="ignore")

    event_id: uuid.UUID
    schema_version: StrictInt  # strict integer: `true` or `"1"` are not version 1
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
    # Unknown fields ignored (evolution §3.3). Python's `re` engine is needed: the price
    # pattern excludes zero by lookahead (`(?!…)`), which the default engine does not handle.
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
    """Valid envelope of a type this service does not know: acknowledged without processing."""

    @field_validator("schema_version")
    @classmethod
    def _known_version(cls, value: int) -> int:  # any version, but an integer
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
    """Validates a message body.

    - known type: full validation (required fields and types); unknown fields ignored;
    - unknown type, valid envelope: `UnknownTypeEvent` (to acknowledge without processing);
    - invalid JSON, missing or badly typed required field, unknown version: `InvalidEvent`,
      without copying the received content.
    """
    try:
        raw = _RAW.validate_json(body)
        if not isinstance(raw, dict):
            raise InvalidEvent("body")
        model = _MODELS.get(str(raw.get("event_type")))
        if model is None:
            return UnknownTypeEvent.model_validate_json(body)
        # `model_validate_json` stays strict on JSON types (a number is not a string).
        return model.model_validate_json(body)
    except ValidationError as error:
        fields = sorted(
            {".".join(str(part) for part in e["loc"]) or "body" for e in error.errors()}
        )
        raise InvalidEvent(",".join(fields)) from error


def notification_type(event: Event) -> str:
    return NEW_ARTICLE if isinstance(event, PublishedEvent) else PRICE_CHANGED


def build_content(event: Event) -> dict[str, Any]:
    """Content usable by the front, without another call: title and price (amounts as strings)."""
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
    """Recipients in one query (RM-08): buyers interested in the category, whose
    preference for the type concerned is active (true if no preference is saved), except the
    article's seller."""
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
    """Creates the notifications of an event in the transaction of `session` (without commit).

    `ON CONFLICT DO NOTHING` on `(user_id, source_event_id)`: a redelivered event creates nothing
    more (RM-09). Returns the buyers actually notified by this call."""
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
