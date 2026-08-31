# Automotive SPC Platform

A production-grade backend for Automotive Statistical Process Control:
Phase 1 historical baseline analysis and Phase 2 manual batch comparison
against a frozen baseline, for continuous/variable measurement data.

No ORM. All PostgreSQL access is explicit, parameterized SQL through a
repository layer (`asyncpg`). All SPC mathematics live in a
database-agnostic, framework-agnostic engine (`app/spc_engine/`) that
takes a pandas DataFrame in and returns typed dataclasses out.

## Architecture

```
CSV Upload -> FastAPI -> Ingestion Service -> PostgreSQL (upload metadata)
                                            -> Snowflake BRONZE (raw, immutable)
                                            -> Validation -> Snowflake SILVER (cleaned)
                                                                  |
                                                                  v
                                                          MeasurementRepository
                                                                  |
                                                                  v
                                          Service layer (app/services)
                                                                  |
                                                                  v
                                     SPC Engine (app/spc_engine) -- pure math, no I/O
                                     profiling -> subgrouping -> chart selection ->
                                     charts -> sigma/statistics -> capability -> rules
                                                                  |
                                                                  v
                                          PostgreSQL (analysis_results, baselines,
                                          manual_check_runs, findings, alerts)
```

PostgreSQL holds all application metadata, configuration, and summarized
results. Snowflake (Bronze/Silver medallion layers) holds the actual
measurement data. See `database-responsibilities` below.

### Database responsibilities

| PostgreSQL | Snowflake |
|---|---|
| organizations, plants, production_lines, machines, products, processes, operations, parameters, specifications | BRONZE.RAW_MEASUREMENTS (immutable raw rows) |
| uploads, spc_configurations, rule_configurations | SILVER.MEASUREMENTS (validated, standardized) |
| analysis_runs, analysis_results, baselines | |
| manual_check_runs, comparison_results, rule_violations, findings, alerts | |

## Project layout

```
app/
  main.py                    FastAPI app, lifespan (pool + migrations), exception handlers
  api/routes/                One router module per resource
  core/                      config, logging, exceptions, DI wiring
  database/
    postgres/                connection pool, transaction helper, plain-SQL migration runner
    snowflake/                connection + SnowflakeIngestionRepository (Bronze/Silver bulk load)
    migrations/                001..022_*.sql  (plain SQL, no ORM)
  repositories/               One repository per table/aggregate; raw parameterized SQL only
  schemas/                    Pydantic v2 request/response models (API boundary only)
  services/                   Orchestration: repositories + SPC engine, transaction boundaries
  ingestion/                   csv_reader -> file_validator -> column_mapper -> bronze_loader
                                -> validation_pipeline -> transformation_pipeline -> silver_loader
  spc_engine/                   Pure Python + pandas/numpy/scipy. Zero FastAPI/SQL/DB imports.
    core/                        enums, dataclass models, Shewhart constants table, exceptions
    validation/                  row + dataset level validation (never discards SPC outliers)
    profiling/                   dataset profiling before subgrouping
    subgrouping/                 EXISTING_ID / FIXED_SIZE / CONSECUTIVE / TIME_WINDOW
    chart_selection/              I-MR / XBAR-R / XBAR-S recommendation + override validation
    charts/                       one module per chart type, shared BaseChart interface
    statistics/                   descriptive stats, within-sigma vs overall-sigma estimation
    capability/                    Cp/Cpk/Cpu/Cpl/Pp/Ppk/Ppu/Ppl -- never crashes, always warns
    rules/                         point-outside-limits, trend, shift/run rules + RuleEngine
    comparison/                    current-vs-frozen-baseline arithmetic
    findings/                      turns comparison + violations into fact-only findings + final status
    results/                       result_builder.run_spc_analysis() -- the engine's one public entrypoint
tests/
  spc_engine/                  Pure unit tests, no DB required
  services/                    Service tests with repositories mocked
  repositories/                Integration tests against a real PostgreSQL (auto-skip if unreachable)
scripts/
  snowflake_ddl.sql            Run once, manually, against your Snowflake account
  smoke_test_engine.py          Quick manual SPC engine sanity check
  e2e_smoke_test.py             Full Phase 1 + Phase 2 flow against local Postgres (Snowflake faked)
```

