"""Écriture en base : une violation d'unicité devient un 409 (RFC 9457)."""

import psycopg.errors
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.errors import ProblemError


async def commit_unique(session: AsyncSession) -> None:
    """Valide la transaction. C'est la base qui garantit l'unicité : deux requêtes concurrentes
    avec le même nom ne peuvent pas toutes deux réussir, quel que soit l'ordre des vérifications."""
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
