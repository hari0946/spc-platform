-- One row per Phase 2 manual batch check: a user-triggered comparison of a
-- newly (manually) uploaded CSV against the ACTIVE historical baseline.
-- This is explicitly NOT continuous/real-time monitoring.
CREATE TABLE IF NOT EXISTS manual_check_runs (
    manual_check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID NOT NULL REFERENCES uploads (upload_id),
    current_analysis_id UUID REFERENCES analysis_runs (analysis_id),
    baseline_id UUID NOT NULL REFERENCES baselines (baseline_id),

    organization_id UUID REFERENCES organizations (organization_id),
    plant_id UUID REFERENCES plants (plant_id),
    production_line_id UUID REFERENCES production_lines (production_line_id),
    machine_id UUID REFERENCES machines (machine_id),
    product_id UUID REFERENCES products (product_id),
    process_id UUID REFERENCES processes (process_id),
    operation_id UUID REFERENCES operations (operation_id),
    parameter_id UUID NOT NULL REFERENCES parameters (parameter_id),

    status TEXT NOT NULL DEFAULT 'MANUAL_CHECK_STARTED'
        CONSTRAINT ck_manual_check_runs_status
        CHECK (status IN ('MANUAL_CHECK_STARTED', 'MANUAL_CHECK_COMPLETED', 'MANUAL_CHECK_FAILED')),
    final_status TEXT
        CONSTRAINT ck_manual_check_runs_final_status
        CHECK (final_status IN ('NORMAL', 'WARNING', 'OUT_OF_CONTROL', 'CRITICAL')),
    error_message TEXT,

    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    triggered_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_manual_check_runs_upload_id ON manual_check_runs (upload_id);
CREATE INDEX IF NOT EXISTS idx_manual_check_runs_baseline_id ON manual_check_runs (baseline_id);
CREATE INDEX IF NOT EXISTS idx_manual_check_runs_status ON manual_check_runs (status);
CREATE INDEX IF NOT EXISTS idx_manual_check_runs_created_at ON manual_check_runs (created_at);
