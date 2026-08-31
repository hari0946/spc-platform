"""Service-layer tests for BaselineService, with repositories mocked --
these verify orchestration logic (draft creation, approve/supersede
sequencing, error translation), not SQL."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.baseline_service import BaselineService


@asynccontextmanager
async def _fake_transaction():
    """BaselineService.approve() runs its supersede+activate sequence inside
    database.postgres.transaction.transaction(), which requires a real
    asyncpg pool. Since this test suite mocks every repository, the
    transaction boundary itself is faked too -- the point of this test is
    to verify supersede-then-activate ordering, not real transactional
    behavior (that belongs in a repository/DB integration test)."""
    yield None


@pytest.fixture(autouse=True)
def patch_transaction(monkeypatch):
    monkeypatch.setattr("app.services.baseline_service.transaction", _fake_transaction)


def _analysis_run(status="COMPLETED"):
    return {
        "analysis_id": "a1", "status": status, "organization_id": "org1", "plant_id": "p1",
        "production_line_id": None, "machine_id": "m1", "product_id": "prod1", "process_id": "proc1",
        "operation_id": "op1", "parameter_id": "param1", "chart_type": "XBAR_R",
    }


def _analysis_result():
    return {
        "within_sigma": 0.01, "overall_sigma": 0.012, "valid_observations": 200, "mean": 20.0,
        "center_line": 20.0, "ucl": 20.02, "lcl": 19.98, "secondary_center_line": 0.03,
        "secondary_ucl": 0.06, "secondary_lcl": 0.0, "specification_id": None, "lsl": 19.94,
        "usl": 20.06, "target": 20.0, "cp": 2.0, "cpk": 1.9, "pp": 1.8, "ppk": 1.7,
    }


@pytest.fixture
def baseline_repository():
    repo = AsyncMock()
    return repo


@pytest.fixture
def analysis_repository():
    repo = AsyncMock()
    repo.get_by_id.return_value = _analysis_run()
    repo.get_result_by_analysis_id.return_value = _analysis_result()
    return repo


@pytest.fixture
def service(baseline_repository, analysis_repository):
    return BaselineService(baseline_repository, analysis_repository)


async def test_create_draft_uses_frozen_analysis_result_values(service, baseline_repository, analysis_repository):
    baseline_repository.create_draft.return_value = {"baseline_id": "b1", "status": "DRAFT"}

    result = await service.create_draft_from_analysis("a1", created_by="qa_engineer")

    assert result["baseline_id"] == "b1"
    values = baseline_repository.create_draft.call_args.args[0]
    assert values["mean"] == 20.0
    assert values["within_sigma"] == 0.01
    assert values["cpk"] == 1.9
    assert values["analysis_id"] == "a1"


async def test_create_draft_rejects_incomplete_analysis(service, analysis_repository):
    analysis_repository.get_by_id.return_value = _analysis_run(status="FAILED")
    with pytest.raises(ValidationError):
        await service.create_draft_from_analysis("a1")


async def test_create_draft_rejects_unknown_analysis(service, analysis_repository):
    analysis_repository.get_by_id.return_value = None
    with pytest.raises(NotFoundError):
        await service.create_draft_from_analysis("unknown")


async def test_approve_supersedes_existing_active_baseline(service, baseline_repository):
    baseline_repository.get_by_id.return_value = {
        "baseline_id": "b2", "status": "DRAFT", "parameter_id": "param1",
        "machine_id": "m1", "product_id": "prod1", "operation_id": "op1",
    }
    existing_active = {"baseline_id": "b1"}
    baseline_repository.get_active_baseline.return_value = existing_active
    baseline_repository.activate.return_value = {"baseline_id": "b2", "status": "ACTIVE"}

    result = await service.approve("b2", approved_by="qa_lead")

    baseline_repository.supersede.assert_awaited_once()
    supersede_args = baseline_repository.supersede.call_args.args
    assert supersede_args[0] == "b1"  # old active baseline is superseded
    assert supersede_args[1] == "b2"  # ...by the newly approved one
    baseline_repository.activate.assert_awaited_once()
    assert result["status"] == "ACTIVE"


async def test_approve_rejects_non_draft_baseline(service, baseline_repository):
    baseline_repository.get_by_id.return_value = {"baseline_id": "b2", "status": "ACTIVE"}
    with pytest.raises(ConflictError):
        await service.approve("b2")


async def test_approve_unknown_baseline_raises_not_found(service, baseline_repository):
    baseline_repository.get_by_id.return_value = None
    with pytest.raises(NotFoundError):
        await service.approve("unknown")
