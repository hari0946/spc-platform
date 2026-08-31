-- Data-driven SPC setup per parameter (optionally scoped further by
-- machine/product/operation). Nothing about chart type, subgroup strategy,
-- or sigma/capability method is hardcoded in application code.
CREATE TABLE IF NOT EXISTS spc_configurations (
    spc_configuration_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parameter_id             UUID NOT NULL REFERENCES parameters (parameter_id) ON DELETE RESTRICT,
    machine_id                UUID REFERENCES machines (machine_id),
    product_id                 UUID REFERENCES products (product_id),
    operation_id                UUID REFERENCES operations (operation_id),
    chart_type                    TEXT NOT NULL
        CONSTRAINT ck_spc_configurations_chart_type
        CHECK (chart_type IN ('XBAR_R', 'XBAR_S', 'IMR', 'AUTO')),
    subgroup_size                  INTEGER NOT NULL DEFAULT 1
        CONSTRAINT ck_spc_configurations_subgroup_size CHECK (subgroup_size >= 1),
    subgroup_method                  TEXT NOT NULL DEFAULT 'CONSECUTIVE'
        CONSTRAINT ck_spc_configurations_subgroup_method
        CHECK (subgroup_method IN ('EXISTING_ID', 'FIXED_SIZE', 'CONSECUTIVE', 'TIME_WINDOW')),
    maximum_time_gap_seconds           INTEGER NOT NULL DEFAULT 3600,
    minimum_sample_size                  INTEGER NOT NULL DEFAULT 20,
    ruleset                                 JSONB NOT NULL DEFAULT '[]'::JSONB,
    sigma_method                             TEXT NOT NULL DEFAULT 'WITHIN_OVERALL'
        CONSTRAINT ck_spc_configurations_sigma_method CHECK (sigma_method IN ('WITHIN_OVERALL')),
    capability_method                          TEXT NOT NULL DEFAULT 'STANDARD'
        CONSTRAINT ck_spc_configurations_capability_method CHECK (capability_method IN ('STANDARD')),
    is_active                                    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                                     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                                       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_spc_configurations_parameter_id ON spc_configurations (parameter_id);
CREATE INDEX IF NOT EXISTS idx_spc_configurations_lookup
    ON spc_configurations (parameter_id, machine_id, product_id, operation_id, is_active);
