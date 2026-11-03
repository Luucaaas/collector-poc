"""Articles (US-03, US-04) : publication avec contrôle automatique, catalogue, prix et historique.

Les événements sont publiés **après** le commit, jamais avant (contrats.md §3.2, limite L2).
"""

import re
import uuid
from decimal import Decimal
from typing import Annotated, Literal

import structlog
from fastapi import APIRouter, Depends, Query, Request
from pydantic import AfterValidator, BaseModel, BeforeValidator, Field, StringConstraints
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.auth import CurrentUser, CurrentUserDep, OptionalUserDep, require_role
from catalog.contact import contact_reasons
from catalog.db import get_session
from catalog.errors import ProblemError, forbidden
from catalog.events import (
    ARTICLE_PRICE_CHANGED,
    ARTICLE_PUBLISHED,
    EventPublisher,
    build_event,
    format_instant,
)
from catalog.metrics import BusinessMetrics
from catalog.models import Article, ArticlePhoto, Category, PriceHistory, Shop, now
from catalog.schemas import ApiModel

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])
logger = structlog.get_logger()

PUBLISHED = "PUBLISHED"
REJECTED = "REJECTED"
MAX_PRICE = Decimal("1000000")
_CENTS = Decimal("0.01")
_AMOUNT = re.compile(r"\d{1,7}(?:\.\d{1,2})?")  # chaîne décimale, 2 décimales au plus


def _parse_amount(value: object) -> Decimal:
    """Un montant est une chaîne décimale (`"120.00"`) : un nombre JSON est refusé (pas de flottant
    pour l'argent)."""
    if not isinstance(value, str) or not _AMOUNT.fullmatch(value):
        raise ValueError("Montant attendu : chaîne décimale, 2 décimales au plus.")
    return Decimal(value).quantize(_CENTS)


def _check_price(value: Decimal) -> Decimal:
    if not 0 < value <= MAX_PRICE:
        raise ValueError("Le prix doit être supérieur à 0 et au plus 1 000 000.")
    return value


def _check_fee(value: Decimal) -> Decimal:
    if value > MAX_PRICE:
        raise ValueError("Les frais de port dépassent le maximum.")
    return value


Price = Annotated[Decimal, BeforeValidator(_parse_amount), AfterValidator(_check_price)]
ShippingFee = Annotated[Decimal, BeforeValidator(_parse_amount), AfterValidator(_check_fee)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=120)]
Description = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=20, max_length=5000)
]
PhotoUrl = Annotated[str, StringConstraints(pattern=r"^https://[^\s/]+(/\S*)?$", max_length=500)]

SellerDep = Annotated[CurrentUser, Depends(require_role("seller"))]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_publisher(request: Request) -> EventPublisher:
    publisher: EventPublisher = request.app.state.publisher
    return publisher


def get_metrics(request: Request) -> BusinessMetrics:
    metrics: BusinessMetrics = request.app.state.business_metrics
    return metrics


PublisherDep = Annotated[EventPublisher, Depends(get_publisher)]
MetricsDep = Annotated[BusinessMetrics, Depends(get_metrics)]


class ArticleCreate(ApiModel):
    shop_id: uuid.UUID
    category_id: uuid.UUID
    title: Title
    description: Description
    photo_urls: Annotated[list[PhotoUrl], Field(min_length=1, max_length=10)]
    price: Price
    shipping_fee: ShippingFee
    currency: Literal["EUR"] = "EUR"


class PriceUpdate(ApiModel):
    price: Price


class ArticleOut(BaseModel):
    id: uuid.UUID
    shop_id: uuid.UUID
    category_id: uuid.UUID
    seller_id: str
    title: str
    description: str
    photo_urls: list[str]
    price: str
    shipping_fee: str
    currency: str
    status: str
    rejection_reasons: list[str]
    created_at: str


class ArticleList(BaseModel):
    items: list[ArticleOut]
    total: int


class PriceHistoryOut(BaseModel):
    old_price: str
    new_price: str
    changed_by: str
    changed_at: str


class PriceHistoryList(BaseModel):
    items: list[PriceHistoryOut]
    total: int


def money(value: Decimal) -> str:
    return f"{value:.2f}"


def to_out(article: Article) -> ArticleOut:
    return ArticleOut(
        id=article.id,
        shop_id=article.shop_id,
        category_id=article.category_id,
        seller_id=article.shop.owner_id,
        title=article.title,
        description=article.description,
        photo_urls=[photo.url for photo in article.photos],
        price=money(article.price),
        shipping_fee=money(article.shipping_fee),
        currency=article.currency,
        status=article.status,
        rejection_reasons=list(article.rejection_reasons),
        created_at=format_instant(article.created_at),
    )


def _can_see_private(article: Article, user: CurrentUser | None) -> bool:
    return user is not None and ("admin" in user.roles or article.shop.owner_id == user.sub)


def _deny(article: Article, user: CurrentUser | None, reason: str) -> ProblemError:
    """Refus pour un utilisateur qui n'a pas le droit d'agir : 404 si l'article n'est pas publié
    et qu'il ne peut pas le voir (on ne révèle pas son existence, §1.2), sinon 403."""
    if article.status != PUBLISHED and not _can_see_private(article, user):
        return ProblemError(404, reason="article_not_visible")
    return forbidden(reason)


async def _get_article(session: AsyncSession, article_id: uuid.UUID) -> Article:
    article = await session.get(Article, article_id)
    if article is None:
        raise ProblemError(404, reason="article_not_found")
    return article


