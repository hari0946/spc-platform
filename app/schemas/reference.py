"""Read-only response schemas for manufacturing context master data
(organizations, plants, machines, products, processes, operations,
parameters). These back the frontend's context-selection dropdowns --
there is no create/update surface here; master data is provisioned
out-of-band (see repositories/*_repository.py for the underlying writes,
used by seed/admin scripts, not by these routes).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.schemas.common import APIModel


class OrganizationSchema(APIModel):
    organization_id: str
    name: str
    code: str
    description: Optional[str] = None
    active: bool


class PlantSchema(APIModel):
    plant_id: str
    organization_id: str
    name: str
    code: str
    timezone: str
    country: Optional[str] = None
    active: bool


class MachineSchema(APIModel):
    machine_id: str
    plant_id: str
    production_line_id: Optional[str] = None
    name: str
    code: str
    machine_type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    active: bool


class ProductSchema(APIModel):
    product_id: str
    organization_id: str
    part_number: str
    name: str
    description: Optional[str] = None
    revision: Optional[str] = None
    active: bool


class ProcessSchema(APIModel):
    process_id: str
    organization_id: str
    name: str
    code: str
    description: Optional[str] = None
    active: bool


class OperationSchema(APIModel):
    operation_id: str
    process_id: str
    name: str
    code: str
    sequence_number: Optional[int] = None
    description: Optional[str] = None
    active: bool


class ParameterSchema(APIModel):
    parameter_id: str
    name: str
    description: Optional[str] = None
    data_type: str
    unit: str
    target_value: Optional[float] = None
    active: bool


class SpecificationCreateRequest(APIModel):
    parameter_id: str
    lsl: Optional[float] = None
    usl: Optional[float] = None
    target: Optional[float] = None
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    operation_id: Optional[str] = None
    created_by: Optional[str] = None


class SpecificationRefSchema(APIModel):
    specification_id: str
    parameter_id: str
    machine_id: Optional[str] = None
    product_id: Optional[str] = None
    operation_id: Optional[str] = None
    lsl: Optional[float] = None
    usl: Optional[float] = None
    target: Optional[float] = None
    effective_from: datetime
    effective_to: Optional[datetime] = None
    status: str
