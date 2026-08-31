"""Phase 1: Historical SPC Analysis and Baseline Creation.

Orchestrates: load cleaned Silver measurements for a context -> resolve SPC
configuration + specification from PostgreSQL -> run the independent SPC
engine -> persist analysis_runs/analysis_results/rule_violations via raw
SQL repositories -> return a strongly-typed result.

This service is the only place that translates between "PostgreSQL rows"
and "SPC engine dataclasses" -- neither the repositories nor the SPC
engine know about each other.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.exceptions import (
    InsufficientDataError as AppInsufficientDataError,
    MissingSPCConfigurationError,
    NotFoundError,
    UploadNotReadyError,
    ValidationError,
)
from app.core.logging import get_logger
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.spc_configuration_repository import SPCConfigurationRepository
from app.repositories.specification_repository import SpecificationRepository
from app.repositories.upload_repository import UploadRepository
from app.spc_engine.capability.capability_calculator import calculate_sigma_level
from app.spc_engine.core import exceptions as engine_exceptions
from app.spc_engine.core.enums import SubgroupMethod
from app.spc_engine.core.models import RuleConfig, SPCAnalysisResult, SPCConfiguration, Specification
from app.spc_engine.core.enums import RuleName, Severity
from app.spc_engine.results.result_builder import run_spc_analysis

logger = get_logger(__name__)


def _row_to_spc_configuration(row: dict[str, Any]) -> SPCConfiguration:
    ruleset_raw = row.get("ruleset") or []
    if isinstance(ruleset_raw, str):
        import json

        ruleset_raw = json.loads(ruleset_raw)
    ruleset = [
        RuleConfig(
            rule_name=RuleName(r["rule_name"]),
            enabled=r.get("enabled", True),
            severity=Severity(r.get("severity", "WARNING")),
            parameters=r.get("parameters", {}),
        )
        for r in ruleset_raw
    ]
    return SPCConfiguration(
        chart_type=row["chart_type"],
        subgroup_size=row["subgroup_size"],
        subgroup_method=SubgroupMethod(row["subgroup_method"]),
        maximum_time_gap_seconds=row["maximum_time_gap_seconds"],
        minimum_sample_size=row["minimum_sample_size"],
        ruleset=ruleset,
        sigma_method=row["sigma_method"],
        capability_method=row["capability_method"],
    )


def _row_to_specification(row: Optional[dict[str, Any]]) -> Optional[Specification]:
    if row is None:
        return None
    return Specification(
        lsl=float(row["lsl"]) if row["lsl"] is not None else None,
        usl=float(row["usl"]) if row["usl"] is not None else None,
        target=float(row["target"]) if row["target"] is not None else None,
        specification_id=row["specification_id"],
    )


class HistoricalAnalysisService:
    def __init__(
        self,
        upload_repository: UploadRepository,
        measurement_repository: MeasurementRepository,
        spc_configuration_repository: SPCConfigurationRepository,
        specification_repository: SpecificationRepository,
        analysis_repository: AnalysisRepository,
        parameter_repository: Optional[ParameterRepository] = None,
    ) -> None:
        self._upload_repository = upload_repository
        self._measurement_repository = measurement_repository
        self._spc_configuration_repository = spc_configuration_repository
        self._specification_repository = specification_repository
        self._analysis_repository = analysis_repository
        self._parameter_repository = parameter_repository or ParameterRepository()

    async def run_historical_analysis(
        self,
        upload_id: str,
        parameter_id: str,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        spc_configuration_id: Optional[str] = None,
    ) -> dict[str, Any]:
        upload = await self._upload_repository.get_by_id(upload_id)
        if upload is None:
            raise NotFoundError(f"Upload {upload_id} not found.")
        if upload["status"] != "SILVER_COMPLETED":
            raise UploadNotReadyError(
                f"Upload {upload_id} is not ready for analysis (status={upload['status']}); "
                f"it must reach SILVER_COMPLETED first."
            )
        if upload["upload_type"] != "HISTORICAL":
            raise ValidationError(f"Upload {upload_id} is not a HISTORICAL upload.")

        if spc_configuration_id:
            config_row = await self._spc_configuration_repository.get_by_id(spc_configuration_id)
        else:
            config_row = await self._spc_configuration_repository.get_effective_configuration(
                parameter_id, machine_id, product_id, operation_id
            )
        if config_row is None:
            raise MissingSPCConfigurationError(
                f"No active SPC configuration found for parameter {parameter_id} "
                f"(machine={machine_id}, product={product_id}, operation={operation_id})."
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
            raise AppInsufficientDataError(
                f"No valid Silver measurements found for parameter {parameter_id} in this context."
            )
        # Snowflake returns event_timestamp as pandas Timestamp; SPC engine
        # expects python datetime or NaT.
        df = df.rename(columns={c: c.lower() for c in df.columns})

        run_row = await self._analysis_repository.create_run(
            analysis_type="HISTORICAL",
            upload_id=upload_id,
            parameter_id=parameter_id,
            chart_type=engine_config.chart_type if engine_config.chart_type != "AUTO" else "IMR",
            spc_configuration_id=config_row["spc_configuration_id"],
            organization_id=upload.get("organization_id"),
            plant_id=upload.get("plant_id"),
            production_line_id=upload.get("production_line_id"),
            machine_id=machine_id,
            product_id=product_id,
            operation_id=operation_id,
        )
        analysis_id = run_row["analysis_id"]
        logger.info("historical_analysis_started", analysis_id=analysis_id, upload_id=upload_id, parameter_id=parameter_id)

        try:
            result = run_spc_analysis(df, engine_config, specification)
        except engine_exceptions.SPCEngineError as exc:
            await self._analysis_repository.mark_failed(analysis_id, str(exc))
            raise AppInsufficientDataError(str(exc)) from exc

        # chart_type on the run row was a best-guess before analysis (in
        # particular "AUTO" configurations were placeholder-recorded as
        # IMR); now that the engine has resolved it, correct it to what
        # actually ran so baseline creation never inherits a stale guess.
        await self._analysis_repository.mark_completed(analysis_id, resolved_chart_type=result.chart.chart_type.value)

        result_row = await self._analysis_repository.save_result(analysis_id, _result_to_db_dict(result))
        violation_dicts = _violations_to_db_dicts(result)
        await self._analysis_repository.save_rule_violations(analysis_id, violation_dicts)

        logger.info(
            "historical_analysis_completed",
            analysis_id=analysis_id,
            chart_type=result.chart.chart_type.value,
            cpk=result.capability.cpk,
            stability=result.stability.status.value,
        )

        parameter = await self._parameter_repository.get_by_id(parameter_id)
        unit = parameter["unit"] if parameter else ""

        return _build_api_response(
            analysis_id, upload, machine_id, product_id, operation_id, parameter_id, unit, result, result_row
        )

    async def list_recent(
        self,
        analysis_type: Optional[str] = None,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        parameter_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return await self._analysis_repository.list_recent(
            analysis_type=analysis_type, machine_id=machine_id, product_id=product_id,
            parameter_id=parameter_id, limit=limit,
        )

    async def get_analysis(self, analysis_id: str) -> dict[str, Any]:
        """Re-fetch a previously completed analysis, in the exact same
        response shape POST /analysis/historical returns -- so the frontend
        can render a freshly-run result and a re-opened historical one with
        identical code, instead of handling two different response shapes
        for the same data."""
        run = await self._analysis_repository.get_by_id(analysis_id)
        if run is None:
            raise NotFoundError(f"Analysis {analysis_id} not found.")
        result_row = await self._analysis_repository.get_result_by_analysis_id(analysis_id)
        if result_row is None:
            raise NotFoundError(f"Analysis result for {analysis_id} not found.")
        violations = await self._analysis_repository.list_rule_violations(analysis_id)

        parameter = await self._parameter_repository.get_by_id(run["parameter_id"])
        unit = parameter["unit"] if parameter else ""

        return _db_row_to_api_response(run, result_row, violations, unit)


def _result_to_db_dict(result: SPCAnalysisResult) -> dict[str, Any]:
    primary = result.chart.primary_chart
    secondary = result.chart.secondary_chart
    return {
        "total_observations": result.data_summary.total_observations,
        "valid_observations": result.data_summary.valid_observations,
        "invalid_observations": result.data_summary.invalid_observations,
        "subgroup_count": len(primary.points),
        "subgroup_size_used": result.chart.subgroup_size_used,
        "mean": result.statistics.mean,
        "minimum": result.statistics.minimum,
        "maximum": result.statistics.maximum,
        "within_sigma": result.sigma.within_sigma,
        "overall_sigma": result.sigma.overall_sigma,
        "center_line": primary.center_line,
        "ucl": primary.ucl,
        "lcl": primary.lcl,
        "secondary_center_line": secondary.center_line if secondary else None,
        "secondary_ucl": secondary.ucl if secondary else None,
        "secondary_lcl": secondary.lcl if secondary else None,
        "specification_id": result.specification.specification_id if result.specification else None,
        "lsl": result.specification.lsl if result.specification else None,
        "usl": result.specification.usl if result.specification else None,
        "target": result.specification.target if result.specification else None,
        "cp": result.capability.cp,
        "cpk": result.capability.cpk,
        "cpu": result.capability.cpu,
        "cpl": result.capability.cpl,
        "pp": result.capability.pp,
        "ppk": result.capability.ppk,
        "ppu": result.capability.ppu,
        "ppl": result.capability.ppl,
        "stability_status": result.stability.status.value,
        "chart_points": {
            "primary": [_chart_point_to_dict(p) for p in primary.points],
            "secondary": [_chart_point_to_dict(p) for p in secondary.points] if secondary else None,
        },
        "warnings": result.warnings,
    }


def _chart_point_to_dict(point: Any) -> dict[str, Any]:
    return {
        "index": point.index,
        "subgroup_id": point.subgroup_id,
        "timestamp": point.timestamp.isoformat() if point.timestamp else None,
        "value": point.value,
        "n": point.n,
    }


def _capability_dict_with_sigma_level(
    cp: Any, cpk: Any, cpu: Any, cpl: Any, pp: Any, ppk: Any, ppu: Any, ppl: Any
) -> dict[str, Any]:
    """Re-fetching a stored analysis doesn't have a sigma_level column to
    read (it's a pure function of cpk, never persisted) -- derive it here
    with the exact same formula the engine used when the analysis first ran."""
    sigma_level_short_term, sigma_level_long_term = calculate_sigma_level(cpk)
    return {
        "cp": cp, "cpk": cpk, "cpu": cpu, "cpl": cpl, "pp": pp, "ppk": ppk, "ppu": ppu, "ppl": ppl,
        "sigma_level_short_term": sigma_level_short_term, "sigma_level_long_term": sigma_level_long_term,
    }


def _db_row_to_api_response(
    run: dict[str, Any], result_row: dict[str, Any], violations: list[dict[str, Any]], unit: str
) -> dict[str, Any]:
    chart_points = result_row.get("chart_points") or {}
    primary_points = chart_points.get("primary", []) if isinstance(chart_points, dict) else chart_points
    secondary_points = chart_points.get("secondary") if isinstance(chart_points, dict) else None

    specification = None
    if result_row.get("lsl") is not None or result_row.get("usl") is not None:
        specification = {"lsl": result_row.get("lsl"), "usl": result_row.get("usl"), "target": result_row.get("target")}

    secondary_chart = None
    if result_row.get("secondary_center_line") is not None:
        secondary_chart = {
            "center_line": result_row["secondary_center_line"],
            "ucl": result_row["secondary_ucl"],
            "lcl": result_row["secondary_lcl"],
            "points": secondary_points or [],
        }

    return {
        "analysis_id": run["analysis_id"],
        "context": {
            "organization_id": run.get("organization_id"),
            "plant_id": run.get("plant_id"),
            "production_line_id": run.get("production_line_id"),
            "machine_id": run.get("machine_id"),
            "product_id": run.get("product_id"),
            "operation_id": run.get("operation_id"),
            "parameter_id": run["parameter_id"],
        },
        "unit": unit,
        "data_summary": {
            "total_observations": result_row["total_observations"],
            "valid_observations": result_row["valid_observations"],
            "invalid_observations": result_row["invalid_observations"],
            "subgroups": result_row["subgroup_count"],
        },
        "chart": {
            "type": run["chart_type"],
            "subgroup_size_used": result_row["subgroup_size_used"],
            "primary_chart": {
                "center_line": result_row["center_line"],
                "ucl": result_row["ucl"],
                "lcl": result_row["lcl"],
                "points": primary_points,
            },
            "secondary_chart": secondary_chart,
            "selection_reason": "Chart type resolved during the original analysis run.",
        },
        "statistics": {
            "mean": result_row["mean"],
            "minimum": result_row["minimum"],
            "maximum": result_row["maximum"],
            "within_sigma": result_row["within_sigma"],
            "overall_sigma": result_row["overall_sigma"],
        },
        "specification": specification,
        "capability": _capability_dict_with_sigma_level(
            cp=result_row.get("cp"), cpk=result_row.get("cpk"), cpu=result_row.get("cpu"),
            cpl=result_row.get("cpl"), pp=result_row.get("pp"), ppk=result_row.get("ppk"),
            ppu=result_row.get("ppu"), ppl=result_row.get("ppl"),
        ),
        "stability": {"status": result_row["stability_status"], "violations": violations},
        "warnings": result_row.get("warnings") or [],
        "created_at": result_row["created_at"],
    }


def _violations_to_db_dicts(result: SPCAnalysisResult) -> list[dict[str, Any]]:
    return [
        {
            "rule_name": v.rule_name.value,
            "chart_type": v.chart_type.value,
            "severity": v.severity.value,
            "start_index": v.start_index,
            "end_index": v.end_index,
            "affected_points": v.affected_points,
            "message": v.message,
            "detected_at": v.detected_at,
        }
        for v in result.stability.violations
    ]


def _build_api_response(
    analysis_id: str,
    upload: dict[str, Any],
    machine_id: Optional[str],
    product_id: Optional[str],
    operation_id: Optional[str],
    parameter_id: str,
    unit: str,
    result: SPCAnalysisResult,
    result_row: dict[str, Any],
) -> dict[str, Any]:
    specification = (
        {"lsl": result.specification.lsl, "usl": result.specification.usl, "target": result.specification.target}
        if result.specification is not None
        else None
    )
    return {
        "analysis_id": analysis_id,
        "context": {
            "organization_id": upload.get("organization_id"),
            "plant_id": upload.get("plant_id"),
            "production_line_id": upload.get("production_line_id"),
            "machine_id": machine_id,
            "product_id": product_id,
            "operation_id": operation_id,
            "parameter_id": parameter_id,
        },
        "unit": unit,
        "specification": specification,
        "data_summary": {
            "total_observations": result.data_summary.total_observations,
            "valid_observations": result.data_summary.valid_observations,
            "invalid_observations": result.data_summary.invalid_observations,
            "subgroups": len(result.chart.primary_chart.points),
        },
        "chart": {
            "type": result.chart.chart_type.value,
            "subgroup_size_used": result.chart.subgroup_size_used,
            "primary_chart": result.chart.primary_chart,
            "secondary_chart": result.chart.secondary_chart,
            "selection_reason": result.chart_selection.selection_reason,
        },
        "statistics": {
            "mean": result.statistics.mean,
            "minimum": result.statistics.minimum,
            "maximum": result.statistics.maximum,
            "within_sigma": result.sigma.within_sigma,
            "overall_sigma": result.sigma.overall_sigma,
        },
        "capability": {
            "cp": result.capability.cp, "cpk": result.capability.cpk,
            "cpu": result.capability.cpu, "cpl": result.capability.cpl,
            "pp": result.capability.pp, "ppk": result.capability.ppk,
            "ppu": result.capability.ppu, "ppl": result.capability.ppl,
            "sigma_level_short_term": result.capability.sigma_level_short_term,
            "sigma_level_long_term": result.capability.sigma_level_long_term,
        },
        "stability": {"status": result.stability.status.value, "violations": result.stability.violations},
        "warnings": result.warnings,
        "created_at": result_row["created_at"],
    }
