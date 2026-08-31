"""Data access for the `operations` table."""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = "operation_id, process_id, name, code, sequence_number, description, active, created_at, updated_at"


class OperationRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self,
        process_id: str,
        name: str,
        code: str,
        sequence_number: Optional[int] = None,
        description: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO operations (process_id, name, code, sequence_number, description)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING {_COLUMNS}
                """,
                process_id, name, code, sequence_number, description,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create operation.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def get_by_id(self, operation_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM operations WHERE operation_id = $1", operation_id)
        return dict(row) if row else None

    async def find_by_code_in_organization(
        self, organization_id: str, code: str, connection: Optional[asyncpg.Connection] = None
    ) -> Optional[dict[str, Any]]:
        """Resolve an operation by code across every process belonging to an
        organization. Used when an inbound CSV identifies an operation by
        code alone, without also specifying which process it belongs to
        (the process is then implied by the resolved operation's process_id)."""
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            SELECT o.operation_id, o.process_id, o.name, o.code, o.sequence_number,
                   o.description, o.active, o.created_at, o.updated_at
            FROM operations o
            JOIN processes p ON p.process_id = o.process_id
            WHERE p.organization_id = $1 AND o.code = $2
            LIMIT 1
            """,
            organization_id, code,
        )
        return dict(row) if row else None

    async def list_by_process(
        self, process_id: str, active_only: bool = True, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        query = f"SELECT {_COLUMNS} FROM operations WHERE process_id = $1"
        if active_only:
            query += " AND active = TRUE"
        query += " ORDER BY sequence_number NULLS LAST, name"
        rows = await db.fetch(query, process_id)
        return [dict(row) for row in rows]
