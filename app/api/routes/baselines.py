"""POST /baselines/create, POST /baselines/{id}/approve, POST
/baselines/{id}/activate, GET /baselines, GET /baselines/{id}"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_baseline_service
from app.schemas.baseline import BaselineApproveRequest, BaselineCreateRequest, BaselineResponse
from app.services.baseline_service import BaselineService

router = APIRouter(prefix="/baselines", tags=["baselines"])


@router.post("/create", response_model=BaselineResponse)
async def create_baseline(
    request: BaselineCreateRequest, service: BaselineService = Depends(get_baseline_service)
) -> BaselineResponse:
    result = await service.create_draft_from_analysis(request.analysis_id, request.created_by)
    return BaselineResponse.model_validate(result)


@router.post("/{baseline_id}/approve", response_model=BaselineResponse)
async def approve_baseline(
    baseline_id: str, request: BaselineApproveRequest, service: BaselineService = Depends(get_baseline_service)
) -> BaselineResponse:
    result = await service.approve(baseline_id, request.approved_by)
    return BaselineResponse.model_validate(result)


@router.post("/{baseline_id}/activate", response_model=BaselineResponse)
async def activate_baseline(
    baseline_id: str, request: BaselineApproveRequest, service: BaselineService = Depends(get_baseline_service)
) -> BaselineResponse:
    """Alias for approve -- DRAFT -> ACTIVE is a single step in this
    platform (approval IS activation); both routes are exposed since API
    consumers may reasonably expect either verb."""
    result = await service.approve(baseline_id, request.approved_by)
    return BaselineResponse.model_validate(result)


@router.get("", response_model=list[BaselineResponse])
async def list_baselines(
    parameter_id: Optional[str] = Query(None),
    machine_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    operation_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    service: BaselineService = Depends(get_baseline_service),
) -> list[BaselineResponse]:
    results = await service.list_baselines(parameter_id, machine_id, product_id, operation_id, status)
    return [BaselineResponse.model_validate(r) for r in results]


@router.get("/{baseline_id}", response_model=BaselineResponse)
async def get_baseline(baseline_id: str, service: BaselineService = Depends(get_baseline_service)) -> BaselineResponse:
    result = await service.get_by_id(baseline_id)
    return BaselineResponse.model_validate(result)
