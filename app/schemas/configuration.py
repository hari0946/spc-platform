"""Request/response schemas for SPC configuration management."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.schemas.common import APIModel


class RuleConfigSchema(APIModel):
    rule_name: str
    enabled: bool = True
    severity: str = "WARNING"
    parameters: dict[str, Any] = Field(default_factory=dict)


class SPCConfigurationCreateRequest(APIModel):
    parameter_id: str
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    operation_id: Optional[str] = None
    chart_type: str = "AUTO"
    subgroup_size: int = 1
    subgroup_method: str = "CONSECUTIVE"
    maximum_time_gap_seconds: int = 3600
    minimum_sample_size: int = 20
    ruleset: list[RuleConfigSchema] = Field(default_factory=list)
    sigma_method: str = "WITHIN_OVERALL"
    capability_method: str = "STANDARD"


class SPCConfigurationUpdateRequest(APIModel):
    chart_type: Optional[str] = None
    subgroup_size: Optional[int] = None
    subgroup_method: Optional[str] = None
    maximum_time_gap_seconds: Optional[int] = None
    minimum_sample_size: Optional[int] = None
    ruleset: Optional[list[RuleConfigSchema]] = None
    sigma_method: Optional[str] = None
    capability_method: Optional[str] = None
    is_active: Optional[bool] = None


class SPCConfigurationResponse(APIModel):
    spc_configuration_id: str
    parameter_id: str
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    operation_id: Optional[str] = None
    chart_type: str
    subgroup_size: int
    subgroup_method: str
    maximum_time_gap_seconds: int
    minimum_sample_size: int
    ruleset: list[dict]
    sigma_method: str
    capability_method: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
