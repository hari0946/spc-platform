-- Versioned engineering specifications (LSL/USL/Target). Never hardcode
-- specification limits in application code -- always resolve them here,
-- scoped to machine/product/operation and an effective date range.
CREATE TABLE IF NOT EXISTS specifications (
    specification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parameter_id      UUID NOT NULL REFERENCES parameters (parameter_id) ON DELETE RESTRICT,
    machine_id        UUID REFERENCES machines (machine_id) ON DELETE RESTRICT,
    product_id        UUID REFERENCES products (product_id) ON DELETE RESTRICT,
    operation_id      UUID REFERENCES operations (operation_id) ON DELETE RESTRICT,
    lsl               NUMERIC,
    usl               NUMERIC,
    target            NUMERIC,
    effective_from    TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to      TIMESTAMPTZ,
    status            TEXT NOT NULL DEFAULT 'ACTIVE'
                          CONSTRAINT ck_specifications_status
                          CHECK (status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED', 'ARCHIVED')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by        TEXT,
    CONSTRAINT ck_specifications_has_bound CHECK (lsl IS NOT NULL OR usl IS NOT NULL),
    CONSTRAINT ck_specifications_bounds_order CHECK (
        lsl IS NULL OR usl IS NULL OR lsl < usl
    ),
    CONSTRAINT ck_specifications_effective_range CHECK (
        effective_to IS NULL OR effective_to > effective_from
    )
);

CREATE INDEX IF NOT EXISTS idx_specifications_parameter_id ON specifications (parameter_id);
CREATE INDEX IF NOT EXISTS idx_specifications_machine_id ON specifications (machine_id);
CREATE INDEX IF NOT EXISTS idx_specifications_product_id ON specifications (product_id);
CREATE INDEX IF NOT EXISTS idx_specifications_operation_id ON specifications (operation_id);
CREATE INDEX IF NOT EXISTS idx_specifications_lookup
    ON specifications (parameter_id, status, effective_from);
