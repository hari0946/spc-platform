"""Request/response schemas for historical baseline management."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.schemas.common import APIModel


class BaselineCreateRequest(APIModel):
    analysis_id: str
    created_by: Optional[str] = None


class BaselineApproveRequest(APIModel):
    approved_by: Optional[str] = None


class BaselineResponse(APIModel):
    baseline_id: str
    analysis_id: str
    organization_id: Optional[str] = None
    plant_id: Optional[str] = None
    production_line_id: Optional[str] = None
    process_id: Optional[str] = None
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    operation_id: Optional[str] = None
    parameter_id: str
    chart_type: str
    unit: str
    baseline_start: Optional[datetime] = None
    baseline_end: Optional[datetime] = None
    sample_count: int
    mean: float
    within_sigma: float
    overall_sigma: float
    center_line: float
    ucl: float
    lcl: float
    secondary_center_line: Optional[float] = None
    secondary_ucl: Optional[float] = None
    secondary_lcl: Optional[float] = None
    lsl: Optional[float] = None
    usl: Optional[float] = None
    target: Optional[float] = None
    cp: Optional[float] = None
    cpk: Optional[float] = None
    pp: Optional[float] = None
    ppk: Optional[float] = None
    status: str
    created_at: datetime
    created_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
