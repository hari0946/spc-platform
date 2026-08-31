"""Tests for the baseline-compatibility guard in ManualDataCheckService --
the rule that a manual check must refuse to compare against a baseline
whose context (machine/product/operation/parameter/chart type) doesn't
match the new dataset, rather than silently comparing anyway."""

from __future__ import annotations

import pytest

from app.core.exceptions import BaselineContextMismatchError
from app.services.manual_data_check_service import _row_to_baseline_snapshot, _validate_baseline_compatibility
from app.spc_engine.core.enums import ChartType


def _baseline_row(**overrides):
    row = {
        "baseline_id": "b1", "chart_type": "XBAR_R", "mean": 20.0, "within_sigma": 0.01,
        "overall_sigma": 0.012, "center_line": 20.0, "ucl": 20.02, "lcl": 19.98,
        "secondary_center_line": None, "secondary_ucl": None, "secondary_lcl": None,
        "cp": 2.0, "cpk": 1.9, "pp": 1.8, "ppk": 1.7, "lsl": 19.94, "usl": 20.06, "target": 20.0,
        "specification_id": "spec1", "unit": "mm", "machine_id": "CNC_01", "product_id": "PART_A",
        "operation_id": "OP_10", "parameter_id": "SHAFT_DIAMETER",
    }
    row.update(overrides)
    return row


def test_compatible_context_does_not_raise():
    baseline = _row_to_baseline_snapshot(_baseline_row())
    _validate_baseline_compatibility(
        baseline, "SHAFT_DIAMETER", "CNC_01", "PART_A", "OP_10", ChartType.XBAR_R
    )  # should not raise


def test_machine_mismatch_raises_baseline_context_mismatch():
    baseline = _row_to_baseline_snapshot(_baseline_row(machine_id="CNC_01"))
    with pytest.raises(BaselineContextMismatchError):
        _validate_baseline_compatibility(
            baseline, "SHAFT_DIAMETER", "CNC_02", "PART_A", "OP_10", ChartType.XBAR_R
        )


def test_chart_type_mismatch_raises_baseline_context_mismatch():
    baseline = _row_to_baseline_snapshot(_baseline_row(chart_type="XBAR_R"))
    with pytest.raises(BaselineContextMismatchError):
        _validate_baseline_compatibility(
            baseline, "SHAFT_DIAMETER", "CNC_01", "PART_A", "OP_10", ChartType.IMR
        )


def test_parameter_mismatch_raises_baseline_context_mismatch():
    baseline = _row_to_baseline_snapshot(_baseline_row(parameter_id="SHAFT_DIAMETER"))
    with pytest.raises(BaselineContextMismatchError):
        _validate_baseline_compatibility(
            baseline, "BORE_DIAMETER", "CNC_01", "PART_A", "OP_10", ChartType.XBAR_R
        )


def test_snapshot_preserves_frozen_baseline_limits_exactly():
    row = _baseline_row(center_line=20.0, ucl=20.02, lcl=19.98)
    baseline = _row_to_baseline_snapshot(row)
    assert baseline.center_line == 20.0
    assert baseline.ucl == 20.02
    assert baseline.lcl == 19.98
