"""Shared pytest fixtures.

The SPC engine test suite (tests/spc_engine/) needs no database connection
at all -- fixtures here are limited to small, reusable data builders.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest


def make_measurements_df(
    n: int = 100,
    mean: float = 20.0,
    sigma: float = 0.01,
    seed: int = 7,
    start: datetime | None = None,
    interval_seconds: int = 300,
    machine_id: str = "CNC_01",
    product_id: str = "PART_A",
    process_id: str = "MACHINING",
    operation_id: str = "OP_10",
    parameter_id: str = "SHAFT_DIAMETER",
) -> pd.DataFrame:
    rng = random.Random(seed)
    start = start or datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(n):
        rows.append(
            {
                "value": rng.gauss(mean, sigma) if sigma > 0 else mean,
                "event_timestamp": start + timedelta(seconds=interval_seconds * i),
                "machine_id": machine_id,
                "product_id": product_id,
                "process_id": process_id,
                "operation_id": operation_id,
                "parameter_id": parameter_id,
                "batch_id": None,
                "subgroup_id": None,
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture
def measurements_df_factory():
    return make_measurements_df
