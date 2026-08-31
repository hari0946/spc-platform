-- Frozen historical baseline. Once ACTIVE, a baseline's limits (ucl/cl/lcl,
-- sigma, capability) are never recalculated automatically -- re-baselining
-- is always an explicit user action (see baseline_service.py), so process
-- drift cannot silently become the new "normal".
CREATE TABLE IF NOT EXISTS baselines (
    baseline_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_runs (analysis_id),

    organization_id UUID REFERENCES organizations (organization_id),
    plant_id UUID REFERENCES plants (plant_id),
    production_line_id UUID REFERENCES production_lines (production_line_id),
    machine_id UUID REFERENCES machines (machine_id),
    product_id UUID REFERENCES products (product_id),
    process_id UUID REFERENCES processes (process_id),
    operation_id UUID REFERENCES operations (operation_id),
    parameter_id UUID NOT NULL REFERENCES parameters (parameter_id),

    chart_type TEXT NOT NULL
        CONSTRAINT ck_baselines_chart_type CHECK (chart_type IN ('XBAR_R', 'XBAR_S', 'IMR')),
    unit TEXT NOT NULL,

    baseline_start TIMESTAMPTZ,
    baseline_end TIMESTAMPTZ,
    sample_count INTEGER NOT NULL,

    mean NUMERIC NOT NULL,
    within_sigma NUMERIC NOT NULL,
    overall_sigma NUMERIC NOT NULL,

    center_line NUMERIC NOT NULL,
    ucl NUMERIC NOT NULL,
    lcl NUMERIC NOT NULL,
    secondary_center_line NUMERIC,
    secondary_ucl NUMERIC,
    secondary_lcl NUMERIC,

    specification_id UUID REFERENCES specifications (specification_id),
    lsl NUMERIC,
    usl NUMERIC,
    target NUMERIC,
    cp NUMERIC,
    cpk NUMERIC,
    pp NUMERIC,
    ppk NUMERIC,

    status TEXT NOT NULL DEFAULT 'DRAFT'
        CONSTRAINT ck_baselines_status CHECK (status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED', 'ARCHIVED')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by TEXT,
    approved_at TIMESTAMPTZ,
    approved_by TEXT,
    superseded_at TIMESTAMPTZ,
    superseded_by_baseline_id UUID REFERENCES baselines (baseline_id)
);

CREATE INDEX IF NOT EXISTS idx_baselines_parameter_id ON baselines (parameter_id);
CREATE INDEX IF NOT EXISTS idx_baselines_status ON baselines (status);

-- Exactly one ACTIVE baseline per manufacturing context (machine + product +
-- operation + parameter). NULLS are treated as "not scoped" and PostgreSQL
-- unique indexes already treat NULLs as distinct, which is the desired
-- behavior here (an unscoped-by-machine baseline and a machine-scoped one
-- are different contexts).
CREATE UNIQUE INDEX IF NOT EXISTS uq_baselines_active_context
    ON baselines (parameter_id, machine_id, product_id, operation_id)
    WHERE status = 'ACTIVE';
