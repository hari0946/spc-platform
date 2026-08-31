"""Compares a freshly-analyzed "current" dataset against a fixed historical
baseline. Pure arithmetic -- no database access, no interpretation into
prose (that's findings_engine.py's job).
"""

from __future__ import annotations

from app.spc_engine.core.models import BaselineSnapshot, ComparisonResult, SPCAnalysisResult

# Thresholds for flagging a change as "detected" rather than noise. These
# are intentionally conservative, simple defaults; a future iteration could
# move them into spc_configurations alongside the ruleset.
_MEAN_SHIFT_SIGMA_THRESHOLD = 1.0  # shift >= 1 baseline within-sigma
_VARIATION_CHANGE_PERCENT_THRESHOLD = 10.0  # +/-10% sigma change
_CAPABILITY_CHANGE_THRESHOLD = 0.2  # +/-0.2 Cpk/Ppk points


def _safe_percentage_change(current: float, baseline: float) -> float | None:
    if baseline == 0:
        return None
    return (current - baseline) / abs(baseline) * 100.0


def compare_to_baseline(baseline: BaselineSnapshot, current: SPCAnalysisResult) -> ComparisonResult:
    baseline_mean = baseline.mean
    current_mean = current.statistics.mean
    mean_shift = current_mean - baseline_mean
    mean_shift_percentage = _safe_percentage_change(current_mean, baseline_mean)

    baseline_within = baseline.within_sigma
    current_within = current.sigma.within_sigma
    within_change = current_within - baseline_within
    within_change_pct = _safe_percentage_change(current_within, baseline_within)

    baseline_overall = baseline.overall_sigma
    current_overall = current.sigma.overall_sigma
    overall_change = current_overall - baseline_overall
    overall_change_pct = _safe_percentage_change(current_overall, baseline_overall)

    baseline_cpk = baseline.cpk
    current_cpk = current.capability.cpk
    cpk_change = (
        current_cpk - baseline_cpk if (current_cpk is not None and baseline_cpk is not None) else None
    )

    baseline_ppk = baseline.ppk
    current_ppk = current.capability.ppk
    ppk_change = (
        current_ppk - baseline_ppk if (current_ppk is not None and baseline_ppk is not None) else None
    )

    mean_shift_detected = (
        baseline_within > 0 and abs(mean_shift) >= _MEAN_SHIFT_SIGMA_THRESHOLD * baseline_within
    )
    variation_increase_detected = (
        within_change_pct is not None and within_change_pct >= _VARIATION_CHANGE_PERCENT_THRESHOLD
    )
    variation_reduction_detected = (
        within_change_pct is not None and within_change_pct <= -_VARIATION_CHANGE_PERCENT_THRESHOLD
    )
    capability_degradation_detected = (
        cpk_change is not None and cpk_change <= -_CAPABILITY_CHANGE_THRESHOLD
    )
    capability_improvement_detected = (
        cpk_change is not None and cpk_change >= _CAPABILITY_CHANGE_THRESHOLD
    )

    return ComparisonResult(
        baseline_mean=baseline_mean,
        current_mean=current_mean,
        mean_shift=mean_shift,
        mean_shift_percentage=mean_shift_percentage,
        baseline_within_sigma=baseline_within,
        current_within_sigma=current_within,
        within_variation_change=within_change,
        within_variation_change_percentage=within_change_pct,
        baseline_overall_sigma=baseline_overall,
        current_overall_sigma=current_overall,
        overall_variation_change=overall_change,
        overall_variation_change_percentage=overall_change_pct,
        baseline_cpk=baseline_cpk,
        current_cpk=current_cpk,
        cpk_change=cpk_change,
        baseline_ppk=baseline_ppk,
        current_ppk=current_ppk,
        ppk_change=ppk_change,
        mean_shift_detected=mean_shift_detected,
        variation_increase_detected=variation_increase_detected,
        variation_reduction_detected=variation_reduction_detected,
        capability_improvement_detected=capability_improvement_detected,
        capability_degradation_detected=capability_degradation_detected,
    )
