"""Validates that a proposed subgrouping is safe to hand to a chart
implementation: no incompatible contexts mixed within a subgroup, and every
subgroup has the minimum size a chart type requires.
"""

from __future__ import annotations

from app.spc_engine.core.exceptions import IncompatibleContextError, InvalidSubgroupSizeError
from app.spc_engine.core.models import MeasurementRecord, Subgroup

_CONTEXT_FIELDS = ("machine_id", "product_id", "process_id", "operation_id", "parameter_id")


def validate_subgroup_context(records: list[MeasurementRecord]) -> None:
    """Never mix incompatible manufacturing contexts inside one subgroup."""
    if not records:
        return
    for field_name in _CONTEXT_FIELDS:
        values = {getattr(r, field_name) for r in records if getattr(r, field_name) is not None}
        if len(values) > 1:
            raise IncompatibleContextError(
                f"Cannot form a subgroup mixing distinct values of '{field_name}': {sorted(values)}."
            )


def validate_subgroups_not_empty(subgroups: list[Subgroup]) -> None:
    if not subgroups:
        raise InvalidSubgroupSizeError("Subgrouping produced zero subgroups from the supplied data.")


def validate_minimum_subgroup_count(subgroups: list[Subgroup], minimum: int = 2) -> None:
    if len(subgroups) < minimum:
        raise InvalidSubgroupSizeError(
            f"At least {minimum} subgroups are required to estimate control limits; "
            f"only {len(subgroups)} were formed."
        )
