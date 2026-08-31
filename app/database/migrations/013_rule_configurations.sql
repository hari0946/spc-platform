-- Named, reusable rule definitions referenced by an spc_configuration's
-- `ruleset` JSONB array (by rule_name). Kept as first-class rows (rather
-- than only inline JSONB) so rules can be listed/edited/audited independently.
CREATE TABLE IF NOT EXISTS rule_configurations (
    rule_configuration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spc_configuration_id UUID REFERENCES spc_configurations (spc_configuration_id) ON DELETE CASCADE,
    rule_name TEXT NOT NULL
        CONSTRAINT ck_rule_configurations_rule_name
        CHECK (rule_name IN (
            'POINT_OUTSIDE_LIMITS',
            'TREND_INCREASING',
            'TREND_DECREASING',
            'RUN_SAME_SIDE'
        )),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    severity TEXT NOT NULL DEFAULT 'WARNING'
        CONSTRAINT ck_rule_configurations_severity
        CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    parameters JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rule_configurations_spc_configuration_id
    ON rule_configurations (spc_configuration_id);
