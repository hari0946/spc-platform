"""Data access for the `machines` table."""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = (
    "machine_id, plant_id, production_line_id, name, code, machine_type, "
    "manufacturer, model, active, created_at, updated_at"
)


class MachineRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self,
        plant_id: str,
        name: str,
        code: str,
        production_line_id: Optional[str] = None,
        machine_type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO machines (plant_id, production_line_id, name, code, machine_type, manufacturer, model)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING {_COLUMNS}
                """,
                plant_id, production_line_id, name, code, machine_type, manufacturer, model,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create machine.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def get_by_id(self, machine_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM machines WHERE machine_id = $1", machine_id)
        return dict(row) if row else None

    async def get_by_code(self, plant_id: str, code: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM machines WHERE plant_id = $1 AND code = $2", plant_id, code)
        return dict(row) if row else None

    async def list_by_plant(
        self, plant_id: str, active_only: bool = True, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        query = f"SELECT {_COLUMNS} FROM machines WHERE plant_id = $1"
        if active_only:
            query += " AND active = TRUE"
        query += " ORDER BY name"
        rows = await db.fetch(query, plant_id)
        return [dict(row) for row in rows]

    async def list_by_production_line(
        self, production_line_id: str, active_only: bool = True, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        query = f"SELECT {_COLUMNS} FROM machines WHERE production_line_id = $1"
        if active_only:
            query += " AND active = TRUE"
        query += " ORDER BY name"
        rows = await db.fetch(query, production_line_id)
        return [dict(row) for row in rows]
