"""Request/response schemas for Phase 2 manual data checks."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.analysis import SpecificationSchema
from app.schemas.common import APIModel, ChartSeriesSchema, RuleViolationSchema
from app.schemas.findings import FindingSchema


class ManualCheckRequest(APIModel):
    upload_id: str
    parameter_id: str
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    operation_id: Optional[str] = None
    baseline_id: Optional[str] = None  # if omitted, resolves the current ACTIVE baseline
    triggered_by: Optional[str] = None


class BaselineSummarySchema(APIModel):
    baseline_id: str
    mean: float
    ucl: float
    center_line: float
    lcl: float
    within_sigma: float
    overall_sigma: float
    secondary_center_line: Optional[float] = None
    secondary_ucl: Optional[float] = None
    secondary_lcl: Optional[float] = None
    cp: Optional[float] = None
    cpk: Optional[float] = None
    pp: Optional[float] = None
    ppk: Optional[float] = None
    lsl: Optional[float] = None
    usl: Optional[float] = None
    target: Optional[float] = None


class CurrentSummarySchema(APIModel):
    mean: float
    within_sigma: float
    overall_sigma: float
    cp: Optional[float] = None
    cpk: Optional[float] = None
    pp: Optional[float] = None
    ppk: Optional[float] = None


class ComparisonSchema(APIModel):
    mean_shift: float
    mean_shift_percentage: Optional[float] = None
    within_variation_change_percentage: Optional[float] = None
    overall_variation_change_percentage: Optional[float] = None
    cpk_change: Optional[float] = None
    ppk_change: Optional[float] = None
    # Detection booleans computed by BaselineComparisonEngine -- the
    # authoritative "is this a significant change" determination. The
    # frontend must render these as-is rather than inventing its own
    # significance threshold from the raw deltas above.
    mean_shift_detected: bool = False
    variation_increase_detected: bool = False
    variation_reduction_detected: bool = False
    capability_improvement_detected: bool = False
    capability_degradation_detected: bool = False


class ControlStatusSchema(APIModel):
    status: str
    violations: list[RuleViolationSchema] = Field(default_factory=list)


class ManualCheckSummaryResponse(APIModel):
    """Lightweight row for list views -- see AnalysisSummaryResponse for
    the same rationale on the historical side."""

    manual_check_id: str
    upload_id: str
    baseline_id: str
    organization_id: Optional[str] = None
    plant_id: Optional[str] = None
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    operation_id: Optional[str] = None
    parameter_id: str
    status: str
    final_status: Optional[str] = None
    current_cpk: Optional[float] = None
    current_ppk: Optional[float] = None
    created_at: datetime


class ManualCheckResultResponse(APIModel):
    manual_check_id: str
    upload_id: str
    unit: str
    chart_type: str
    specification: Optional[SpecificationSchema] = None
    baseline: BaselineSummarySchema
    current: CurrentSummarySchema
    current_chart: ChartSeriesSchema
    secondary_chart: Optional[ChartSeriesSchema] = None
    comparison: ComparisonSchema
    control_status: ControlStatusSchema
    findings: list[FindingSchema] = Field(default_factory=list)
    final_status: str
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime
