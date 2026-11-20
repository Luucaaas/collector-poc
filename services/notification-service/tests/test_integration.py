"""Integration against a real PostgreSQL (testcontainers): probes and session lifecycle."""

from collections.abc import Iterator
from typing import Annotated

import httpx
import pytest
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.community.postgres import PostgresContainer

from notification.db import get_session
from notification.main import create_app
from tests.conftest import POSTGRES_IMAGE, build_settings


def _container() -> PostgresContainer:
    return PostgresContainer(POSTGRES_IMAGE, driver="psycopg")


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    with _container() as container:
        yield container.get_connection_url()


def _client(database_url: str) -> httpx.AsyncClient:
    app = create_app(build_settings(database_url))
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


async def test_ready_gives_200_when_postgresql_answers(postgres_url: str) -> None:
    async with _client(postgres_url) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_gives_503_when_the_database_is_stopped() -> None:
    with _container() as container:
        url = container.get_connection_url()
        async with _client(url) as client:
            assert (await client.get("/health/ready")).status_code == 200
            container.get_wrapped_container().stop()
            response = await client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["title"] == "Base de données indisponible"
    assert "psycopg" not in response.text  # no internal detail


async def test_ready_gives_503_when_the_url_is_invalid() -> None:
    async with _client("postgresql+psycopg://u:p@127.0.0.1:1/db") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503


async def test_live_does_not_depend_on_the_database() -> None:
    async with _client("postgresql+psycopg://u:p@127.0.0.1:1/db") as client:
        assert (await client.get("/health/live")).status_code == 200


async def test_session_per_request_and_clean_application_shutdown(postgres_url: str) -> None:
    app = create_app(build_settings(postgres_url))

    @app.get("/_probe/db")
    async def probe(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, int]:
        return {"value": (await session.execute(text("SELECT 42"))).scalar_one()}

    async with app.router.lifespan_context(app):  # on exit, the pool is closed
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/_probe/db")
    assert response.json() == {"value": 42}
