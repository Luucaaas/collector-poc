"""Boutiques (US-02) : création et liste pour un vendeur, page publique d'une boutique."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.auth import CurrentUser, require_role
from catalog.contact import contact_reasons
from catalog.db import get_session
from catalog.errors import ProblemError
from catalog.models import Shop
from catalog.persistence import commit_unique
from catalog.schemas import ApiModel

router = APIRouter(prefix="/api/v1/shops", tags=["boutiques"])

ShopName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=60)]
ShopDescription = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]
SellerDep = Annotated[CurrentUser, Depends(require_role("seller"))]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class ShopCreate(ApiModel):
    name: ShopName
    description: ShopDescription | None = None


class ShopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: str
    name: str
    description: str | None
    seller_type: str
    created_at: datetime


class ShopList(BaseModel):
    items: list[ShopOut]
    total: int


@router.post("", status_code=201)
async def create_shop(payload: ShopCreate, user: SellerDep, session: SessionDep) -> ShopOut:
    # RM-05 : une boutique qui contient des coordonnées est refusée, et rien n'est enregistré.
    errors = [
        {"field": field, "code": code}
        for field, value in (("name", payload.name), ("description", payload.description))
        for code in contact_reasons(value)
    ]
    if errors:
        raise ProblemError(
            422,
            detail="Le nom et la description ne doivent contenir ni email ni téléphone.",
            errors=errors,
        )
    description = payload.description or None  # une description vide est enregistrée `null`
    shop = Shop(owner_id=user.sub, name=payload.name, description=description)
    session.add(shop)
    await commit_unique(session)
    return ShopOut.model_validate(shop)


@router.get("/me")
async def my_shops(user: SellerDep, session: SessionDep) -> ShopList:
    rows = (
        await session.scalars(
            select(Shop).where(Shop.owner_id == user.sub).order_by(Shop.created_at, Shop.id)
        )
    ).all()
    return ShopList(items=[ShopOut.model_validate(row) for row in rows], total=len(rows))


@router.get("/{shop_id}")
async def get_shop(shop_id: uuid.UUID, session: SessionDep) -> ShopOut:
    shop = await session.get(Shop, shop_id)
    if shop is None:
        raise ProblemError(404, reason="shop_not_found")
    return ShopOut.model_validate(shop)
