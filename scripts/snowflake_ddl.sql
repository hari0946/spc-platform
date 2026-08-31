-- =============================================================================
-- Snowflake medallion architecture setup: SPC_PLATFORM database, BRONZE and
-- SILVER schemas. Run this once against your Snowflake account (as a role
-- with CREATE DATABASE / CREATE SCHEMA / CREATE TABLE privileges) before
-- starting the API. This is intentionally plain, explicit SQL -- it is not
-- executed by the application; run it manually via SnowSQL, the Snowflake
-- web UI, or your own deployment tooling.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS SPC_PLATFORM;

CREATE SCHEMA IF NOT EXISTS SPC_PLATFORM.BRONZE;
CREATE SCHEMA IF NOT EXISTS SPC_PLATFORM.SILVER;
-- Reserved for future aggregate/analytics views -- not used by this phase.
CREATE SCHEMA IF NOT EXISTS SPC_PLATFORM.GOLD;

-- -----------------------------------------------------------------------------
-- BRONZE: raw, untouched ingested rows. Never updated or overwritten -- one
-- row per source CSV row, exactly as uploaded, with the full original row
-- preserved in raw_payload for traceability.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS SPC_PLATFORM.BRONZE.RAW_MEASUREMENTS (
    raw_record_id       STRING NOT NULL,
    upload_id            STRING NOT NULL,
    source_file_name      STRING NOT NULL,
    source_row_number      NUMBER NOT NULL,
    ingestion_timestamp      TIMESTAMP_NTZ NOT NULL,
    raw_timestamp              STRING,
    raw_machine_id               STRING,
    raw_product_id                 STRING,
    raw_operation                   STRING,
    raw_parameter                     STRING,
    raw_value                           STRING,
    raw_unit                              STRING,
    raw_payload                             VARIANT,
    processing_status                         STRING DEFAULT 'INGESTED',
    load_timestamp                              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- -----------------------------------------------------------------------------
-- SILVER: validated, standardized, typed measurements ready for SPC.
-- quality_status = 'VALID' rows are the only ones normally used for SPC
-- calculations; others remain queryable for traceability.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS SPC_PLATFORM.SILVER.MEASUREMENTS (
    measurement_id       STRING NOT NULL,
    upload_id             STRING NOT NULL,
    event_timestamp        TIMESTAMP_NTZ,
    organization_id          STRING,
    plant_id                   STRING,
    production_line_id           STRING,
    machine_id                     STRING,
    product_id                       STRING,
    process_id                         STRING,
    operation_id                         STRING,
    parameter_id                           STRING NOT NULL,
    measurement_value                        FLOAT,
    unit                                       STRING,
    batch_id                                     STRING,
    subgroup_id                                    STRING,
    shift                                            STRING,
    operator_id                                        STRING,
    source_file_name                                     STRING,
    source_row_number                                      NUMBER,
    quality_status                                           STRING NOT NULL,
    validation_notes                                           STRING,
    created_at                                                   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Internal named stage used by the DEMO/PRODUCTION bulk-loading strategy
-- (see app/database/snowflake/repository.py). write_pandas() manages its
-- own temporary stage by default, but an explicit named stage is kept here
-- for PRODUCTION-mode COPY INTO usage against pre-staged files.
CREATE STAGE IF NOT EXISTS SPC_PLATFORM.BRONZE.SPC_INGEST_STAGE
    FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);
