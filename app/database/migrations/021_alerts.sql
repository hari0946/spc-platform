-- Actionable alerts surfaced to quality engineers, generally raised from a
-- CRITICAL/WARNING finding or an OUT_OF_CONTROL manual check result.
CREATE TABLE IF NOT EXISTS alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manual_check_id UUID REFERENCES manual_check_runs (manual_check_id) ON DELETE CASCADE,
    finding_id UUID REFERENCES findings (finding_id) ON DELETE CASCADE,

    machine_id UUID REFERENCES machines (machine_id),
    parameter_id UUID REFERENCES parameters (parameter_id),

    severity TEXT NOT NULL
        CONSTRAINT ck_alerts_severity CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    status TEXT NOT NULL DEFAULT 'OPEN'
        CONSTRAINT ck_alerts_status CHECK (status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')),
    message TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT,
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status);
CREATE INDEX IF NOT EXISTS idx_alerts_machine_id ON alerts (machine_id);
CREATE INDEX IF NOT EXISTS idx_alerts_parameter_id ON alerts (parameter_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts (created_at);
