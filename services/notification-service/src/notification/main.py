"""Fabrique de l'application. Lancement : `uvicorn --factory notification.main:create_app`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from notification.auth import JwksCache, TokenVerifier
from notification.config import Settings
from notification.consumer import ArticleEventConsumer, EventProcessor
from notification.correlation import REQUEST_ID_HEADER, CorrelationMiddleware
from notification.db import create_engine
from notification.errors import register_error_handlers
from notification.health import router as health_router
from notification.logging import configure_logging
from notification.me import router as me_router
from notification.metrics import setup_metrics


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()  # lu dans l'environnement
    configure_logging(settings.log_level)

    engine = create_engine(settings.database_url, settings.db_connect_timeout_seconds)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        await application.state.consumer.start()  # rend la main même si RabbitMQ est absent
        yield
        await application.state.consumer.close()  # arrêt propre : le consommateur est fermé
        await engine.dispose()  # arrêt propre : les connexions sont fermées

    app = FastAPI(
        title="notification-service",
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
    app.include_router(me_router)
    setup_metrics(app)
    app.state.consumer = ArticleEventConsumer(
        settings.rabbitmq_url,
        EventProcessor(app.state.session_factory, app.state.business_metrics),
        app.state.business_metrics,
        prefetch=settings.consumer_prefetch,
        retry_seconds=settings.amqp_retry_seconds,
    )
    # Le dernier middleware ajouté est le plus externe : CORS en dernier (Sonar python:S8414), pour
    # que les en-têtes CORS figurent sur les réponses des routes et des gestionnaires d'erreurs
    # (401, 403, 404, 422). La corrélation est juste en dessous : elle enveloppe les routes et les
    # erreurs, donc X-Request-ID est posé avant le passage de CORS. Exception : une erreur 500 non
    # gérée est produite par ServerErrorMiddleware de Starlette, placé au-dessus de tout, donc sans
    # en-têtes CORS ; une requête préliminaire OPTIONS reçoit sa réponse de CORS, sans X-Request-ID.
    app.add_middleware(CorrelationMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_methods=["GET", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )
    return app
