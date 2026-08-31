"""Facade repository for measurement data.

Measurement rows (Bronze + Silver) physically live in Snowflake, not
PostgreSQL -- see database/snowflake/repository.py for the actual SQL /
bulk-load implementation. This module exists so services can depend on a
single, uniform `repositories.*` import surface (consistent with every
other repository in this package) without needing to know that this
particular repository's backing store is Snowflake rather than Postgres.
No SQL lives here; this is pure delegation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd

from app.database.snowflake.repository import SnowflakeIngestionRepository


class MeasurementRepository:
    def __init__(self, snowflake_repository: Optional[SnowflakeIngestionRepository] = None) -> None:
        self._snowflake = snowflake_repository or SnowflakeIngestionRepository()

    async def load_raw_to_bronze(self, upload_id: str, source_file_name: str, df: pd.DataFrame) -> int:
        return await self._snowflake.load_csv_to_bronze(upload_id, source_file_name, df)

    async def load_cleaned_to_silver(self, upload_id: str, source_file_name: str, df: pd.DataFrame) -> int:
        return await self._snowflake.load_cleaned_data_to_silver(upload_id, source_file_name, df)

    async def get_by_upload(self, upload_id: str, valid_only: bool = True) -> pd.DataFrame:
        return await self._snowflake.get_measurements_by_upload(upload_id, valid_only=valid_only)

    async def get_by_context(
        self,
        parameter_id: str,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        valid_only: bool = True,
    ) -> pd.DataFrame:
        return await self._snowflake.get_measurements_by_context(
            parameter_id, machine_id, product_id, operation_id, valid_only=valid_only
        )

    async def get_by_time_range(
        self, parameter_id: str, start: datetime, end: datetime, valid_only: bool = True
    ) -> pd.DataFrame:
        return await self._snowflake.get_measurements_by_time_range(parameter_id, start, end, valid_only=valid_only)