## Setup

### 1. Python environment

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements-dev.txt
```

### 2. PostgreSQL (local demo)

```bash
docker compose up -d postgres
cp .env.example .env          # defaults already match docker-compose.yml
```

Migrations run automatically on API startup (see `app/main.py` lifespan).
To apply them without starting the API:

```python
import asyncio
from app.database.postgres.connection import create_pool, close_pool
from app.database.postgres.migration_runner import run_migrations

async def main():
    pool = await create_pool()
    await run_migrations(pool)
    await close_pool()

asyncio.run(main())
```

### 3. Snowflake

Run `scripts/snowflake_ddl.sql` once against your Snowflake account (creates
the `SPC_PLATFORM` database, `BRONZE`/`SILVER` schemas, tables, and an
internal stage). Fill in the `SNOWFLAKE_*` variables in `.env` -- in
particular `SNOWFLAKE_ROLE` and `SNOWFLAKE_WAREHOUSE` must name a role and
warehouse that already exist in your account (the DDL script doesn't create
either); `SHOW WAREHOUSES` / `SHOW ROLES` in a Snowflake worksheet will list
what you have available (a trial account typically has `COMPUTE_WH`).

For a client demo without a provisioned Snowflake account, set
`INGESTION_MODE=DEMO` in `.env` -- this only changes how bulk-loading
happens once you *do* have a Snowflake connection (chunked parameterized
inserts vs. stage+COPY INTO); it does not remove the Snowflake dependency
itself. The full ingestion pipeline can also be exercised without any
Snowflake account at all by substituting an in-memory
`MeasurementRepository` (see `scripts/e2e_smoke_test.py`), which is how
this project was validated during development.

### 4. Run the API

```bash
uvicorn app.main:app --reload
```

Interactive API docs: `http://localhost:8000/docs`

## Testing

```bash
pytest                       # full suite; repository integration tests
                              # auto-skip if PostgreSQL isn't reachable
pytest tests/spc_engine       # pure SPC math, no DB required
pytest tests/services         # service orchestration, repositories mocked
pytest tests/repositories     # real SQL against a real DB (docker compose up -d postgres)
```

`scripts/e2e_smoke_test.py` exercises the complete business flow (seed
manufacturing context -> historical upload -> historical analysis ->
baseline draft -> baseline approval -> current upload -> manual check ->
findings/final status) against a live local PostgreSQL instance. By default
it fakes the Snowflake-backed MeasurementRepository in-memory; pass
`--real-snowflake` to run the same flow against your actual Snowflake
account (requires `.env` to be filled in and `scripts/snowflake_ddl.sql` to
have already been run):

```bash
python scripts/e2e_smoke_test.py --real-snowflake
```

## Design decisions worth knowing about

- **Baselines are frozen.** Approving a baseline snapshots its control
  limits, sigma, and capability indices into `baselines`. Phase 2 manual
  checks apply those exact numbers to new data -- they are never
  recalculated automatically. Only a brand-new historical analysis +
  explicit approval can change what "the baseline" means.
- **Statistical unusualness is not a data quality problem.** The
  validation pipeline only marks a row invalid for genuine data issues
  (missing/malformed values, duplicates, unresolvable context, unit
  mismatches). SPC outliers are exactly what the chart/rule engine exists
  to detect and are never silently dropped upstream of it.
- **Findings state fact, not cause.** `findings_engine.py` reports "Cpk
  decreased from 1.50 to 1.05", never a guess like "tool wear caused
  this". Root-cause tooling, if added later, is a separate, clearly
  labelled concern.
- **PostgreSQL and Snowflake are separate databases.** Upload processing
  cannot share one ACID transaction across them, so `uploads.status` is a
  compensating-transaction ledger (`UPLOADED -> BRONZE_LOADING -> ... ->
  SILVER_COMPLETED`, or `FAILED` with an error message) rather than a
  pretend distributed transaction.
- **Unequal subgroup sizes are handled, not ignored.** Time-gap-based
  subgrouping can legitimately produce a smaller trailing subgroup. Rather
  than mixing subgroup sizes into one (invalid) set of Shewhart constants,
  `charts/base_chart.py` selects the dominant subgroup size and reports
  the rest as excluded via a warning.
