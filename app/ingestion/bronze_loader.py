"""Assembles the Bronze-layer DataFrame and loads it via
MeasurementRepository (Snowflake). Bronze rows carry both:
  - the mapped-but-not-yet-validated semantic fields (raw_timestamp,
    raw_machine_id, raw_product_id, raw_operation, raw_parameter,
    raw_value, raw_unit) so Bronze is still useful to query, and
  - the full original CSV row, untouched, in raw_payload -- so the exact
    original source data is always traceable regardless of what the
    column mapping or later cleaning does to it.
"""

from __future__ import annotations

import pandas as pd

from app.core.logging import get_logger
from app.repositories.measurement_repository import MeasurementRepository

logger = get_logger(__name__)

_BRONZE_SEMANTIC_COLUMN_MAP = {
    "event_timestamp": "raw_timestamp",
    "machine_code": "raw_machine_id",
    "product_code": "raw_product_id",
    "operation_code": "raw_operation",
    "parameter_name": "raw_parameter",
    "value": "raw_value",
    "unit": "raw_unit",
}


def build_bronze_dataframe(original_df: pd.DataFrame, mapped_df: pd.DataFrame) -> pd.DataFrame:
    bronze = mapped_df.rename(columns=_BRONZE_SEMANTIC_COLUMN_MAP)[list(_BRONZE_SEMANTIC_COLUMN_MAP.values())].copy()
    bronze["raw_payload"] = original_df.to_dict(orient="records")
    return bronze


async def load_bronze(
    upload_id: str,
    source_file_name: str,
    original_df: pd.DataFrame,
    mapped_df: pd.DataFrame,
    measurement_repository: MeasurementRepository,
) -> int:
    bronze_df = build_bronze_dataframe(original_df, mapped_df)
    rows_loaded = await measurement_repository.load_raw_to_bronze(upload_id, source_file_name, bronze_df)
    logger.info("bronze_load_completed", upload_id=upload_id, rows=rows_loaded)
    return rows_loaded
