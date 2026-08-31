"""POST/GET/PUT /spc/configurations"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_spc_configuration_service
from app.schemas.configuration import (
    SPCConfigurationCreateRequest,
    SPCConfigurationResponse,
    SPCConfigurationUpdateRequest,
)
from app.services.spc_configuration_service import SPCConfigurationService

router = APIRouter(prefix="/spc/configurations", tags=["spc-configurations"])


@router.get("/effective", response_model=Optional[SPCConfigurationResponse])
async def get_effective_configuration(
    parameter_id: str = Query(...),
    machine_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    operation_id: Optional[str] = Query(None),
    service: SPCConfigurationService = Depends(get_spc_configuration_service),
) -> Optional[SPCConfigurationResponse]:
    result = await service.get_effective(parameter_id, machine_id, product_id, operation_id)
    return SPCConfigurationResponse.model_validate(result) if result else None


@router.post("", response_model=SPCConfigurationResponse)
async def create_configuration(
    request: SPCConfigurationCreateRequest, service: SPCConfigurationService = Depends(get_spc_configuration_service)
) -> SPCConfigurationResponse:
    result = await service.create(request.model_dump())
    return SPCConfigurationResponse.model_validate(result)


@router.get("", response_model=list[SPCConfigurationResponse])
async def list_configurations(
    service: SPCConfigurationService = Depends(get_spc_configuration_service),
) -> list[SPCConfigurationResponse]:
    results = await service.list_all()
    return [SPCConfigurationResponse.model_validate(r) for r in results]


@router.get("/{spc_configuration_id}", response_model=SPCConfigurationResponse)
async def get_configuration(
    spc_configuration_id: str, service: SPCConfigurationService = Depends(get_spc_configuration_service)
) -> SPCConfigurationResponse:
    result = await service.get_by_id(spc_configuration_id)
    return SPCConfigurationResponse.model_validate(result)


@router.put("/{spc_configuration_id}", response_model=SPCConfigurationResponse)
async def update_configuration(
    spc_configuration_id: str,
    request: SPCConfigurationUpdateRequest,
    service: SPCConfigurationService = Depends(get_spc_configuration_service),
) -> SPCConfigurationResponse:
    result = await service.update(spc_configuration_id, request.model_dump(exclude_unset=True))
    return SPCConfigurationResponse.model_validate(result)
