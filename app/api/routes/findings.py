"""GET /findings"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_findings_service
from app.schemas.findings import FindingSchema
from app.services.findings_service import FindingsService

router = APIRouter(tags=["findings"])


@router.get("/findings", response_model=list[FindingSchema])
async def list_findings(
    severity: Optional[str] = Query(None),
    finding_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    service: FindingsService = Depends(get_findings_service),
) -> list[FindingSchema]:
    results = await service.list_findings(severity=severity, finding_type=finding_type, limit=limit)
    return [FindingSchema.model_validate(r) for r in results]
