"""Phase 2: Manual Periodic New Data Analysis and Comparison Against
Historical Baseline.

This is explicitly a MANUAL, user-triggered, batch comparison -- not
continuous/real-time monitoring. Every run here is initiated by a human
uploading a new CSV and calling POST /manual-check/run.

CRITICAL RULE enforced throughout this service: the ACTIVE baseline's
control limits (ucl/cl/lcl, sigma, capability) are NEVER recalculated here.
They are read as-is from PostgreSQL and applied, frozen, against the new
dataset. Re-baselining only ever happens through the explicit
baseline_service.approve() workflow.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.exceptions import (
    BaselineContextMismatchError,
    InsufficientDataError as AppInsufficientDataError,
    MissingActiveBaselineError,
    MissingSPCConfigurationError,
    NotFoundError,
    UploadNotReadyError,
    ValidationError,
)
from app.core.logging import get_logger
from app.repositories.alert_repository import AlertRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.baseline_repository import BaselineRepository
from app.repositories.findings_repository import FindingsRepository
from app.repositories.manual_check_repository import ManualCheckRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.spc_configuration_repository import SPCConfigurationRepository
from app.repositories.specification_repository import SpecificationRepository
from app.repositories.upload_repository import UploadRepository
from app.services.historical_analysis_service import _result_to_db_dict, _row_to_spc_configuration, _row_to_specification
from app.spc_engine.comparison.baseline_comparison_engine import compare_to_baseline
from app.spc_engine.core import exceptions as engine_exceptions
from app.spc_engine.core.enums import ChartType, FinalProcessStatus, Severity
from app.spc_engine.core.models import BaselineSnapshot, ComparisonResult, Finding, RuleViolation, Specification
from app.spc_engine.findings.findings_engine import build_findings, determine_final_status
from app.spc_engine.results.result_builder import run_spc_analysis
from app.spc_engine.rules.rule_engine import RuleEngine

logger = get_logger(__name__)


def _row_to_baseline_snapshot(row: dict[str, Any]) -> BaselineSnapshot:
    spec = None
    if row.get("lsl") is not None or row.get("usl") is not None:
        spec = Specification(
            lsl=float(row["lsl"]) if row["lsl"] is not None else None,
            usl=float(row["usl"]) if row["usl"] is not None else None,
            target=float(row["target"]) if row["target"] is not None else None,
            specification_id=row.get("specification_id"),
        )
    return BaselineSnapshot(
        baseline_id=row["baseline_id"],
        chart_type=ChartType(row["chart_type"]),
        mean=float(row["mean"]),
        within_sigma=float(row["within_sigma"]),
        overall_sigma=float(row["overall_sigma"]),
        center_line=float(row["center_line"]),
        ucl=float(row["ucl"]),
        lcl=float(row["lcl"]),
        secondary_center_line=_float_or_none(row.get("secondary_center_line")),
        secondary_ucl=_float_or_none(row.get("secondary_ucl")),
        secondary_lcl=_float_or_none(row.get("secondary_lcl")),
        cp=_float_or_none(row.get("cp")),
        cpk=_float_or_none(row.get("cpk")),
        pp=_float_or_none(row.get("pp")),
        ppk=_float_or_none(row.get("ppk")),
        specification=spec,
        unit=row.get("unit") or "",
        machine_id=row.get("machine_id"),
        product_id=row.get("product_id"),
        operation_id=row.get("operation_id"),
        parameter_id=row["parameter_id"],
    )


def _float_or_none(value: Any) -> Optional[float]:
    return float(value) if value is not None else None


def _validate_baseline_compatibility(
    baseline: BaselineSnapshot,
    parameter_id: str,
    machine_id: Optional[str],
    product_id: Optional[str],
    operation_id: Optional[str],
    current_chart_type: ChartType,
) -> None:
    mismatches = []
    if baseline.parameter_id != parameter_id:
        mismatches.append(f"parameter ({baseline.parameter_id} != {parameter_id})")
    if baseline.machine_id != machine_id:
        mismatches.append(f"machine ({baseline.machine_id} != {machine_id})")
    if baseline.product_id != product_id:
        mismatches.append(f"product ({baseline.product_id} != {product_id})")
    if baseline.operation_id != operation_id:
        mismatches.append(f"operation ({baseline.operation_id} != {operation_id})")
    if baseline.chart_type != current_chart_type:
        mismatches.append(f"chart type ({baseline.chart_type.value} != {current_chart_type.value})")

    if mismatches:
        raise BaselineContextMismatchError(
            f"The active baseline is not compatible with the new dataset's context: {'; '.join(mismatches)}.",
            details={"mismatches": mismatches},
        )


class ManualDataCheckService:
    def __init__(
        self,
        upload_repository: UploadRepository,
        measurement_repository: MeasurementRepository,
        spc_configuration_repository: SPCConfigurationRepository,
        specification_repository: SpecificationRepository,
        analysis_repository: AnalysisRepository,
        baseline_repository: BaselineRepository,
        manual_check_repository: ManualCheckRepository,
        findings_repository: FindingsRepository,
        alert_repository: AlertRepository,
        parameter_repository: Optional[ParameterRepository] = None,
    ) -> None:
        self._upload_repository = upload_repository
        self._measurement_repository = measurement_repository
        self._spc_configuration_repository = spc_configuration_repository
        self._specification_repository = specification_repository
        self._analysis_repository = analysis_repository
        self._baseline_repository = baseline_repository
        self._manual_check_repository = manual_check_repository
        self._findings_repository = findings_repository
        self._alert_repository = alert_repository
        self._parameter_repository = parameter_repository or ParameterRepository()

    async def run_manual_check(
        self,
        upload_id: str,
        parameter_id: str,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        baseline_id: Optional[str] = None,
        triggered_by: Optional[str] = None,
    ) -> dict[str, Any]:
        upload = await self._upload_repository.get_by_id(upload_id)
        if upload is None:
            raise NotFoundError(f"Upload {upload_id} not found.")
        if upload["status"] != "SILVER_COMPLETED":
            raise UploadNotReadyError(
                f"Upload {upload_id} is not ready for a manual check (status={upload['status']})."
            )
        if upload["upload_type"] != "CURRENT":
            raise ValidationError(f"Upload {upload_id} is not a CURRENT upload.")

        if baseline_id:
            baseline_row = await self._baseline_repository.get_by_id(baseline_id)
            if baseline_row is None or baseline_row["status"] != "ACTIVE":
                raise MissingActiveBaselineError(f"Baseline {baseline_id} is not an ACTIVE baseline.")
        else:
            baseline_row = await self._baseline_repository.get_active_baseline(
                parameter_id, machine_id, product_id, operation_id
            )
            if baseline_row is None:
                raise MissingActiveBaselineError(
                    f"No ACTIVE baseline found for parameter {parameter_id} "
                    f"(machine={machine_id}, product={product_id}, operation={operation_id}). "
                    f"Run and approve a historical baseline before performing a manual check."
                )
        baseline = _row_to_baseline_snapshot(baseline_row)

        config_row = await self._spc_configuration_repository.get_effective_configuration(
            parameter_id, machine_id, product_id, operation_id
        )
        if config_row is None:
            raise MissingSPCConfigurationError(
                f"No active SPC configuration found for parameter {parameter_id}."
            )
        engine_config = _row_to_spc_configuration(config_row)

        spec_row = await self._specification_repository.get_effective_specification(
            parameter_id, machine_id, product_id, operation_id
        )
        specification = _row_to_specification(spec_row)

        df = await self._measurement_repository.get_by_context(
            parameter_id, machine_id, product_id, operation_id, valid_only=True
        )
        if df.empty:
            raise AppInsufficientDataError(f"No valid Silver measurements found for upload {upload_id}.")
        df = df.rename(columns={c: c.lower() for c in df.columns})

        manual_check_row = await self._manual_check_repository.create_run(
            upload_id=upload_id,
            baseline_id=baseline.baseline_id,
            parameter_id=parameter_id,
            organization_id=upload.get("organization_id"),
            plant_id=upload.get("plant_id"),
            production_line_id=upload.get("production_line_id"),
            machine_id=machine_id,
            product_id=product_id,
            operation_id=operation_id,
            triggered_by=triggered_by,
        )
        manual_check_id = manual_check_row["manual_check_id"]
        logger.info("manual_check_started", manual_check_id=manual_check_id, upload_id=upload_id, baseline_id=baseline.baseline_id)

        try:
            current_result = run_spc_analysis(df, engine_config, specification)
        except engine_exceptions.SPCEngineError as exc:
            await self._manual_check_repository.mark_failed(manual_check_id, str(exc))
            raise AppInsufficientDataError(str(exc)) from exc

        _validate_baseline_compatibility(
            baseline, parameter_id, machine_id, product_id, operation_id, current_result.chart.chart_type
        )

        current_analysis_row = await self._analysis_repository.create_run(
            analysis_type="MANUAL_CHECK_CURRENT",
            upload_id=upload_id,
            parameter_id=parameter_id,
            chart_type=current_result.chart.chart_type.value,
            spc_configuration_id=config_row["spc_configuration_id"],
            organization_id=upload.get("organization_id"),
            plant_id=upload.get("plant_id"),
            production_line_id=upload.get("production_line_id"),
            machine_id=machine_id,
            product_id=product_id,
            operation_id=operation_id,
        )
        current_analysis_id = current_analysis_row["analysis_id"]
        await self._analysis_repository.mark_completed(current_analysis_id)
        await self._analysis_repository.save_result(current_analysis_id, _result_to_db_dict(current_result))
        await self._manual_check_repository.link_current_analysis(manual_check_id, current_analysis_id)

        # Apply the FIXED historical baseline limits to the current
        # dataset's own chart points -- never the freshly-calculated
        # current limits. This is what actually answers "is the process
        # still behaving the way it did when the baseline was set?".
        rule_engine = RuleEngine(engine_config.ruleset)
        baseline_violations = rule_engine.evaluate(
            current_result.chart.primary_chart.points,
            baseline.center_line,
            baseline.ucl,
            baseline.lcl,
            baseline.chart_type,
        )
        await self._manual_check_repository.save_rule_violations(manual_check_id, _violations_to_db_dicts(baseline_violations))

        comparison = compare_to_baseline(baseline, current_result)
        new_limit_violations_detected = any(v.rule_name.value == "POINT_OUTSIDE_LIMITS" for v in baseline_violations)
        await self._manual_check_repository.save_comparison_result(
            manual_check_id, _comparison_to_db_dict(comparison, new_limit_violations_detected)
        )

        findings = build_findings(comparison, baseline_violations)
        saved_findings = await self._findings_repository.save_findings(
            _findings_to_db_dicts(findings), manual_check_id=manual_check_id
        )

        final_status = determine_final_status(comparison, baseline_violations)
        await self._manual_check_repository.mark_completed(manual_check_id, final_status.value)

        await self._raise_alerts_if_needed(manual_check_id, machine_id, parameter_id, saved_findings, final_status)

        logger.info(
            "manual_check_completed",
            manual_check_id=manual_check_id,
            final_status=final_status.value,
            findings=len(findings),
            baseline_violations=len(baseline_violations),
        )

        parameter = await self._parameter_repository.get_by_id(parameter_id)
        unit = parameter["unit"] if parameter else baseline.unit

        return _build_api_response(
            manual_check_id, upload_id, unit, baseline, current_result, comparison, baseline_violations,
            saved_findings, final_status,
        )

    async def _raise_alerts_if_needed(
        self,
        manual_check_id: str,
        machine_id: Optional[str],
        parameter_id: str,
        saved_findings: list[dict[str, Any]],
        final_status: FinalProcessStatus,
    ) -> None:
        if final_status not in (FinalProcessStatus.OUT_OF_CONTROL, FinalProcessStatus.CRITICAL):
            return
        for finding in saved_findings:
            if finding["severity"] in (Severity.CRITICAL.value, Severity.WARNING.value):
                await self._alert_repository.create(
                    severity=finding["severity"],
                    message=finding["message"],
                    manual_check_id=manual_check_id,
                    finding_id=finding["finding_id"],
                    machine_id=machine_id,
                    parameter_id=parameter_id,
                )

    async def list_recent(
        self,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        parameter_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return await self._manual_check_repository.list_recent(
            machine_id=machine_id, product_id=product_id, parameter_id=parameter_id, limit=limit,
        )

    async def get_manual_check(self, manual_check_id: str) -> dict[str, Any]:
        """Re-fetch a previously completed manual check in the exact same
        response shape POST /manual-check/run returns (see the analogous
        note on HistoricalAnalysisService.get_analysis)."""
        run = await self._manual_check_repository.get_by_id(manual_check_id)
        if run is None:
            raise NotFoundError(f"Manual check {manual_check_id} not found.")
        comparison = await self._manual_check_repository.get_comparison_result(manual_check_id)
        violations = await self._manual_check_repository.list_rule_violations(manual_check_id)
        findings = await self._findings_repository.list_by_manual_check(manual_check_id)
        baseline = await self._baseline_repository.get_by_id(run["baseline_id"])

        current_run = None
        current_result_row = None
        if run.get("current_analysis_id"):
            current_run = await self._analysis_repository.get_by_id(run["current_analysis_id"])
            current_result_row = await self._analysis_repository.get_result_by_analysis_id(run["current_analysis_id"])

        parameter = await self._parameter_repository.get_by_id(run["parameter_id"])
        unit = parameter["unit"] if parameter else (baseline.get("unit") if baseline else "")

        return _db_row_to_api_response(run, baseline, current_run, current_result_row, comparison, violations, findings, unit)


def _violations_to_db_dicts(violations: list[RuleViolation]) -> list[dict[str, Any]]:
    return [
        {
            "rule_name": v.rule_name.value, "chart_type": v.chart_type.value, "severity": v.severity.value,
            "start_index": v.start_index, "end_index": v.end_index, "affected_points": v.affected_points,
            "message": v.message, "detected_at": v.detected_at,
        }
        for v in violations
    ]


def _comparison_to_db_dict(comparison: ComparisonResult, new_limit_violations_detected: bool) -> dict[str, Any]:
    return {
        "baseline_mean": comparison.baseline_mean, "current_mean": comparison.current_mean,
        "mean_shift": comparison.mean_shift, "mean_shift_percentage": comparison.mean_shift_percentage,
        "baseline_within_sigma": comparison.baseline_within_sigma, "current_within_sigma": comparison.current_within_sigma,
        "within_variation_change": comparison.within_variation_change,
        "within_variation_change_percentage": comparison.within_variation_change_percentage,
        "baseline_overall_sigma": comparison.baseline_overall_sigma, "current_overall_sigma": comparison.current_overall_sigma,
        "overall_variation_change": comparison.overall_variation_change,
        "overall_variation_change_percentage": comparison.overall_variation_change_percentage,
        "baseline_cpk": comparison.baseline_cpk, "current_cpk": comparison.current_cpk, "cpk_change": comparison.cpk_change,
        "baseline_ppk": comparison.baseline_ppk, "current_ppk": comparison.current_ppk, "ppk_change": comparison.ppk_change,
        "mean_shift_detected": comparison.mean_shift_detected,
        "variation_increase_detected": comparison.variation_increase_detected,
        "variation_reduction_detected": comparison.variation_reduction_detected,
        "capability_improvement_detected": comparison.capability_improvement_detected,
        "capability_degradation_detected": comparison.capability_degradation_detected,
        "new_limit_violations_detected": new_limit_violations_detected,
    }


def _findings_to_db_dicts(findings: list[Finding]) -> list[dict[str, Any]]:
    return [
        {"finding_type": f.finding_type.value, "severity": f.severity.value, "message": f.message, "statistical_fact": f.statistical_fact}
        for f in findings
    ]


def _db_row_to_api_response(
    run: dict[str, Any],
    baseline: Optional[dict[str, Any]],
    current_run: Optional[dict[str, Any]],
    current_result_row: Optional[dict[str, Any]],
    comparison: Optional[dict[str, Any]],
    violations: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    unit: str,
) -> dict[str, Any]:
    specification = None
    if baseline and (baseline.get("lsl") is not None or baseline.get("usl") is not None):
        specification = {"lsl": baseline.get("lsl"), "usl": baseline.get("usl"), "target": baseline.get("target")}

    current_chart_points: list[dict[str, Any]] = []
    secondary_points: Optional[list[dict[str, Any]]] = None
    if current_result_row:
        chart_points = current_result_row.get("chart_points") or {}
        current_chart_points = chart_points.get("primary", []) if isinstance(chart_points, dict) else chart_points
        secondary_points = chart_points.get("secondary") if isinstance(chart_points, dict) else None

    # Mirrors the current_chart shape below: carries the current dataset's
    # own secondary (range/moving-range) points so they can be plotted, but
    # the UCL/CL/LCL actually judged against on screen are the baseline's
    # frozen secondary_* limits, not these recalculated ones -- same rule
    # as the primary chart.
    secondary_chart = None
    if current_result_row and current_result_row.get("secondary_center_line") is not None:
        secondary_chart = {
            "center_line": current_result_row["secondary_center_line"],
            "ucl": current_result_row["secondary_ucl"],
            "lcl": current_result_row["secondary_lcl"],
            "points": secondary_points or [],
        }

    return {
        "manual_check_id": run["manual_check_id"],
        "upload_id": run["upload_id"],
        "unit": unit,
        "chart_type": current_run["chart_type"] if current_run else (baseline["chart_type"] if baseline else ""),
        "specification": specification,
        "baseline": {
            "baseline_id": baseline["baseline_id"], "mean": baseline["mean"], "ucl": baseline["ucl"],
            "center_line": baseline["center_line"], "lcl": baseline["lcl"], "within_sigma": baseline["within_sigma"],
            "overall_sigma": baseline["overall_sigma"],
            "secondary_center_line": baseline.get("secondary_center_line"),
            "secondary_ucl": baseline.get("secondary_ucl"), "secondary_lcl": baseline.get("secondary_lcl"),
            "cp": baseline.get("cp"), "cpk": baseline.get("cpk"),
            "pp": baseline.get("pp"), "ppk": baseline.get("ppk"),
            "lsl": baseline.get("lsl"), "usl": baseline.get("usl"), "target": baseline.get("target"),
        },
        "current": {
            "mean": current_result_row["mean"] if current_result_row else None,
            "within_sigma": current_result_row["within_sigma"] if current_result_row else None,
            "overall_sigma": current_result_row["overall_sigma"] if current_result_row else None,
            "cp": current_result_row.get("cp") if current_result_row else None,
            "cpk": current_result_row.get("cpk") if current_result_row else None,
            "pp": current_result_row.get("pp") if current_result_row else None,
            "ppk": current_result_row.get("ppk") if current_result_row else None,
        },
        "current_chart": {
            "center_line": current_result_row["center_line"] if current_result_row else 0,
            "ucl": current_result_row["ucl"] if current_result_row else 0,
            "lcl": current_result_row["lcl"] if current_result_row else 0,
            "points": current_chart_points,
        },
        "secondary_chart": secondary_chart,
        "comparison": {
            "mean_shift": comparison["mean_shift"] if comparison else 0,
            "mean_shift_percentage": comparison.get("mean_shift_percentage") if comparison else None,
            "within_variation_change_percentage": comparison.get("within_variation_change_percentage") if comparison else None,
            "overall_variation_change_percentage": comparison.get("overall_variation_change_percentage") if comparison else None,
            "cpk_change": comparison.get("cpk_change") if comparison else None,
            "ppk_change": comparison.get("ppk_change") if comparison else None,
            "mean_shift_detected": comparison.get("mean_shift_detected", False) if comparison else False,
            "variation_increase_detected": comparison.get("variation_increase_detected", False) if comparison else False,
            "variation_reduction_detected": comparison.get("variation_reduction_detected", False) if comparison else False,
            "capability_improvement_detected": comparison.get("capability_improvement_detected", False) if comparison else False,
            "capability_degradation_detected": comparison.get("capability_degradation_detected", False) if comparison else False,
        },
        "control_status": {"status": run.get("final_status") or "NORMAL", "violations": violations},
        "findings": findings,
        "final_status": run.get("final_status") or "NORMAL",
        "warnings": (current_result_row.get("warnings") if current_result_row else None) or [],
        "created_at": run["created_at"],
    }


def _build_api_response(
    manual_check_id: str,
    upload_id: str,
    unit: str,
    baseline: BaselineSnapshot,
    current_result,
    comparison: ComparisonResult,
    baseline_violations: list[RuleViolation],
    saved_findings: list[dict[str, Any]],
    final_status: FinalProcessStatus,
) -> dict[str, Any]:
    from datetime import datetime, timezone

    specification = None
    if baseline.specification is not None:
        specification = {
            "lsl": baseline.specification.lsl, "usl": baseline.specification.usl, "target": baseline.specification.target,
        }

    return {
        "manual_check_id": manual_check_id,
        "upload_id": upload_id,
        "unit": unit,
        "chart_type": current_result.chart.chart_type.value,
        "specification": specification,
        "baseline": {
            "baseline_id": baseline.baseline_id, "mean": baseline.mean, "ucl": baseline.ucl,
            "center_line": baseline.center_line, "lcl": baseline.lcl, "within_sigma": baseline.within_sigma,
            "overall_sigma": baseline.overall_sigma,
            "secondary_center_line": baseline.secondary_center_line,
            "secondary_ucl": baseline.secondary_ucl, "secondary_lcl": baseline.secondary_lcl,
            "cp": baseline.cp, "cpk": baseline.cpk,
            "pp": baseline.pp, "ppk": baseline.ppk,
            "lsl": baseline.specification.lsl if baseline.specification else None,
            "usl": baseline.specification.usl if baseline.specification else None,
            "target": baseline.specification.target if baseline.specification else None,
        },
        "current": {
            "mean": current_result.statistics.mean, "within_sigma": current_result.sigma.within_sigma,
            "overall_sigma": current_result.sigma.overall_sigma, "cp": current_result.capability.cp,
            "cpk": current_result.capability.cpk, "pp": current_result.capability.pp, "ppk": current_result.capability.ppk,
        },
        "current_chart": current_result.chart.primary_chart,
        "secondary_chart": current_result.chart.secondary_chart,
        "comparison": {
            "mean_shift": comparison.mean_shift, "mean_shift_percentage": comparison.mean_shift_percentage,
            "within_variation_change_percentage": comparison.within_variation_change_percentage,
            "overall_variation_change_percentage": comparison.overall_variation_change_percentage,
            "cpk_change": comparison.cpk_change, "ppk_change": comparison.ppk_change,
            "mean_shift_detected": comparison.mean_shift_detected,
            "variation_increase_detected": comparison.variation_increase_detected,
            "variation_reduction_detected": comparison.variation_reduction_detected,
            "capability_improvement_detected": comparison.capability_improvement_detected,
            "capability_degradation_detected": comparison.capability_degradation_detected,
        },
        "control_status": {
            "status": final_status.value,
            "violations": baseline_violations,
        },
        "findings": saved_findings,
        "final_status": final_status.value,
        "warnings": current_result.warnings,
        "created_at": datetime.now(timezone.utc),
    }
