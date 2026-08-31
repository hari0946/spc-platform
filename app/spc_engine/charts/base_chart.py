"""Common interface and shared helpers for all control chart implementations.

Every concrete chart (xbar_r.py, xbar_s.py, imr.py) implements
`calculate(subgroups) -> ChartResult` and shares the "dominant subgroup
size" filtering logic here, since real-world rational subgrouping (see
subgroup_engine.py) can legitimately produce a few non-conforming
subgroups at context/time-gap boundaries.
"""

from __future__ import annotations

import statistics
from abc import ABC, abstractmethod
from collections import Counter

from app.spc_engine.core.exceptions import InvalidSubgroupSizeError
from app.spc_engine.core.models import ChartResult, Subgroup


class BaseChart(ABC):
    """Interface implemented by XbarRChart, XbarSChart, and ImrChart."""

    @abstractmethod
    def calculate(self, subgroups: list[Subgroup]) -> tuple[ChartResult, list[str]]:
        """Compute control limits and per-point chart data.

        Returns (ChartResult, warnings) -- warnings communicate things like
        excluded non-conforming subgroups without raising an exception.
        """
        raise NotImplementedError


def select_conforming_subgroups(subgroups: list[Subgroup]) -> tuple[list[Subgroup], int, list[str]]:
    """Pick the dominant (modal) subgroup size and keep only subgroups that
    match it, since classic Shewhart Xbar-R/Xbar-S formulas assume a
    constant subgroup size n for their A2/A3/D3/D4/B3/B4 constants.

    Returns (conforming_subgroups, subgroup_size_used, warnings).
    """
    if not subgroups:
        raise InvalidSubgroupSizeError("No subgroups were supplied to the chart engine.")

    size_counts = Counter(sg.count for sg in subgroups)
    modal_size, modal_count = size_counts.most_common(1)[0]

    conforming = [sg for sg in subgroups if sg.count == modal_size]
    excluded = [sg for sg in subgroups if sg.count != modal_size]

    warnings: list[str] = []
    if excluded:
        excluded_sizes = sorted({sg.count for sg in excluded})
        warnings.append(
            f"{len(excluded)} of {len(subgroups)} subgroup(s) had a size other than the "
            f"dominant subgroup size ({modal_size}) -- sizes {excluded_sizes} were excluded "
            f"from control limit estimation to keep constants valid for a constant n. "
            f"This typically happens at time-gap boundaries or dataset edges."
        )
    return conforming, modal_size, warnings


def grand_mean_of_means(subgroups: list[Subgroup]) -> float:
    return statistics.fmean(sg.mean for sg in subgroups)
