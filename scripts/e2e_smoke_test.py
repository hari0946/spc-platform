"""End-to-end smoke test exercising the full Phase 1 + Phase 2 business flow
against a real (local docker-compose) PostgreSQL instance and real CSV
files on disk. This is NOT part of the pytest suite (it seeds/mutates real
reference data) -- it is a manual verification script for development use.

By default, MeasurementRepository is swapped for an in-memory fake so the
ingestion pipeline's Bronze/Silver steps can be exercised without a live
Snowflake account, while everything else (PostgreSQL schema, repositories,
ingestion validation/transformation, services, SPC engine) runs for real.

Pass --real-snowflake to instead use the real Snowflake-backed
MeasurementRepository (requires SNOWFLAKE_* to be configured in .env and
scripts/snowflake_ddl.sql to have already been run against that account).
"""

from __future__ import annotations

import asyncio
import csv
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

USE_REAL_SNOWFLAKE = "--real-snowflake" in sys.argv

from app.core.config import get_settings
from app.database.postgres.connection import close_pool, create_pool
from app.database.postgres.migration_runner import run_migrations
from app.repositories.machine_repository import MachineRepository
from app.repositories.operation_repository import OperationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.plant_repository import PlantRepository
from app.repositories.process_repository import ProcessRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.specification_repository import SpecificationRepository
from app.repositories.spc_configuration_repository import SPCConfigurationRepository
from app.repositories.upload_repository import UploadRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.services.baseline_service import BaselineService
from app.services.historical_analysis_service import HistoricalAnalysisService
from app.services.manual_data_check_service import ManualDataCheckService
from app.services.upload_service import UploadService
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.baseline_repository import BaselineRepository
from app.repositories.manual_check_repository import ManualCheckRepository
from app.repositories.findings_repository import FindingsRepository
from app.repositories.alert_repository import AlertRepository


class InMemoryMeasurementRepository:
    """Fakes the Snowflake-backed MeasurementRepository with an in-process
    pandas store, so this script can run without a live Snowflake account."""

    def __init__(self) -> None:
        import pandas as pd

        self._silver = pd.DataFrame()

    async def load_raw_to_bronze(self, upload_id, source_file_name, df):
        return len(df)

    async def load_cleaned_to_silver(self, upload_id, source_file_name, df):
        import pandas as pd

        self._silver = pd.concat([self._silver, df], ignore_index=True)
        return len(df)

    async def get_by_upload(self, upload_id, valid_only=True):
        df = self._silver[self._silver["upload_id"] == upload_id]
        if valid_only:
            df = df[df["quality_status"] == "VALID"]
        return df.rename(columns={"measurement_value": "value"})

    async def get_by_context(self, parameter_id, machine_id=None, product_id=None, operation_id=None, valid_only=True):
        df = self._silver[self._silver["parameter_id"] == parameter_id]
        if machine_id:
            df = df[df["machine_id"] == machine_id]
        if product_id:
            df = df[df["product_id"] == product_id]
        if operation_id:
            df = df[df["operation_id"] == operation_id]
        if valid_only:
            df = df[df["quality_status"] == "VALID"]
        return df.rename(columns={"measurement_value": "value"}).reset_index(drop=True)

    async def get_by_time_range(self, *args, **kwargs):
        raise NotImplementedError


def write_csv(path: Path, n: int, mean: float, sigma: float, seed: int, start: datetime) -> None:
    rng = random.Random(seed)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["DATE_TIME", "MACHINE_NAME", "PART_NUMBER", "PROCESS_STEP", "CHARACTERISTIC", "MEASURED_VALUE"])
        for i in range(n):
            ts = start + timedelta(minutes=5 * i)
            writer.writerow([ts.isoformat(), "CNC_01", "PART_A", "OP_10", "SHAFT_DIAMETER", f"{rng.gauss(mean, sigma):.5f}"])


