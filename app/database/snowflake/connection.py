"""Snowflake connection management.

snowflake-connector-python is a synchronous client; every call to it in
this module (and in snowflake/repository.py) is a blocking call and must
be dispatched via asyncio.to_thread() from async service code so it never
blocks the FastAPI event loop.
"""

from __future__ import annotations

import snowflake.connector

from app.core.config import Settings, get_settings
from app.core.exceptions import SnowflakeOperationError
from app.core.logging import get_logger

logger = get_logger(__name__)


def open_connection(settings: Settings | None = None) -> snowflake.connector.SnowflakeConnection:
    """Open a new, single-use Snowflake connection.

    Kept intentionally simple (no persistent pool) since Snowflake
    connections are comparatively expensive to hold open and ingestion /
    query operations here are batch-oriented, not high-frequency.
    """
    settings = settings or get_settings()
    try:
        return snowflake.connector.connect(
            account=settings.snowflake_account,
            user=settings.snowflake_user,
            password=settings.snowflake_password,
            role=settings.snowflake_role or None,
            warehouse=settings.snowflake_warehouse or None,
            database=settings.snowflake_database,
            client_session_keep_alive=False,
        )
    except snowflake.connector.errors.Error as exc:
        logger.error("snowflake_connection_failed", error=str(exc))
        raise SnowflakeOperationError(
            "Could not connect to Snowflake. Check SNOWFLAKE_* environment variables and "
            "that the account/warehouse are reachable.",
            details={"reason": str(exc)},
        ) from exc
