from types import SimpleNamespace

import pytest

from app.spc_engine.comparison.baseline_comparison_engine import compare_to_baseline
from app.spc_engine.core.enums import RuleName
from app.spc_engine.core.models import RuleViolation
from app.spc_engine.findings.findings_engine import build_findings, determine_final_status


def _baseline(mean=20.0, within_sigma=0.01, overall_sigma=0.012, cpk=1.5, ppk=1.4):
    return SimpleNamespace(mean=mean, within_sigma=within_sigma, overall_sigma=overall_sigma, cpk=cpk, ppk=ppk)


def _current(mean=20.0, within_sigma=0.01, overall_sigma=0.012, cpk=1.5, ppk=1.4):
    return SimpleNamespace(
        statistics=SimpleNamespace(mean=mean),
        sigma=SimpleNamespace(within_sigma=within_sigma, overall_sigma=overall_sigma),
        capability=SimpleNamespace(cpk=cpk, ppk=ppk),
    )


def test_no_change_detects_nothing():
    comparison = compare_to_baseline(_baseline(), _current())
    assert comparison.mean_shift == 0.0
    assert not comparison.mean_shift_detected
    assert not comparison.variation_increase_detected
    assert not comparison.capability_degradation_detected


def test_mean_shift_detected_when_beyond_one_sigma():
    # baseline within_sigma=0.01; shift by 0.02 (2 sigma) should trigger.
    comparison = compare_to_baseline(_baseline(within_sigma=0.01), _current(mean=20.02, within_sigma=0.01))
    assert comparison.mean_shift == pytest.approx(0.02)
    assert comparison.mean_shift_detected


def test_variation_increase_detected():
    comparison = compare_to_baseline(_baseline(within_sigma=0.01), _current(within_sigma=0.02))
    assert comparison.variation_increase_detected
    assert not comparison.variation_reduction_detected


def test_variation_reduction_detected():
    comparison = compare_to_baseline(_baseline(within_sigma=0.02), _current(within_sigma=0.01))
    assert comparison.variation_reduction_detected
    assert not comparison.variation_increase_detected


def test_capability_degradation_detected():
    comparison = compare_to_baseline(_baseline(cpk=1.5), _current(cpk=1.0))
    assert comparison.cpk_change == pytest.approx(-0.5)
    assert comparison.capability_degradation_detected


def test_capability_improvement_detected():
    comparison = compare_to_baseline(_baseline(cpk=1.0), _current(cpk=1.5))
    assert comparison.cpk_change == pytest.approx(0.5)
    assert comparison.capability_improvement_detected


def test_zero_baseline_mean_handled_safely():
    comparison = compare_to_baseline(_baseline(mean=0.0), _current(mean=0.01))
    assert comparison.mean_shift_percentage is None  # cannot compute % change from a zero baseline


def test_findings_engine_reports_capability_degradation_as_fact_not_cause():
    comparison = compare_to_baseline(_baseline(cpk=1.5), _current(cpk=1.05))
    findings = build_findings(comparison, [])
    degradation = [f for f in findings if f.finding_type.value == "CAPABILITY_DEGRADATION"]
    assert len(degradation) == 1
    assert "1.5" in degradation[0].message or "1.50" in degradation[0].message
    assert "1.05" in degradation[0].message
    # Must not speculate about root cause.
    for banned_word in ("tool wear", "operator error", "material"):
        assert banned_word not in degradation[0].message.lower()


def test_final_status_out_of_control_when_point_violation_present():
    comparison = compare_to_baseline(_baseline(), _current())
    violation = RuleViolation(
        rule_name=RuleName.POINT_OUTSIDE_LIMITS, chart_type=None, severity=None,
        start_index=0, end_index=0, affected_points=[0], message="x", detected_at=None,
    )
    status = determine_final_status(comparison, [violation])
    assert status.value == "OUT_OF_CONTROL"


def test_final_status_normal_when_nothing_detected():
    comparison = compare_to_baseline(_baseline(), _current())
    status = determine_final_status(comparison, [])
    assert status.value == "NORMAL"


def test_missing_baseline_cpk_does_not_crash_comparison():
    comparison = compare_to_baseline(_baseline(cpk=None), _current(cpk=1.2))
    assert comparison.cpk_change is None
    assert not comparison.capability_degradation_detected
