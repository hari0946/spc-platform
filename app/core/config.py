"""Centralized application configuration, loaded from environment
variables / .env via pydantic-settings. Nothing else in the codebase reads
os.environ directly -- every configurable value (DB credentials, ingestion
mode, upload limits, SPC defaults) flows through this module.
"""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


def _ensure_sslmode_require(dsn: str) -> str:
    """Append ``sslmode=require`` to a Postgres DSN if it isn't already
    present. Railway's Postgres SSL template requires TLS connections --
    without this, asyncpg's connection attempt is rejected and the pool
    never comes up, crashing the app on startup.
    """
    parts = urlsplit(dsn)
    query_pairs = parse_qsl(parts.query, keep_blank_values=True)
    if any(key.lower() == "sslmode" for key, _ in query_pairs):
        return dsn
    query_pairs.append(("sslmode", "require"))
    new_query = urlencode(query_pairs)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "SPC Platform"
    app_env: str = "development"
    app_debug: bool = True
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    log_format: str = "json"

    # Comma-separated list of origins allowed to call this API from a
    # browser (the React frontend runs on a different origin/port during
    # development, e.g. http://localhost:5173, so CORS must be explicit --
    # without it every browser-based API call fails silently while curl/
    # server-to-server calls appear to work fine).
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "spc_platform"
    postgres_user: str = "spc_app"
    postgres_password: str = "change_me"
    postgres_pool_min_size: int = 2
    postgres_pool_max_size: int = 10
    postgres_command_timeout_seconds: int = 30

    # Snowflake
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_role: str = ""
    snowflake_warehouse: str = ""
    snowflake_database: str = "SPC_PLATFORM"
    snowflake_bronze_schema: str = "BRONZE"
    snowflake_silver_schema: str = "SILVER"
    snowflake_internal_stage: str = "SPC_INGEST_STAGE"

    ingestion_mode: str = "DEMO"  # DEMO | PRODUCTION
    ingestion_batch_rows: int = 5000

    # Uploads
    upload_max_file_size_mb: int = 200
    upload_temp_dir: str = "./var/uploads"
    upload_allowed_extensions: str = ".csv"

    # SPC defaults
    spc_default_minimum_sample_size: int = 20
    spc_default_subgroup_size: int = 5
    spc_default_max_time_gap_seconds: int = 3600

    @property
    def postgres_dsn(self) -> str:
        dsn = (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        return _ensure_sslmode_require(dsn)

    @property
    def allowed_upload_extensions(self) -> list[str]:
        return [ext.strip().lower() for ext in self.upload_allowed_extensions.split(",") if ext.strip()]

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
