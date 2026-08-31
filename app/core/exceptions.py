"""Application-level (HTTP-facing) exceptions.

Services and repositories raise these (or let SPC-engine exceptions and
asyncpg/Snowflake exceptions bubble up to the service layer, which wraps
them here). main.py registers a single exception handler that turns any
AppException into a structured JSON error response, and turns any other
unhandled exception into a generic 500 without leaking a stack trace to
the client.
"""

from __future__ import annotations

from typing import Any, Optional


class AppException(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {"error_code": self.error_code, "message": self.message, "details": self.details}


class NotFoundError(AppException):
    status_code = 404
    error_code = "NOT_FOUND"


class ValidationError(AppException):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class ConflictError(AppException):
    status_code = 409
    error_code = "CONFLICT"


class FileValidationError(AppException):
    status_code = 400
    error_code = "FILE_VALIDATION_ERROR"


class InsufficientDataError(AppException):
    status_code = 422
    error_code = "INSUFFICIENT_DATA"


class MissingSpecificationError(AppException):
    status_code = 422
    error_code = "MISSING_SPECIFICATION"


class MissingSPCConfigurationError(AppException):
    status_code = 422
    error_code = "MISSING_SPC_CONFIGURATION"


class MissingActiveBaselineError(AppException):
    status_code = 404
    error_code = "MISSING_ACTIVE_BASELINE"


class BaselineContextMismatchError(AppException):
    status_code = 409
    error_code = "BASELINE_CONTEXT_MISMATCH"


class UploadNotReadyError(AppException):
    status_code = 409
    error_code = "UPLOAD_NOT_READY"


class UploadProcessingError(AppException):
    status_code = 422
    error_code = "UPLOAD_PROCESSING_FAILED"


class DatabaseConnectionError(AppException):
    status_code = 503
    error_code = "DATABASE_CONNECTION_ERROR"


class SnowflakeOperationError(AppException):
    status_code = 502
    error_code = "SNOWFLAKE_OPERATION_ERROR"
