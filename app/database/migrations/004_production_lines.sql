CREATE TABLE IF NOT EXISTS production_lines (
    production_line_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plant_id            UUID NOT NULL REFERENCES plants (plant_id) ON DELETE RESTRICT,
    name                TEXT NOT NULL,
    code                TEXT NOT NULL,
    description         TEXT,
    active              BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_production_lines_plant_code UNIQUE (plant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_production_lines_plant_id ON production_lines (plant_id);
