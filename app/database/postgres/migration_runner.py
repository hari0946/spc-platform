"""Plain-SQL migration runner. No ORM, no Alembic.

Reads *.sql files from app/database/migrations/, applies any not yet
recorded in the `schema_migrations` table (in numeric filename order,
inside a transaction per file), and records each applied version with a
timestamp. Designed to be safe to re-run: already-applied migrations are
skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

import asyncpg

from app.core.logging import get_logger

logger = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"

_FILENAME_PATTERN = re.compile(r"^(\d+)_.*\.sql$")


async def _ensure_migrations_table(connection: asyncpg.Connection) -> None:
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version      TEXT PRIMARY KEY,
            filename     TEXT NOT NULL,
            applied_at   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def _discover_migration_files() -> list[Path]:
    files = [p for p in MIGRATIONS_DIR.glob("*.sql") if _FILENAME_PATTERN.match(p.name)]
    return sorted(files, key=lambda p: int(_FILENAME_PATTERN.match(p.name).group(1)))


async def run_migrations(pool: asyncpg.Pool) -> list[str]:
    """Apply all unapplied migration files. Returns the list of filenames
    that were newly applied (empty if the schema was already current)."""
    applied: list[str] = []
    async with pool.acquire() as connection:
        await _ensure_migrations_table(connection)
        already_applied = {
            row["version"] for row in await connection.fetch("SELECT version FROM schema_migrations")
        }

        for path in _discover_migration_files():
            match = _FILENAME_PATTERN.match(path.name)
            version = match.group(1)
            if version in already_applied:
                continue

            sql = path.read_text(encoding="utf-8")
            logger.info("migration_applying", filename=path.name)
            try:
                async with connection.transaction():
                    await connection.execute(sql)
                    await connection.execute(
                        "INSERT INTO schema_migrations (version, filename) VALUES ($1, $2)",
                        version,
                        path.name,
                    )
            except asyncpg.PostgresError as exc:
                logger.error("migration_failed", filename=path.name, error=str(exc))
                raise
            applied.append(path.name)
            logger.info("migration_applied", filename=path.name)

    if not applied:
        logger.info("migrations_up_to_date")
    return applied
