"""Repository tests exercise real SQL against a real PostgreSQL instance --
they are integration tests, not unit tests. They auto-skip when no
database is reachable (e.g. `docker compose up -d postgres` has not been
run), so the rest of the suite (SPC engine + mocked-repository service
tests) always runs standalone.
"""

from __future__ import annotations

import asyncpg
import pytest
import pytest_asyncio

from app.core.config import get_settings
from app.database.postgres.connection import close_pool, create_pool
from app.database.postgres.migration_runner import run_migrations


@pytest_asyncio.fixture
async def pg_pool():
    settings = get_settings()
    try:
        pool = await asyncpg.create_pool(dsn=settings.postgres_dsn, min_size=1, max_size=2, timeout=3)
    except (OSError, asyncpg.PostgresError):
        pytest.skip("PostgreSQL is not reachable; skipping repository integration tests.")
        return
    await run_migrations(pool)
    yield pool
    await pool.close()


@pytest_asyncio.fixture
async def pg_connection(pg_pool):
    """One connection per test, wrapped in a transaction that is always
    rolled back afterward (regardless of test outcome) so tests never leave
    data behind or depend on each other."""
    async with pg_pool.acquire() as connection:
        transaction = connection.transaction()
        await transaction.start()
        try:
            yield connection
        finally:
            await transaction.rollback()
