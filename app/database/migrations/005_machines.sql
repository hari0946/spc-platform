CREATE TABLE IF NOT EXISTS machines (
    machine_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plant_id            UUID NOT NULL REFERENCES plants (plant_id) ON DELETE RESTRICT,
    production_line_id  UUID REFERENCES production_lines (production_line_id) ON DELETE SET NULL,
    name                TEXT NOT NULL,
    code                TEXT NOT NULL,
    machine_type        TEXT,
    manufacturer        TEXT,
    model               TEXT,
    active              BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_machines_plant_code UNIQUE (plant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_machines_plant_id ON machines (plant_id);
CREATE INDEX IF NOT EXISTS idx_machines_production_line_id ON machines (production_line_id);
