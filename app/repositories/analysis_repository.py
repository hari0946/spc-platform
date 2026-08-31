"""Data access for `analysis_runs`, `analysis_results`, and their
associated `rule_violations` rows.

Historical analysis and the "current dataset" half of a manual check both
go through this repository -- see analysis_type on analysis_runs.
"""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_RUN_COLUMNS = (
    "analysis_id, analysis_type, upload_id, spc_configuration_id, organization_id, plant_id, "
    "production_line_id, machine_id, product_id, process_id, operation_id, parameter_id, "
    "chart_type, status, error_message, started_at, completed_at, created_at"
)

_RESULT_COLUMNS = (
    "analysis_result_id, analysis_id, total_observations, valid_observations, invalid_observations, "
    "subgroup_count, subgroup_size_used, mean, minimum, maximum, within_sigma, overall_sigma, "
    "center_line, ucl, lcl, secondary_center_line, secondary_ucl, secondary_lcl, specification_id, "
    "lsl, usl, target, cp, cpk, cpu, cpl, pp, ppk, ppu, ppl, stability_status, chart_points, warnings, created_at"
)


class AnalysisRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create_run(
        self,
        analysis_type: str,
        upload_id: str,
        parameter_id: str,
        chart_type: str,
        spc_configuration_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        plant_id: Optional[str] = None,
        production_line_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        process_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO analysis_runs
                    (analysis_type, upload_id, spc_configuration_id, organization_id, plant_id,
                     production_line_id, machine_id, product_id, process_id, operation_id,
                     parameter_id, chart_type, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'STARTED')
                RETURNING {_RUN_COLUMNS}
                """,
                analysis_type, upload_id, spc_configuration_id, organization_id, plant_id,
                production_line_id, machine_id, product_id, process_id, operation_id,
                parameter_id, chart_type,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create analysis run.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def mark_completed(
        self, analysis_id: str, resolved_chart_type: Optional[str] = None, connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        """resolved_chart_type corrects the placeholder chart_type written
        at create_run() time (which is a best guess when the SPC
        configuration's chart_type is "AUTO") to whatever the engine
        actually selected, so downstream consumers (e.g. baseline creation)
        never inherit a stale guess."""
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            UPDATE analysis_runs
            SET status = 'COMPLETED', completed_at = now(), chart_type = COALESCE($2, chart_type)
            WHERE analysis_id = $1 RETURNING {_RUN_COLUMNS}
            """,
            analysis_id, resolved_chart_type,
        )
        if row is None:
            raise DatabaseConnectionError(f"Analysis run {analysis_id} not found.")
        return dict(row)

    async def mark_failed(
        self, analysis_id: str, error_message: str, connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            UPDATE analysis_runs SET status = 'FAILED', error_message = $2, completed_at = now()
            WHERE analysis_id = $1 RETURNING {_RUN_COLUMNS}
            """,
            analysis_id, error_message,
        )
        if row is None:
            raise DatabaseConnectionError(f"Analysis run {analysis_id} not found.")
        return dict(row)

    async def get_by_id(self, analysis_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_RUN_COLUMNS} FROM analysis_runs WHERE analysis_id = $1", analysis_id)
        return dict(row) if row else None

    async def list_recent(
        self,
        analysis_type: Optional[str] = None,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        parameter_id: Optional[str] = None,
        limit: int = 50,
        connection: Optional[asyncpg.Connection] = None,
    ) -> list[dict[str, Any]]:
        """Summary listing for the Dashboard / Analysis History pages --
        joins in capability + stability from the latest analysis_results
        row for each run, so the frontend never needs a second round trip
        per row just to show Cpk/status in a table."""
        db = self._db(connection)
        conditions = []
        params: list[Any] = []
        if analysis_type:
            params.append(analysis_type)
            conditions.append(f"ar.analysis_type = ${len(params)}")
        if machine_id:
            params.append(machine_id)
            conditions.append(f"ar.machine_id = ${len(params)}")
        if product_id:
            params.append(product_id)
            conditions.append(f"ar.product_id = ${len(params)}")
        if parameter_id:
            params.append(parameter_id)
            conditions.append(f"ar.parameter_id = ${len(params)}")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        rows = await db.fetch(
            f"""
            SELECT
                ar.analysis_id, ar.analysis_type, ar.upload_id, ar.organization_id, ar.plant_id,
                ar.machine_id, ar.product_id, ar.operation_id, ar.parameter_id, ar.chart_type,
                ar.status, ar.created_at, res.cpk, res.ppk, res.stability_status
            FROM analysis_runs ar
            LEFT JOIN LATERAL (
                SELECT cpk, ppk, stability_status
                FROM analysis_results
                WHERE analysis_results.analysis_id = ar.analysis_id
                ORDER BY created_at DESC
                LIMIT 1
            ) res ON TRUE
            {where}
            ORDER BY ar.created_at DESC
            LIMIT ${len(params)}
            """,
            *params,
        )
        return [dict(row) for row in rows]

    async def save_result(
        self, analysis_id: str, result: dict[str, Any], connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            INSERT INTO analysis_results
                (analysis_id, total_observations, valid_observations, invalid_observations,
                 subgroup_count, subgroup_size_used, mean, minimum, maximum, within_sigma,
                 overall_sigma, center_line, ucl, lcl, secondary_center_line, secondary_ucl,
                 secondary_lcl, specification_id, lsl, usl, target, cp, cpk, cpu, cpl, pp, ppk,
                 ppu, ppl, stability_status, chart_points, warnings)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17,
                    $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32)
            RETURNING {_RESULT_COLUMNS}
            """,
            analysis_id,
            result["total_observations"], result["valid_observations"], result["invalid_observations"],
            result["subgroup_count"], result["subgroup_size_used"], result["mean"], result["minimum"],
            result["maximum"], result["within_sigma"], result["overall_sigma"], result["center_line"],
            result["ucl"], result["lcl"], result.get("secondary_center_line"), result.get("secondary_ucl"),
            result.get("secondary_lcl"), result.get("specification_id"), result.get("lsl"), result.get("usl"),
            result.get("target"), result.get("cp"), result.get("cpk"), result.get("cpu"), result.get("cpl"),
            result.get("pp"), result.get("ppk"), result.get("ppu"), result.get("ppl"),
            result["stability_status"], result.get("chart_points", []),
            result.get("warnings", []),
        )
        return dict(row)

    async def get_result_by_analysis_id(
        self, analysis_id: str, connection: Optional[asyncpg.Connection] = None
    ) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_RESULT_COLUMNS} FROM analysis_results WHERE analysis_id = $1", analysis_id)
        return dict(row) if row else None

    async def save_rule_violations(
        self, analysis_id: str, violations: list[dict[str, Any]], connection: Optional[asyncpg.Connection] = None
    ) -> None:
        if not violations:
            return
        db = self._db(connection)
        await db.executemany(
            """
            INSERT INTO rule_violations
                (analysis_id, rule_name, chart_type, severity, start_index, end_index,
                 affected_points, message, detected_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            [
                (
                    analysis_id, v["rule_name"], v["chart_type"], v["severity"], v["start_index"],
                    v["end_index"], v["affected_points"], v["message"], v["detected_at"],
                )
                for v in violations
            ],
        )

    async def list_rule_violations(
        self, analysis_id: str, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        rows = await db.fetch(
            """
            SELECT violation_id, rule_name, chart_type, severity, start_index, end_index,
                   affected_points, message, detected_at
            FROM rule_violations
            WHERE analysis_id = $1
            ORDER BY start_index
            """,
            analysis_id,
        )
        return [dict(row) for row in rows]
