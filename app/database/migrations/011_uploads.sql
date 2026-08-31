-- Upload metadata lives in PostgreSQL; the actual measurement rows the
-- upload produces live in Snowflake (Bronze then Silver). This table is
-- also the compensating-status ledger across the two independent
-- databases, since Snowflake + PostgreSQL cannot share one ACID transaction.
CREATE TABLE IF NOT EXISTS uploads (
    upload_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_type         TEXT NOT NULL
                             CONSTRAINT ck_uploads_type CHECK (upload_type IN ('HISTORICAL', 'CURRENT')),
    file_name           TEXT NOT NULL,
    file_size_bytes     BIGINT,
    file_checksum       TEXT,
    column_mapping      JSONB NOT NULL DEFAULT '{}'::JSONB,

    -- Optional default manufacturing context hints for the upload. A single
    -- CSV may span multiple machines/products, so per-row context always
    -- takes precedence; these are used as fallback/validation hints only.
    organization_id     UUID REFERENCES organizations (organization_id),
    plant_id            UUID REFERENCES plants (plant_id),
    production_line_id  UUID REFERENCES production_lines (production_line_id),
    machine_id          UUID REFERENCES machines (machine_id),
    product_id          UUID REFERENCES products (product_id),
    process_id          UUID REFERENCES processes (process_id),
    operation_id        UUID REFERENCES operations (operation_id),
    parameter_id        UUID REFERENCES parameters (parameter_id),

    status              TEXT NOT NULL DEFAULT 'UPLOADED'
                             CONSTRAINT ck_uploads_status CHECK (status IN (
                                 'UPLOADED',
                                 'BRONZE_LOADING', 'BRONZE_COMPLETED',
                                 'VALIDATING', 'VALIDATION_COMPLETED',
                                 'SILVER_LOADING', 'SILVER_COMPLETED',
                                 'FAILED'
                             )),
    total_rows          INTEGER,
    valid_rows          INTEGER,
    invalid_rows        INTEGER,
    bronze_loaded       BOOLEAN NOT NULL DEFAULT FALSE,
    silver_loaded       BOOLEAN NOT NULL DEFAULT FALSE,
    error_message       TEXT,
    uploaded_by         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads (status);
CREATE INDEX IF NOT EXISTS idx_uploads_upload_type ON uploads (upload_type);
CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON uploads (created_at);

-- Status history audit trail (append-only) for observability of the
-- multi-stage, non-transactional ingestion pipeline.
CREATE TABLE IF NOT EXISTS upload_status_history (
    upload_status_history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id                UUID NOT NULL REFERENCES uploads (upload_id) ON DELETE CASCADE,
    status                   TEXT NOT NULL,
    message                  TEXT,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_upload_status_history_upload_id
    ON upload_status_history (upload_id);
