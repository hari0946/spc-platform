-- Output of BaselineComparisonEngine for one manual_check_runs row:
-- current-vs-historical deltas and the boolean detections derived from them.
CREATE TABLE IF NOT EXISTS comparison_results (
    comparison_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manual_check_id UUID NOT NULL REFERENCES manual_check_runs (manual_check_id) ON DELETE CASCADE,

    baseline_mean NUMERIC NOT NULL,
    current_mean NUMERIC NOT NULL,
    mean_shift NUMERIC NOT NULL,
    mean_shift_percentage NUMERIC,

    baseline_within_sigma NUMERIC NOT NULL,
    current_within_sigma NUMERIC NOT NULL,
    within_variation_change NUMERIC NOT NULL,
    within_variation_change_percentage NUMERIC,

    baseline_overall_sigma NUMERIC NOT NULL,
    current_overall_sigma NUMERIC NOT NULL,
    overall_variation_change NUMERIC NOT NULL,
    overall_variation_change_percentage NUMERIC,

    baseline_cpk NUMERIC,
    current_cpk NUMERIC,
    cpk_change NUMERIC,

    baseline_ppk NUMERIC,
    current_ppk NUMERIC,
    ppk_change NUMERIC,

    mean_shift_detected BOOLEAN NOT NULL DEFAULT FALSE,
    variation_increase_detected BOOLEAN NOT NULL DEFAULT FALSE,
    variation_reduction_detected BOOLEAN NOT NULL DEFAULT FALSE,
    capability_improvement_detected BOOLEAN NOT NULL DEFAULT FALSE,
    capability_degradation_detected BOOLEAN NOT NULL DEFAULT FALSE,
    new_limit_violations_detected BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_comparison_results_manual_check_id
    ON comparison_results (manual_check_id);
