"""Validates that a cleaned measurements DataFrame is fit to run through the
SPC engine at all -- distinct from row-level measurement validation, this
checks dataset-level preconditions (required columns present, minimum
sample size, single manufacturing context).
"""

from __future__ import annotations

import pandas as pd

from app.spc_engine.core.exceptions import IncompatibleContextError, InsufficientDataError

REQUIRED_COLUMNS = ("value",)
CONTEXT_COLUMNS = (
    "machine_id",
    "product_id",
    "process_id",
    "operation_id",
    "parameter_id",
)


def validate_required_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise InsufficientDataError(
            f"Measurement dataset is missing required column(s): {', '.join(missing)}."
        )


def validate_minimum_sample_size(df: pd.DataFrame, minimum_sample_size: int) -> None:
    valid_count = int(df["value"].notna().sum())
    if valid_count < minimum_sample_size:
        raise InsufficientDataError(
            f"Only {valid_count} valid observation(s) available; "
            f"minimum required for SPC analysis is {minimum_sample_size}."
        )


def validate_single_context(df: pd.DataFrame) -> None:
    """SPC statistics (mean, sigma, control limits) are only meaningful for
    a single, homogeneous manufacturing context. A caller that wants to
    analyze multiple machines/parameters must run the engine once per
    context -- the engine itself refuses to silently blend contexts."""
    for column in CONTEXT_COLUMNS:
        if column not in df.columns:
            continue
        distinct = df[column].dropna().unique()
        if len(distinct) > 1:
            raise IncompatibleContextError(
                f"Dataset contains {len(distinct)} distinct values for '{column}' "
                f"({sorted(str(v) for v in distinct)}); SPC analysis requires a single "
                f"homogeneous manufacturing context. Filter the dataset per context first."
            )


def validate_dataset(df: pd.DataFrame, minimum_sample_size: int) -> None:
    validate_required_columns(df)
    validate_single_context(df)
    validate_minimum_sample_size(df, minimum_sample_size)
