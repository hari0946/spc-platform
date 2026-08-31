"""Converts mathematical comparison/stability results into human-readable
findings, and rolls everything up into a final process status.

IMPORTANT: findings state statistical fact only ("process mean shifted
upward by 0.020"), never speculative root cause ("tool wear caused the
shift"). Root-cause investigation support, if added later, must live in a
separate, clearly-labelled field/table -- never blended into a finding's
message.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.spc_engine.core.enums import FinalProcessStatus, FindingType, RuleName, Severity
from app.spc_engine.core.models import ComparisonResult, Finding, RuleViolation


@dataclass(frozen=True)
class FinalStatusThresholds:
    """All thresholds are explicit and overridable -- never hardcoded deep
    inside conditional logic."""

    critical_violation_count: int = 2
    critical_cpk_change: float = -0.5
    critical_cpk_absolute: float = 1.00
    warning_cpk_absolute: float = 1.33


_DEFAULT_THRESHOLDS = FinalStatusThresholds()


def _fmt(value: float) -> str:
    return f"{value:.4g}"


def build_findings(
    comparison: ComparisonResult, baseline_violations: list[RuleViolation]
) -> list[Finding]:
    findings: list[Finding] = []

    if comparison.mean_shift_detected:
        direction = "upward" if comparison.mean_shift > 0 else "downward"
        findings.append(
            Finding(
                finding_type=FindingType.MEAN_SHIFT,
                severity=Severity.WARNING,
                message=(
                    f"Process mean shifted {direction} by {_fmt(abs(comparison.mean_shift))} "
                    f"(from {_fmt(comparison.baseline_mean)} to {_fmt(comparison.current_mean)})."
                ),
                statistical_fact={
                    "baseline_mean": comparison.baseline_mean,
                    "current_mean": comparison.current_mean,
                    "mean_shift": comparison.mean_shift,
                    "mean_shift_percentage": comparison.mean_shift_percentage,
                },
            )
        )

    if comparison.variation_increase_detected:
        findings.append(
            Finding(
                finding_type=FindingType.VARIATION_INCREASE,
                severity=Severity.WARNING,
                message=(
                    f"Process variation (within-subgroup sigma) increased from "
                    f"{_fmt(comparison.baseline_within_sigma)} to {_fmt(comparison.current_within_sigma)} "
                    f"({_fmt(comparison.within_variation_change_percentage or 0)}%)."
                ),
                statistical_fact={
                    "baseline_within_sigma": comparison.baseline_within_sigma,
                    "current_within_sigma": comparison.current_within_sigma,
                    "within_variation_change_percentage": comparison.within_variation_change_percentage,
                },
            )
        )

    if comparison.variation_reduction_detected:
        findings.append(
            Finding(
                finding_type=FindingType.VARIATION_REDUCTION,
                severity=Severity.INFO,
                message=(
                    f"Process variation (within-subgroup sigma) decreased from "
                    f"{_fmt(comparison.baseline_within_sigma)} to {_fmt(comparison.current_within_sigma)} "
                    f"({_fmt(comparison.within_variation_change_percentage or 0)}%)."
                ),
                statistical_fact={
                    "baseline_within_sigma": comparison.baseline_within_sigma,
                    "current_within_sigma": comparison.current_within_sigma,
                    "within_variation_change_percentage": comparison.within_variation_change_percentage,
                },
            )
        )

    if comparison.capability_degradation_detected and comparison.baseline_cpk is not None and comparison.current_cpk is not None:
        findings.append(
            Finding(
                finding_type=FindingType.CAPABILITY_DEGRADATION,
                severity=Severity.WARNING,
                message=(
                    f"Process capability (Cpk) decreased from {_fmt(comparison.baseline_cpk)} "
                    f"to {_fmt(comparison.current_cpk)}."
                ),
                statistical_fact={
                    "baseline_cpk": comparison.baseline_cpk,
                    "current_cpk": comparison.current_cpk,
                    "cpk_change": comparison.cpk_change,
                },
            )
        )

    if comparison.capability_improvement_detected and comparison.baseline_cpk is not None and comparison.current_cpk is not None:
        findings.append(
            Finding(
                finding_type=FindingType.CAPABILITY_IMPROVEMENT,
                severity=Severity.INFO,
                message=(
                    f"Process capability (Cpk) improved from {_fmt(comparison.baseline_cpk)} "
                    f"to {_fmt(comparison.current_cpk)}."
                ),
                statistical_fact={
                    "baseline_cpk": comparison.baseline_cpk,
                    "current_cpk": comparison.current_cpk,
                    "cpk_change": comparison.cpk_change,
                },
            )
        )

    point_violations = [v for v in baseline_violations if v.rule_name == RuleName.POINT_OUTSIDE_LIMITS]
    if point_violations:
        findings.append(
            Finding(
                finding_type=FindingType.NEW_LIMIT_VIOLATION,
                severity=Severity.CRITICAL,
                message=(
                    f"{len(point_violations)} point(s) in the new dataset fall outside the fixed "
                    f"historical baseline control limits."
                ),
                statistical_fact={
                    "violation_count": len(point_violations),
                    "affected_indices": [v.start_index for v in point_violations],
                },
            )
        )

    trend_violations = [
        v for v in baseline_violations if v.rule_name in (RuleName.TREND_INCREASING, RuleName.TREND_DECREASING)
    ]
    if trend_violations:
        findings.append(
            Finding(
                finding_type=FindingType.TREND_DETECTED,
                severity=Severity.WARNING,
                message=f"{len(trend_violations)} trend pattern(s) detected against the historical baseline.",
                statistical_fact={"violation_count": len(trend_violations)},
            )
        )

    shift_violations = [v for v in baseline_violations if v.rule_name == RuleName.RUN_SAME_SIDE]
    if shift_violations:
        findings.append(
            Finding(
                finding_type=FindingType.SHIFT_DETECTED,
                severity=Severity.WARNING,
                message=(
                    f"{len(shift_violations)} sustained run(s) on one side of the historical "
                    f"baseline center line detected."
                ),
                statistical_fact={"violation_count": len(shift_violations)},
            )
        )

    if not findings:
        findings.append(
            Finding(
                finding_type=FindingType.PROCESS_STABLE,
                severity=Severity.INFO,
                message="No significant deviation from the historical baseline was detected.",
                statistical_fact={},
            )
        )

    return findings


def determine_final_status(
    comparison: ComparisonResult,
    baseline_violations: list[RuleViolation],
    thresholds: FinalStatusThresholds = _DEFAULT_THRESHOLDS,
) -> FinalProcessStatus:
    point_violations = [v for v in baseline_violations if v.rule_name == RuleName.POINT_OUTSIDE_LIMITS]

    severe_signals = 0
    if point_violations:
        severe_signals += 1
    if comparison.capability_degradation_detected and comparison.current_cpk is not None:
        if comparison.current_cpk < thresholds.critical_cpk_absolute:
            severe_signals += 1
        if comparison.cpk_change is not None and comparison.cpk_change <= thresholds.critical_cpk_change:
            severe_signals += 1
    if comparison.mean_shift_detected and comparison.variation_increase_detected:
        severe_signals += 1

    if severe_signals >= thresholds.critical_violation_count:
        return FinalProcessStatus.CRITICAL

    if point_violations:
        return FinalProcessStatus.OUT_OF_CONTROL

    warning_signals = (
        comparison.mean_shift_detected
        or comparison.variation_increase_detected
        or comparison.capability_degradation_detected
        or any(
            v.rule_name in (RuleName.TREND_INCREASING, RuleName.TREND_DECREASING, RuleName.RUN_SAME_SIDE)
            for v in baseline_violations
        )
    )
    if warning_signals:
        return FinalProcessStatus.WARNING

    if comparison.current_cpk is not None and comparison.current_cpk < thresholds.warning_cpk_absolute:
        return FinalProcessStatus.WARNING

    return FinalProcessStatus.NORMAL
