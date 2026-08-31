"""One-time seed of the manufacturing-context reference data that
var/demo/historical.csv (and var/demo/current.csv, if present) assume
already exist: organization, plant, machine (CNC_01), product (PART_A),
process/operation (OP_10), parameter (SHAFT_DIAMETER), its specification,
and an SPC configuration.

There is no create-via-API path for this reference data by design (see
app/api/routes/reference_data.py -- GET-only, master data is managed
directly), so this script is the intended way to seed it once against a
target database. Safe to run against an empty database; not idempotent
(re-running against a database that already has this context will create
a duplicate machine/product/etc., since codes aren't checked first) --
run it exactly once per environment.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.database.postgres.connection import close_pool, create_pool
from app.repositories.machine_repository import MachineRepository
from app.repositories.operation_repository import OperationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.plant_repository import PlantRepository
from app.repositories.process_repository import ProcessRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.specification_repository import SpecificationRepository
from app.repositories.spc_configuration_repository import SPCConfigurationRepository


async def main() -> None:
    settings = get_settings()
    await create_pool(settings)

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

    print(f"organization_id={org['organization_id']}  ({org['name']})")
    print(f"plant_id={plant['plant_id']}  ({plant['name']})")
    print(f"machine_id={machine['machine_id']}  ({machine['name']} / {machine['code']})")
    print(f"product_id={product['product_id']}  ({product['name']} / {product['part_number']})")
    print(f"process_id={process['process_id']}  ({process['name']})")
    print(f"operation_id={operation['operation_id']}  ({operation['name']} / {operation['code']})")
    print(f"parameter_id={parameter['parameter_id']}  ({parameter['name']}, unit={parameter['unit']})")
    print("Specification: LSL=19.94 USL=20.06 Target=20.0")
    print("SPC configuration: AUTO chart, subgroup size 5, CONSECUTIVE method")

    await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
