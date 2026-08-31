"""Data access for `baselines`.

Baseline approval (DRAFT -> ACTIVE, with the previous ACTIVE baseline for
the same context moving to SUPERSEDED) is a multi-statement operation that
must be atomic -- callers should run `approve` inside a
database.postgres.transaction() block alongside anything else in that
business transaction (see services/baseline_service.py).
"""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = (
    "baseline_id, analysis_id, organization_id, plant_id, production_line_id, machine_id, "
    "product_id, process_id, operation_id, parameter_id, chart_type, unit, baseline_start, "
    "baseline_end, sample_count, mean, within_sigma, overall_sigma, center_line, ucl, lcl, "
    "secondary_center_line, secondary_ucl, secondary_lcl, specification_id, lsl, usl, target, "
    "cp, cpk, pp, ppk, status, created_at, created_by, approved_at, approved_by, "
    "superseded_at, superseded_by_baseline_id"
)


class BaselineRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create_draft(self, values: dict[str, Any], connection: Optional[asyncpg.Connection] = None) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO baselines
                    (analysis_id, organization_id, plant_id, production_line_id, machine_id, product_id,
                     process_id, operation_id, parameter_id, chart_type, unit, baseline_start, baseline_end,
                     sample_count, mean, within_sigma, overall_sigma, center_line, ucl, lcl,
                     secondary_center_line, secondary_ucl, secondary_lcl, specification_id, lsl, usl, target,
                     cp, cpk, pp, ppk, status, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19,
                        $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, 'DRAFT', $32)
                RETURNING {_COLUMNS}
                """,
                values["analysis_id"], values.get("organization_id"), values.get("plant_id"),
                values.get("production_line_id"), values.get("machine_id"), values.get("product_id"),
                values.get("process_id"), values.get("operation_id"), values["parameter_id"],
                values["chart_type"], values["unit"], values.get("baseline_start"), values.get("baseline_end"),
                values["sample_count"], values["mean"], values["within_sigma"], values["overall_sigma"],
                values["center_line"], values["ucl"], values["lcl"], values.get("secondary_center_line"),
                values.get("secondary_ucl"), values.get("secondary_lcl"), values.get("specification_id"),
                values.get("lsl"), values.get("usl"), values.get("target"), values.get("cp"), values.get("cpk"),
                values.get("pp"), values.get("ppk"), values.get("created_by"),
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create draft baseline.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def get_by_id(self, baseline_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM baselines WHERE baseline_id = $1", baseline_id)
        return dict(row) if row else None

    async def get_active_baseline(
        self,
        parameter_id: str,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            SELECT {_COLUMNS}
            FROM baselines
            WHERE parameter_id = $1
              AND machine_id IS NOT DISTINCT FROM $2
              AND product_id IS NOT DISTINCT FROM $3
              AND operation_id IS NOT DISTINCT FROM $4
              AND status = 'ACTIVE'
            """,
            parameter_id, machine_id, product_id, operation_id,
        )
        return dict(row) if row else None

    async def supersede(
        self, baseline_id: str, superseded_by_baseline_id: str, connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            UPDATE baselines
            SET status = 'SUPERSEDED', superseded_at = now(), superseded_by_baseline_id = $2
            WHERE baseline_id = $1
            RETURNING {_COLUMNS}
            """,
            baseline_id, superseded_by_baseline_id,
        )
        if row is None:
            raise DatabaseConnectionError(f"Baseline {baseline_id} not found when superseding.")
        return dict(row)

    async def activate(
        self, baseline_id: str, approved_by: Optional[str], connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            UPDATE baselines
            SET status = 'ACTIVE', approved_at = now(), approved_by = $2
            WHERE baseline_id = $1
            RETURNING {_COLUMNS}
            """,
            baseline_id, approved_by,
        )
        if row is None:
            raise DatabaseConnectionError(f"Baseline {baseline_id} not found when activating.")
        return dict(row)

    async def archive(self, baseline_id: str, connection: Optional[asyncpg.Connection] = None) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"UPDATE baselines SET status = 'ARCHIVED' WHERE baseline_id = $1 RETURNING {_COLUMNS}",
            baseline_id,
        )
        if row is None:
            raise DatabaseConnectionError(f"Baseline {baseline_id} not found when archiving.")
        return dict(row)

    async def list_all(
        self,
        parameter_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        connection: Optional[asyncpg.Connection] = None,
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        conditions = []
        params: list[Any] = []
        if parameter_id:
            params.append(parameter_id)
            conditions.append(f"parameter_id = ${len(params)}")
        if machine_id:
            params.append(machine_id)
            conditions.append(f"machine_id = ${len(params)}")
        if product_id:
            params.append(product_id)
            conditions.append(f"product_id = ${len(params)}")
        if operation_id:
            params.append(operation_id)
            conditions.append(f"operation_id = ${len(params)}")
        if status:
            params.append(status)
            conditions.append(f"status = ${len(params)}")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)
        rows = await db.fetch(
            f"SELECT {_COLUMNS} FROM baselines {where} ORDER BY created_at DESC LIMIT ${len(params)}", *params
        )
        return [dict(row) for row in rows]
