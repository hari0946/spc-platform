"""RULE 4: N consecutive points on the same side of the center line -- a
sustained shift in process mean. N is configurable via
RuleConfig.parameters["consecutive_points"] (default 8, a common
Western Electric-style threshold for this rule) -- never hardcoded.
"""

from __future__ import annotations

from app.spc_engine.core.enums import ChartType, RuleName, Severity
from app.spc_engine.core.models import ChartPoint, RuleConfig, RuleViolation
from app.spc_engine.rules.base_rule import BaseRule, utcnow

_DEFAULT_CONSECUTIVE_POINTS = 8


class ShiftRule(BaseRule):
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

        def side(value: float) -> int:
            if value > center_line:
                return 1
            if value < center_line:
                return -1
            return 0  # exactly on the center line breaks a run, by design

        violations: list[RuleViolation] = []
        run_start = 0
        current_side = side(points[0].value)
        for i in range(1, len(points)):
            point_side = side(points[i].value)
            if point_side == 0 or point_side != current_side:
                run_start = i
                current_side = point_side
                continue

            run_length = i - run_start + 1
            if run_length == threshold:
                affected = list(range(run_start, i + 1))
                direction = "above" if current_side == 1 else "below"
                violations.append(
                    RuleViolation(
                        rule_name=RuleName.RUN_SAME_SIDE,
                        chart_type=chart_type,
                        severity=config.severity if config else Severity.WARNING,
                        start_index=points[run_start].index,
                        end_index=points[i].index,
                        affected_points=[points[j].index for j in affected],
                        message=(
                            f"{threshold} consecutive points {direction} the center line detected "
                            f"(indices {points[run_start].index}..{points[i].index}); "
                            f"this indicates a sustained process shift."
                        ),
                        detected_at=utcnow(),
                    )
                )
                run_start = i
        return violations
