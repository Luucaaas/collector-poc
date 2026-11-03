"""Catégories (US-01) : liste publique, création réservée à l'admin."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.auth import CurrentUser, require_role
from catalog.db import get_session
from catalog.errors import ProblemError
from catalog.models import Category
from catalog.persistence import commit_unique
from catalog.schemas import ApiModel
from catalog.slug import slugify

router = APIRouter(prefix="/api/v1/categories", tags=["catégories"])

SLUG_MAX_LENGTH = 120  # 60 caractères à 2 lettres (« œ » : « oe ») ; au-delà (« ﬃ » : « ffi »), 422

CategoryName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=60)]


class CategoryCreate(ApiModel):
    name: CategoryName


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime


class CategoryList(BaseModel):
    items: list[CategoryOut]
    total: int


@router.get("")
async def list_categories(session: Annotated[AsyncSession, Depends(get_session)]) -> CategoryList:
    """Liste publique, triée par nom."""
    rows = (await session.scalars(select(Category).order_by(func.lower(Category.name)))).all()
    return CategoryList(items=[CategoryOut.model_validate(row) for row in rows], total=len(rows))


@router.post("", status_code=201)
async def create_category(
    payload: CategoryCreate,
    _: Annotated[CurrentUser, Depends(require_role("admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CategoryOut:
    slug = slugify(payload.name)
    if not slug or len(slug) > SLUG_MAX_LENGTH:  # aucun slug exploitable, ou trop long
        raise ProblemError(
            422,
            detail="Le nom doit donner un identifiant d'URL valide (lettres ou chiffres).",
            errors=[{"field": "name", "code": "NAME_INVALID"}],
        )
    category = Category(name=payload.name, slug=slug)
    session.add(category)
    await commit_unique(session)
    return CategoryOut.model_validate(category)
