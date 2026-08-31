"""Resolves human-readable codes (machine name, part number, operation
code, parameter name) from the validated CSV into the platform's internal
UUIDs, and reshapes the DataFrame into the Silver measurement schema.

This is the one ingestion module that talks to PostgreSQL (via
repositories) -- it is the boundary where "raw client vocabulary" becomes
"this platform's canonical manufacturing context IDs". A code that cannot
be resolved does not crash the pipeline: the row's quality_status is
downgraded to INVALID_CONTEXT and it is excluded from SPC analysis while
remaining visible/traceable.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from app.core.logging import get_logger
from app.repositories.machine_repository import MachineRepository
from app.repositories.operation_repository import OperationRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.product_repository import ProductRepository
from app.spc_engine.core.enums import QualityStatus

logger = get_logger(__name__)


class UploadContext:
    """Default manufacturing context supplied at upload time, used to scope
    code resolution (e.g. a machine code is only meaningful within a plant)
    and to fill in context that a CSV export doesn't repeat per row."""

    def __init__(
        self,
        organization_id: Optional[str] = None,
        plant_id: Optional[str] = None,
        production_line_id: Optional[str] = None,
    ) -> None:
        self.organization_id = organization_id
        self.plant_id = plant_id
        self.production_line_id = production_line_id


class ContextResolver:
    def __init__(
        self,
        machine_repository: MachineRepository,
        product_repository: ProductRepository,
        operation_repository: OperationRepository,
        parameter_repository: ParameterRepository,
    ) -> None:
        self._machine_repository = machine_repository
        self._product_repository = product_repository
        self._operation_repository = operation_repository
        self._parameter_repository = parameter_repository
        self._machine_cache: dict[str, Optional[dict[str, Any]]] = {}
        self._product_cache: dict[str, Optional[dict[str, Any]]] = {}
        self._operation_cache: dict[str, Optional[dict[str, Any]]] = {}
        self._parameter_cache: dict[str, Optional[dict[str, Any]]] = {}

    async def resolve_machine(self, plant_id: Optional[str], code: Optional[str]) -> Optional[dict[str, Any]]:
        if not code or not plant_id:
            return None
        key = f"{plant_id}:{code}"
        if key not in self._machine_cache:
            self._machine_cache[key] = await self._machine_repository.get_by_code(plant_id, code)
        return self._machine_cache[key]

    async def resolve_product(self, organization_id: Optional[str], code: Optional[str]) -> Optional[dict[str, Any]]:
        if not code or not organization_id:
            return None
        key = f"{organization_id}:{code}"
        if key not in self._product_cache:
            self._product_cache[key] = await self._product_repository.get_by_part_number(organization_id, code)
        return self._product_cache[key]

    async def resolve_operation(self, organization_id: Optional[str], code: Optional[str]) -> Optional[dict[str, Any]]:
        if not code or not organization_id:
            return None
        key = f"{organization_id}:{code}"
        if key not in self._operation_cache:
            self._operation_cache[key] = await self._operation_repository.find_by_code_in_organization(
                organization_id, code
            )
        return self._operation_cache[key]

    async def resolve_parameter(self, name: Optional[str]) -> Optional[dict[str, Any]]:
        if not name:
            return None
        if name not in self._parameter_cache:
            self._parameter_cache[name] = await self._parameter_repository.get_by_name(name)
        return self._parameter_cache[name]


async def run_transformation_pipeline(
    df: pd.DataFrame, upload_context: UploadContext, resolver: ContextResolver
) -> pd.DataFrame:
    """Input: validated DataFrame (from validation_pipeline.run_validation_pipeline),
    with canonical fields + quality_status/validation_notes. Output: a
    DataFrame shaped for Snowflake SILVER.MEASUREMENTS."""
    records: list[dict[str, Any]] = []

    for _, row in df.iterrows():
        quality_status = row["quality_status"]
        validation_notes = row.get("validation_notes") or ""

        machine = await resolver.resolve_machine(upload_context.plant_id, row.get("machine_code"))
        product = await resolver.resolve_product(upload_context.organization_id, row.get("product_code"))
        operation = await resolver.resolve_operation(upload_context.organization_id, row.get("operation_code"))
        parameter = await resolver.resolve_parameter(row.get("parameter_name"))

        if quality_status == QualityStatus.VALID.value and parameter is None:
            quality_status = QualityStatus.INVALID_CONTEXT.value
            validation_notes = (
                f"Unknown parameter '{row.get('parameter_name')}'; no matching parameter is configured."
            )
        elif quality_status == QualityStatus.VALID.value and row.get("machine_code") and machine is None:
            quality_status = QualityStatus.INVALID_CONTEXT.value
            validation_notes = f"Unknown machine code '{row.get('machine_code')}' for the configured plant."
        elif quality_status == QualityStatus.VALID.value and row.get("product_code") and product is None:
            quality_status = QualityStatus.INVALID_CONTEXT.value
            validation_notes = f"Unknown product/part number '{row.get('product_code')}'."
        elif quality_status == QualityStatus.VALID.value and row.get("operation_code") and operation is None:
            quality_status = QualityStatus.INVALID_CONTEXT.value
            validation_notes = f"Unknown operation code '{row.get('operation_code')}'."

        records.append(
            {
                "event_timestamp": row.get("event_timestamp"),
                "organization_id": upload_context.organization_id,
                "plant_id": upload_context.plant_id,
                "production_line_id": upload_context.production_line_id,
                "machine_id": machine["machine_id"] if machine else None,
                "product_id": product["product_id"] if product else None,
                "process_id": operation["process_id"] if operation else None,
                "operation_id": operation["operation_id"] if operation else None,
                "parameter_id": parameter["parameter_id"] if parameter else None,
                "measurement_value": row.get("value"),
                "unit": row.get("unit") or (parameter["unit"] if parameter else None),
                "batch_id": row.get("batch_id"),
                "subgroup_id": row.get("subgroup_id"),
                "shift": row.get("shift"),
                "operator_id": row.get("operator_id"),
                "quality_status": quality_status,
                "validation_notes": validation_notes,
            }
        )

    silver_df = pd.DataFrame.from_records(records)
    invalid_count = int((silver_df["quality_status"] != QualityStatus.VALID.value).sum())
    logger.info("transformation_completed", total_rows=len(silver_df), invalid_rows=invalid_count)
    return silver_df
