"""Plain-Python data models for the SPC engine.

Deliberately implemented with stdlib `dataclasses` rather than Pydantic:
the engine's contract is "DataFrame + SPCConfiguration + Specification in,
SPCAnalysisResult out" with no framework or transport concerns. Pydantic
API schemas (app/schemas) are a thin, separate translation layer built on
top of these models at the service boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.spc_engine.core.enums import (
    ChartType,
    FinalProcessStatus,
    FindingType,
    RuleName,
    Severity,
    StabilityStatus,
    SubgroupMethod,
)


# ---------------------------------------------------------------------------
# Configuration inputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuleConfig:
    rule_name: RuleName
    enabled: bool = True
    severity: Severity = Severity.WARNING
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SPCConfiguration:
    chart_type: str  # ChartType value, or "AUTO" to let ChartSelector decide
    subgroup_size: int = 1
    subgroup_method: SubgroupMethod = SubgroupMethod.CONSECUTIVE
    maximum_time_gap_seconds: int = 3600
    minimum_sample_size: int = 20
    ruleset: list[RuleConfig] = field(default_factory=list)
    sigma_method: str = "WITHIN_OVERALL"
    capability_method: str = "STANDARD"


@dataclass(frozen=True)
class Specification:
    lsl: Optional[float] = None
    usl: Optional[float] = None
    target: Optional[float] = None
    specification_id: Optional[str] = None

    def has_lower(self) -> bool:
        return self.lsl is not None

    def has_upper(self) -> bool:
        return self.usl is not None

    def is_defined(self) -> bool:
        return self.has_lower() or self.has_upper()


# ---------------------------------------------------------------------------
# Measurement / subgroup structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MeasurementRecord:
    row_number: int
    value: float
    event_timestamp: Optional[datetime]
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    process_id: Optional[str] = None
    operation_id: Optional[str] = None
    parameter_id: Optional[str] = None
    batch_id: Optional[str] = None
    subgroup_hint: Optional[str] = None  # existing subgroup id, if present in source data


@dataclass(frozen=True)
class Subgroup:
    subgroup_id: str
    indices: list[int]
    values: list[float]
    mean: float
    range_: float
    std_dev: Optional[float]
    count: int
    start_timestamp: Optional[datetime]
    end_timestamp: Optional[datetime]


# ---------------------------------------------------------------------------
# Profiling
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DataProfile:
    total_observations: int
    valid_observations: int
    invalid_observations: int
    unique_machines: int
    unique_products: int
    unique_processes: int
    unique_operations: int
    unique_parameters: int
    parameters: list[str]
    time_start: Optional[datetime]
    time_end: Optional[datetime]
    missing_values: int
    existing_subgroup_ids_detected: bool
    potential_subgroup_sizes: list[int]
    average_sampling_interval_seconds: Optional[float]


# ---------------------------------------------------------------------------
# Chart selection
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChartSelection:
    recommended_chart: ChartType
    configured_chart: ChartType
    selection_reason: str


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChartPoint:
    index: int
    subgroup_id: Optional[str]
    timestamp: Optional[datetime]
    value: float
    n: int = 1


@dataclass(frozen=True)
class ChartSeries:
    center_line: float
    ucl: float
    lcl: float
    points: list[ChartPoint]


@dataclass(frozen=True)
class ChartLimits:
    """Just the control limits, decoupled from any particular dataset's
    points -- this is what gets frozen into a baseline and later re-applied
    to a brand new dataset without recalculating limits."""

    center_line: float
    ucl: float
    lcl: float
    secondary_center_line: Optional[float] = None
    secondary_ucl: Optional[float] = None
    secondary_lcl: Optional[float] = None


@dataclass(frozen=True)
class ChartResult:
    chart_type: ChartType
    primary_chart: ChartSeries
    secondary_chart: Optional[ChartSeries]
    grand_mean: float
    subgroup_size_used: int


# ---------------------------------------------------------------------------
# Statistics / sigma / capability
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DescriptiveStatistics:
    mean: float
    minimum: float
    maximum: float
    count: int
    median: float
    range_: float


@dataclass(frozen=True)
class SigmaEstimate:
    within_sigma: float
    overall_sigma: float
    method: str


@dataclass(frozen=True)
class CapabilityResult:
    cp: Optional[float]
    cpk: Optional[float]
    cpu: Optional[float]
    cpl: Optional[float]
    pp: Optional[float]
    ppk: Optional[float]
    ppu: Optional[float]
    ppl: Optional[float]
    # "Sigma level" / Six Sigma process rating, derived from Cpk (see
    # capability_calculator.calculate_sigma_level for the formula).
    sigma_level_short_term: Optional[float] = None
    sigma_level_long_term: Optional[float] = None
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Rules / stability
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RuleViolation:
    rule_name: RuleName
    chart_type: ChartType
    severity: Severity
    start_index: int
    end_index: int
    affected_points: list[int]
    message: str
    detected_at: datetime


@dataclass(frozen=True)
class StabilityResult:
    status: StabilityStatus
    violations: list[RuleViolation]


# ---------------------------------------------------------------------------
# Top level analysis result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SPCAnalysisResult:
    data_summary: DataProfile
    chart_selection: ChartSelection
    chart: ChartResult
    statistics: DescriptiveStatistics
    sigma: SigmaEstimate
    capability: CapabilityResult
    stability: StabilityResult
    specification: Optional[Specification]
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Baseline (as read back from PostgreSQL) and comparison
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaselineSnapshot:
    """Immutable historical baseline, exactly as approved -- the engine
    treats these fields as ground truth and never recomputes them."""

    baseline_id: str
    chart_type: ChartType
    mean: float
    within_sigma: float
    overall_sigma: float
    center_line: float
    ucl: float
    lcl: float
    secondary_center_line: Optional[float]
    secondary_ucl: Optional[float]
    secondary_lcl: Optional[float]
    cp: Optional[float]
    cpk: Optional[float]
    pp: Optional[float]
    ppk: Optional[float]
    specification: Optional[Specification]
    unit: str
    machine_id: Optional[str]
    product_id: Optional[str]
    operation_id: Optional[str]
    parameter_id: str


@dataclass(frozen=True)
class ComparisonResult:
    baseline_mean: float
    current_mean: float
    mean_shift: float
    mean_shift_percentage: Optional[float]

    baseline_within_sigma: float
    current_within_sigma: float
    within_variation_change: float
    within_variation_change_percentage: Optional[float]

    baseline_overall_sigma: float
    current_overall_sigma: float
    overall_variation_change: float
    overall_variation_change_percentage: Optional[float]

    baseline_cpk: Optional[float]
    current_cpk: Optional[float]
    cpk_change: Optional[float]

    baseline_ppk: Optional[float]
    current_ppk: Optional[float]
    ppk_change: Optional[float]

    mean_shift_detected: bool
    variation_increase_detected: bool
    variation_reduction_detected: bool
    capability_improvement_detected: bool
    capability_degradation_detected: bool


@dataclass(frozen=True)
class Finding:
    finding_type: FindingType
    severity: Severity
    message: str
    statistical_fact: dict[str, Any]


@dataclass(frozen=True)
class ManualCheckResult:
    current: SPCAnalysisResult
    baseline: BaselineSnapshot
    baseline_violations: list[RuleViolation]
    comparison: ComparisonResult
    findings: list[Finding]
    final_status: FinalProcessStatus
    warnings: list[str] = field(default_factory=list)
