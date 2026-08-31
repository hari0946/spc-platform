"""Request/response schemas for findings."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from app.schemas.common import APIModel


class FindingSchema(APIModel):
    finding_id: Optional[str] = None
    finding_type: str
    severity: str
    message: str
    statistical_fact: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
