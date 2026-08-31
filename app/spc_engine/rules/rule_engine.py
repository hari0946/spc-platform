"""Orchestrates the configured set of SPC rules against one chart series
and derives an overall process stability status from the violations found.

The same engine is reused for two distinct situations:
  1. Historical analysis: rules evaluated against that dataset's own,
     freshly-calculated control limits.
  2. Phase 2 manual check: rules evaluated against the FIXED historical
     baseline's limits applied to the new dataset (see
     services/manual_data_check_service.py) -- this module doesn't care
     where the limits came from, it just needs center_line/ucl/lcl.
"""

from __future__ import annotations

from app.spc_engine.core.enums import ChartType, RuleName, StabilityStatus
from app.spc_engine.core.models import ChartPoint, RuleConfig, RuleViolation, StabilityResult
from app.spc_engine.rules.base_rule import BaseRule
from app.spc_engine.rules.point_outside_limits import PointOutsideLimitsRule
from app.spc_engine.rules.shift_rule import ShiftRule
from app.spc_engine.rules.trend_rule import TrendRule

# Sensible, fully-overridable defaults used only when an spc_configuration
# has not defined an explicit ruleset. Any configuration-driven ruleset
# read from PostgreSQL (rule_configurations table) always takes precedence.
DEFAULT_RULESET: list[RuleConfig] = [
    RuleConfig(rule_name=RuleName.POINT_OUTSIDE_LIMITS, enabled=True),
    RuleConfig(rule_name=RuleName.TREND_INCREASING, enabled=True, parameters={"consecutive_points": 7}),
    RuleConfig(rule_name=RuleName.TREND_DECREASING, enabled=True, parameters={"consecutive_points": 7}),
    RuleConfig(rule_name=RuleName.RUN_SAME_SIDE, enabled=True, parameters={"consecutive_points": 8}),
]


def _build_rule(rule_name: RuleName) -> BaseRule:
    if rule_name == RuleName.POINT_OUTSIDE_LIMITS:
        return PointOutsideLimitsRule()
    if rule_name == RuleName.TREND_INCREASING:
        return TrendRule(RuleName.TREND_INCREASING)
    if rule_name == RuleName.TREND_DECREASING:
        return TrendRule(RuleName.TREND_DECREASING)
    if rule_name == RuleName.RUN_SAME_SIDE:
        return ShiftRule()
    raise ValueError(f"Unsupported rule: {rule_name}")


class RuleEngine:
    def __init__(self, ruleset: list[RuleConfig] | None = None) -> None:
        self._ruleset = ruleset if ruleset else DEFAULT_RULESET

    def evaluate(
        self,
        points: list[ChartPoint],
        center_line: float,
        ucl: float,
        lcl: float,
        chart_type: ChartType,
    ) -> list[RuleViolation]:
        violations: list[RuleViolation] = []
        for rule_config in self._ruleset:
            if not rule_config.enabled:
                continue
            rule = _build_rule(rule_config.rule_name)
            violations.extend(rule.evaluate(points, center_line, ucl, lcl, chart_type, rule_config))
        return sorted(violations, key=lambda v: v.start_index)

    @staticmethod
    def determine_stability(violations: list[RuleViolation]) -> StabilityResult:
        if any(v.rule_name == RuleName.POINT_OUTSIDE_LIMITS for v in violations):
            status = StabilityStatus.OUT_OF_CONTROL
        elif violations:
            status = StabilityStatus.WARNING
        else:
            status = StabilityStatus.IN_CONTROL
        return StabilityResult(status=status, violations=violations)
