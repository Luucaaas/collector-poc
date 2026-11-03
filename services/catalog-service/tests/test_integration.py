"""Tests d'intégration contre un vrai PostgreSQL (testcontainers) : /health/ready et Alembic."""

from collections.abc import Iterator
from typing import Annotated

import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi import Depends
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.community.postgres import PostgresContainer

from catalog.db import get_session
from catalog.main import create_app
from tests.conftest import build_settings

POSTGRES_IMAGE = "postgres:18.4-alpine"  # version retenue pour le POC (ADR 0008)


def _container() -> PostgresContainer:
    return PostgresContainer(POSTGRES_IMAGE, driver="psycopg")


@pytest.fixture(scope="module")
def postgres_url() -> Iterator[str]:
    with _container() as container:
        yield container.get_connection_url()


def _client(database_url: str) -> httpx.AsyncClient:
    app = create_app(build_settings(database_url))
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


async def test_ready_donne_200_quand_postgresql_repond(postgres_url: str) -> None:
    async with _client(postgres_url) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_donne_503_quand_la_base_est_arretee() -> None:
    with _container() as container:
        url = container.get_connection_url()
        async with _client(url) as client:
            assert (await client.get("/health/ready")).status_code == 200
            container.get_wrapped_container().stop()
            response = await client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["title"] == "Base de données indisponible"
    assert "psycopg" not in response.text  # aucun détail interne


async def test_ready_donne_503_quand_l_url_est_invalide() -> None:
    async with _client("postgresql+psycopg://u:p@127.0.0.1:1/db") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503


async def test_live_ne_depend_pas_de_la_base() -> None:
    async with _client("postgresql+psycopg://u:p@127.0.0.1:1/db") as client:
        assert (await client.get("/health/live")).status_code == 200


def test_la_migration_alembic_de_reference_s_applique(
    postgres_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(postgres_url)
    with engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    engine.dispose()
    assert version == "0001"
    command.downgrade(config, "base")


def test_alembic_exige_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        command.upgrade(Config("alembic.ini"), "head")


async def test_session_par_requete_et_arret_propre_de_l_application(postgres_url: str) -> None:
    app = create_app(build_settings(postgres_url))

    @app.get("/_probe/db")
    async def probe(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, int]:
        return {"value": (await session.execute(text("SELECT 42"))).scalar_one()}

    async with app.router.lifespan_context(app):  # à la sortie, le pool est fermé
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/_probe/db")
    assert response.json() == {"value": 42}
