"""POST /uploads/historical, POST /uploads/current, GET /uploads/{upload_id}/status"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.config import Settings
from app.core.dependencies import get_app_settings, get_upload_service
from app.core.exceptions import FileValidationError
from app.schemas.upload import UploadResponse, UploadStatusResponse
from app.services.upload_service import UploadService

router = APIRouter(tags=["uploads"])


def _blank_to_none(value: Optional[str]) -> Optional[str]:
    """Swagger UI's "Try it out" form (and many HTML form clients) submits
    an untouched optional text field as an empty string, not as an absent
    field -- so FastAPI's Form(None) still receives "". An empty string is
    not valid input for a UUID column, so every optional *_id field must be
    normalized to None before it reaches the service/repository layer.
    """
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


async def _save_upload_to_disk(file: UploadFile, settings: Settings) -> tuple[Path, int]:
    upload_dir = Path(settings.upload_temp_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / f"{uuid.uuid4().hex}_{file.filename}"

    size = 0
    with destination.open("wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            f.write(chunk)
    return destination, size


async def _handle_upload(
    upload_type: str,
    file: UploadFile,
    column_mapping: Optional[str],
    organization_id: Optional[str],
    plant_id: Optional[str],
    production_line_id: Optional[str],
    machine_id: Optional[str],
    product_id: Optional[str],
    process_id: Optional[str],
    operation_id: Optional[str],
    parameter_id: Optional[str],
    uploaded_by: Optional[str],
    settings: Settings,
    upload_service: UploadService,
) -> UploadResponse:
    if not file.filename:
        raise FileValidationError("No file was provided.")

    column_mapping = _blank_to_none(column_mapping)
    parsed_mapping: dict[str, str] = {}
    if column_mapping:
        try:
            parsed_mapping = json.loads(column_mapping)
        except json.JSONDecodeError as exc:
            raise FileValidationError(f"column_mapping is not valid JSON: {exc}") from exc

    file_path, size_bytes = await _save_upload_to_disk(file, settings)
    try:
        result = await upload_service.process_upload(
            upload_type=upload_type,
            file_path=file_path,
            file_name=file.filename,
            file_size_bytes=size_bytes,
            column_mapping=parsed_mapping,
            organization_id=_blank_to_none(organization_id),
            plant_id=_blank_to_none(plant_id),
            production_line_id=_blank_to_none(production_line_id),
            machine_id=_blank_to_none(machine_id),
            product_id=_blank_to_none(product_id),
            process_id=_blank_to_none(process_id),
            operation_id=_blank_to_none(operation_id),
            parameter_id=_blank_to_none(parameter_id),
            uploaded_by=_blank_to_none(uploaded_by),
        )
    finally:
        file_path.unlink(missing_ok=True)
    return UploadResponse.model_validate(result)


@router.post("/uploads/historical", response_model=UploadResponse)
async def upload_historical(
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(None, description="JSON: {source_column: canonical_field}"),
    organization_id: Optional[str] = Form(None),
    plant_id: Optional[str] = Form(None),
    production_line_id: Optional[str] = Form(None),
    machine_id: Optional[str] = Form(None),
    product_id: Optional[str] = Form(None),
    process_id: Optional[str] = Form(None),
    operation_id: Optional[str] = Form(None),
    parameter_id: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None),
    settings: Settings = Depends(get_app_settings),
    upload_service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    return await _handle_upload(
        "HISTORICAL", file, column_mapping, organization_id, plant_id, production_line_id,
        machine_id, product_id, process_id, operation_id, parameter_id, uploaded_by, settings, upload_service,
    )


@router.post("/uploads/current", response_model=UploadResponse)
async def upload_current(
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(None, description="JSON: {source_column: canonical_field}"),
    organization_id: Optional[str] = Form(None),
    plant_id: Optional[str] = Form(None),
    production_line_id: Optional[str] = Form(None),
    machine_id: Optional[str] = Form(None),
    product_id: Optional[str] = Form(None),
    process_id: Optional[str] = Form(None),
    operation_id: Optional[str] = Form(None),
    parameter_id: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None),
    settings: Settings = Depends(get_app_settings),
    upload_service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    return await _handle_upload(
        "CURRENT", file, column_mapping, organization_id, plant_id, production_line_id,
        machine_id, product_id, process_id, operation_id, parameter_id, uploaded_by, settings, upload_service,
    )


@router.get("/uploads/{upload_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str, upload_service: UploadService = Depends(get_upload_service)
) -> UploadStatusResponse:
    result = await upload_service.get_status(upload_id)
    return UploadStatusResponse.model_validate(result)
