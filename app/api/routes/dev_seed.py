"""TEMPORARY, one-shot route to seed the demo manufacturing-context
reference data (matching var/demo/historical.csv) into a fresh database.

There is no create-via-API path for organizations/plants/machines/etc. by
design (see reference_data.py -- GET-only, master data managed directly),
so this exists purely to seed a brand-new deployment once, over HTTPS,
without exposing the database itself. Remove this file and its
registration in app/main.py immediately after the one call this is meant
for -- it has no guard against being called twice (would create a
duplicate machine/product/etc.) and no auth of its own.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.repositories.machine_repository import MachineRepository
from app.repositories.operation_repository import OperationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.plant_repository import PlantRepository
from app.repositories.process_repository import ProcessRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.spc_configuration_repository import SPCConfigurationRepository
from app.repositories.specification_repository import SpecificationRepository

router = APIRouter(prefix="/dev", tags=["dev-temporary"])


@router.post("/seed-demo-reference-data")
async def seed_demo_reference_data() -> dict:
    org_repo, plant_repo, machine_repo = OrganizationRepository(), PlantRepository(), MachineRepository()
    product_repo, process_repo, operation_repo = ProductRepository(), ProcessRepository(), OperationRepository()
    parameter_repo, spec_repo, config_repo = ParameterRepository(), SpecificationRepository(), SPCConfigurationRepository()

    org = await org_repo.create("Demo Automotive Inc", "DEMO")
    plant = await plant_repo.create(org["organization_id"], "Demo Plant 1", "PLANT1")
    machine = await machine_repo.create(plant["plant_id"], "CNC Machine 01", "CNC_01")
    product = await product_repo.create(org["organization_id"], "PART_A", "Demo Shaft")
    process = await process_repo.create(org["organization_id"], "Machining", "MACHINING")
    operation = await operation_repo.create(process["process_id"], "Turning Op 10", "OP_10", sequence_number=10)
    parameter = await parameter_repo.create("SHAFT_DIAMETER", unit="mm", description="Shaft outer diameter")
    await spec_repo.create(
        parameter["parameter_id"], lsl=19.94, usl=20.06, target=20.0,
        machine_id=machine["machine_id"], product_id=product["product_id"], operation_id=operation["operation_id"],
    )
    await config_repo.create(
        parameter_id=parameter["parameter_id"], chart_type="AUTO", subgroup_size=5,
        subgroup_method="CONSECUTIVE", maximum_time_gap_seconds=3600, minimum_sample_size=20,
        ruleset=[{"rule_name": "POINT_OUTSIDE_LIMITS", "enabled": True, "severity": "CRITICAL", "parameters": {}}],
        machine_id=machine["machine_id"], product_id=product["product_id"], operation_id=operation["operation_id"],
    )

    return {
        "organization": {"id": org["organization_id"], "name": org["name"]},
        "plant": {"id": plant["plant_id"], "name": plant["name"]},
        "machine": {"id": machine["machine_id"], "name": machine["name"], "code": machine["code"]},
        "product": {"id": product["product_id"], "name": product["name"], "code": product["code"]},
        "process": {"id": process["process_id"], "name": process["name"]},
        "operation": {"id": operation["operation_id"], "name": operation["name"], "code": operation["code"]},
        "parameter": {"id": parameter["parameter_id"], "name": parameter["name"], "unit": parameter["unit"]},
        "specification": {"lsl": 19.94, "usl": 20.06, "target": 20.0},
    }
