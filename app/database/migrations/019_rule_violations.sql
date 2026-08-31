-- SPC rule engine violations, attached either to a historical analysis_runs
-- row or to a manual_check_runs row (never both).
CREATE TABLE IF NOT EXISTS rule_violations (
    violation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES analysis_runs (analysis_id) ON DELETE CASCADE,
    manual_check_id UUID REFERENCES manual_check_runs (manual_check_id) ON DELETE CASCADE,

    rule_name TEXT NOT NULL,
    chart_type TEXT NOT NULL,
    severity TEXT NOT NULL
        CONSTRAINT ck_rule_violations_severity CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    start_index INTEGER NOT NULL,
    end_index INTEGER NOT NULL,
    affected_points JSONB NOT NULL DEFAULT '[]'::JSONB,
    message TEXT NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_rule_violations_owner CHECK (
        (analysis_id IS NOT NULL AND manual_check_id IS NULL)
        OR (analysis_id IS NULL AND manual_check_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_rule_violations_analysis_id ON rule_violations (analysis_id);
CREATE INDEX IF NOT EXISTS idx_rule_violations_manual_check_id ON rule_violations (manual_check_id);