@router.post("", status_code=201)
async def create_article(
    payload: ArticleCreate,
    user: SellerDep,
    session: SessionDep,
    publisher: PublisherDep,
    metrics: MetricsDep,
) -> ArticleOut:
    shop = await session.get(Shop, payload.shop_id)
    category = await session.get(Category, payload.category_id)
    errors = []
    if shop is None:
        errors.append({"field": "shop_id", "code": "SHOP_NOT_FOUND"})
    if category is None:
        errors.append({"field": "category_id", "code": "CATEGORY_NOT_FOUND"})
    if shop is None or category is None:
        raise ProblemError(
            422, detail="La boutique ou la catégorie indiquée n'existe pas.", errors=errors
        )
    if shop.owner_id != user.sub:
        raise forbidden("shop_not_owned")

    # RM-02 : un article qui contient des coordonnées est conservé, au statut REJECTED.
    reasons = contact_reasons(payload.title, payload.description)
    moment = now()
    article = Article(
        shop_id=shop.id,
        category_id=category.id,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        shipping_fee=payload.shipping_fee,
        currency=payload.currency,
        status=REJECTED if reasons else PUBLISHED,
        rejection_reasons=reasons,
        created_at=moment,
        updated_at=moment,
        shop=shop,
        photos=[
            ArticlePhoto(url=url, position=position)
            for position, url in enumerate(payload.photo_urls)
        ],
    )
    session.add(article)
    await session.commit()

    logger.info(
        "article_created", article_id=str(article.id), status=article.status, reasons=reasons
    )
    if reasons:
        for reason in reasons:
            metrics.articles_rejected.labels(reason=reason).inc()
    else:
        metrics.articles_published.inc()
        event = build_event(
            ARTICLE_PUBLISHED,
            moment,
            {
                "article_id": str(article.id),
                "shop_id": str(shop.id),
                "seller_id": shop.owner_id,
                "category_id": str(category.id),
                "title": article.title,
                "price": money(article.price),
                "shipping_fee": money(article.shipping_fee),
                "currency": article.currency,
            },
        )
        await publisher.publish(event)  # après le commit ; un échec est journalisé, pas propagé
    return to_out(article)


@router.get("")
async def list_articles(
    session: SessionDep,
    category_id: uuid.UUID | None = None,
    shop_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ArticleList:
    conditions = [Article.status == PUBLISHED]
    if category_id is not None:
        conditions.append(Article.category_id == category_id)
    if shop_id is not None:
        conditions.append(Article.shop_id == shop_id)
    total = await session.scalar(select(func.count()).select_from(Article).where(*conditions))
    rows = (
        await session.scalars(
            select(Article)
            .where(*conditions)
            .order_by(Article.created_at.desc(), Article.id)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return ArticleList(items=[to_out(row) for row in rows], total=total or 0)


@router.get("/{article_id}")
async def get_article(
    article_id: uuid.UUID, session: SessionDep, user: OptionalUserDep
) -> ArticleOut:
    article = await _get_article(session, article_id)
    if article.status != PUBLISHED and not _can_see_private(article, user):
        # 404 et non 403 : on ne révèle pas l'existence d'un article non publié (§1.2).
        raise ProblemError(404, reason="article_not_visible")
    return to_out(article)


@router.put("/{article_id}/price")
async def change_price(
    article_id: uuid.UUID,
    payload: PriceUpdate,
    user: SellerDep,
    session: SessionDep,
    publisher: PublisherDep,
    metrics: MetricsDep,
) -> ArticleOut:
    # Verrou de ligne : deux modifications concurrentes s'enchaînent, l'historique reste cohérent.
    article = (
        await session.scalars(
            select(Article).where(Article.id == article_id).with_for_update(of=Article)
        )
    ).one_or_none()
    if article is None:
        raise ProblemError(404, reason="article_not_found")
    if article.shop.owner_id != user.sub:
        raise _deny(article, user, "article_not_owned")
    if article.status != PUBLISHED:
        raise ProblemError(
            409,
            detail="Seul un article publié peut changer de prix.",
            reason="article_not_published",
        )
    if payload.price == article.price:
        return to_out(article)  # RM-04 : prix identique, ni historique ni événement

    moment = now()
    old_price = article.price
    session.add(
        PriceHistory(
            article_id=article.id,
            old_price=old_price,
            new_price=payload.price,
            changed_by=user.sub,
            changed_at=moment,
        )
    )
    article.price = payload.price
    article.updated_at = moment
    await session.commit()

    metrics.price_changes.inc()
    logger.info(
        "article_price_changed",
        article_id=str(article.id),
        old_price=money(old_price),
        new_price=money(payload.price),
    )
    event = build_event(
        ARTICLE_PRICE_CHANGED,
        moment,
        {
            "article_id": str(article.id),
            "seller_id": article.shop.owner_id,
            "category_id": str(article.category_id),
            "title": article.title,
            "old_price": money(old_price),
            "new_price": money(payload.price),
            "currency": article.currency,
            "changed_by": user.sub,
        },
    )
    await publisher.publish(event)
    return to_out(article)


@router.get("/{article_id}/price-history")
async def price_history(
    article_id: uuid.UUID, user: CurrentUserDep, session: SessionDep
) -> PriceHistoryList:
    article = await _get_article(session, article_id)
    if not _can_see_private(article, user):
        raise _deny(article, user, "history_not_allowed")
    rows = (
        await session.scalars(
            select(PriceHistory)
            .where(PriceHistory.article_id == article_id)
            .order_by(PriceHistory.changed_at, PriceHistory.id)
        )
    ).all()
    items = [
        PriceHistoryOut(
            old_price=money(row.old_price),
            new_price=money(row.new_price),
            changed_by=row.changed_by,
            changed_at=format_instant(row.changed_at),
        )
        for row in rows
    ]
    return PriceHistoryList(items=items, total=len(items))
