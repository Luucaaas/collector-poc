"""PostgreSQL access: asynchronous SQLAlchemy 2.0 with psycopg 3, one session per request."""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base of the models, added by P4-02; `migrations/env.py` relies on its metadata."""


def create_engine(url: str, connect_timeout: int) -> AsyncEngine:
    return create_async_engine(
        url, pool_pre_ping=True, connect_args={"connect_timeout": connect_timeout}
    )


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Dependency: one session per request, closed at the end."""
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield session
