"""Data access for the `organizations` table. Explicit, parameterized SQL
only -- no ORM. Every method returns plain dict/DTO rows, never a cursor or
connection object.
"""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection


class OrganizationRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self, name: str, code: str, description: Optional[str] = None, connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                """
                INSERT INTO organizations (name, code, description)
                VALUES ($1, $2, $3)
                RETURNING organization_id, name, code, description, active, created_at, updated_at
                """,
                name,
                code,
                description,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create organization.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def get_by_id(self, organization_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(
            """
            SELECT organization_id, name, code, description, active, created_at, updated_at
            FROM organizations
            WHERE organization_id = $1
            """,
            organization_id,
        )
        return dict(row) if row else None

    async def get_by_code(self, code: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(
            """
            SELECT organization_id, name, code, description, active, created_at, updated_at
            FROM organizations
            WHERE code = $1
            """,
            code,
        )
        return dict(row) if row else None

    async def list_all(self, active_only: bool = True, connection: Optional[asyncpg.Connection] = None) -> list[dict[str, Any]]:
        db = self._db(connection)
        query = "SELECT organization_id, name, code, description, active, created_at, updated_at FROM organizations"
        if active_only:
            query += " WHERE active = TRUE"
        query += " ORDER BY name"
        rows = await db.fetch(query)
        return [dict(row) for row in rows]
