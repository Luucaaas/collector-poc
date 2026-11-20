"""Alembic environment: URL read from DATABASE_URL, synchronous connection (psycopg 3)."""

import os

from alembic import context
from sqlalchemy import create_engine

from catalog import models  # noqa: F401  (registers the tables in Base.metadata)
from catalog.db import Base

target_metadata = Base.metadata


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("The DATABASE_URL environment variable is required.")
    return url


def run_migrations_offline() -> None:
    context.configure(url=_database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
