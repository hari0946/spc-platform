"""Data access for the `plants` table."""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = "plant_id, organization_id, name, code, timezone, country, active, created_at, updated_at"


class PlantRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self,
        organization_id: str,
        name: str,
        code: str,
        timezone: str = "UTC",
        country: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO plants (organization_id, name, code, timezone, country)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING {_COLUMNS}
                """,
                organization_id,
                name,
                code,
                timezone,
                country,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create plant.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def get_by_id(self, plant_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM plants WHERE plant_id = $1", plant_id)
        return dict(row) if row else None

    async def list_by_organization(
        self, organization_id: str, active_only: bool = True, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        query = f"SELECT {_COLUMNS} FROM plants WHERE organization_id = $1"
        if active_only:
            query += " AND active = TRUE"
        query += " ORDER BY name"
        rows = await db.fetch(query, organization_id)
        return [dict(row) for row in rows]
