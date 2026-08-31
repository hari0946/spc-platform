"""FastAPI application entry point.

Wires together: structured logging, the PostgreSQL connection pool +
migration runner (startup), all API routers, and a single exception
handler that turns AppException (and its SPC-engine-derived subclasses)
into structured JSON error responses without ever leaking a raw stack
trace to the client.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    alerts,
    baselines,
    configurations,
    dev_seed,
    findings,
    historical_analysis,
    manual_check,
    reference_data,
    uploads,
)
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging, get_logger
from app.database.postgres.connection import close_pool, create_pool
from app.database.postgres.migration_runner import run_migrations

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    pool = await create_pool(settings)
    applied = await run_migrations(pool)
    if applied:
        logger.info("startup_migrations_applied", count=len(applied), files=applied)
    else:
        logger.info("startup_migrations_up_to_date")
    yield
    await close_pool()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Automotive Statistical Process Control (SPC) platform -- "
        "historical baseline analysis and manual batch comparison for continuous/variable data.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        logger.warning("app_exception", path=str(request.url.path), error_code=exc.error_code, message=exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", path=str(request.url.path), error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "An unexpected error occurred.", "details": {}},
        )

    prefix = settings.api_prefix
    app.include_router(uploads.router, prefix=prefix)
    app.include_router(historical_analysis.router, prefix=prefix)
    app.include_router(baselines.router, prefix=prefix)
    app.include_router(manual_check.router, prefix=prefix)
    app.include_router(configurations.router, prefix=prefix)
    app.include_router(findings.router, prefix=prefix)
    app.include_router(alerts.router, prefix=prefix)
    app.include_router(reference_data.router, prefix=prefix)
    app.include_router(dev_seed.router, prefix=prefix)  # TEMPORARY -- remove after one-time seeding

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
