"""Data access for `manual_check_runs` and `comparison_results` (Phase 2:
manual, user-triggered comparison of a new upload against the active
historical baseline)."""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_RUN_COLUMNS = (
    "manual_check_id, upload_id, current_analysis_id, baseline_id, organization_id, plant_id, "
    "production_line_id, machine_id, product_id, process_id, operation_id, parameter_id, status, "
    "final_status, error_message, started_at, completed_at, created_at, triggered_by"
)

_COMPARISON_COLUMNS = (
    "comparison_result_id, manual_check_id, baseline_mean, current_mean, mean_shift, mean_shift_percentage, "
    "baseline_within_sigma, current_within_sigma, within_variation_change, within_variation_change_percentage, "
    "baseline_overall_sigma, current_overall_sigma, overall_variation_change, overall_variation_change_percentage, "
    "baseline_cpk, current_cpk, cpk_change, baseline_ppk, current_ppk, ppk_change, mean_shift_detected, "
    "variation_increase_detected, variation_reduction_detected, capability_improvement_detected, "
    "capability_degradation_detected, new_limit_violations_detected, created_at"
)


class ManualCheckRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create_run(
        self,
        upload_id: str,
        baseline_id: str,
        parameter_id: str,
        organization_id: Optional[str] = None,
        plant_id: Optional[str] = None,
        production_line_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        process_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        triggered_by: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO manual_check_runs
                    (upload_id, baseline_id, organization_id, plant_id, production_line_id, machine_id,
                     product_id, process_id, operation_id, parameter_id, status, triggered_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'MANUAL_CHECK_STARTED', $11)
                RETURNING {_RUN_COLUMNS}
                """,
                upload_id, baseline_id, organization_id, plant_id, production_line_id, machine_id,
                product_id, process_id, operation_id, parameter_id, triggered_by,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create manual check run.", details={"reason": str(exc)}) from exc
        return dict(row)

    async def link_current_analysis(
        self, manual_check_id: str, current_analysis_id: str, connection: Optional[asyncpg.Connection] = None
    ) -> None:
        db = self._db(connection)
        await db.execute(
            "UPDATE manual_check_runs SET current_analysis_id = $2 WHERE manual_check_id = $1",
            manual_check_id, current_analysis_id,
        )

    async def mark_completed(
        self, manual_check_id: str, final_status: str, connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            UPDATE manual_check_runs
            SET status = 'MANUAL_CHECK_COMPLETED', final_status = $2, completed_at = now()
            WHERE manual_check_id = $1
            RETURNING {_RUN_COLUMNS}
            """,
            manual_check_id, final_status,
        )
        if row is None:
            raise DatabaseConnectionError(f"Manual check run {manual_check_id} not found.")
        return dict(row)

    async def mark_failed(
        self, manual_check_id: str, error_message: str, connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            UPDATE manual_check_runs
            SET status = 'MANUAL_CHECK_FAILED', error_message = $2, completed_at = now()
            WHERE manual_check_id = $1
            RETURNING {_RUN_COLUMNS}
            """,
            manual_check_id, error_message,
        )
        if row is None:
            raise DatabaseConnectionError(f"Manual check run {manual_check_id} not found.")
        return dict(row)

    async def get_by_id(self, manual_check_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_RUN_COLUMNS} FROM manual_check_runs WHERE manual_check_id = $1", manual_check_id)
        return dict(row) if row else None

    async def save_comparison_result(
        self, manual_check_id: str, comparison: dict[str, Any], connection: Optional[asyncpg.Connection] = None
    ) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            INSERT INTO comparison_results
                (manual_check_id, baseline_mean, current_mean, mean_shift, mean_shift_percentage,
                 baseline_within_sigma, current_within_sigma, within_variation_change,
                 within_variation_change_percentage, baseline_overall_sigma, current_overall_sigma,
                 overall_variation_change, overall_variation_change_percentage, baseline_cpk, current_cpk,
                 cpk_change, baseline_ppk, current_ppk, ppk_change, mean_shift_detected,
                 variation_increase_detected, variation_reduction_detected, capability_improvement_detected,
                 capability_degradation_detected, new_limit_violations_detected)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19,
                    $20, $21, $22, $23, $24, $25)
            RETURNING {_COMPARISON_COLUMNS}
            """,
            manual_check_id,
            comparison["baseline_mean"], comparison["current_mean"], comparison["mean_shift"],
            comparison.get("mean_shift_percentage"), comparison["baseline_within_sigma"],
            comparison["current_within_sigma"], comparison["within_variation_change"],
            comparison.get("within_variation_change_percentage"), comparison["baseline_overall_sigma"],
            comparison["current_overall_sigma"], comparison["overall_variation_change"],
            comparison.get("overall_variation_change_percentage"), comparison.get("baseline_cpk"),
            comparison.get("current_cpk"), comparison.get("cpk_change"), comparison.get("baseline_ppk"),
            comparison.get("current_ppk"), comparison.get("ppk_change"), comparison["mean_shift_detected"],
            comparison["variation_increase_detected"], comparison["variation_reduction_detected"],
            comparison["capability_improvement_detected"], comparison["capability_degradation_detected"],
            comparison["new_limit_violations_detected"],
        )
        return dict(row)

    async def get_comparison_result(
        self, manual_check_id: str, connection: Optional[asyncpg.Connection] = None
    ) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"SELECT {_COMPARISON_COLUMNS} FROM comparison_results WHERE manual_check_id = $1", manual_check_id
        )
        return dict(row) if row else None

    async def save_rule_violations(
        self, manual_check_id: str, violations: list[dict[str, Any]], connection: Optional[asyncpg.Connection] = None
    ) -> None:
        if not violations:
            return
        db = self._db(connection)
        await db.executemany(
            """
            INSERT INTO rule_violations
                (manual_check_id, rule_name, chart_type, severity, start_index, end_index,
                 affected_points, message, detected_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            [
                (
                    manual_check_id, v["rule_name"], v["chart_type"], v["severity"], v["start_index"],
                    v["end_index"], v["affected_points"], v["message"], v["detected_at"],
                )
                for v in violations
            ],
        )

    async def list_rule_violations(
        self, manual_check_id: str, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        rows = await db.fetch(
            """
            SELECT violation_id, rule_name, chart_type, severity, start_index, end_index,
                   affected_points, message, detected_at
            FROM rule_violations
            WHERE manual_check_id = $1
            ORDER BY start_index
            """,
            manual_check_id,
        )
        return [dict(row) for row in rows]

    async def list_recent(
        self,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        parameter_id: Optional[str] = None,
        limit: int = 50,
        connection: Optional[asyncpg.Connection] = None,
    ) -> list[dict[str, Any]]:
        """Summary listing for the Dashboard / Analysis History pages --
        joins in current Cpk/Ppk from comparison_results so the frontend
        doesn't need a second round trip per row."""
        db = self._db(connection)
        conditions = []
        params: list[Any] = []
        if machine_id:
            params.append(machine_id)
            conditions.append(f"mc.machine_id = ${len(params)}")
        if product_id:
            params.append(product_id)
            conditions.append(f"mc.product_id = ${len(params)}")
        if parameter_id:
            params.append(parameter_id)
            conditions.append(f"mc.parameter_id = ${len(params)}")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        rows = await db.fetch(
            f"""
            SELECT
                mc.manual_check_id, mc.upload_id, mc.baseline_id, mc.organization_id, mc.plant_id,
                mc.machine_id, mc.product_id, mc.operation_id, mc.parameter_id, mc.status,
                mc.final_status, mc.created_at, cr.current_cpk, cr.current_ppk
            FROM manual_check_runs mc
            LEFT JOIN comparison_results cr ON cr.manual_check_id = mc.manual_check_id
            {where}
            ORDER BY mc.created_at DESC
            LIMIT ${len(params)}
            """,
            *params,
        )
        return [dict(row) for row in rows]
