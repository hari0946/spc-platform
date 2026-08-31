"""Rational subgrouping engine.

Implements the four supported subgroup formation strategies described in
the platform's SPC design: EXISTING_ID, FIXED_SIZE, CONSECUTIVE, and
TIME_WINDOW. A subgroup never mixes incompatible manufacturing contexts
(machine/product/process/operation/parameter) -- see subgroup_validator.

Design note on unequal subgroup sizes: CONSECUTIVE and TIME_WINDOW can
legitimately produce a smaller-than-configured trailing subgroup when a
time-gap boundary or the end of the dataset is reached before subgroup_size
readings accumulate. Rather than silently mixing subgroup sizes into a
single set of Shewhart constants (which assumes constant n), this module
returns every subgroup it forms, unmodified; it is the chart layer's
responsibility (see charts/base_chart.py) to select the dominant subgroup
size for control-limit estimation and report the rest as excluded, with a
warning surfaced to the caller.
"""

from __future__ import annotations

import statistics
import uuid
from datetime import datetime, timedelta

from app.spc_engine.core.enums import SubgroupMethod
from app.spc_engine.core.exceptions import InvalidSubgroupSizeError
from app.spc_engine.core.models import MeasurementRecord, Subgroup
from app.spc_engine.subgrouping.subgroup_validator import validate_subgroup_context


def _sort_records(records: list[MeasurementRecord]) -> list[MeasurementRecord]:
    has_all_timestamps = all(r.event_timestamp is not None for r in records)
    if has_all_timestamps:
        return sorted(records, key=lambda r: (r.event_timestamp, r.row_number))
    return sorted(records, key=lambda r: r.row_number)


def _build_subgroup(records: list[MeasurementRecord], subgroup_id: str) -> Subgroup:
    validate_subgroup_context(records)
    values = [r.value for r in records]
    timestamps = [r.event_timestamp for r in records if r.event_timestamp is not None]
    mean = statistics.fmean(values)
    range_ = max(values) - min(values)
    std_dev = statistics.stdev(values) if len(values) > 1 else None
    return Subgroup(
        subgroup_id=subgroup_id,
        indices=[r.row_number for r in records],
        values=values,
        mean=mean,
        range_=range_,
        std_dev=std_dev,
        count=len(values),
        start_timestamp=min(timestamps) if timestamps else None,
        end_timestamp=max(timestamps) if timestamps else None,
    )


def _form_existing_id(records: list[MeasurementRecord]) -> list[Subgroup]:
    if any(r.subgroup_hint is None for r in records):
        raise InvalidSubgroupSizeError(
            "Subgroup method EXISTING_ID requires every measurement to carry a "
            "subgroup identifier, but at least one record does not have one."
        )
    buckets: dict[str, list[MeasurementRecord]] = {}
    for record in records:
        buckets.setdefault(record.subgroup_hint, []).append(record)
    return [_build_subgroup(recs, hint) for hint, recs in buckets.items()]


def _form_fixed_size(records: list[MeasurementRecord], subgroup_size: int) -> list[Subgroup]:
    ordered = _sort_records(records)
    subgroups: list[Subgroup] = []
    for start in range(0, len(ordered), subgroup_size):
        chunk = ordered[start : start + subgroup_size]
        if len(chunk) < subgroup_size:
            break  # incomplete trailing chunk is dropped for FIXED_SIZE
        subgroups.append(_build_subgroup(chunk, f"SG-{len(subgroups) + 1:05d}"))
    return subgroups


def _form_consecutive(
    records: list[MeasurementRecord], subgroup_size: int, maximum_time_gap_seconds: int
) -> list[Subgroup]:
    ordered = _sort_records(records)
    max_gap = timedelta(seconds=maximum_time_gap_seconds)
    subgroups: list[Subgroup] = []
    current: list[MeasurementRecord] = []

    def flush() -> None:
        if current:
            subgroups.append(_build_subgroup(list(current), f"SG-{len(subgroups) + 1:05d}"))
            current.clear()

    previous_timestamp: datetime | None = None
    for record in ordered:
        gap_exceeded = (
            previous_timestamp is not None
            and record.event_timestamp is not None
            and (record.event_timestamp - previous_timestamp) > max_gap
        )
        if gap_exceeded:
            flush()
        current.append(record)
        if len(current) >= subgroup_size:
            flush()
        previous_timestamp = record.event_timestamp
    flush()
    return subgroups


def _form_time_window(
    records: list[MeasurementRecord], subgroup_size: int, maximum_time_gap_seconds: int
) -> list[Subgroup]:
    ordered = [r for r in _sort_records(records) if r.event_timestamp is not None]
    if not ordered:
        raise InvalidSubgroupSizeError(
            "Subgroup method TIME_WINDOW requires event timestamps, but none of the "
            "supplied measurements have one."
        )
    window = timedelta(seconds=maximum_time_gap_seconds)
    subgroups: list[Subgroup] = []
    window_start = ordered[0].event_timestamp
    current: list[MeasurementRecord] = []

    def flush() -> None:
        if current:
            subgroups.append(_build_subgroup(list(current), f"SG-{len(subgroups) + 1:05d}"))
            current.clear()

    for record in ordered:
        if record.event_timestamp - window_start > window or len(current) >= subgroup_size:
            flush()
            window_start = record.event_timestamp
        current.append(record)
    flush()
    return subgroups


def form_subgroups(
    records: list[MeasurementRecord],
    method: SubgroupMethod,
    subgroup_size: int,
    maximum_time_gap_seconds: int,
) -> list[Subgroup]:
    """Form rational subgroups from a flat list of measurement records
    belonging to a single, already-validated manufacturing context."""
    if subgroup_size < 1:
        raise InvalidSubgroupSizeError(f"subgroup_size must be >= 1, got {subgroup_size}.")

    if subgroup_size == 1:
        # Individuals (I-MR): every observation is its own singleton subgroup,
        # preserving chronological (or row) order.
        ordered = _sort_records(records)
        return [_build_subgroup([r], f"SG-{i + 1:05d}") for i, r in enumerate(ordered)]

    if method == SubgroupMethod.EXISTING_ID:
        return _form_existing_id(records)
    if method == SubgroupMethod.FIXED_SIZE:
        return _form_fixed_size(records, subgroup_size)
    if method == SubgroupMethod.CONSECUTIVE:
        return _form_consecutive(records, subgroup_size, maximum_time_gap_seconds)
    if method == SubgroupMethod.TIME_WINDOW:
        return _form_time_window(records, subgroup_size, maximum_time_gap_seconds)

    raise InvalidSubgroupSizeError(f"Unsupported subgroup method: {method}")


def new_subgroup_id() -> str:
    return f"SG-{uuid.uuid4().hex[:10]}"
