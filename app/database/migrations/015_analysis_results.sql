-- Summarized SPC analysis output for one analysis_runs row: descriptive
-- statistics, control limits, capability indices, and stability status.
-- Per-point chart series data (for frontend rendering) is stored as JSONB
-- since its shape is chart-type dependent and is never queried by value.
CREATE TABLE IF NOT EXISTS analysis_results (
    analysis_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_runs (analysis_id) ON DELETE CASCADE,

    total_observations INTEGER NOT NULL,
    valid_observations INTEGER NOT NULL,
    invalid_observations INTEGER NOT NULL,
    subgroup_count INTEGER NOT NULL,
    subgroup_size_used INTEGER NOT NULL,

    mean NUMERIC,
    minimum NUMERIC,
    maximum NUMERIC,
    within_sigma NUMERIC,
    overall_sigma NUMERIC,

    center_line NUMERIC,
    ucl NUMERIC,
    lcl NUMERIC,
    secondary_center_line NUMERIC,
    secondary_ucl NUMERIC,
    secondary_lcl NUMERIC,

    specification_id UUID REFERENCES specifications (specification_id),
    lsl NUMERIC,
    usl NUMERIC,
    target NUMERIC,

    cp NUMERIC,
    cpk NUMERIC,
    cpu NUMERIC,
    cpl NUMERIC,
    pp NUMERIC,
    ppk NUMERIC,
    ppu NUMERIC,
    ppl NUMERIC,

    stability_status TEXT
        CONSTRAINT ck_analysis_results_stability_status
        CHECK (stability_status IN ('IN_CONTROL', 'WARNING', 'OUT_OF_CONTROL')),

    chart_points JSONB NOT NULL DEFAULT '[]'::JSONB,
    warnings JSONB NOT NULL DEFAULT '[]'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analysis_results_analysis_id ON analysis_results (analysis_id);
