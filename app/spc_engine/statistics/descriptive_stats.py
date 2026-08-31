"""Basic descriptive statistics over the raw (individual) valid observations
-- independent of subgrouping. Uses sample statistics (ddof=1) throughout,
consistent with overall-sigma estimation elsewhere in the engine.
"""

from __future__ import annotations

import statistics

from app.spc_engine.core.exceptions import InsufficientDataError
from app.spc_engine.core.models import DescriptiveStatistics


def calculate_descriptive_statistics(values: list[float]) -> DescriptiveStatistics:
    if not values:
        raise InsufficientDataError("Cannot calculate descriptive statistics on an empty dataset.")

    return DescriptiveStatistics(
        mean=statistics.fmean(values),
        minimum=min(values),
        maximum=max(values),
        count=len(values),
        median=statistics.median(values),
        range_=max(values) - min(values),
    )
