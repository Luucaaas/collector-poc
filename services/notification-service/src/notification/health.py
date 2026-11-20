"""Technical endpoints, not prefixed and not routed by Traefik (contrats.md §1.1)."""

import asyncio

import structlog
from fastapi import APIRouter, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from notification.errors import ProblemError

router = APIRouter(tags=["technique"])
logger = structlog.get_logger()
READY_TIMEOUT_SECONDS = 3


@router.get("/health/live")
async def live() -> dict[str, str]:
    """Liveness: the process answers, no dependency."""
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(request: Request) -> dict[str, str]:
    """Readiness: PostgreSQL only. Never RabbitMQ, whose reconnection is automatic."""
    engine: AsyncEngine = request.app.state.engine
    try:
        async with asyncio.timeout(READY_TIMEOUT_SECONDS), engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as error:
        logger.error("readiness_failed", error=type(error).__name__, message=str(error)[:200])
        raise ProblemError(503, title="Base de données indisponible") from error
    return {"status": "ok"}
