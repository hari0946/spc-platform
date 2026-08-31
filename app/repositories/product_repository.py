"""Data access for the `products` table."""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = "product_id, organization_id, part_number, name, description, revision, active, created_at, updated_at"


class ProductRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self,
        organization_id: str,
        part_number: str,
        name: str,
        description: Optional[str] = None,
        revision: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO products (organization_id, part_number, name, description, revision)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING {_COLUMNS}
                """,
                organization_id, part_number, name, description, revision,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create product.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def get_by_id(self, product_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM products WHERE product_id = $1", product_id)
        return dict(row) if row else None

    async def get_by_part_number(
        self, organization_id: str, part_number: str, connection: Optional[asyncpg.Connection] = None
    ) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"SELECT {_COLUMNS} FROM products WHERE organization_id = $1 AND part_number = $2",
            organization_id, part_number,
        )
        return dict(row) if row else None

    async def list_by_organization(
        self, organization_id: str, active_only: bool = True, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        query = f"SELECT {_COLUMNS} FROM products WHERE organization_id = $1"
        if active_only:
            query += " AND active = TRUE"
        query += " ORDER BY name"
        rows = await db.fetch(query, organization_id)
        return [dict(row) for row in rows]
