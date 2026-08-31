"""Data access for the `specifications` table.

The most important method here is `get_effective_specification`, which
resolves the correct LSL/USL/target for a given manufacturing context and
point in time -- specification limits are never hardcoded in application
code, always looked up here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = (
    "specification_id, parameter_id, machine_id, product_id, operation_id, lsl, usl, target, "
    "effective_from, effective_to, status, created_at, created_by"
)


class SpecificationRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self,
        parameter_id: str,
        lsl: Optional[float],
        usl: Optional[float],
        target: Optional[float] = None,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        effective_from: Optional[datetime] = None,
        created_by: Optional[str] = None,
        status: str = "ACTIVE",
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO specifications
                    (parameter_id, machine_id, product_id, operation_id, lsl, usl, target,
                     effective_from, status, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, COALESCE($8, now()), $9, $10)
                RETURNING {_COLUMNS}
                """,
                parameter_id, machine_id, product_id, operation_id, lsl, usl, target,
                effective_from, status, created_by,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create specification.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def get_by_id(self, specification_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM specifications WHERE specification_id = $1", specification_id)
        return dict(row) if row else None

    async def get_effective_specification(
        self,
        parameter_id: str,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        as_of: Optional[datetime] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> Optional[dict[str, Any]]:
        """Resolve the single most specific ACTIVE specification applicable
        to this context and point in time. A specification scoped to
        machine/product/operation is preferred over a less specific one
        that only requires the parameter to match."""
        db = self._db(connection)
        as_of = as_of or datetime.now(timezone.utc)
        row = await db.fetchrow(
            f"""
            SELECT {_COLUMNS}
            FROM specifications
            WHERE parameter_id = $1
              AND status = 'ACTIVE'
              AND (machine_id IS NULL OR machine_id = $2)
              AND (product_id IS NULL OR product_id = $3)
              AND (operation_id IS NULL OR operation_id = $4)
              AND effective_from <= $5
              AND (effective_to IS NULL OR effective_to > $5)
            ORDER BY
                (machine_id IS NOT NULL)::int
                + (product_id IS NOT NULL)::int
                + (operation_id IS NOT NULL)::int DESC,
                effective_from DESC
            LIMIT 1
            """,
            parameter_id, machine_id, product_id, operation_id, as_of,
        )
        return dict(row) if row else None

    async def list_by_parameter(
        self, parameter_id: str, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        rows = await db.fetch(
            f"SELECT {_COLUMNS} FROM specifications WHERE parameter_id = $1 ORDER BY effective_from DESC", parameter_id
        )
        return [dict(row) for row in rows]
