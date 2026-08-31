CREATE TABLE IF NOT EXISTS operations (
    operation_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    process_id      UUID NOT NULL REFERENCES processes (process_id) ON DELETE RESTRICT,
    name            TEXT NOT NULL,
    code            TEXT NOT NULL,
    sequence_number INTEGER,
    description     TEXT,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_operations_process_code UNIQUE (process_id, code)
);

CREATE INDEX IF NOT EXISTS idx_operations_process_id ON operations (process_id);
