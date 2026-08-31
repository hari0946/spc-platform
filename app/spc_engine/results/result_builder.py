"""Orchestrates the SPC engine sub-modules (profiling -> subgrouping ->
chart selection -> chart calculation -> statistics -> capability -> rules)
into one SPCAnalysisResult.

This is the SPC engine's single public entry point (`run_spc_analysis`).
Everything above it in the call stack (services/historical_analysis_service.py,
services/manual_data_check_service.py) only ever calls into this module --
they never reach into individual sub-packages directly. Everything below it
is pure computation with no I/O.
"""

from __future__ import annotations

import pandas as pd

from app.spc_engine.capability.capability_calculator import calculate_capability
from app.spc_engine.chart_selection.chart_selector import select_chart
from app.spc_engine.charts.base_chart import BaseChart
from app.spc_engine.charts.imr import ImrChart
from app.spc_engine.charts.xbar_r import XbarRChart
from app.spc_engine.charts.xbar_s import XbarSChart
from app.spc_engine.core.enums import ChartType
from app.spc_engine.core.exceptions import InvalidSubgroupSizeError
from app.spc_engine.core.models import (
    MeasurementRecord,
    RuleConfig,
    SPCAnalysisResult,
    SPCConfiguration,
    Specification,
)
from app.spc_engine.profiling.data_profiler import profile_dataset
from app.spc_engine.rules.rule_engine import RuleEngine
from app.spc_engine.statistics.descriptive_stats import calculate_descriptive_statistics
from app.spc_engine.statistics.sigma_estimator import estimate_sigma
from app.spc_engine.subgrouping.subgroup_engine import form_subgroups
from app.spc_engine.subgrouping.subgroup_validator import (
    validate_minimum_subgroup_count,
    validate_subgroups_not_empty,
)
from app.spc_engine.validation.spc_data_validator import validate_dataset

_CHART_IMPLEMENTATIONS: dict[ChartType, type[BaseChart]] = {
    ChartType.XBAR_R: XbarRChart,
    ChartType.XBAR_S: XbarSChart,
    ChartType.IMR: ImrChart,
}


def _dataframe_to_records(df: pd.DataFrame) -> list[MeasurementRecord]:
    records: list[MeasurementRecord] = []
    for row_number, row in enumerate(df.itertuples(index=False), start=1):
        row_dict = row._asdict()
        timestamp = row_dict.get("event_timestamp")
        if pd.isna(timestamp):
            timestamp = None
        records.append(
            MeasurementRecord(
                row_number=row_number,
                value=float(row_dict["value"]),
                event_timestamp=timestamp,
                machine_id=_none_if_nan(row_dict.get("machine_id")),
                product_id=_none_if_nan(row_dict.get("product_id")),
                process_id=_none_if_nan(row_dict.get("process_id")),
                operation_id=_none_if_nan(row_dict.get("operation_id")),
                parameter_id=_none_if_nan(row_dict.get("parameter_id")),
                batch_id=_none_if_nan(row_dict.get("batch_id")),
                subgroup_hint=_none_if_nan(row_dict.get("subgroup_id")),
            )
        )
    return records


def _none_if_nan(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    return str(value) if value is not None else None


def run_spc_analysis(
    df: pd.DataFrame,
    config: SPCConfiguration,
    specification: Specification | None,
) -> SPCAnalysisResult:
    """Run a full, independent SPC analysis on a cleaned measurements
    DataFrame. `df` is expected to already be filtered to a single
    manufacturing context (one machine/product/process/operation/parameter),
    with at least a `value` column and, ideally, `event_timestamp`.
    """
    validate_dataset(df, config.minimum_sample_size)

    profile = profile_dataset(df)
    valid_df = df[df["value"].notna()].copy()
    all_valid_values = [float(v) for v in valid_df["value"].tolist()]

    records = _dataframe_to_records(valid_df)
    subgroups = form_subgroups(
        records,
        method=config.subgroup_method,
        subgroup_size=config.subgroup_size,
        maximum_time_gap_seconds=config.maximum_time_gap_seconds,
    )
    validate_subgroups_not_empty(subgroups)
    validate_minimum_subgroup_count(subgroups, minimum=2)

    detected_subgroup_size = max(set(sg.count for sg in subgroups), key=[sg.count for sg in subgroups].count)
    chart_selection = select_chart(config.chart_type, detected_subgroup_size)

    chart_impl_cls = _CHART_IMPLEMENTATIONS.get(chart_selection.configured_chart)
    if chart_impl_cls is None:
        raise InvalidSubgroupSizeError(f"No chart implementation registered for {chart_selection.configured_chart}")
    chart_result, chart_warnings = chart_impl_cls().calculate(subgroups)

    conforming_subgroups = [sg for sg in subgroups if sg.count == chart_result.subgroup_size_used]

    statistics_result = calculate_descriptive_statistics(all_valid_values)
    sigma_result = estimate_sigma(
        chart_selection.configured_chart, conforming_subgroups, chart_result.subgroup_size_used, all_valid_values
    )

    capability_result = calculate_capability(
        specification=specification,
        mean=statistics_result.mean,
        within_sigma=sigma_result.within_sigma,
        overall_sigma=sigma_result.overall_sigma,
        sample_size=statistics_result.count,
    )

    ruleset: list[RuleConfig] = config.ruleset
    rule_engine = RuleEngine(ruleset)
    primary_violations = rule_engine.evaluate(
        chart_result.primary_chart.points,
        chart_result.primary_chart.center_line,
        chart_result.primary_chart.ucl,
        chart_result.primary_chart.lcl,
        chart_result.chart_type,
    )
    stability_result = RuleEngine.determine_stability(primary_violations)

    warnings: list[str] = list(chart_warnings) + list(capability_result.warnings)
    if sigma_result.within_sigma == 0:
        warnings.append("Within-sigma is zero: control limits collapse to the center line.")

    return SPCAnalysisResult(
        data_summary=profile,
        chart_selection=chart_selection,
        chart=chart_result,
        statistics=statistics_result,
        sigma=sigma_result,
        capability=capability_result,
        stability=stability_result,
        specification=specification,
        warnings=warnings,
    )
