CREATE TABLE IF NOT EXISTS products (
    product_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations (organization_id) ON DELETE RESTRICT,
    part_number     TEXT NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    revision        TEXT,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_products_org_part_number UNIQUE (organization_id, part_number)
);

CREATE INDEX IF NOT EXISTS idx_products_organization_id ON products (organization_id);
