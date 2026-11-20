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
    settings = settings or Settings()  # read from the environment
    configure_logging(settings.log_level)

    engine = create_engine(settings.database_url, settings.db_connect_timeout_seconds)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        await application.state.consumer.start()  # returns even if RabbitMQ is absent
        try:
            yield
        finally:  # even on early exit: the closing is never skipped (Sonar python:S9152)
            try:
                await application.state.consumer.close()  # clean shutdown: the consumer is closed
            finally:
                await engine.dispose()  # clean shutdown: the connections are closed

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
    # The last middleware added is the outermost: CORS last (Sonar python:S8414), so
    # that the CORS headers appear on the responses of the routes and of the error handlers
    # (401, 403, 404, 422). Correlation is just below: it wraps the routes and the
    # errors, so X-Request-ID is set before CORS runs. Exception: an unhandled 500 error
    # is produced by Starlette's ServerErrorMiddleware, placed above everything, hence without
    # CORS headers; an OPTIONS preflight request gets its response from CORS, without X-Request-ID.
    app.add_middleware(CorrelationMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_methods=["GET", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )
    return app
