"""Shared Pydantic v2 schema building blocks used across the API layer."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(APIModel):
    error_code: str
    message: str
    details: dict[str, Any] = {}


class PaginatedResponse(APIModel, Generic[T]):
    items: list[T]
    total: int


class ChartPointSchema(APIModel):
    index: int
    subgroup_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    value: float
    n: int = 1


class ChartSeriesSchema(APIModel):
    center_line: float
    ucl: float
    lcl: float
    points: list[ChartPointSchema]


class RuleViolationSchema(APIModel):
    rule_name: str
    chart_type: str
    severity: str
    start_index: int
    end_index: int
    affected_points: list[int]
    message: str
    detected_at: datetime
