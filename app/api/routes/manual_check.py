"""POST /manual-check/run, GET /manual-check, GET /manual-check/{manual_check_id}"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_manual_data_check_service
from app.schemas.manual_check import ManualCheckRequest, ManualCheckResultResponse, ManualCheckSummaryResponse
from app.services.manual_data_check_service import ManualDataCheckService

router = APIRouter(prefix="/manual-check", tags=["manual-check"])


@router.post("/run", response_model=ManualCheckResultResponse)
async def run_manual_check(
    request: ManualCheckRequest, service: ManualDataCheckService = Depends(get_manual_data_check_service)
) -> ManualCheckResultResponse:
    result = await service.run_manual_check(
        upload_id=request.upload_id,
        parameter_id=request.parameter_id,
        machine_id=request.machine_id,
        product_id=request.product_id,
        operation_id=request.operation_id,
        baseline_id=request.baseline_id,
        triggered_by=request.triggered_by,
    )
    return ManualCheckResultResponse.model_validate(result)


@router.get("", response_model=list[ManualCheckSummaryResponse])
async def list_manual_checks(
    machine_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    parameter_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    service: ManualDataCheckService = Depends(get_manual_data_check_service),
) -> list[ManualCheckSummaryResponse]:
    results = await service.list_recent(machine_id=machine_id, product_id=product_id, parameter_id=parameter_id, limit=limit)
    return [ManualCheckSummaryResponse.model_validate(r) for r in results]


@router.get("/{manual_check_id}", response_model=ManualCheckResultResponse)
async def get_manual_check(
    manual_check_id: str, service: ManualDataCheckService = Depends(get_manual_data_check_service)
) -> ManualCheckResultResponse:
    result = await service.get_manual_check(manual_check_id)
    return ManualCheckResultResponse.model_validate(result)
