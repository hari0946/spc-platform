"""Data access for `uploads` and `upload_status_history`.

This is the ledger of the multi-stage, cross-database (PostgreSQL +
Snowflake) ingestion pipeline -- see ingestion/upload_status_manager.py for
the state machine that drives status transitions through this repository.
"""

from __future__ import annotations

from typing import Any, Optional

import asyncpg

from app.core.exceptions import DatabaseConnectionError
from app.database.postgres.connection import get_pool

Executor = asyncpg.Pool | asyncpg.Connection

_COLUMNS = (
    "upload_id, upload_type, file_name, file_size_bytes, file_checksum, column_mapping, "
    "organization_id, plant_id, production_line_id, machine_id, product_id, process_id, "
    "operation_id, parameter_id, status, total_rows, valid_rows, invalid_rows, "
    "bronze_loaded, silver_loaded, error_message, uploaded_by, created_at, updated_at, completed_at"
)


class UploadRepository:
    def _db(self, connection: Optional[asyncpg.Connection]) -> Executor:
        return connection or get_pool()

    async def create(
        self,
        upload_type: str,
        file_name: str,
        file_size_bytes: Optional[int],
        column_mapping: dict[str, Any],
        uploaded_by: Optional[str] = None,
        organization_id: Optional[str] = None,
        plant_id: Optional[str] = None,
        production_line_id: Optional[str] = None,
        machine_id: Optional[str] = None,
        product_id: Optional[str] = None,
        process_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        parameter_id: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        try:
            row = await db.fetchrow(
                f"""
                INSERT INTO uploads
                    (upload_type, file_name, file_size_bytes, column_mapping, uploaded_by,
                     organization_id, plant_id, production_line_id, machine_id, product_id,
                     process_id, operation_id, parameter_id, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'UPLOADED')
                RETURNING {_COLUMNS}
                """,
                upload_type, file_name, file_size_bytes, column_mapping, uploaded_by,
                organization_id, plant_id, production_line_id, machine_id, product_id,
                process_id, operation_id, parameter_id,
            )
        except asyncpg.PostgresError as exc:
            raise DatabaseConnectionError("Failed to create upload record.", details={"reason": str(exc)}) from exc
        await self._record_status_history(db, row["upload_id"], "UPLOADED", None)
        return dict(row)

    async def get_by_id(self, upload_id: str, connection: Optional[asyncpg.Connection] = None) -> Optional[dict[str, Any]]:
        db = self._db(connection)
        row = await db.fetchrow(f"SELECT {_COLUMNS} FROM uploads WHERE upload_id = $1", upload_id)
        return dict(row) if row else None

    async def update_status(
        self,
        upload_id: str,
        status: str,
        error_message: Optional[str] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        completed = status in ("SILVER_COMPLETED", "FAILED")
        row = await db.fetchrow(
            f"""
            UPDATE uploads
            SET status = $2,
                error_message = $3,
                updated_at = now(),
                completed_at = CASE WHEN $4 THEN now() ELSE completed_at END
            WHERE upload_id = $1
            RETURNING {_COLUMNS}
            """,
            upload_id, status, error_message, completed,
        )
        if row is None:
            raise DatabaseConnectionError(f"Upload {upload_id} not found when updating status.")
        await self._record_status_history(db, upload_id, status, error_message)
        return dict(row)

    async def update_row_counts(
        self,
        upload_id: str,
        total_rows: Optional[int] = None,
        valid_rows: Optional[int] = None,
        invalid_rows: Optional[int] = None,
        bronze_loaded: Optional[bool] = None,
        silver_loaded: Optional[bool] = None,
        connection: Optional[asyncpg.Connection] = None,
    ) -> dict[str, Any]:
        db = self._db(connection)
        row = await db.fetchrow(
            f"""
            UPDATE uploads
            SET total_rows = COALESCE($2, total_rows),
                valid_rows = COALESCE($3, valid_rows),
                invalid_rows = COALESCE($4, invalid_rows),
                bronze_loaded = COALESCE($5, bronze_loaded),
                silver_loaded = COALESCE($6, silver_loaded),
                updated_at = now()
            WHERE upload_id = $1
            RETURNING {_COLUMNS}
            """,
            upload_id, total_rows, valid_rows, invalid_rows, bronze_loaded, silver_loaded,
        )
        if row is None:
            raise DatabaseConnectionError(f"Upload {upload_id} not found when updating row counts.")
        return dict(row)

    async def list_status_history(
        self, upload_id: str, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        rows = await db.fetch(
            """
            SELECT upload_status_history_id, upload_id, status, message, created_at
            FROM upload_status_history
            WHERE upload_id = $1
            ORDER BY created_at
            """,
            upload_id,
        )
        return [dict(row) for row in rows]

    async def list_recent(
        self, upload_type: Optional[str] = None, limit: int = 50, connection: Optional[asyncpg.Connection] = None
    ) -> list[dict[str, Any]]:
        db = self._db(connection)
        if upload_type:
            rows = await db.fetch(
                f"SELECT {_COLUMNS} FROM uploads WHERE upload_type = $1 ORDER BY created_at DESC LIMIT $2",
                upload_type, limit,
            )
        else:
            rows = await db.fetch(f"SELECT {_COLUMNS} FROM uploads ORDER BY created_at DESC LIMIT $1", limit)
        return [dict(row) for row in rows]

    async def _record_status_history(self, db: Executor, upload_id: str, status: str, message: Optional[str]) -> None:
        await db.execute(
            "INSERT INTO upload_status_history (upload_id, status, message) VALUES ($1, $2, $3)",
            upload_id, status, message,
        )
