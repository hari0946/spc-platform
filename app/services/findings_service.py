"""Read-side service for findings (GET /findings)."""

from __future__ import annotations

from typing import Any, Optional

from app.repositories.findings_repository import FindingsRepository


class FindingsService:
    def __init__(self, findings_repository: FindingsRepository) -> None:
        self._findings_repository = findings_repository

    async def list_findings(
        self, severity: Optional[str] = None, finding_type: Optional[str] = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        return await self._findings_repository.list_recent(severity=severity, finding_type=finding_type, limit=limit)
