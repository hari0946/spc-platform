"""Thin read-only service over the manufacturing-context repositories,
backing the frontend's context-selection dropdowns. No business logic --
kept as a service purely to preserve the Route -> Service -> Repository
boundary consistently across the whole API (see spc_configuration_service.py
for the same rationale on another simple-CRUD resource).
"""

from __future__ import annotations

from typing import Any, Optional

from app.repositories.machine_repository import MachineRepository
from app.repositories.operation_repository import OperationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.plant_repository import PlantRepository
from app.repositories.process_repository import ProcessRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.specification_repository import SpecificationRepository


class ReferenceDataService:
    def __init__(
        self,
        organization_repository: OrganizationRepository,
        plant_repository: PlantRepository,
        machine_repository: MachineRepository,
        product_repository: ProductRepository,
        process_repository: ProcessRepository,
        operation_repository: OperationRepository,
        parameter_repository: ParameterRepository,
        specification_repository: SpecificationRepository,
    ) -> None:
        self._organization_repository = organization_repository
        self._plant_repository = plant_repository
        self._machine_repository = machine_repository
        self._product_repository = product_repository
        self._process_repository = process_repository
        self._operation_repository = operation_repository
        self._parameter_repository = parameter_repository
        self._specification_repository = specification_repository

    async def list_organizations(self) -> list[dict[str, Any]]:
        return await self._organization_repository.list_all()

    async def list_plants(self, organization_id: str) -> list[dict[str, Any]]:
        return await self._plant_repository.list_by_organization(organization_id)

    async def list_machines(self, plant_id: str) -> list[dict[str, Any]]:
        return await self._machine_repository.list_by_plant(plant_id)

    async def list_products(self, organization_id: str) -> list[dict[str, Any]]:
        return await self._product_repository.list_by_organization(organization_id)

    async def list_processes(self, organization_id: str) -> list[dict[str, Any]]:
        return await self._process_repository.list_by_organization(organization_id)

    async def list_operations(self, process_id: str) -> list[dict[str, Any]]:
        return await self._operation_repository.list_by_process(process_id)

    async def list_parameters(self) -> list[dict[str, Any]]:
        return await self._parameter_repository.list_all()

    async def get_effective_specification(
        self,
        parameter_id: str,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        return await self._specification_repository.get_effective_specification(
            parameter_id, machine_id, product_id, operation_id
        )

    async def create_specification(
        self,
        parameter_id: str,
        lsl: Optional[float],
        usl: Optional[float],
        target: Optional[float] = None,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> dict[str, Any]:
        return await self._specification_repository.create(
            parameter_id=parameter_id, lsl=lsl, usl=usl, target=target,
            machine_id=machine_id, product_id=product_id, operation_id=operation_id, created_by=created_by,
        )