async def main() -> None:
    settings = get_settings()
    pool = await create_pool(settings)
    await run_migrations(pool)

    org_repo, plant_repo, machine_repo = OrganizationRepository(), PlantRepository(), MachineRepository()
    product_repo, process_repo, operation_repo = ProductRepository(), ProcessRepository(), OperationRepository()
    parameter_repo, spec_repo, config_repo = ParameterRepository(), SpecificationRepository(), SPCConfigurationRepository()
    upload_repo = UploadRepository()

    suffix = datetime.now().strftime("%H%M%S%f")
    org = await org_repo.create("Demo Automotive Inc", f"DEMO{suffix}")
    plant = await plant_repo.create(org["organization_id"], "Demo Plant 1", f"PLANT1{suffix}")
    machine = await machine_repo.create(plant["plant_id"], "CNC Machine 01", "CNC_01")
    product = await product_repo.create(org["organization_id"], "PART_A", "Demo Shaft")
    process = await process_repo.create(org["organization_id"], "Machining", "MACHINING")
    operation = await operation_repo.create(process["process_id"], "Turning Op 10", "OP_10", sequence_number=10)
    parameter = await parameter_repo.create("SHAFT_DIAMETER", unit="mm", description="Shaft outer diameter")
    await spec_repo.create(parameter["parameter_id"], lsl=19.94, usl=20.06, target=20.0,
                            machine_id=machine["machine_id"], product_id=product["product_id"],
                            operation_id=operation["operation_id"])
    spc_config = await config_repo.create(
        parameter_id=parameter["parameter_id"], chart_type="AUTO", subgroup_size=5,
        subgroup_method="CONSECUTIVE", maximum_time_gap_seconds=3600, minimum_sample_size=20,
        ruleset=[{"rule_name": "POINT_OUTSIDE_LIMITS", "enabled": True, "severity": "CRITICAL", "parameters": {}}],
        machine_id=machine["machine_id"], product_id=product["product_id"], operation_id=operation["operation_id"],
    )
    print(f"Seeded context: org={org['name']} machine={machine['code']} parameter={parameter['name']}")

    measurement_repo = MeasurementRepository() if USE_REAL_SNOWFLAKE else InMemoryMeasurementRepository()
    print(f"Measurement store: {'real Snowflake' if USE_REAL_SNOWFLAKE else 'in-memory fake'}")
    upload_service = UploadService(settings, upload_repo, measurement_repo, machine_repo, product_repo, operation_repo, parameter_repo)

    tmp_dir = Path(settings.upload_temp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    historical_csv = tmp_dir / "historical.csv"
    write_csv(historical_csv, n=250, mean=20.0, sigma=0.012, seed=1, start=datetime(2026, 1, 1, tzinfo=timezone.utc))

    mapping = {
        "DATE_TIME": "event_timestamp", "MACHINE_NAME": "machine_code", "PART_NUMBER": "product_code",
        "PROCESS_STEP": "operation_code", "CHARACTERISTIC": "parameter_name", "MEASURED_VALUE": "value",
    }
    historical_upload = await upload_service.process_upload(
        upload_type="HISTORICAL", file_path=historical_csv, file_name="historical.csv",
        file_size_bytes=historical_csv.stat().st_size, column_mapping=mapping,
        organization_id=org["organization_id"], plant_id=plant["plant_id"],
    )
    print(f"Historical upload status: {historical_upload['status']} "
          f"(valid={historical_upload['valid_rows']}, invalid={historical_upload['invalid_rows']})")
    assert historical_upload["status"] == "SILVER_COMPLETED"

    historical_service = HistoricalAnalysisService(upload_repo, measurement_repo, config_repo, spec_repo, AnalysisRepository())
    analysis = await historical_service.run_historical_analysis(
        upload_id=historical_upload["upload_id"], parameter_id=parameter["parameter_id"],
        machine_id=machine["machine_id"], product_id=product["product_id"], operation_id=operation["operation_id"],
    )
    print(f"Historical analysis: chart={analysis['chart']['type']} cpk={analysis['capability']['cpk']:.3f} "
          f"stability={analysis['stability']['status']}")

    baseline_service = BaselineService(BaselineRepository(), AnalysisRepository())
    draft = await baseline_service.create_draft_from_analysis(analysis["analysis_id"], created_by="e2e_script")
    active_baseline = await baseline_service.approve(draft["baseline_id"], approved_by="e2e_script")
    print(f"Baseline approved: id={active_baseline['baseline_id']} status={active_baseline['status']} "
          f"ucl={active_baseline['ucl']:.4f} cl={active_baseline['center_line']:.4f} lcl={active_baseline['lcl']:.4f}")
    assert active_baseline["status"] == "ACTIVE"

    current_csv = tmp_dir / "current.csv"
    # Shifted mean (+0.02) and larger variation to trigger findings.
    write_csv(current_csv, n=100, mean=20.02, sigma=0.02, seed=2, start=datetime(2026, 3, 1, tzinfo=timezone.utc))
    current_upload = await upload_service.process_upload(
        upload_type="CURRENT", file_path=current_csv, file_name="current.csv",
        file_size_bytes=current_csv.stat().st_size, column_mapping=mapping,
        organization_id=org["organization_id"], plant_id=plant["plant_id"],
    )
    print(f"Current upload status: {current_upload['status']} (valid={current_upload['valid_rows']})")

    manual_check_service = ManualDataCheckService(
        upload_repo, measurement_repo, config_repo, spec_repo, AnalysisRepository(),
        BaselineRepository(), ManualCheckRepository(), FindingsRepository(), AlertRepository(),
    )
    result = await manual_check_service.run_manual_check(
        upload_id=current_upload["upload_id"], parameter_id=parameter["parameter_id"],
        machine_id=machine["machine_id"], product_id=product["product_id"], operation_id=operation["operation_id"],
        triggered_by="e2e_script",
    )
    print(f"\nManual check final status: {result['final_status']}")
    print(f"Mean shift: {result['comparison']['mean_shift']:.5f} "
          f"({result['comparison']['mean_shift_percentage']:.2f}%)")
    print(f"Within-sigma change: {result['comparison']['within_variation_change_percentage']:.1f}%")
    print(f"Cpk change: {result['comparison']['cpk_change']}")
    print(f"Control status: {result['control_status']['status']} "
          f"violations={len(result['control_status']['violations'])}")
    print("Findings:")
    for f in result["findings"]:
        print(f"  [{f['severity']}] {f['finding_type']}: {f['message']}")

    assert result["comparison"]["mean_shift"] > 0, "expected an upward mean shift to be detected"
    assert len(result["findings"]) > 0

    historical_csv.unlink(missing_ok=True)
    current_csv.unlink(missing_ok=True)
    await close_pool()
    print("\nEnd-to-end smoke test PASSED.")


if __name__ == "__main__":
    asyncio.run(main())
