"""Request/response schemas for historical SPC analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.common import APIModel, ChartSeriesSchema, RuleViolationSchema


class HistoricalAnalysisRequest(APIModel):
    upload_id: str
    parameter_id: str
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    process_id: Optional[str] = None
    operation_id: Optional[str] = None
    spc_configuration_id: Optional[str] = None


class ContextSchema(APIModel):
    organization_id: Optional[str] = None
    plant_id: Optional[str] = None
    production_line_id: Optional[str] = None
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    process_id: Optional[str] = None
    operation_id: Optional[str] = None
    parameter_id: str


class DataSummarySchema(APIModel):
    total_observations: int
    valid_observations: int
    invalid_observations: int
    subgroups: int


class ChartSchema(APIModel):
    type: str
    subgroup_size_used: int
    primary_chart: ChartSeriesSchema
    secondary_chart: Optional[ChartSeriesSchema] = None
    selection_reason: str


class StatisticsSchema(APIModel):
    mean: float
    minimum: float
    maximum: float
    within_sigma: float
    overall_sigma: float


class SpecificationSchema(APIModel):
    lsl: Optional[float] = None
    usl: Optional[float] = None
    target: Optional[float] = None


class CapabilitySchema(APIModel):
    cp: Optional[float] = None
    cpk: Optional[float] = None
    cpu: Optional[float] = None
    cpl: Optional[float] = None
    pp: Optional[float] = None
    ppk: Optional[float] = None
    ppu: Optional[float] = None
    ppl: Optional[float] = None
    sigma_level_short_term: Optional[float] = None
    sigma_level_long_term: Optional[float] = None


class StabilitySchema(APIModel):
    status: str
    violations: list[RuleViolationSchema] = Field(default_factory=list)


class AnalysisSummaryResponse(APIModel):
    """Lightweight row for list views (Dashboard recent-analysis table,
    Analysis History) -- avoids shipping full chart point series to a
    table that only needs Cpk/status/date per row."""

    analysis_id: str
    analysis_type: str
    upload_id: str
    organization_id: Optional[str] = None
    plant_id: Optional[str] = None
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    operation_id: Optional[str] = None
    parameter_id: str
    chart_type: str
    status: str
    cpk: Optional[float] = None
    ppk: Optional[float] = None
    stability_status: Optional[str] = None
    created_at: datetime


class SPCAnalysisResultResponse(APIModel):
    analysis_id: str
    context: ContextSchema
    unit: str
    data_summary: DataSummarySchema
    chart: ChartSchema
    statistics: StatisticsSchema
    specification: Optional[SpecificationSchema] = None
    capability: CapabilitySchema
    stability: StabilitySchema
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime
