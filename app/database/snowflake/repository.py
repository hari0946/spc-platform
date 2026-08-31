"""SnowflakeIngestionRepository: all Bronze/Silver read & write access lives
here. No SPC math, no PostgreSQL access -- this module talks to Snowflake
only, via explicit SQL / the Snowflake pandas bulk-load helpers.

Ingestion strategy is configurable via settings.ingestion_mode:
  DEMO       - chunked, parameterized batch INSERT statements
               (snowflake-connector executemany), sized by
               settings.ingestion_batch_rows. No external stage/cloud
               storage setup required -- ideal for a client demo.
  PRODUCTION - snowflake.connector.pandas_tools.write_pandas(), which
               transparently PUTs the DataFrame to a temporary stage and
               COPY INTOs it -- the standard high-volume bulk load path.

All snowflake-connector-python calls are synchronous; every public method
here is `async def` and dispatches the actual connector work via
asyncio.to_thread so the FastAPI event loop is never blocked.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

from app.core.config import Settings, get_settings
from app.core.exceptions import SnowflakeOperationError
from app.core.logging import get_logger
from app.database.snowflake.connection import open_connection

logger = get_logger(__name__)

_BRONZE_TABLE = "RAW_MEASUREMENTS"
_SILVER_TABLE = "MEASUREMENTS"


class SnowflakeIngestionRepository:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    # ------------------------------------------------------------------
    # Bronze
    # ------------------------------------------------------------------

    async def load_csv_to_bronze(self, upload_id: str, source_file_name: str, df: pd.DataFrame) -> int:
        """Load raw, untouched CSV rows into Bronze. `df` should carry the
        original column names/values (already read as strings where
        possible) plus a `raw_payload` dict per row for full traceability.

        upload_id is coerced to str here (not just type-hinted as one):
        callers upstream generally source it from a PostgreSQL row via
        asyncpg, which returns UUID columns as uuid.UUID objects, and the
        Snowflake connector's parameter binding does not know how to bind
        those directly.
        """
        return await asyncio.to_thread(self._load_csv_to_bronze_sync, str(upload_id), source_file_name, df)

    def _load_csv_to_bronze_sync(self, upload_id: str, source_file_name: str, df: pd.DataFrame) -> int:
        connection = open_connection(self._settings)
        try:
            if self._settings.ingestion_mode.upper() == "PRODUCTION":
                return self._bulk_load_bronze_production(connection, upload_id, source_file_name, df)
            return self._batch_insert_bronze_demo(connection, upload_id, source_file_name, df)
        except snowflake.connector.errors.Error as exc:
            logger.error("snowflake_bronze_load_failed", upload_id=upload_id, error=str(exc))
            raise SnowflakeOperationError(
                f"Failed to load raw data into Snowflake Bronze for upload {upload_id}.",
                details={"reason": str(exc)},
            ) from exc
        finally:
            connection.close()

    def _batch_insert_bronze_demo(
        self, connection: snowflake.connector.SnowflakeConnection, upload_id: str, source_file_name: str, df: pd.DataFrame
    ) -> int:
        """DEMO-mode bulk insert.

        NOTE: snowflake-connector-python's executemany() multi-row rewrite
        cannot bind a value into a semi-structured VARIANT column (neither
        `VALUES (..., PARSE_JSON(%(x)s))` -- rejected by Snowflake as an
        invalid VALUES-clause expression -- nor `SELECT ..., PARSE_JSON(%(x)s)`
        -- rejected by the connector itself with "Failed to rewrite
        multi-row insert", since the rewrite optimization only recognizes a
        literal VALUES(...) template). So raw_payload is first batch-inserted
        as plain STRING into a temporary staging table (a shape executemany
        handles natively), then converted to VARIANT in a single
        INSERT ... SELECT ..., PARSE_JSON(...) statement -- the same
        staging-then-transform pattern PRODUCTION mode uses via write_pandas.
        """
        now = datetime.now(timezone.utc)
        rows = []
        for row_number, record in enumerate(df.to_dict(orient="records"), start=1):
            rows.append(
                {
                    "raw_record_id": str(uuid.uuid4()),
                    "upload_id": upload_id,
                    "source_file_name": source_file_name,
                    "source_row_number": row_number,
                    "ingestion_timestamp": now,
                    "raw_timestamp": _to_str(record.get("raw_timestamp")),
                    "raw_machine_id": _to_str(record.get("raw_machine_id")),
                    "raw_product_id": _to_str(record.get("raw_product_id")),
                    "raw_operation": _to_str(record.get("raw_operation")),
                    "raw_parameter": _to_str(record.get("raw_parameter")),
                    "raw_value": _to_str(record.get("raw_value")),
                    "raw_unit": _to_str(record.get("raw_unit")),
                    "raw_payload": _to_json(record.get("raw_payload", record)),
                    "processing_status": "INGESTED",
                }
            )

        schema = self._settings.snowflake_bronze_schema
        staging_table = f"BRONZE_STAGING_{uuid.uuid4().hex[:12].upper()}"
        insert_sql = f"""
            INSERT INTO {schema}.{staging_table}
                (raw_record_id, upload_id, source_file_name, source_row_number,
                 ingestion_timestamp, raw_timestamp, raw_machine_id, raw_product_id,
                 raw_operation, raw_parameter, raw_value, raw_unit, raw_payload_json, processing_status)
            VALUES (%(raw_record_id)s, %(upload_id)s, %(source_file_name)s, %(source_row_number)s,
                    %(ingestion_timestamp)s, %(raw_timestamp)s, %(raw_machine_id)s, %(raw_product_id)s,
                    %(raw_operation)s, %(raw_parameter)s, %(raw_value)s, %(raw_unit)s,
                    %(raw_payload)s, %(processing_status)s)
        """
        batch_size = self._settings.ingestion_batch_rows
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TEMPORARY TABLE {schema}.{staging_table} (
                    raw_record_id STRING, upload_id STRING, source_file_name STRING,
                    source_row_number NUMBER, ingestion_timestamp TIMESTAMP_NTZ,
                    raw_timestamp STRING, raw_machine_id STRING, raw_product_id STRING,
                    raw_operation STRING, raw_parameter STRING, raw_value STRING,
                    raw_unit STRING, raw_payload_json STRING, processing_status STRING
                )
                """
            )
            try:
                for start in range(0, len(rows), batch_size):
                    chunk = rows[start : start + batch_size]
                    cursor.executemany(insert_sql, chunk)

                cursor.execute(
                    f"""
                    INSERT INTO {schema}.{_BRONZE_TABLE}
                        (raw_record_id, upload_id, source_file_name, source_row_number,
                         ingestion_timestamp, raw_timestamp, raw_machine_id, raw_product_id,
                         raw_operation, raw_parameter, raw_value, raw_unit, raw_payload, processing_status)
                    SELECT raw_record_id, upload_id, source_file_name, source_row_number,
                           ingestion_timestamp, raw_timestamp, raw_machine_id, raw_product_id,
                           raw_operation, raw_parameter, raw_value, raw_unit,
                           PARSE_JSON(raw_payload_json), processing_status
                    FROM {schema}.{staging_table}
                    """
                )
                loaded = len(rows)
            finally:
                cursor.execute(f"DROP TABLE IF EXISTS {schema}.{staging_table}")

        logger.info("snowflake_bronze_batch_insert_completed", upload_id=upload_id, rows=loaded)
        return loaded

    def _bulk_load_bronze_production(
        self, connection: snowflake.connector.SnowflakeConnection, upload_id: str, source_file_name: str, df: pd.DataFrame
    ) -> int:
        now = datetime.now(timezone.utc)
        staging = df.copy()
        staging.insert(0, "RAW_RECORD_ID", [str(uuid.uuid4()) for _ in range(len(staging))])
        staging.insert(1, "UPLOAD_ID", upload_id)
        staging.insert(2, "SOURCE_FILE_NAME", source_file_name)
        staging["SOURCE_ROW_NUMBER"] = range(1, len(staging) + 1)
        staging["INGESTION_TIMESTAMP"] = now
        staging["RAW_PAYLOAD_JSON"] = [
            _to_json(record) for record in df.to_dict(orient="records")
        ]
        staging["PROCESSING_STATUS"] = "INGESTED"
        staging = staging.rename(
            columns={
                "raw_timestamp": "RAW_TIMESTAMP",
                "raw_machine_id": "RAW_MACHINE_ID",
                "raw_product_id": "RAW_PRODUCT_ID",
                "raw_operation": "RAW_OPERATION",
                "raw_parameter": "RAW_PARAMETER",
                "raw_value": "RAW_VALUE",
                "raw_unit": "RAW_UNIT",
            }
        )
        keep_columns = [
            "RAW_RECORD_ID", "UPLOAD_ID", "SOURCE_FILE_NAME", "SOURCE_ROW_NUMBER",
            "INGESTION_TIMESTAMP", "RAW_TIMESTAMP", "RAW_MACHINE_ID", "RAW_PRODUCT_ID",
            "RAW_OPERATION", "RAW_PARAMETER", "RAW_VALUE", "RAW_UNIT", "RAW_PAYLOAD_JSON",
            "PROCESSING_STATUS",
        ]
        staging = staging[[c for c in keep_columns if c in staging.columns]]

        staging_table = f"BRONZE_STAGING_{uuid.uuid4().hex[:12].upper()}"
        schema = self._settings.snowflake_bronze_schema
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TEMPORARY TABLE {schema}.{staging_table} (
                    RAW_RECORD_ID STRING, UPLOAD_ID STRING, SOURCE_FILE_NAME STRING,
                    SOURCE_ROW_NUMBER NUMBER, INGESTION_TIMESTAMP TIMESTAMP_NTZ,
                    RAW_TIMESTAMP STRING, RAW_MACHINE_ID STRING, RAW_PRODUCT_ID STRING,
                    RAW_OPERATION STRING, RAW_PARAMETER STRING, RAW_VALUE STRING,
                    RAW_UNIT STRING, RAW_PAYLOAD_JSON STRING, PROCESSING_STATUS STRING
                )
                """
            )
        try:
            success, _, num_rows, _ = write_pandas(
                connection, staging, staging_table, schema=schema, quote_identifiers=False
            )
            if not success:
                raise SnowflakeOperationError("write_pandas reported failure loading Bronze staging table.")

            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {schema}.{_BRONZE_TABLE}
                        (raw_record_id, upload_id, source_file_name, source_row_number,
                         ingestion_timestamp, raw_timestamp, raw_machine_id, raw_product_id,
                         raw_operation, raw_parameter, raw_value, raw_unit, raw_payload, processing_status)
                    SELECT RAW_RECORD_ID, UPLOAD_ID, SOURCE_FILE_NAME, SOURCE_ROW_NUMBER,
                           INGESTION_TIMESTAMP, RAW_TIMESTAMP, RAW_MACHINE_ID, RAW_PRODUCT_ID,
                           RAW_OPERATION, RAW_PARAMETER, RAW_VALUE, RAW_UNIT,
                           PARSE_JSON(RAW_PAYLOAD_JSON), PROCESSING_STATUS
                    FROM {schema}.{staging_table}
                    """
                )
            logger.info("snowflake_bronze_bulk_load_completed", upload_id=upload_id, rows=int(num_rows))
            return int(num_rows)
        finally:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {schema}.{staging_table}")

    # ------------------------------------------------------------------
    # Silver
    # ------------------------------------------------------------------

    async def load_cleaned_data_to_silver(self, upload_id: str, source_file_name: str, df: pd.DataFrame) -> int:
        """Load validated/standardized measurements into Silver. Expects
        columns matching SILVER.MEASUREMENTS (see transformation_pipeline.py
        for the DataFrame shape produced upstream). See load_csv_to_bronze()
        for why upload_id is explicitly coerced to str."""
        return await asyncio.to_thread(self._load_silver_sync, str(upload_id), source_file_name, df)

    def _load_silver_sync(self, upload_id: str, source_file_name: str, df: pd.DataFrame) -> int:
        connection = open_connection(self._settings)
        try:
            if self._settings.ingestion_mode.upper() == "PRODUCTION":
                return self._bulk_load_silver_production(connection, df)
            return self._batch_insert_silver_demo(connection, df)
        except snowflake.connector.errors.Error as exc:
            logger.error("snowflake_silver_load_failed", upload_id=upload_id, error=str(exc))
            raise SnowflakeOperationError(
                f"Failed to load cleaned data into Snowflake Silver for upload {upload_id}.",
                details={"reason": str(exc)},
            ) from exc
        finally:
            connection.close()

    def _batch_insert_silver_demo(
        self, connection: snowflake.connector.SnowflakeConnection, df: pd.DataFrame
    ) -> int:
        # The connector's pyformat binding path only accepts Python
        # str/int/float/bool/None (plus a few Snowflake-native wrapper
        # types) -- not raw datetime/pandas.Timestamp/numpy scalars, which
        # pandas DataFrames naturally carry. Normalize every value to a
        # bindable type before executemany().
        rows = [{k: _normalize_for_binding(v) for k, v in record.items()} for record in df.to_dict(orient="records")]
        for row in rows:
            row.setdefault("measurement_id", str(uuid.uuid4()))

        sql = f"""
            INSERT INTO {self._settings.snowflake_silver_schema}.{_SILVER_TABLE}
                (measurement_id, upload_id, event_timestamp, organization_id, plant_id,
                 production_line_id, machine_id, product_id, process_id, operation_id,
                 parameter_id, measurement_value, unit, batch_id, subgroup_id, shift,
                 operator_id, source_file_name, source_row_number, quality_status, validation_notes)
            VALUES (%(measurement_id)s, %(upload_id)s, %(event_timestamp)s, %(organization_id)s, %(plant_id)s,
                    %(production_line_id)s, %(machine_id)s, %(product_id)s, %(process_id)s, %(operation_id)s,
                    %(parameter_id)s, %(measurement_value)s, %(unit)s, %(batch_id)s, %(subgroup_id)s, %(shift)s,
                    %(operator_id)s, %(source_file_name)s, %(source_row_number)s, %(quality_status)s, %(validation_notes)s)
        """
        batch_size = self._settings.ingestion_batch_rows
        loaded = 0
        with connection.cursor() as cursor:
            for start in range(0, len(rows), batch_size):
                chunk = rows[start : start + batch_size]
                cursor.executemany(sql, chunk)
                loaded += len(chunk)
        logger.info("snowflake_silver_batch_insert_completed", rows=loaded)
        return loaded

    def _bulk_load_silver_production(
        self, connection: snowflake.connector.SnowflakeConnection, df: pd.DataFrame
    ) -> int:
        staging = df.copy()
        if "measurement_id" not in staging.columns:
            staging.insert(0, "measurement_id", [str(uuid.uuid4()) for _ in range(len(staging))])
        # write_pandas serializes via pyarrow, which -- like the connector's
        # own pyformat binding -- cannot handle uuid.UUID/pandas.Timestamp
        # values directly (see _normalize_for_binding for why these appear
        # here at all).
        staging = staging.map(_normalize_for_binding)
        staging.columns = [c.upper() for c in staging.columns]
        success, _, num_rows, _ = write_pandas(
            connection,
            staging,
            _SILVER_TABLE,
            schema=self._settings.snowflake_silver_schema,
            quote_identifiers=False,
        )
        if not success:
            raise SnowflakeOperationError("write_pandas reported failure loading Silver.")
        logger.info("snowflake_silver_bulk_load_completed", rows=int(num_rows))
        return int(num_rows)

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def get_measurements_by_upload(self, upload_id: str, valid_only: bool = True) -> pd.DataFrame:
        where = "WHERE upload_id = %(upload_id)s"
        if valid_only:
            where += " AND quality_status = 'VALID'"
        sql = f"{self._select_measurements_sql()} {where} ORDER BY event_timestamp NULLS LAST, source_row_number"
        return await asyncio.to_thread(self._fetch_df_sync, sql, {"upload_id": upload_id})

    async def get_measurements_by_context(
        self,
        parameter_id: str,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        valid_only: bool = True,
    ) -> pd.DataFrame:
        conditions = ["parameter_id = %(parameter_id)s"]
        params: dict[str, Any] = {"parameter_id": parameter_id}
        if machine_id:
            conditions.append("machine_id = %(machine_id)s")
            params["machine_id"] = machine_id
        if product_id:
            conditions.append("product_id = %(product_id)s")
            params["product_id"] = product_id
        if operation_id:
            conditions.append("operation_id = %(operation_id)s")
            params["operation_id"] = operation_id
        if valid_only:
            conditions.append("quality_status = 'VALID'")
        sql = (
            f"{self._select_measurements_sql()} WHERE {' AND '.join(conditions)} "
            f"ORDER BY event_timestamp NULLS LAST, source_row_number"
        )
        return await asyncio.to_thread(self._fetch_df_sync, sql, params)

    async def get_measurements_by_time_range(
        self, parameter_id: str, start: datetime, end: datetime, valid_only: bool = True
    ) -> pd.DataFrame:
        conditions = [
            "parameter_id = %(parameter_id)s",
            "event_timestamp >= %(start)s",
            "event_timestamp <= %(end)s",
        ]
        if valid_only:
            conditions.append("quality_status = 'VALID'")
        sql = (
            f"{self._select_measurements_sql()} WHERE {' AND '.join(conditions)} "
            f"ORDER BY event_timestamp"
        )
        params = {"parameter_id": parameter_id, "start": start, "end": end}
        return await asyncio.to_thread(self._fetch_df_sync, sql, params)

    def _select_measurements_sql(self) -> str:
        return f"""
            SELECT
                measurement_id, upload_id, event_timestamp, organization_id, plant_id,
                production_line_id, machine_id, product_id, process_id, operation_id,
                parameter_id, measurement_value AS value, unit, batch_id, subgroup_id,
                shift, operator_id, quality_status
            FROM {self._settings.snowflake_silver_schema}.{_SILVER_TABLE}
        """

    def _fetch_df_sync(self, sql: str, params: dict[str, Any]) -> pd.DataFrame:
        connection = open_connection(self._settings)
        try:
            with connection.cursor() as cursor:
                # Query params (parameter_id, machine_id, ...) are typically
                # sourced straight from a PostgreSQL row via asyncpg, i.e.
                # uuid.UUID objects -- see _normalize_for_binding.
                cursor.execute(sql, {k: _normalize_for_binding(v) for k, v in params.items()})
                return cursor.fetch_pandas_all()
        except snowflake.connector.errors.Error as exc:
            logger.error("snowflake_query_failed", error=str(exc))
            raise SnowflakeOperationError(
                "Failed to query measurements from Snowflake Silver.", details={"reason": str(exc)}
            ) from exc
        finally:
            connection.close()


