"""Read/acknowledge service for alerts (GET /alerts, PUT /alerts/{id}/acknowledge).

Alert *creation* happens inside manual_data_check_service.py as a
consequence of CRITICAL/WARNING findings -- this service does not create
alerts itself.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.exceptions import NotFoundError
from app.repositories.alert_repository import AlertRepository


class AlertService:
    def __init__(self, alert_repository: AlertRepository) -> None:
        self._alert_repository = alert_repository

    async def list_alerts(self, status: Optional[str] = None, limit: int = 100) -> list[dict[str, Any]]:
        return await self._alert_repository.list_all(status=status, limit=limit)

    async def acknowledge(self, alert_id: str, acknowledged_by: Optional[str] = None) -> dict[str, Any]:
        alert = await self._alert_repository.get_by_id(alert_id)
        if alert is None:
            raise NotFoundError(f"Alert {alert_id} not found.")
        return await self._alert_repository.acknowledge(alert_id, acknowledged_by)
