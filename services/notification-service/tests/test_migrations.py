"""Migration 0001 sur un vrai PostgreSQL : montée, contraintes appliquées, descente."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from testcontainers.community.postgres import PostgresContainer

from tests.conftest import POSTGRES_IMAGE

TABLES = {"interests", "preferences", "notifications"}


def _names(url: str, query: str) -> set[str]:
    engine = create_engine(url)
    with engine.connect() as connection:
        names = {row[0] for row in connection.execute(text(query))}
    engine.dispose()
    return names


def _tables(url: str) -> set[str]:
    return _names(url, "SELECT tablename FROM pg_tables WHERE schemaname = 'public'")


def _indexes(url: str) -> set[str]:
    return _names(url, "SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")


def test_migration_0001_monte_applique_les_contraintes_puis_descend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with PostgresContainer(POSTGRES_IMAGE, driver="psycopg") as container:
        url = container.get_connection_url()
        monkeypatch.setenv("DATABASE_URL", url)
        config = Config("alembic.ini")

        assert not TABLES & _tables(url)
        command.upgrade(config, "head")
        assert TABLES <= _tables(url)
        assert {
            "interests_pkey",
            "ix_interests_category_id",
            "preferences_pkey",
            "uq_notifications_user_event",
            "ix_notifications_user_created",
        } <= _indexes(url)

        engine = create_engine(url)
        with engine.connect() as connection:
            definition = connection.execute(
                text(
                    "SELECT indexdef FROM pg_indexes "
                    "WHERE indexname = 'ix_notifications_user_created'"
                )
            ).scalar_one()
            defaults = connection.execute(
                text(
                    "SELECT column_name, column_default FROM information_schema.columns "
                    "WHERE table_name = 'preferences' "
                    "AND column_name IN ('new_article', 'price_changed')"
                )
            ).all()
        assert "user_id, created_at DESC" in definition
        assert {name: default for name, default in defaults} == {
            "new_article": "true",
            "price_changed": "true",
        }

        insert = text(
            "INSERT INTO notifications (id, user_id, type, article_id, content, source_event_id) "
            "VALUES (gen_random_uuid(), :user_id, :type, gen_random_uuid(), '{}', :event)"
        )
        event = "0f8e2d4c-6b1a-4f3e-9d7c-5a4b3c2d1e0f"
        with engine.begin() as connection:
            connection.execute(insert, {"user_id": "chloe", "type": "NEW_ARTICLE", "event": event})
            # même acheteur, même événement : refusé (RM-09) ; autre acheteur : accepté
            connection.execute(insert, {"user_id": "dave", "type": "NEW_ARTICLE", "event": event})
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(
                insert, {"user_id": "chloe", "type": "PRICE_CHANGED", "event": event}
            )
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(
                insert,
                {
                    "user_id": "erin",
                    "type": "AUTRE",
                    "event": "5d3c1b2a-9e8f-4a7b-8c6d-0e1f2a3b4c5d",
                },
            )
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO preferences (user_id) VALUES ('chloe')"))
            row = connection.execute(
                text("SELECT new_article, price_changed FROM preferences")
            ).one()
        assert tuple(row) == (True, True)
        engine.dispose()

        command.downgrade(config, "base")
        assert not TABLES & _tables(url)
        assert not {i for i in _indexes(url) if i.startswith(("ix_", "uq_"))}

        command.upgrade(config, "head")  # rejouable
        assert TABLES <= _tables(url)
        command.downgrade(config, "base")


def test_alembic_exige_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        command.upgrade(Config("alembic.ini"), "head")
