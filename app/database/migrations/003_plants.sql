CREATE TABLE IF NOT EXISTS plants (
    plant_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations (organization_id) ON DELETE RESTRICT,
    name            TEXT NOT NULL,
    code            TEXT NOT NULL,
    timezone        TEXT NOT NULL DEFAULT 'UTC',
    country         TEXT,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_plants_org_code UNIQUE (organization_id, code)
);

CREATE INDEX IF NOT EXISTS idx_plants_organization_id ON plants (organization_id);
