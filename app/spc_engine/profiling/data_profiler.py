"""Profiles a cleaned measurements DataFrame before subgrouping/chart
selection, so downstream engine stages and the API response can report
what the dataset actually looks like.
"""

from __future__ import annotations

import pandas as pd

from app.spc_engine.core.models import DataProfile


def _nunique(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0
    return int(df[column].dropna().nunique())


def _candidate_subgroup_sizes(valid_count: int) -> list[int]:
    """Suggest subgroup sizes that evenly (or near-evenly) divide the valid
    observation count, restricted to the sizes the constants table supports."""
    if valid_count < 2:
        return []
    candidates = []
    for n in (2, 3, 4, 5, 6, 8, 10):
        if valid_count // n >= 2:
            candidates.append(n)
    return candidates


def profile_dataset(df: pd.DataFrame) -> DataProfile:
    total = int(len(df))
    valid_mask = df["value"].notna() if "value" in df.columns else pd.Series([], dtype=bool)
    valid = int(valid_mask.sum())
    invalid = total - valid

    parameters: list[str] = []
    if "parameter_id" in df.columns:
        parameters = sorted(str(v) for v in df["parameter_id"].dropna().unique())

    time_start = None
    time_end = None
    avg_interval = None
    if "event_timestamp" in df.columns:
        timestamps = pd.to_datetime(df["event_timestamp"], errors="coerce").dropna().sort_values()
        if len(timestamps) > 0:
            time_start = timestamps.iloc[0].to_pydatetime()
            time_end = timestamps.iloc[-1].to_pydatetime()
        if len(timestamps) > 1:
            deltas = timestamps.diff().dropna().dt.total_seconds()
            if len(deltas) > 0:
                avg_interval = float(deltas.mean())

    existing_subgroup_ids_detected = bool(
        "subgroup_hint" in df.columns and df["subgroup_hint"].notna().any()
    )

    return DataProfile(
        total_observations=total,
        valid_observations=valid,
        invalid_observations=invalid,
        unique_machines=_nunique(df, "machine_id"),
        unique_products=_nunique(df, "product_id"),
        unique_processes=_nunique(df, "process_id"),
        unique_operations=_nunique(df, "operation_id"),
        unique_parameters=_nunique(df, "parameter_id"),
        parameters=parameters,
        time_start=time_start,
        time_end=time_end,
        missing_values=invalid,
        existing_subgroup_ids_detected=existing_subgroup_ids_detected,
        potential_subgroup_sizes=_candidate_subgroup_sizes(valid),
        average_sampling_interval_seconds=avg_interval,
    )
