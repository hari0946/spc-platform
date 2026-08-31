"""Data access for the `parameters` table (quality characteristics, e.g.
SHAFT_DIAMETER)."""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = "parameter_id, name, description, data_type, unit, target_value, active, created_at, updated_at"


class ParameterRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self,
        name: str,
        unit: str,
        description: Optional[str] = None,
        data_type: str = "CONTINUOUS",
        target_value: Optional[float] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO parameters (name, description, data_type, unit, target_value)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING {_COLUMNS}
                """,
                name, description, data_type, unit, target_value,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create parameter.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def get_by_id(self, parameter_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM parameters WHERE parameter_id = $1", parameter_id)
        return dict(row) if row else None

    async def get_by_name(self, name: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM parameters WHERE name = $1", name)
        return dict(row) if row else None

    async def list_all(self, active_only: bool = True, connection: Optional[asyncpg.Connection] = None) -> list[dict[str, Any]]:
        db = self._db(connection)
        query = f"SELECT {_COLUMNS} FROM parameters"
        if active_only:
            query += " WHERE active = TRUE"
        query += " ORDER BY name"
        rows = await db.fetch(query)
        return [dict(row) for row in rows]
