"""`/me/*` routes of the buyer (US-05): interests, preferences and notifications.

The user is always the one of the token (`sub`): no user identifier in the URL.
"""

import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from notification.auth import CurrentUser, require_role
from notification.db import get_session
from notification.errors import ProblemError
from notification.models import Interest, Notification, Preference
from notification.schemas import ApiModel

router = APIRouter(prefix="/api/v1/me", tags=["acheteur"])

MAX_INTERESTS = 20
MAX_RAW_IDS = 200
BuyerDep = Annotated[CurrentUser, Depends(require_role("buyer"))]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class InterestsBody(ApiModel):
    # Technical bound on the raw list; the business limit (20 distinct) is checked after
    # deduplication.
    category_ids: Annotated[list[uuid.UUID], Field(max_length=MAX_RAW_IDS)]


class InterestsOut(BaseModel):
    category_ids: list[uuid.UUID]


class PreferencesBody(ApiModel):
    new_article: StrictBool
    price_changed: StrictBool


class PreferencesOut(BaseModel):
    new_article: bool
    price_changed: bool


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    article_id: uuid.UUID
    content: dict[str, Any]
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationOut]
    total: int


async def _interests(session: AsyncSession, user_id: str) -> InterestsOut:
    rows = await session.scalars(
        select(Interest.category_id)
        .where(Interest.user_id == user_id)
        .order_by(Interest.category_id)
    )
    return InterestsOut(category_ids=list(rows.all()))


@router.get("/interests")
async def get_interests(user: BuyerDep, session: SessionDep) -> InterestsOut:
    return await _interests(session, user.sub)


@router.put("/interests")
async def put_interests(body: InterestsBody, user: BuyerDep, session: SessionDep) -> InterestsOut:
    """Replaces the whole list. The format of the identifiers is checked, not their existence:
    this service does not know the categories and does not call the catalog (ADR 0001)."""
    category_ids = list(dict.fromkeys(body.category_ids))  # deduplicated, order kept
    if len(category_ids) > MAX_INTERESTS:
        raise ProblemError(
            422,
            detail=f"Au plus {MAX_INTERESTS} catégories distinctes.",
            errors=[{"field": "category_ids", "code": "TOO_MANY_CATEGORIES"}],
        )
    # Two simultaneous replacements by the same user are serialized: the result is that of
    # one of the two, never a mix nor a primary key violation.
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:user_id, 0))"), {"user_id": user.sub}
    )
    await session.execute(delete(Interest).where(Interest.user_id == user.sub))
    if category_ids:
        await session.execute(
            insert(Interest).values(
                [{"user_id": user.sub, "category_id": category} for category in category_ids]
            )
        )
    await session.commit()
    return await _interests(session, user.sub)


@router.get("/preferences")
async def get_preferences(user: BuyerDep, session: SessionDep) -> PreferencesOut:
    preference = await session.get(Preference, user.sub)
    if preference is None:  # no preference saved: both types are active
        return PreferencesOut(new_article=True, price_changed=True)
    return PreferencesOut(
        new_article=preference.new_article, price_changed=preference.price_changed
    )


@router.put("/preferences")
async def put_preferences(
    body: PreferencesBody, user: BuyerDep, session: SessionDep
) -> PreferencesOut:
    values = {
        "user_id": user.sub,
        "new_article": body.new_article,
        "price_changed": body.price_changed,
    }
    statement = insert(Preference).values(values)
    await session.execute(
        statement.on_conflict_do_update(
            index_elements=["user_id"],
            set_={
                "new_article": statement.excluded.new_article,
                "price_changed": statement.excluded.price_changed,
                "updated_at": func.now(),
            },
        )
    )
    await session.commit()
    return PreferencesOut(new_article=body.new_article, price_changed=body.price_changed)


@router.get("/notifications")
async def get_notifications(
    user: BuyerDep,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> NotificationList:
    """Notifications of the user only, from the most recent to the oldest."""
    total = await session.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.sub)
    )
    rows = await session.scalars(
        select(Notification)
        .where(Notification.user_id == user.sub)
        .order_by(Notification.created_at.desc(), Notification.id)
        .limit(limit)
        .offset(offset)
    )
    return NotificationList(
        items=[NotificationOut.model_validate(row) for row in rows.all()], total=total or 0
    )
