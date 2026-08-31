"""Data access for `alerts`."""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = (
    "alert_id, manual_check_id, finding_id, machine_id, parameter_id, severity, status, message, "
    "created_at, acknowledged_at, acknowledged_by, resolved_at, resolved_by"
)


class AlertRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self,
        severity: str,
        message: str,
        manual_check_id: Optional[str] = None,
        finding_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        parameter_id: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO alerts (manual_check_id, finding_id, machine_id, parameter_id, severity, message)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING {_COLUMNS}
                """,
                manual_check_id, finding_id, machine_id, parameter_id, severity, message,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create alert.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def get_by_id(self, alert_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM alerts WHERE alert_id = $1", alert_id)
        return dict(row) if row else None

    async def list_all(
        self, status: Optional[str] = None, limit: int = 100, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        if status:
            rows = await db.fetch(
                f"SELECT {_COLUMNS} FROM alerts WHERE status = $1 ORDER BY created_at DESC LIMIT $2", status, limit
            )
        else:
            rows = await db.fetch(f"SELECT {_COLUMNS} FROM alerts ORDER BY created_at DESC LIMIT $1", limit)
        return [dict(row) for row in rows]

    async def acknowledge(
        self, alert_id: str, acknowledged_by: Optional[str], connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            UPDATE alerts SET status = 'ACKNOWLEDGED', acknowledged_at = now(), acknowledged_by = $2
            WHERE alert_id = $1
            RETURNING {_COLUMNS}
            """,
            alert_id, acknowledged_by,
        )
        if row is None:
            raise DatabaseConnectionError(f"Alert {alert_id} not found.")
        return dict(row)

    async def resolve(
        self, alert_id: str, resolved_by: Optional[str], connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            UPDATE alerts SET status = 'RESOLVED', resolved_at = now(), resolved_by = $2
            WHERE alert_id = $1
            RETURNING {_COLUMNS}
            """,
            alert_id, resolved_by,
        )
        if row is None:
            raise DatabaseConnectionError(f"Alert {alert_id} not found.")
        return dict(row)
