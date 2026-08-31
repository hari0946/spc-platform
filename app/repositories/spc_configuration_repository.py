"""Data access for `spc_configurations`."""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = (
    "spc_configuration_id, parameter_id, machine_id, product_id, operation_id, chart_type, "
    "subgroup_size, subgroup_method, maximum_time_gap_seconds, minimum_sample_size, ruleset, "
    "sigma_method, capability_method, is_active, created_at, updated_at"
)


class SPCConfigurationRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self,
        parameter_id: str,
        chart_type: str,
        subgroup_size: int,
        subgroup_method: str,
        maximum_time_gap_seconds: int,
        minimum_sample_size: int,
        ruleset: list[dict[str, Any]],
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        sigma_method: str = "WITHIN_OVERALL",
        capability_method: str = "STANDARD",
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO spc_configurations
                    (parameter_id, machine_id, product_id, operation_id, chart_type, subgroup_size,
                     subgroup_method, maximum_time_gap_seconds, minimum_sample_size, ruleset,
                     sigma_method, capability_method)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING {_COLUMNS}
                """,
                parameter_id, machine_id, product_id, operation_id, chart_type, subgroup_size,
                subgroup_method, maximum_time_gap_seconds, minimum_sample_size, ruleset,
                sigma_method, capability_method,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create SPC configuration.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def get_by_id(self, spc_configuration_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM spc_configurations WHERE spc_configuration_id = $1", spc_configuration_id)
        return dict(row) if row else None

    async def get_effective_configuration(
        self,
        parameter_id: str,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> Optional[dict[str, Any]]:
        """Most specific active configuration for this context, mirroring
        the specification resolution strategy (see specification_repository)."""
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            SELECT {_COLUMNS}
            FROM spc_configurations
            WHERE parameter_id = $1
              AND is_active = TRUE
              AND (machine_id IS NULL OR machine_id = $2)
              AND (product_id IS NULL OR product_id = $3)
              AND (operation_id IS NULL OR operation_id = $4)
            ORDER BY
                (machine_id IS NOT NULL)::int
                + (product_id IS NOT NULL)::int
                + (operation_id IS NOT NULL)::int DESC,
                created_at DESC
            LIMIT 1
            """,
            parameter_id, machine_id, product_id, operation_id,
        )
        return dict(row) if row else None

    async def update(
        self, spc_configuration_id: str, updates: dict[str, Any], connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        if not updates:
            existing = await self.get_by_id(spc_configuration_id, connection)
            if existing is None:
                raise DatabaseConnectionError(f"SPC configuration {spc_configuration_id} not found.")
            return existing

        db = self._db(connection)
        allowed = {
            "chart_type", "subgroup_size", "subgroup_method", "maximum_time_gap_seconds",
            "minimum_sample_size", "ruleset", "sigma_method", "capability_method", "is_active",
        }
        set_clauses = []
        values: list[Any] = []
        for i, (key, value) in enumerate(updates.items(), start=2):
            if key not in allowed:
                continue
            set_clauses.append(f"{key} = ${i}")
            values.append(value)
        if not set_clauses:
            existing = await self.get_by_id(spc_configuration_id, connection)
            if existing is None:
                raise DatabaseConnectionError(f"SPC configuration {spc_configuration_id} not found.")
            return existing

        set_clauses.append("updated_at = now()")
        query = (
            f"UPDATE spc_configurations SET {', '.join(set_clauses)} "
            f"WHERE spc_configuration_id = $1 RETURNING {_COLUMNS}"
        )
        row = await db.fetchrow(query, spc_configuration_id, *values)
        if row is None:
            raise DatabaseConnectionError(f"SPC configuration {spc_configuration_id} not found.")
        return dict(row)

    async def list_all(self, connection: Optional[asyncpg.Connection] = None) -> list[dict[str, Any]]:
        db = self._db(connection)
        rows = await db.fetch(f"SELECT {_COLUMNS} FROM spc_configurations ORDER BY created_at DESC")
        return [dict(row) for row in rows]
