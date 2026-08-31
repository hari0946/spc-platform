"""Data access for `rule_configurations`."""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = "rule_configuration_id, spc_configuration_id, rule_name, enabled, severity, parameters, created_at, updated_at"


class RuleConfigurationRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self,
        spc_configuration_id: str,
        rule_name: str,
        enabled: bool = True,
        severity: str = "WARNING",
        parameters: Optional[dict[str, Any]] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO rule_configurations (spc_configuration_id, rule_name, enabled, severity, parameters)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING {_COLUMNS}
                """,
                spc_configuration_id, rule_name, enabled, severity, parameters or {},
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create rule configuration.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def list_by_spc_configuration(
        self, spc_configuration_id: str, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        rows = await db.fetch(
            f"SELECT {_COLUMNS} FROM rule_configurations WHERE spc_configuration_id = $1 ORDER BY created_at",
            spc_configuration_id,
        )
        return [dict(row) for row in rows]
