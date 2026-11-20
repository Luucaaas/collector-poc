"""Database write: a uniqueness violation becomes a 409 (RFC 9457)."""

import psycopg.errors
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.errors import ProblemError


async def commit_unique(session: AsyncSession) -> None:
    """Commits the transaction. The database guarantees uniqueness: two concurrent requests
    with the same name cannot both succeed, whatever the order of the checks."""
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        if not isinstance(error.orig, psycopg.errors.UniqueViolation):
            raise
        raise ProblemError(
            409,
            detail="Nom déjà utilisé ou trop proche d'un nom existant.",
            errors=[{"field": "name", "code": "NAME_ALREADY_USED"}],
        ) from error
