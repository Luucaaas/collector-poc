"""Fabrique de l'application. Lancement : `uvicorn --factory catalog.main:create_app`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from catalog.auth import JwksCache, TokenVerifier
from catalog.categories import router as categories_router
from catalog.config import Settings
from catalog.correlation import REQUEST_ID_HEADER, CorrelationMiddleware
from catalog.db import create_engine
from catalog.errors import register_error_handlers
from catalog.health import router as health_router
from catalog.logging import configure_logging
from catalog.metrics import setup_metrics
from catalog.shops import router as shops_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()  # lu dans l'environnement
    configure_logging(settings.log_level)

    engine = create_engine(settings.database_url, settings.db_connect_timeout_seconds)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await engine.dispose()  # arrêt propre : le pool de connexions est fermé

    app = FastAPI(
        title="catalog-service",
        lifespan=lifespan,
        openapi_url="/api/v1/openapi.json",
        docs_url=None,
        redoc_url=None,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    app.state.verifier = TokenVerifier(
        settings.issuer,
        settings.audience,
        JwksCache(
            settings.jwks_url,
            settings.jwks_ttl_seconds,
            settings.jwks_min_refetch_seconds,
            max_stale=settings.jwks_max_stale_seconds,
            timeout=settings.jwks_timeout_seconds,
        ),
    )

    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(categories_router)
    app.include_router(shops_router)
    setup_metrics(app)
    # Le dernier middleware ajouté est le plus externe : la corrélation enveloppe tout.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )
    app.add_middleware(CorrelationMiddleware)
    return app
