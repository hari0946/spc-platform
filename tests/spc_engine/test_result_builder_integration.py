import pandas as pd
import pytest

from app.spc_engine.core.enums import SubgroupMethod
from app.spc_engine.core.exceptions import IncompatibleContextError, InsufficientDataError
from app.spc_engine.core.models import SPCConfiguration, Specification
from app.spc_engine.results.result_builder import run_spc_analysis


def _config(**overrides):
    defaults = dict(
        chart_type="AUTO",
        subgroup_size=5,
        subgroup_method=SubgroupMethod.CONSECUTIVE,
        maximum_time_gap_seconds=3600,
        minimum_sample_size=20,
        ruleset=[],
    )
    defaults.update(overrides)
    return SPCConfiguration(**defaults)


def test_full_analysis_in_control_process(measurements_df_factory):
    df = measurements_df_factory(n=200, mean=20.0, sigma=0.01)
    spec = Specification(lsl=19.94, usl=20.06, target=20.0)
    result = run_spc_analysis(df, _config(), spec)

    assert result.chart.chart_type.value == "XBAR_R"
    assert result.stability.status.value == "IN_CONTROL"
    assert result.capability.cpk > 1.0
    assert result.data_summary.total_observations == 200


def test_subgroup_size_one_selects_imr(measurements_df_factory):
    df = measurements_df_factory(n=30, mean=20.0, sigma=0.01)
    result = run_spc_analysis(df, _config(subgroup_size=1), None)
    assert result.chart.chart_type.value == "IMR"


def test_empty_dataset_raises_insufficient_data():
    df = pd.DataFrame(columns=["value", "event_timestamp", "machine_id", "product_id", "process_id", "operation_id", "parameter_id"])
    with pytest.raises(InsufficientDataError):
        run_spc_analysis(df, _config(), None)


def test_very_small_sample_size_raises_insufficient_data(measurements_df_factory):
    df = measurements_df_factory(n=3, sigma=0.01)
    with pytest.raises(InsufficientDataError):
        run_spc_analysis(df, _config(minimum_sample_size=20), None)


def test_missing_values_excluded_from_analysis(measurements_df_factory):
    df = measurements_df_factory(n=100, sigma=0.01)
    df.loc[0:9, "value"] = None  # 10 missing values
    result = run_spc_analysis(df, _config(minimum_sample_size=20), None)
    assert result.data_summary.invalid_observations == 10
    assert result.data_summary.valid_observations == 90


def test_context_mismatch_raises(measurements_df_factory):
    df = measurements_df_factory(n=50, sigma=0.01)
    df.loc[0:24, "machine_id"] = "CNC_01"
    df.loc[25:49, "machine_id"] = "CNC_02"
    with pytest.raises(IncompatibleContextError):
        run_spc_analysis(df, _config(), None)


def test_all_identical_observations_zero_sigma_no_crash(measurements_df_factory):
    df = measurements_df_factory(n=50, sigma=0.0)
    result = run_spc_analysis(df, _config(subgroup_size=5), Specification(lsl=19.9, usl=20.1))
    assert result.sigma.within_sigma == 0.0
    assert result.capability.cpk is None
    assert any("zero" in w.lower() for w in result.warnings)


def test_missing_specification_produces_warning_not_crash(measurements_df_factory):
    df = measurements_df_factory(n=50, sigma=0.01)
    result = run_spc_analysis(df, _config(), None)
    assert result.capability.cpk is None
    assert len(result.capability.warnings) >= 1
