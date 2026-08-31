-- One row per invocation of the SPC engine, either for Phase 1 historical
-- analysis or for the independent "current dataset" analysis that is part
-- of a Phase 2 manual check. This is metadata only -- the underlying
-- measurements and per-point chart data are not stored redundantly here.
CREATE TABLE IF NOT EXISTS analysis_runs (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_type TEXT NOT NULL
        CONSTRAINT ck_analysis_runs_type CHECK (analysis_type IN ('HISTORICAL', 'MANUAL_CHECK_CURRENT')),
    upload_id UUID NOT NULL REFERENCES uploads (upload_id),
    spc_configuration_id UUID REFERENCES spc_configurations (spc_configuration_id),

    organization_id UUID REFERENCES organizations (organization_id),
    plant_id UUID REFERENCES plants (plant_id),
    production_line_id UUID REFERENCES production_lines (production_line_id),
    machine_id UUID REFERENCES machines (machine_id),
    product_id UUID REFERENCES products (product_id),
    process_id UUID REFERENCES processes (process_id),
    operation_id UUID REFERENCES operations (operation_id),
    parameter_id UUID NOT NULL REFERENCES parameters (parameter_id),

    chart_type TEXT NOT NULL
        CONSTRAINT ck_analysis_runs_chart_type CHECK (chart_type IN ('XBAR_R', 'XBAR_S', 'IMR')),
    status TEXT NOT NULL DEFAULT 'STARTED'
        CONSTRAINT ck_analysis_runs_status CHECK (status IN ('STARTED', 'COMPLETED', 'FAILED')),
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_upload_id ON analysis_runs (upload_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_parameter_id ON analysis_runs (parameter_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_machine_id ON analysis_runs (machine_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_status ON analysis_runs (status);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_created_at ON analysis_runs (created_at);
