-- Quality characteristics measured on the shop floor (e.g. SHAFT_DIAMETER).
--
-- data_type is intentionally constrained to CONTINUOUS only for this phase
-- of the platform (variable/continuous SPC only). Attribute data types
-- (e.g. ATTRIBUTE_DEFECT_COUNT) can be added later via an ALTER TABLE that
-- widens this CHECK constraint -- no structural redesign is required.
CREATE TABLE IF NOT EXISTS parameters (
    parameter_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    description   TEXT,
    data_type     TEXT NOT NULL DEFAULT 'CONTINUOUS'
                      CONSTRAINT ck_parameters_data_type CHECK (data_type IN ('CONTINUOUS')),
    unit          TEXT NOT NULL,
    target_value  NUMERIC,
    active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_parameters_name UNIQUE (name)
);