def _normalize_for_binding(value: Any) -> Any:
    """Coerce a pandas/numpy-flavored value into something
    snowflake-connector-python's pyformat parameter binding actually
    supports.

    The connector dispatches on the *exact* class name of the value (see
    snowflake.connector.converter.to_snowflake), not on isinstance/MRO, so
    a pandas.Timestamp (a datetime.datetime subclass) is NOT accepted where
    a plain datetime.datetime is, a uuid.UUID is not accepted at all, and
    numpy scalar types (numpy.int64, numpy.float64, ...) are likewise not
    guaranteed to match. Everything is normalized down to plain Python
    str/int/float/bool/datetime/None.

    UUID values are extremely common here: manufacturing-context columns
    (machine_id, product_id, organization_id, ...) are resolved from
    PostgreSQL via asyncpg, which returns UUID columns as uuid.UUID
    objects, not strings.
    """
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.to_pydatetime()
    if isinstance(value, float) and pd.isna(value):
        return None
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        # numpy scalar (int64, float64, bool_, ...) -> native Python type.
        try:
            return value.item()
        except (ValueError, AttributeError):
            return value
    return value


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    return str(value)


def _to_json(value: Any) -> str:
    import json

    if isinstance(value, dict):
        return json.dumps({k: (None if isinstance(v, float) and pd.isna(v) else v) for k, v in value.items()}, default=str)
    return json.dumps(value, default=str)
