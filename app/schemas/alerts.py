"""Request/response schemas for alerts."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.schemas.common import APIModel


class AlertAcknowledgeRequest(APIModel):
    acknowledged_by: Optional[str] = None


class AlertResponse(APIModel):
    alert_id: str
    manual_check_id: Optional[str] = None
    finding_id: Optional[str] = None
    machine_id: Optional[str] = None
    parameter_id: Optional[str] = None
    severity: str
    status: str
    message: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
