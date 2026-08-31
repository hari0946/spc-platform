-- Human-readable findings produced by FindingsEngine. Findings state
-- statistical fact only (e.g. "process mean shifted upward by 0.020") --
-- never speculative root cause. Root-cause investigation suggestions, if
-- ever added, belong in a separate, clearly-labelled field/table.
CREATE TABLE IF NOT EXISTS findings (
    finding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES analysis_runs (analysis_id) ON DELETE CASCADE,
    manual_check_id UUID REFERENCES manual_check_runs (manual_check_id) ON DELETE CASCADE,

    finding_type TEXT NOT NULL
        CONSTRAINT ck_findings_type CHECK (finding_type IN (
            'MEAN_SHIFT',
            'VARIATION_INCREASE',
            'VARIATION_REDUCTION',
            'CAPABILITY_DEGRADATION',
            'CAPABILITY_IMPROVEMENT',
            'NEW_LIMIT_VIOLATION',
            'TREND_DETECTED',
            'SHIFT_DETECTED',
            'PROCESS_STABLE',
            'PROCESS_UNSTABLE'
        )),
    severity TEXT NOT NULL
        CONSTRAINT ck_findings_severity CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    message TEXT NOT NULL,
    statistical_fact JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_findings_owner CHECK (
        analysis_id IS NOT NULL OR manual_check_id IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_findings_analysis_id ON findings (analysis_id);
CREATE INDEX IF NOT EXISTS idx_findings_manual_check_id ON findings (manual_check_id);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings (severity);
CREATE INDEX IF NOT EXISTS idx_findings_created_at ON findings (created_at);
