"""Row-level validation and cleaning pipeline: takes the column-mapped raw
DataFrame and produces a DataFrame with two additional columns,
`quality_status` and `validation_notes`, per the pipeline described in the
platform design:

    Schema Validation -> Required Column Validation -> Data Type Validation
    -> Timestamp Validation -> Numeric Validation -> Duplicate Detection
    -> Unit Validation -> Context Validation -> Standardization
    -> Quality Status Assignment

IMPORTANT: this never discards a statistically unusual (but well-formed)
value. Only genuine data-quality problems (missing/invalid values,
duplicates, unit mismatches, missing required context) get a non-VALID
quality_status. Everything -- valid and invalid -- is preserved and
returned; only VALID rows should normally feed SPC calculations, but
INVALID rows remain traceable through Bronze/Silver.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from app.spc_engine.core.enums import QualityStatus
from app.spc_engine.validation.measurement_validator import (
    validate_numeric_value,
    validate_timestamp,
    validate_unit,
)


def _first_failing_status(statuses: list[QualityStatus]) -> QualityStatus:
    for status in statuses:
        if status != QualityStatus.VALID:
            return status
    return QualityStatus.VALID


def run_validation_pipeline(df: pd.DataFrame, expected_unit: Optional[str] = None) -> pd.DataFrame:
    df = df.copy()

    parsed_values: list[Optional[float]] = []
    parsed_timestamps: list = []
    row_statuses: list[QualityStatus] = []
    notes: list[str] = []

    for _, row in df.iterrows():
        statuses: list[QualityStatus] = []

        value, value_status = validate_numeric_value(row.get("value"))
        parsed_values.append(value)
        statuses.append(value_status)

        timestamp, timestamp_status = validate_timestamp(row.get("event_timestamp"))
        parsed_timestamps.append(timestamp)
        statuses.append(timestamp_status)

        unit_status = validate_unit(row.get("unit"), expected_unit)
        statuses.append(unit_status)

        if not row.get("parameter_name"):
            statuses.append(QualityStatus.INVALID_CONTEXT)

        final_status = _first_failing_status(statuses)
        row_statuses.append(final_status)
        notes.append("" if final_status == QualityStatus.VALID else final_status.value)

    df["value"] = parsed_values
    df["event_timestamp"] = parsed_timestamps
    df["quality_status"] = [s.value for s in row_statuses]
    df["validation_notes"] = notes

    df = _flag_duplicates(df)
    return df


def _flag_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """A duplicate is a row sharing the same (parameter, machine, product,
    operation, timestamp, value) as an earlier VALID row -- an exact
    re-submission, not merely two similar readings close in time."""
    dedup_columns = [
        c
        for c in ["parameter_name", "machine_code", "product_code", "operation_code", "event_timestamp", "value"]
        if c in df.columns
    ]
    is_duplicate = df.duplicated(subset=dedup_columns, keep="first")
    valid_mask = df["quality_status"] == QualityStatus.VALID.value
    duplicate_mask = is_duplicate & valid_mask

    df.loc[duplicate_mask, "quality_status"] = QualityStatus.DUPLICATE.value
    df.loc[duplicate_mask, "validation_notes"] = QualityStatus.DUPLICATE.value
    return df
