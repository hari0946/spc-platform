"""Configurable CSV column mapping.

Different automotive clients export CSVs with wildly different column
names for the same concept (DATE_TIME vs. Timestamp vs. event_time). This
module renames a raw DataFrame's columns to this platform's canonical
internal field names, driven entirely by a mapping dict supplied with the
upload -- never by guessing or hardcoding a specific client's column names.

Canonical internal fields produced here (consumed by validation_pipeline.py
and transformation_pipeline.py downstream):
    event_timestamp, machine_code, product_code, operation_code,
    parameter_name, value, unit, batch_id, subgroup_id, shift, operator_id
"""

from __future__ import annotations

import pandas as pd

from app.core.exceptions import ValidationError

CANONICAL_FIELDS = (
    "event_timestamp",
    "machine_code",
    "product_code",
    "operation_code",
    "parameter_name",
    "value",
    "unit",
    "batch_id",
    "subgroup_id",
    "shift",
    "operator_id",
)

REQUIRED_CANONICAL_FIELDS = ("parameter_name", "value")

# Identity default: assumes the source CSV already uses canonical field
# names. Any client-specific mapping supplied on upload fully overrides
# this (see uploads.column_mapping).
DEFAULT_MAPPING: dict[str, str] = {field: field for field in CANONICAL_FIELDS}


def apply_column_mapping(df: pd.DataFrame, column_mapping: dict[str, str]) -> pd.DataFrame:
    """`column_mapping` maps SOURCE column name -> CANONICAL field name,
    e.g. {"DATE_TIME": "event_timestamp", "MEASURED_VALUE": "value"}.
    """
    mapping = column_mapping or DEFAULT_MAPPING

    unknown_targets = set(mapping.values()) - set(CANONICAL_FIELDS)
    if unknown_targets:
        raise ValidationError(f"Column mapping targets unknown canonical field(s): {sorted(unknown_targets)}")

    missing_source_columns = [src for src in mapping if src not in df.columns]
    if missing_source_columns:
        raise ValidationError(
            f"Column mapping references source column(s) not present in the uploaded file: "
            f"{missing_source_columns}. Available columns: {list(df.columns)}"
        )

    mapped = df.rename(columns=mapping)
    mapped = mapped[[c for c in mapped.columns if c in CANONICAL_FIELDS]]

    missing_required = [f for f in REQUIRED_CANONICAL_FIELDS if f not in mapped.columns]
    if missing_required:
        raise ValidationError(
            f"Column mapping does not produce required field(s): {missing_required}. "
            f"Every upload must map a source column to each of: {REQUIRED_CANONICAL_FIELDS}."
        )

    for field in CANONICAL_FIELDS:
        if field not in mapped.columns:
            mapped[field] = None

    return mapped[list(CANONICAL_FIELDS)]
