"""RULE 2 / RULE 3: N consecutive strictly increasing (or decreasing)
points. N is fully configurable via RuleConfig.parameters["consecutive_points"]
(default 7, a common Western Electric-style threshold) -- never hardcoded.
"""

from __future__ import annotations

from app.spc_engine.core.enums import ChartType, RuleName, Severity
from app.spc_engine.core.models import ChartPoint, RuleConfig, RuleViolation
from app.spc_engine.rules.base_rule import BaseRule, utcnow

_DEFAULT_CONSECUTIVE_POINTS = 7


class TrendRule(BaseRule):
    """direction must be RuleName.TREND_INCREASING or RuleName.TREND_DECREASING."""

    def __init__(self, direction: RuleName) -> None:
        if direction not in (RuleName.TREND_INCREASING, RuleName.TREND_DECREASING):
            raise ValueError(f"TrendRule direction must be a trend rule name, got {direction}")
        self._direction = direction

    def evaluate(
        self,
        points: list[ChartPoint],
        center_line: float,
        ucl: float,
        lcl: float,
        chart_type: ChartType,
        config: RuleConfig,
    ) -> list[RuleViolation]:
        threshold = int((config.parameters or {}).get("consecutive_points", _DEFAULT_CONSECUTIVE_POINTS))
        if threshold < 2 or len(points) < threshold:
            return []

        violations: list[RuleViolation] = []
        run_start = 0
        for i in range(1, len(points)):
            increasing = points[i].value > points[i - 1].value
            decreasing = points[i].value < points[i - 1].value
            continues_run = (
                increasing if self._direction == RuleName.TREND_INCREASING else decreasing
            )
            if not continues_run:
                run_start = i

            run_length = i - run_start + 1
            if run_length == threshold:
                affected = list(range(run_start, i + 1))
                direction_word = "increasing" if self._direction == RuleName.TREND_INCREASING else "decreasing"
                violations.append(
                    RuleViolation(
                        rule_name=self._direction,
                        chart_type=chart_type,
                        severity=config.severity if config else Severity.WARNING,
                        start_index=points[run_start].index,
                        end_index=points[i].index,
                        affected_points=[points[j].index for j in affected],
                        message=(
                            f"{threshold} consecutive {direction_word} points detected "
                            f"(indices {points[run_start].index}..{points[i].index})."
                        ),
                        detected_at=utcnow(),
                    )
                )
                # Reset so overlapping windows within the same run aren't
                # reported as separate violations for every subsequent point.
                run_start = i
        return violations
