"""Selects (or validates a user-configured override for) the SPC chart type.

Recommendation rules:
  - subgroup size 1                       -> I-MR
  - rational subgroup, small size (2-8)   -> XBAR-R  (range-based, simpler,
                                              standard choice for n <= 8..10)
  - rational subgroup, larger size (>=9)  -> XBAR-S  (std-dev based, more
                                              statistically efficient for
                                              larger subgroups)
"""

from __future__ import annotations

from app.spc_engine.core.enums import ChartType
from app.spc_engine.core.exceptions import ChartSelectionError
from app.spc_engine.core.models import ChartSelection

_XBAR_R_MAX_SIZE = 8


def recommend_chart(subgroup_size: int) -> tuple[ChartType, str]:
    if subgroup_size <= 1:
        return ChartType.IMR, (
            "Subgroup size is 1 (individual observations); recommending the "
            "Individuals & Moving Range (I-MR) chart."
        )
    if subgroup_size <= _XBAR_R_MAX_SIZE:
        return ChartType.XBAR_R, (
            f"Rational subgroup size is {subgroup_size} (<= {_XBAR_R_MAX_SIZE}); "
            f"recommending the range-based XBAR-R chart."
        )
    return ChartType.XBAR_S, (
        f"Rational subgroup size is {subgroup_size} (> {_XBAR_R_MAX_SIZE}); "
        f"recommending the standard-deviation-based XBAR-S chart for better "
        f"statistical efficiency at larger subgroup sizes."
    )


def select_chart(configured_chart_type: str, subgroup_size: int) -> ChartSelection:
    """Resolve the chart to actually run.

    If configured_chart_type is "AUTO", the recommendation is used as-is.
    Otherwise the user's explicit configuration overrides the
    recommendation, but it is still validated for basic compatibility with
    the detected subgroup size (e.g. XBAR-R/XBAR-S require subgroup size > 1).
    """
    recommended, reason = recommend_chart(subgroup_size)

    if configured_chart_type == "AUTO":
        return ChartSelection(
            recommended_chart=recommended, configured_chart=recommended, selection_reason=reason
        )

    try:
        configured = ChartType(configured_chart_type)
    except ValueError as exc:
        raise ChartSelectionError(f"Unknown configured chart type: {configured_chart_type}") from exc

    if configured in (ChartType.XBAR_R, ChartType.XBAR_S) and subgroup_size <= 1:
        raise ChartSelectionError(
            f"Configured chart type {configured.value} requires a rational subgroup size > 1, "
            f"but the detected/configured subgroup size is {subgroup_size}. Use I-MR instead, or "
            f"reconfigure subgrouping."
        )
    if configured == ChartType.IMR and subgroup_size > 1:
        raise ChartSelectionError(
            f"Configured chart type IMR expects individual observations (subgroup size 1), "
            f"but the detected/configured subgroup size is {subgroup_size}."
        )

    reason = (
        f"User configuration explicitly selected {configured.value}, overriding the "
        f"auto-recommendation of {recommended.value}. Reason for auto-recommendation: {reason}"
        if configured != recommended
        else reason
    )
    return ChartSelection(
        recommended_chart=recommended, configured_chart=configured, selection_reason=reason
    )
