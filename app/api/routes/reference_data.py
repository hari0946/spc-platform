"""GET endpoints for manufacturing context master data (read-only) --
backs the frontend's context-selection dropdowns."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_reference_data_service
from app.schemas.reference import (
    MachineSchema,
    OperationSchema,
    OrganizationSchema,
    ParameterSchema,
    PlantSchema,
    ProcessSchema,
    ProductSchema,
    SpecificationCreateRequest,
    SpecificationRefSchema,
)
from app.services.reference_data_service import ReferenceDataService

router = APIRouter(prefix="/reference", tags=["reference-data"])


@router.get("/organizations", response_model=list[OrganizationSchema])
async def list_organizations(
    service: ReferenceDataService = Depends(get_reference_data_service),
) -> list[OrganizationSchema]:
    results = await service.list_organizations()
    return [OrganizationSchema.model_validate(r) for r in results]


@router.get("/plants", response_model=list[PlantSchema])
async def list_plants(
    organization_id: str = Query(...), service: ReferenceDataService = Depends(get_reference_data_service)
) -> list[PlantSchema]:
    results = await service.list_plants(organization_id)
    return [PlantSchema.model_validate(r) for r in results]


@router.get("/machines", response_model=list[MachineSchema])
async def list_machines(
    plant_id: str = Query(...), service: ReferenceDataService = Depends(get_reference_data_service)
) -> list[MachineSchema]:
    results = await service.list_machines(plant_id)
    return [MachineSchema.model_validate(r) for r in results]


@router.get("/products", response_model=list[ProductSchema])
async def list_products(
    organization_id: str = Query(...), service: ReferenceDataService = Depends(get_reference_data_service)
) -> list[ProductSchema]:
    results = await service.list_products(organization_id)
    return [ProductSchema.model_validate(r) for r in results]


@router.get("/processes", response_model=list[ProcessSchema])
async def list_processes(
    organization_id: str = Query(...), service: ReferenceDataService = Depends(get_reference_data_service)
) -> list[ProcessSchema]:
    results = await service.list_processes(organization_id)
    return [ProcessSchema.model_validate(r) for r in results]


@router.get("/operations", response_model=list[OperationSchema])
async def list_operations(
    process_id: str = Query(...), service: ReferenceDataService = Depends(get_reference_data_service)
) -> list[OperationSchema]:
    results = await service.list_operations(process_id)
    return [OperationSchema.model_validate(r) for r in results]


@router.get("/parameters", response_model=list[ParameterSchema])
async def list_parameters(
    service: ReferenceDataService = Depends(get_reference_data_service),
) -> list[ParameterSchema]:
    results = await service.list_parameters()
    return [ParameterSchema.model_validate(r) for r in results]


@router.get("/specification", response_model=Optional[SpecificationRefSchema])
async def get_effective_specification(
    parameter_id: str = Query(...),
    machine_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    operation_id: Optional[str] = Query(None),
    service: ReferenceDataService = Depends(get_reference_data_service),
) -> Optional[SpecificationRefSchema]:
    result = await service.get_effective_specification(parameter_id, machine_id, product_id, operation_id)
    return SpecificationRefSchema.model_validate(result) if result else None


@router.post("/specifications", response_model=SpecificationRefSchema)
async def create_specification(
    request: SpecificationCreateRequest, service: ReferenceDataService = Depends(get_reference_data_service)
) -> SpecificationRefSchema:
    result = await service.create_specification(
        parameter_id=request.parameter_id, lsl=request.lsl, usl=request.usl, target=request.target,
        machine_id=request.machine_id, product_id=request.product_id, operation_id=request.operation_id,
        created_by=request.created_by,
    )
    return SpecificationRefSchema.model_validate(result)
