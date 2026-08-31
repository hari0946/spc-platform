"""Thin service wrapping SPCConfigurationRepository (and its associated
rule_configurations) for the /spc/configurations API. Kept as a service --
rather than letting the route call the repository directly -- so the
Route -> Service -> Repository boundary stays consistent across the whole
API, even for straightforward CRUD.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.exceptions import NotFoundError
from app.repositories.spc_configuration_repository import SPCConfigurationRepository


class SPCConfigurationService:
    def __init__(self, spc_configuration_repository: SPCConfigurationRepository) -> None:
        self._repository = spc_configuration_repository

    async def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._repository.create(
            parameter_id=payload["parameter_id"],
            chart_type=payload["chart_type"],
            subgroup_size=payload["subgroup_size"],
            subgroup_method=payload["subgroup_method"],
            maximum_time_gap_seconds=payload["maximum_time_gap_seconds"],
            minimum_sample_size=payload["minimum_sample_size"],
            ruleset=[r.model_dump() if hasattr(r, "model_dump") else r for r in payload.get("ruleset", [])],
            machine_id=payload.get("machine_id"),
            product_id=payload.get("product_id"),
            operation_id=payload.get("operation_id"),
            sigma_method=payload.get("sigma_method", "WITHIN_OVERALL"),
            capability_method=payload.get("capability_method", "STANDARD"),
        )

    async def get_by_id(self, spc_configuration_id: str) -> dict[str, Any]:
        result = await self._repository.get_by_id(spc_configuration_id)
        if result is None:
            raise NotFoundError(f"SPC configuration {spc_configuration_id} not found.")
        return result

    async def get_effective(
        self,
        parameter_id: str,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        return await self._repository.get_effective_configuration(parameter_id, machine_id, product_id, operation_id)

    async def list_all(self) -> list[dict[str, Any]]:
        return await self._repository.list_all()

    async def update(self, spc_configuration_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        if "ruleset" in clean_updates:
            clean_updates["ruleset"] = [
                r.model_dump() if hasattr(r, "model_dump") else r for r in clean_updates["ruleset"]
            ]
        return await self._repository.update(spc_configuration_id, clean_updates)
