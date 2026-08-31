CREATE TABLE IF NOT EXISTS processes (
    process_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations (organization_id) ON DELETE RESTRICT,
    name            TEXT NOT NULL,
    code            TEXT NOT NULL,
    description     TEXT,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_processes_org_code UNIQUE (organization_id, code)
);

CREATE INDEX IF NOT EXISTS idx_processes_organization_id ON processes (organization_id);
