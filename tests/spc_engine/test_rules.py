from datetime import datetime, timedelta, timezone

from app.spc_engine.core.enums import ChartType, RuleName
from app.spc_engine.core.models import ChartPoint, RuleConfig
from app.spc_engine.rules.point_outside_limits import PointOutsideLimitsRule
from app.spc_engine.rules.rule_engine import RuleEngine
from app.spc_engine.rules.shift_rule import ShiftRule
from app.spc_engine.rules.trend_rule import TrendRule

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _points(values):
    return [ChartPoint(index=i, subgroup_id=f"SG-{i}", timestamp=START + timedelta(minutes=i), value=v) for i, v in enumerate(values)]


def test_point_outside_limits_detects_high_and_low():
    points = _points([10, 10, 15, 10, 5])
    violations = PointOutsideLimitsRule().evaluate(points, center_line=10, ucl=12, lcl=8, chart_type=ChartType.IMR, config=RuleConfig(RuleName.POINT_OUTSIDE_LIMITS))
    assert len(violations) == 2
    assert violations[0].start_index == 2
    assert violations[1].start_index == 4


def test_point_outside_limits_none_when_all_in_control():
    points = _points([10, 11, 9, 10, 10])
    violations = PointOutsideLimitsRule().evaluate(points, center_line=10, ucl=12, lcl=8, chart_type=ChartType.IMR, config=RuleConfig(RuleName.POINT_OUTSIDE_LIMITS))
    assert violations == []


def test_trend_rule_detects_n_consecutive_increasing():
    points = _points([1, 2, 3, 4, 5, 6, 7])  # 7 strictly increasing points
    config = RuleConfig(RuleName.TREND_INCREASING, parameters={"consecutive_points": 7})
    violations = TrendRule(RuleName.TREND_INCREASING).evaluate(points, center_line=4, ucl=10, lcl=-10, chart_type=ChartType.IMR, config=config)
    assert len(violations) == 1
    assert violations[0].start_index == 0
    assert violations[0].end_index == 6


def test_trend_rule_no_violation_below_threshold():
    points = _points([1, 2, 3, 4, 5])  # only 5 increasing, threshold 7
    config = RuleConfig(RuleName.TREND_INCREASING, parameters={"consecutive_points": 7})
    violations = TrendRule(RuleName.TREND_INCREASING).evaluate(points, center_line=3, ucl=10, lcl=-10, chart_type=ChartType.IMR, config=config)
    assert violations == []


def test_trend_rule_decreasing():
    points = _points([10, 9, 8, 7, 6, 5, 4])
    config = RuleConfig(RuleName.TREND_DECREASING, parameters={"consecutive_points": 7})
    violations = TrendRule(RuleName.TREND_DECREASING).evaluate(points, center_line=7, ucl=15, lcl=-5, chart_type=ChartType.IMR, config=config)
    assert len(violations) == 1


def test_shift_rule_detects_run_above_center_line():
    points = _points([11, 12, 11, 13, 12, 11, 12, 13])  # 8 consecutive above CL=10
    config = RuleConfig(RuleName.RUN_SAME_SIDE, parameters={"consecutive_points": 8})
    violations = ShiftRule().evaluate(points, center_line=10, ucl=20, lcl=0, chart_type=ChartType.IMR, config=config)
    assert len(violations) == 1
    assert "above" in violations[0].message


def test_shift_rule_no_violation_when_run_broken():
    points = _points([11, 12, 11, 9, 12, 11, 12, 13])  # broken by a point below CL
    config = RuleConfig(RuleName.RUN_SAME_SIDE, parameters={"consecutive_points": 8})
    violations = ShiftRule().evaluate(points, center_line=10, ucl=20, lcl=0, chart_type=ChartType.IMR, config=config)
    assert violations == []


def test_rule_engine_determines_out_of_control_on_point_violation():
    points = _points([10, 10, 15])
    engine = RuleEngine([RuleConfig(RuleName.POINT_OUTSIDE_LIMITS)])
    violations = engine.evaluate(points, center_line=10, ucl=12, lcl=8, chart_type=ChartType.IMR)
    stability = RuleEngine.determine_stability(violations)
    assert stability.status.value == "OUT_OF_CONTROL"


def test_rule_engine_in_control_with_no_violations():
    points = _points([10, 11, 9, 10])
    engine = RuleEngine([RuleConfig(RuleName.POINT_OUTSIDE_LIMITS)])
    violations = engine.evaluate(points, center_line=10, ucl=12, lcl=8, chart_type=ChartType.IMR)
    stability = RuleEngine.determine_stability(violations)
    assert stability.status.value == "IN_CONTROL"
