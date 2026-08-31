"""RULE 1: One (or more) point(s) outside the UCL or LCL -- the classic
single most important out-of-control signal."""

from __future__ import annotations

from app.spc_engine.core.enums import ChartType, RuleName, Severity
from app.spc_engine.core.models import ChartPoint, RuleConfig, RuleViolation
from app.spc_engine.rules.base_rule import BaseRule, utcnow


class PointOutsideLimitsRule(BaseRule):
    def evaluate(
        self,
        points: list[ChartPoint],
        center_line: float,
        ucl: float,
        lcl: float,
        chart_type: ChartType,
        config: RuleConfig,
    ) -> list[RuleViolation]:
        violations: list[RuleViolation] = []
        for point in points:
            if point.value > ucl or point.value < lcl:
                side = "above UCL" if point.value > ucl else "below LCL"
                violations.append(
                    RuleViolation(
                        rule_name=RuleName.POINT_OUTSIDE_LIMITS,
                        chart_type=chart_type,
                        severity=config.severity if config else Severity.CRITICAL,
                        start_index=point.index,
                        end_index=point.index,
                        affected_points=[point.index],
                        message=(
                            f"Point at index {point.index} (value={point.value:.6g}) is {side} "
                            f"(UCL={ucl:.6g}, LCL={lcl:.6g})."
                        ),
                        detected_at=utcnow(),
                    )
                )
        return violations
