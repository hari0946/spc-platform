"""asyncpg connection pool management.

This is the ONLY module that owns the asyncpg pool. Repositories receive a
pool (or a single connection, inside a transaction) through dependency
injection -- they never construct their own connections and never leak
cursor/connection objects back to services.
"""

from __future__ import annotations

import json

import asyncpg

from app.core.config import Settings, get_settings
from app.core.exceptions import DatabaseConnectionError
from app.core.logging import get_logger

logger = get_logger(__name__)

_pool: asyncpg.Pool | None = None


async def _init_connection(connection: asyncpg.Connection) -> None:
    """Every connection in the pool gets two type-codec overrides applied
    to asyncpg's defaults, so repository code never has to remember to
    convert these itself at every call site:

    - `uuid` columns decode to plain Python `str`, not `uuid.UUID`. Every
      UUID primary/foreign key in this schema is treated as an opaque
      string identifier everywhere else in the codebase -- Pydantic
      response schemas, the Snowflake connector's parameter binding, JSON
      serialization -- none of which accept a raw uuid.UUID.
    - `json`/`jsonb` columns decode to native Python dict/list (asyncpg's
      default is to hand back the raw JSON text), so a column like
      findings.statistical_fact or spc_configurations.ruleset comes back
      already parsed.
    - `numeric` columns decode to plain Python `float`, not
      `decimal.Decimal`. asyncpg's default Decimal return value mixes
      badly with ordinary float arithmetic elsewhere in the codebase (SPC
      engine formulas, e.g. `3 * cpk - 1.5`, raise TypeError the moment a
      Decimal meets a float literal) -- Pydantic quietly coerces Decimal
      to float at the API-response boundary, which is exactly why this
      class of bug doesn't show up until some code does raw arithmetic on
      a value read straight from the database, before it ever reaches a
      schema. Float64 precision is far beyond what any measurement or
      capability index here needs, so there is no meaningful precision
      loss from doing this uniformly at the connection level.
    """
    await connection.set_type_codec(
        "uuid", schema="pg_catalog", encoder=str, decoder=str, format="text"
    )
    for type_name in ("json", "jsonb"):
        await connection.set_type_codec(
            type_name,
            schema="pg_catalog",
            encoder=json.dumps,
            decoder=json.loads,
            format="text",
        )
    await connection.set_type_codec(
        "numeric", schema="pg_catalog", encoder=str, decoder=float, format="text"
    )


async def create_pool(settings: Settings | None = None) -> asyncpg.Pool:
    global _pool
    settings = settings or get_settings()
    try:
        _pool = await asyncpg.create_pool(
            dsn=settings.postgres_dsn,
            min_size=settings.postgres_pool_min_size,
            max_size=settings.postgres_pool_max_size,
            command_timeout=settings.postgres_command_timeout_seconds,
            init=_init_connection,
        )
    except (OSError, asyncpg.PostgresError) as exc:
        logger.error("postgres_pool_creation_failed", error=str(exc))
        raise DatabaseConnectionError(
            "Could not connect to PostgreSQL. Check POSTGRES_* environment variables and "
            "that the database is reachable.",
            details={"reason": str(exc)},
        ) from exc
    logger.info("postgres_pool_created", min_size=settings.postgres_pool_min_size, max_size=settings.postgres_pool_max_size)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("postgres_pool_closed")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise DatabaseConnectionError("PostgreSQL connection pool has not been initialized yet.")
    return _pool
