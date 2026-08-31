"""Sigma estimation engine.

Clearly separates two distinct estimates of process variation, which must
never be confused with each other:

  WITHIN sigma  - short-term, "common cause only" variation estimated from
                  rational subgroups (Rbar/d2 for XBAR-R, Sbar/c4 for
                  XBAR-S, MRbar/d2(span=2) for I-MR). This is what feeds
                  Cp/Cpk.

  OVERALL sigma - long-term variation: the sample standard deviation
                  (ddof=1) across ALL valid individual observations,
                  regardless of subgroup structure or subgroup conformance.
                  This is what feeds Pp/Ppk.
"""

from __future__ import annotations

import statistics

from app.spc_engine.core.constants import D2_MOVING_RANGE_2, get_constants
from app.spc_engine.core.enums import ChartType
from app.spc_engine.core.exceptions import InsufficientDataError
from app.spc_engine.core.models import SigmaEstimate, Subgroup


def estimate_overall_sigma(all_valid_values: list[float]) -> float:
    if len(all_valid_values) < 2:
        raise InsufficientDataError(
            "At least 2 valid individual observations are required to estimate overall sigma."
        )
    return statistics.stdev(all_valid_values)  # sample std dev, ddof=1


def estimate_within_sigma(
    chart_type: ChartType, conforming_subgroups: list[Subgroup], subgroup_size_used: int
) -> float:
    if chart_type == ChartType.XBAR_R:
        rbar = statistics.fmean(sg.range_ for sg in conforming_subgroups)
        d2 = get_constants(subgroup_size_used).d2
        return rbar / d2

    if chart_type == ChartType.XBAR_S:
        std_devs = [sg.std_dev for sg in conforming_subgroups if sg.std_dev is not None]
        sbar = statistics.fmean(std_devs)
        c4 = get_constants(subgroup_size_used).c4
        return sbar / c4

    if chart_type == ChartType.IMR:
        values = [sg.values[0] for sg in conforming_subgroups]
        if len(values) < 2:
            raise InsufficientDataError("I-MR within-sigma requires at least 2 individual observations.")
        moving_ranges = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
        mrbar = statistics.fmean(moving_ranges)
        return mrbar / D2_MOVING_RANGE_2

    raise ValueError(f"Unsupported chart type for within-sigma estimation: {chart_type}")


def estimate_sigma(
    chart_type: ChartType,
    conforming_subgroups: list[Subgroup],
    subgroup_size_used: int,
    all_valid_values: list[float],
) -> SigmaEstimate:
    within_sigma = estimate_within_sigma(chart_type, conforming_subgroups, subgroup_size_used)
    overall_sigma = estimate_overall_sigma(all_valid_values)

    # Zero (or, from floating point noise, negative-but-effectively-zero)
    # sigma is a legitimate outcome when every observation is identical --
    # it is not an error condition here. Downstream consumers (capability
    # engine, control limit interpretation) are responsible for treating a
    # zero sigma as "undefined capability, return a warning" rather than
    # dividing by zero. See capability/capability_calculator.py.
    within_sigma = max(within_sigma, 0.0)
    overall_sigma = max(overall_sigma, 0.0)

    return SigmaEstimate(within_sigma=within_sigma, overall_sigma=overall_sigma, method="WITHIN_OVERALL")
