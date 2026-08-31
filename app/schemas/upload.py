"""Request/response schemas for the upload API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.common import APIModel


class UploadResponse(APIModel):
    upload_id: str
    upload_type: str
    file_name: str
    status: str
    total_rows: Optional[int] = None
    valid_rows: Optional[int] = None
    invalid_rows: Optional[int] = None
    bronze_loaded: bool
    silver_loaded: bool
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class UploadStatusHistoryEntry(APIModel):
    status: str
    message: Optional[str] = None
    created_at: datetime


class UploadStatusResponse(UploadResponse):
    history: list[UploadStatusHistoryEntry] = Field(default_factory=list)
