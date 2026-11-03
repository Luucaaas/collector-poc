"""Accès PostgreSQL : SQLAlchemy 2.0 asynchrone avec psycopg 3, une session par requête."""

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
    """Base des modèles, ajoutés par P4-02 ; `migrations/env.py` s'appuie sur ses métadonnées."""


def create_engine(url: str, connect_timeout: int) -> AsyncEngine:
    return create_async_engine(
        url, pool_pre_ping=True, connect_args={"connect_timeout": connect_timeout}
    )


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Dépendance : une session par requête, fermée à la fin."""
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield session
