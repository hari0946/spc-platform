"""GET /alerts, PUT /alerts/{alert_id}/acknowledge"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_alert_service
from app.schemas.alerts import AlertAcknowledgeRequest, AlertResponse
from app.services.alert_service import AlertService

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    service: AlertService = Depends(get_alert_service),
) -> list[AlertResponse]:
    results = await service.list_alerts(status=status, limit=limit)
    return [AlertResponse.model_validate(r) for r in results]


@router.put("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str, request: AlertAcknowledgeRequest, service: AlertService = Depends(get_alert_service)
) -> AlertResponse:
    result = await service.acknowledge(alert_id, request.acknowledged_by)
    return AlertResponse.model_validate(result)
