"""Data access for `findings`."""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = "finding_id, analysis_id, manual_check_id, finding_type, severity, message, statistical_fact, created_at"


class FindingsRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def save_findings(
        self,
        findings: list[dict[str, Any]],
        analysis_id: Optional[str] = None,
        manual_check_id: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> list[dict[str, Any]]:
        if not findings:
            return []
        db = self._db(connection)
        saved: list[dict[str, Any]] = []
        for finding in findings:
            row = await db.fetchrow(
                f"""
                INSERT INTO findings (analysis_id, manual_check_id, finding_type, severity, message, statistical_fact)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING {_COLUMNS}
                """,
                analysis_id, manual_check_id, finding["finding_type"], finding["severity"],
                finding["message"], finding.get("statistical_fact", {}),
            )
            saved.append(dict(row))
        return saved

    async def list_by_manual_check(
        self, manual_check_id: str, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        rows = await db.fetch(
            f"SELECT {_COLUMNS} FROM findings WHERE manual_check_id = $1 ORDER BY created_at", manual_check_id
        )
        return [dict(row) for row in rows]

    async def list_recent(
        self,
        severity: Optional[str] = None,
        finding_type: Optional[str] = None,
        limit: int = 100,
        connection: Optional[asyncpg.Connection] = None,
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        conditions = []
        params: list[Any] = []
        if severity:
            params.append(severity)
            conditions.append(f"severity = ${len(params)}")
        if finding_type:
            params.append(finding_type)
            conditions.append(f"finding_type = ${len(params)}")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)
        rows = await db.fetch(
            f"SELECT {_COLUMNS} FROM findings {where} ORDER BY created_at DESC LIMIT ${len(params)}", *params
        )
        return [dict(row) for row in rows]
