"""FastAPI dependency-injection wiring.

Every route depends on a *service*, never directly on a repository or the
SPC engine -- this module is the single place that assembles
repositories -> services for injection into routes (app/api/routes/*.py).
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.repositories.alert_repository import AlertRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.baseline_repository import BaselineRepository
from app.repositories.findings_repository import FindingsRepository
from app.repositories.machine_repository import MachineRepository
from app.repositories.manual_check_repository import ManualCheckRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.repositories.operation_repository import OperationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.plant_repository import PlantRepository
from app.repositories.process_repository import ProcessRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.rule_configuration_repository import RuleConfigurationRepository
from app.repositories.spc_configuration_repository import SPCConfigurationRepository
from app.repositories.specification_repository import SpecificationRepository
from app.repositories.upload_repository import UploadRepository
from app.services.alert_service import AlertService
from app.services.baseline_service import BaselineService
from app.services.findings_service import FindingsService
from app.services.historical_analysis_service import HistoricalAnalysisService
from app.services.manual_data_check_service import ManualDataCheckService
from app.services.reference_data_service import ReferenceDataService
from app.services.spc_configuration_service import SPCConfigurationService
from app.services.upload_service import UploadService


def get_app_settings() -> Settings:
    return get_settings()


# Repositories are cheap, stateless wrappers around the shared connection
# pool -- safe to construct fresh per request rather than pooling them.


def get_upload_repository() -> UploadRepository:
    return UploadRepository()


def get_measurement_repository() -> MeasurementRepository:
    return MeasurementRepository()


def get_organization_repository() -> OrganizationRepository:
    return OrganizationRepository()


def get_plant_repository() -> PlantRepository:
    return PlantRepository()


def get_process_repository() -> ProcessRepository:
    return ProcessRepository()


def get_machine_repository() -> MachineRepository:
    return MachineRepository()


def get_product_repository() -> ProductRepository:
    return ProductRepository()


def get_operation_repository() -> OperationRepository:
    return OperationRepository()


def get_parameter_repository() -> ParameterRepository:
    return ParameterRepository()


def get_specification_repository() -> SpecificationRepository:
    return SpecificationRepository()


def get_spc_configuration_repository() -> SPCConfigurationRepository:
    return SPCConfigurationRepository()


def get_rule_configuration_repository() -> RuleConfigurationRepository:
    return RuleConfigurationRepository()


def get_analysis_repository() -> AnalysisRepository:
    return AnalysisRepository()


def get_baseline_repository() -> BaselineRepository:
    return BaselineRepository()


def get_manual_check_repository() -> ManualCheckRepository:
    return ManualCheckRepository()


def get_findings_repository() -> FindingsRepository:
    return FindingsRepository()


def get_alert_repository() -> AlertRepository:
    return AlertRepository()


def get_upload_service() -> UploadService:
    return UploadService(
        settings=get_app_settings(),
        upload_repository=get_upload_repository(),
        measurement_repository=get_measurement_repository(),
        machine_repository=get_machine_repository(),
        product_repository=get_product_repository(),
        operation_repository=get_operation_repository(),
        parameter_repository=get_parameter_repository(),
    )


def get_historical_analysis_service() -> HistoricalAnalysisService:
    return HistoricalAnalysisService(
        upload_repository=get_upload_repository(),
        measurement_repository=get_measurement_repository(),
        spc_configuration_repository=get_spc_configuration_repository(),
        specification_repository=get_specification_repository(),
        analysis_repository=get_analysis_repository(),
    )


def get_baseline_service() -> BaselineService:
    return BaselineService(
        baseline_repository=get_baseline_repository(), analysis_repository=get_analysis_repository()
    )


def get_manual_data_check_service() -> ManualDataCheckService:
    return ManualDataCheckService(
        upload_repository=get_upload_repository(),
        measurement_repository=get_measurement_repository(),
        spc_configuration_repository=get_spc_configuration_repository(),
        specification_repository=get_specification_repository(),
        analysis_repository=get_analysis_repository(),
        baseline_repository=get_baseline_repository(),
        manual_check_repository=get_manual_check_repository(),
        findings_repository=get_findings_repository(),
        alert_repository=get_alert_repository(),
    )


def get_spc_configuration_service() -> SPCConfigurationService:
    return SPCConfigurationService(spc_configuration_repository=get_spc_configuration_repository())


def get_reference_data_service() -> ReferenceDataService:
    return ReferenceDataService(
        organization_repository=get_organization_repository(),
        plant_repository=get_plant_repository(),
        machine_repository=get_machine_repository(),
        product_repository=get_product_repository(),
        process_repository=get_process_repository(),
        operation_repository=get_operation_repository(),
        parameter_repository=get_parameter_repository(),
        specification_repository=get_specification_repository(),
    )


def get_findings_service() -> FindingsService:
    return FindingsService(findings_repository=get_findings_repository())


def get_alert_service() -> AlertService:
    return AlertService(alert_repository=get_alert_repository())
