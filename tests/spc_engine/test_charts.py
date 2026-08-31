import statistics
from datetime import datetime, timedelta, timezone

import pytest

from app.spc_engine.charts.imr import ImrChart
from app.spc_engine.charts.xbar_r import XbarRChart
from app.spc_engine.charts.xbar_s import XbarSChart
from app.spc_engine.core.enums import ChartType
from app.spc_engine.core.models import Subgroup

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _subgroup(values, idx):
    return Subgroup(
        subgroup_id=f"SG-{idx}",
        indices=list(range(len(values))),
        values=values,
        mean=statistics.fmean(values),
        range_=max(values) - min(values),
        std_dev=statistics.stdev(values) if len(values) > 1 else None,
        count=len(values),
        start_timestamp=START + timedelta(minutes=idx),
        end_timestamp=START + timedelta(minutes=idx),
    )


def test_xbar_r_limits_match_standard_constants():
    # n=5 -> A2=0.577, D3=0.000, D4=2.114 (Montgomery table).
    subgroup_values = [
        [20.01, 20.02, 20.00, 20.01, 20.03],
        [20.02, 20.00, 20.01, 19.99, 20.02],
        [19.98, 20.00, 20.01, 20.02, 20.00],
        [20.00, 20.01, 19.99, 20.02, 20.01],
    ]
    subgroups = [_subgroup(v, i) for i, v in enumerate(subgroup_values)]
    result, warnings = XbarRChart().calculate(subgroups)

    xbarbar = statistics.fmean(sg.mean for sg in subgroups)
    rbar = statistics.fmean(sg.range_ for sg in subgroups)

    assert result.chart_type == ChartType.XBAR_R
    assert result.subgroup_size_used == 5
    assert result.primary_chart.center_line == pytest.approx(xbarbar)
    assert result.primary_chart.ucl == pytest.approx(xbarbar + 0.577 * rbar, abs=1e-6)
    assert result.primary_chart.lcl == pytest.approx(xbarbar - 0.577 * rbar, abs=1e-6)
    assert result.secondary_chart.center_line == pytest.approx(rbar)
    assert result.secondary_chart.ucl == pytest.approx(2.114 * rbar, abs=1e-6)
    assert result.secondary_chart.lcl == pytest.approx(0.0, abs=1e-6)
    assert warnings == []


def test_xbar_s_limits_match_standard_constants():
    # n=10 -> A3=0.975, B3=0.284, B4=1.716 (Montgomery table).
    subgroup_values = [
        [20.0 + 0.001 * i for i in range(10)],
        [19.99 + 0.001 * i for i in range(10)],
        [20.01 - 0.001 * i for i in range(10)],
    ]
    subgroups = [_subgroup(v, i) for i, v in enumerate(subgroup_values)]
    result, _ = XbarSChart().calculate(subgroups)

    xbarbar = statistics.fmean(sg.mean for sg in subgroups)
    sbar = statistics.fmean(sg.std_dev for sg in subgroups)

    assert result.chart_type == ChartType.XBAR_S
    assert result.primary_chart.ucl == pytest.approx(xbarbar + 0.975 * sbar, abs=1e-6)
    assert result.secondary_chart.ucl == pytest.approx(1.716 * sbar, abs=1e-6)
    assert result.secondary_chart.lcl == pytest.approx(0.284 * sbar, abs=1e-6)


def test_xbar_r_excludes_nonconforming_subgroups_with_warning():
    subgroups = [
        _subgroup([1, 2, 3, 4, 5], 0),
        _subgroup([1, 2, 3, 4, 5], 1),
        _subgroup([1, 2, 3], 2),  # different size -> excluded
    ]
    result, warnings = XbarRChart().calculate(subgroups)
    assert result.subgroup_size_used == 5
    assert len(warnings) == 1
    assert "excluded" in warnings[0]


def test_imr_chart_moving_range_and_limits():
    values = [10.0, 10.2, 9.9, 10.1, 10.0]
    subgroups = [_subgroup([v], i) for i, v in enumerate(values)]
    result, warnings = ImrChart().calculate(subgroups)

    xbar = statistics.fmean(values)
    moving_ranges = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
    mrbar = statistics.fmean(moving_ranges)
    sigma_within = mrbar / 1.128

    assert result.chart_type == ChartType.IMR
    assert result.primary_chart.center_line == pytest.approx(xbar)
    assert result.primary_chart.ucl == pytest.approx(xbar + 3 * sigma_within, abs=1e-9)
    assert result.primary_chart.lcl == pytest.approx(xbar - 3 * sigma_within, abs=1e-9)
    assert result.secondary_chart.center_line == pytest.approx(mrbar)
    assert result.secondary_chart.ucl == pytest.approx(3.267 * mrbar, abs=1e-6)
    assert warnings == []


def test_imr_requires_at_least_two_observations():
    from app.spc_engine.core.exceptions import InsufficientDataError

    subgroups = [_subgroup([10.0], 0)]
    with pytest.raises(InsufficientDataError):
        ImrChart().calculate(subgroups)
