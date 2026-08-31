"""Drives the upload's status through the pipeline's compensating-status
state machine (see database/migrations/011_uploads.sql and the module
docstring in app/database/postgres for why PostgreSQL and Snowflake can't
share one ACID transaction here).

    UPLOADED -> BRONZE_LOADING -> BRONZE_COMPLETED -> VALIDATING ->
    VALIDATION_COMPLETED -> SILVER_LOADING -> SILVER_COMPLETED
                                                    \\-> FAILED (from any state)

Every transition is persisted immediately via UploadRepository, so if the
process crashes mid-pipeline the upload's last-known-good stage is always
recorded and visible via GET /uploads/{id}/status.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.repositories.upload_repository import UploadRepository

logger = get_logger(__name__)

_VALID_STATUSES = (
    "UPLOADED",
    "BRONZE_LOADING",
    "BRONZE_COMPLETED",
    "VALIDATING",
    "VALIDATION_COMPLETED",
    "SILVER_LOADING",
    "SILVER_COMPLETED",
    "FAILED",
)


class UploadStatusManager:
    def __init__(self, upload_repository: UploadRepository) -> None:
        self._upload_repository = upload_repository

    async def transition(self, upload_id: str, status: str, error_message: str | None = None) -> None:
        if status not in _VALID_STATUSES:
            raise ValueError(f"Unknown upload status: {status}")
        await self._upload_repository.update_status(upload_id, status, error_message)
        logger.info("upload_status_transition", upload_id=upload_id, status=status)

    async def fail(self, upload_id: str, error_message: str) -> None:
        logger.error("upload_pipeline_failed", upload_id=upload_id, error=error_message)
        await self.transition(upload_id, "FAILED", error_message)
