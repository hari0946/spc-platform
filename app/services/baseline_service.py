"""Historical baseline lifecycle: DRAFT -> ACTIVE (superseding any prior
ACTIVE baseline for the same context) -> SUPERSEDED/ARCHIVED.

A baseline's numeric limits are frozen at creation time from a completed
historical analysis_results row -- baseline_service never recalculates
them. Only an explicit new historical analysis + a new approval can change
what "the baseline" means for a context (see docs on Phase 2 in
manual_data_check_service.py for why this matters).
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.database.postgres.transaction import transaction
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.baseline_repository import BaselineRepository

logger = get_logger(__name__)


class BaselineService:
    def __init__(self, baseline_repository: BaselineRepository, analysis_repository: AnalysisRepository) -> None:
        self._baseline_repository = baseline_repository
        self._analysis_repository = analysis_repository

    async def create_draft_from_analysis(self, analysis_id: str, created_by: Optional[str] = None) -> dict[str, Any]:
        run = await self._analysis_repository.get_by_id(analysis_id)
        if run is None:
            raise NotFoundError(f"Analysis {analysis_id} not found.")
        if run["status"] != "COMPLETED":
            raise ValidationError(f"Analysis {analysis_id} has not completed successfully (status={run['status']}).")

        result = await self._analysis_repository.get_result_by_analysis_id(analysis_id)
        if result is None:
            raise NotFoundError(f"Analysis result for {analysis_id} not found.")
        if result["within_sigma"] is None or result["overall_sigma"] is None:
            raise ValidationError(
                f"Analysis {analysis_id} does not have valid sigma estimates and cannot be used as a baseline."
            )

        values = {
            "analysis_id": analysis_id,
            "organization_id": run["organization_id"],
            "plant_id": run["plant_id"],
            "production_line_id": run["production_line_id"],
            "machine_id": run["machine_id"],
            "product_id": run["product_id"],
            "process_id": run["process_id"],
            "operation_id": run["operation_id"],
            "parameter_id": run["parameter_id"],
            "chart_type": run["chart_type"],
            "unit": "",  # resolved from parameter metadata by the API layer if needed; kept simple for this phase
            "baseline_start": None,
            "baseline_end": None,
            "sample_count": result["valid_observations"],
            "mean": result["mean"],
            "within_sigma": result["within_sigma"],
            "overall_sigma": result["overall_sigma"],
            "center_line": result["center_line"],
            "ucl": result["ucl"],
            "lcl": result["lcl"],
            "secondary_center_line": result["secondary_center_line"],
            "secondary_ucl": result["secondary_ucl"],
            "secondary_lcl": result["secondary_lcl"],
            "specification_id": result["specification_id"],
            "lsl": result["lsl"],
            "usl": result["usl"],
            "target": result["target"],
            "cp": result["cp"],
            "cpk": result["cpk"],
            "pp": result["pp"],
            "ppk": result["ppk"],
            "created_by": created_by,
        }
        baseline = await self._baseline_repository.create_draft(values)
        logger.info("baseline_draft_created", baseline_id=baseline["baseline_id"], analysis_id=analysis_id)
        return baseline

    async def approve(self, baseline_id: str, approved_by: Optional[str] = None) -> dict[str, Any]:
        draft = await self._baseline_repository.get_by_id(baseline_id)
        if draft is None:
            raise NotFoundError(f"Baseline {baseline_id} not found.")
        if draft["status"] != "DRAFT":
            raise ConflictError(f"Baseline {baseline_id} is not in DRAFT status (status={draft['status']}).")

        async with transaction() as connection:
            existing_active = await self._baseline_repository.get_active_baseline(
                draft["parameter_id"], draft["machine_id"], draft["product_id"], draft["operation_id"], connection=connection
            )
            if existing_active is not None:
                await self._baseline_repository.supersede(
                    existing_active["baseline_id"], baseline_id, connection=connection
                )
            activated = await self._baseline_repository.activate(baseline_id, approved_by, connection=connection)

        logger.info(
            "baseline_approved",
            baseline_id=baseline_id,
            superseded_baseline_id=existing_active["baseline_id"] if existing_active else None,
        )
        return activated

    async def get_active_baseline(
        self, parameter_id: str, machine_id: Optional[str], product_id: Optional[str], operation_id: Optional[str]
    ) -> Optional[dict[str, Any]]:
        return await self._baseline_repository.get_active_baseline(parameter_id, machine_id, product_id, operation_id)

    async def get_by_id(self, baseline_id: str) -> dict[str, Any]:
        baseline = await self._baseline_repository.get_by_id(baseline_id)
        if baseline is None:
            raise NotFoundError(f"Baseline {baseline_id} not found.")
        return baseline

    async def list_baselines(
        self,
        parameter_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        return await self._baseline_repository.list_all(
            parameter_id=parameter_id, machine_id=machine_id, product_id=product_id,
            operation_id=operation_id, status=status,
        )
