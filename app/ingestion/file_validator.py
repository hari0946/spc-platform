"""Validates the uploaded file itself (extension, size, non-emptiness)
before it is ever parsed as CSV content.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.exceptions import FileValidationError


def validate_file_metadata(filename: str, size_bytes: int, settings: Settings) -> None:
    if not filename:
        raise FileValidationError("Upload is missing a file name.")

    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in settings.allowed_upload_extensions:
        raise FileValidationError(
            f"Unsupported file type '{extension or filename}'. "
            f"Allowed extensions: {', '.join(settings.allowed_upload_extensions)}."
        )

    if size_bytes <= 0:
        raise FileValidationError("The uploaded file is empty (0 bytes).")

    max_bytes = settings.upload_max_file_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileValidationError(
            f"The uploaded file ({size_bytes / (1024 * 1024):.1f} MB) exceeds the maximum "
            f"allowed size of {settings.upload_max_file_size_mb} MB."
        )
