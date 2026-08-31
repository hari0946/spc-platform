"""Loads the transformed, validated DataFrame into Snowflake Silver via
MeasurementRepository, adding source_file_name/source_row_number for
traceability back to Bronze."""

from __future__ import annotations

import pandas as pd

from app.core.logging import get_logger
from app.repositories.measurement_repository import MeasurementRepository

logger = get_logger(__name__)


async def load_silver(
    upload_id: str, source_file_name: str, silver_df: pd.DataFrame, measurement_repository: MeasurementRepository
) -> int:
    df = silver_df.copy()
    df.insert(0, "upload_id", upload_id)
    df["source_file_name"] = source_file_name
    df["source_row_number"] = range(1, len(df) + 1)

    rows_loaded = await measurement_repository.load_cleaned_to_silver(upload_id, source_file_name, df)
    logger.info("silver_load_completed", upload_id=upload_id, rows=rows_loaded)
    return rows_loaded
