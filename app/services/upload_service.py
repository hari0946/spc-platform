"""Orchestrates the full CSV ingestion pipeline for both HISTORICAL and
CURRENT uploads:

    file validation -> CSV read -> column mapping -> upload metadata (Postgres)
    -> Bronze (Snowflake) -> row validation/cleaning -> context resolution
    -> Silver (Snowflake) -> row-count summary (Postgres)

PostgreSQL and Snowflake cannot share one transaction, so failure at any
stage after upload-record-creation is handled by transitioning the
upload's status to FAILED with an error message (see
ingestion/upload_status_manager.py) rather than attempting a rollback that
spans both databases.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from app.core.config import Settings
from app.core.exceptions import FileValidationError, UploadProcessingError
from app.core.logging import get_logger
from app.ingestion.bronze_loader import load_bronze
from app.ingestion.column_mapper import apply_column_mapping
from app.ingestion.csv_reader import read_csv
from app.ingestion.file_validator import validate_file_metadata
from app.ingestion.silver_loader import load_silver
from app.ingestion.transformation_pipeline import ContextResolver, UploadContext, run_transformation_pipeline
from app.ingestion.upload_status_manager import UploadStatusManager
from app.ingestion.validation_pipeline import run_validation_pipeline
from app.repositories.machine_repository import MachineRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.operation_repository import OperationRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.upload_repository import UploadRepository
from app.spc_engine.core.enums import QualityStatus

logger = get_logger(__name__)


class UploadService:
    def __init__(
        self,
        settings: Settings,
        upload_repository: UploadRepository,
        measurement_repository: MeasurementRepository,
        machine_repository: MachineRepository,
        product_repository: ProductRepository,
        operation_repository: OperationRepository,
        parameter_repository: ParameterRepository,
    ) -> None:
        self._settings = settings
        self._upload_repository = upload_repository
        self._measurement_repository = measurement_repository
        self._status_manager = UploadStatusManager(upload_repository)
        self._resolver = ContextResolver(machine_repository, product_repository, operation_repository, parameter_repository)

    async def process_upload(
        self,
        upload_type: str,
        file_path: str | Path,
        file_name: str,
        file_size_bytes: int,
        column_mapping: dict[str, str],
        organization_id: Optional[str] = None,
        plant_id: Optional[str] = None,
        production_line_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        process_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        parameter_id: Optional[str] = None,
        uploaded_by: Optional[str] = None,
    ) -> dict[str, Any]:
        if upload_type not in ("HISTORICAL", "CURRENT"):
            raise UploadProcessingError(f"Invalid upload_type: {upload_type}")

        validate_file_metadata(file_name, file_size_bytes, self._settings)

        upload = await self._upload_repository.create(
            upload_type=upload_type,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            column_mapping=column_mapping,
            uploaded_by=uploaded_by,
            organization_id=organization_id,
            plant_id=plant_id,
            production_line_id=production_line_id,
            machine_id=machine_id,
            product_id=product_id,
            process_id=process_id,
            operation_id=operation_id,
            parameter_id=parameter_id,
        )
        upload_id = upload["upload_id"]
        logger.info("upload_created", upload_id=upload_id, upload_type=upload_type, file_name=file_name)

        try:
            await self._run_pipeline(upload_id, file_path, file_name, column_mapping, organization_id, plant_id, production_line_id)
        except FileValidationError:
            raise
        except Exception as exc:  # noqa: BLE001 -- deliberately broad: any pipeline failure must mark FAILED
            logger.error("upload_pipeline_error", upload_id=upload_id, error=str(exc))
            await self._status_manager.fail(upload_id, str(exc))
            raise UploadProcessingError(
                f"Upload processing failed for {upload_id}: {exc}", details={"upload_id": upload_id}
            ) from exc

        return await self._upload_repository.get_by_id(upload_id)

    async def _run_pipeline(
        self,
        upload_id: str,
        file_path: str | Path,
        file_name: str,
        column_mapping: dict[str, str],
        organization_id: Optional[str],
        plant_id: Optional[str],
        production_line_id: Optional[str],
    ) -> None:
        original_df = read_csv(file_path)
        mapped_df = apply_column_mapping(original_df, column_mapping)

        await self._status_manager.transition(upload_id, "BRONZE_LOADING")
        await load_bronze(upload_id, file_name, original_df, mapped_df, self._measurement_repository)
        await self._status_manager.transition(upload_id, "BRONZE_COMPLETED")
        await self._upload_repository.update_row_counts(upload_id, total_rows=len(mapped_df), bronze_loaded=True)

        await self._status_manager.transition(upload_id, "VALIDATING")
        validated_df = run_validation_pipeline(mapped_df)
        valid_rows = int((validated_df["quality_status"] == QualityStatus.VALID.value).sum())
        invalid_rows = len(validated_df) - valid_rows
        await self._status_manager.transition(upload_id, "VALIDATION_COMPLETED")

        upload_context = UploadContext(
            organization_id=organization_id, plant_id=plant_id, production_line_id=production_line_id
        )
        silver_df = await run_transformation_pipeline(validated_df, upload_context, self._resolver)
        valid_after_context = int((silver_df["quality_status"] == QualityStatus.VALID.value).sum())
        invalid_after_context = len(silver_df) - valid_after_context

        await self._status_manager.transition(upload_id, "SILVER_LOADING")
        await load_silver(upload_id, file_name, silver_df, self._measurement_repository)
        await self._status_manager.transition(upload_id, "SILVER_COMPLETED")

        await self._upload_repository.update_row_counts(
            upload_id,
            valid_rows=valid_after_context,
            invalid_rows=invalid_after_context,
            silver_loaded=True,
        )
        logger.info(
            "upload_pipeline_completed",
            upload_id=upload_id,
            total_rows=len(silver_df),
            valid_rows=valid_after_context,
            invalid_rows=invalid_after_context,
        )

    async def get_status(self, upload_id: str) -> dict[str, Any]:
        upload = await self._upload_repository.get_by_id(upload_id)
        if upload is None:
            raise UploadProcessingError(f"Upload {upload_id} not found.")
        history = await self._upload_repository.list_status_history(upload_id)
        return {**upload, "history": history}
