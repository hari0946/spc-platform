"""Row-level validation of a single measurement value, used both by the
ingestion validation pipeline (app/ingestion/validation_pipeline.py) and,
defensively, by the SPC engine's own data validator before any statistics
are computed.

This module intentionally only judges *data quality* (missing/invalid
numeric, invalid timestamp) -- it never flags a value as bad merely for
being a statistical outlier. Statistical unusualness is the SPC engine's
job to interpret (via control limits and rules), not the validator's job
to discard.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.spc_engine.core.enums import QualityStatus


def validate_numeric_value(raw_value: object) -> tuple[Optional[float], QualityStatus]:
    """Validate and coerce a raw measurement value.

    Returns (parsed_value, quality_status). parsed_value is None whenever
    quality_status is not VALID.
    """
    if raw_value is None:
        return None, QualityStatus.MISSING_VALUE

    if isinstance(raw_value, str) and raw_value.strip() == "":
        return None, QualityStatus.MISSING_VALUE

    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None, QualityStatus.INVALID_NUMERIC_VALUE

    if value != value:  # NaN check without importing math for one use
        return None, QualityStatus.MISSING_VALUE

    if value in (float("inf"), float("-inf")):
        return None, QualityStatus.INVALID_NUMERIC_VALUE

    return value, QualityStatus.VALID


def validate_timestamp(raw_timestamp: object) -> tuple[Optional[datetime], QualityStatus]:
    """Validate and coerce a raw event timestamp.

    Accepts datetime instances directly, or ISO-8601-ish strings (delegating
    to pandas at the ingestion layer for broader parsing -- this function
    stays stdlib-only and handles the already-parsed case plus the common
    string case).
    """
    if raw_timestamp is None:
        return None, QualityStatus.INVALID_TIMESTAMP

    if isinstance(raw_timestamp, datetime):
        return raw_timestamp, QualityStatus.VALID

    if isinstance(raw_timestamp, str):
        text = raw_timestamp.strip()
        if not text:
            return None, QualityStatus.INVALID_TIMESTAMP
        try:
            return datetime.fromisoformat(text), QualityStatus.VALID
        except ValueError:
            return None, QualityStatus.INVALID_TIMESTAMP

    return None, QualityStatus.INVALID_TIMESTAMP


def validate_unit(raw_unit: Optional[str], expected_unit: Optional[str]) -> QualityStatus:
    """Compares a row's unit against the parameter's canonical unit.

    Missing unit is not automatically invalid (some source systems omit it
    when it is implicit); a present-but-mismatched unit is always invalid,
    since silently mixing e.g. mm and inch would corrupt SPC statistics.
    """
    if raw_unit is None or raw_unit.strip() == "":
        return QualityStatus.VALID
    if expected_unit is None:
        return QualityStatus.VALID
    if raw_unit.strip().lower() != expected_unit.strip().lower():
        return QualityStatus.INVALID_UNIT
    return QualityStatus.VALID
