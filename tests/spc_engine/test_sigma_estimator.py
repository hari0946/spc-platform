import statistics
from datetime import datetime, timezone

import pytest

from app.spc_engine.core.enums import ChartType
from app.spc_engine.core.models import Subgroup
from app.spc_engine.statistics.sigma_estimator import estimate_overall_sigma, estimate_sigma, estimate_within_sigma

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _subgroup(values):
    return Subgroup(
        subgroup_id="SG", indices=[], values=values, mean=statistics.fmean(values),
        range_=max(values) - min(values), std_dev=statistics.stdev(values) if len(values) > 1 else None,
        count=len(values), start_timestamp=START, end_timestamp=START,
    )


def test_within_sigma_xbar_r_uses_rbar_over_d2():
    subgroups = [_subgroup([10, 11, 9, 10, 10]), _subgroup([9, 10, 11, 10, 9])]
    rbar = statistics.fmean(sg.range_ for sg in subgroups)
    within = estimate_within_sigma(ChartType.XBAR_R, subgroups, 5)
    assert within == pytest.approx(rbar / 2.326)  # d2 for n=5


def test_within_sigma_imr_uses_mrbar_over_1_128():
    values = [10.0, 10.2, 9.9, 10.1]
    subgroups = [_subgroup([v]) for v in values]
    within = estimate_within_sigma(ChartType.IMR, subgroups, 1)
    mrbar = statistics.fmean(abs(values[i] - values[i - 1]) for i in range(1, len(values)))
    assert within == pytest.approx(mrbar / 1.128)


def test_overall_sigma_is_sample_stdev():
    values = [10.0, 10.2, 9.9, 10.1, 10.0]
    overall = estimate_overall_sigma(values)
    assert overall == pytest.approx(statistics.stdev(values))


def test_overall_sigma_requires_two_observations():
    from app.spc_engine.core.exceptions import InsufficientDataError

    with pytest.raises(InsufficientDataError):
        estimate_overall_sigma([10.0])


def test_zero_variation_produces_zero_sigma_not_a_crash():
    subgroups = [_subgroup([5.0, 5.0]), _subgroup([5.0, 5.0])]
    result = estimate_sigma(ChartType.XBAR_R, subgroups, 2, [5.0, 5.0, 5.0, 5.0])
    assert result.within_sigma == 0.0
    assert result.overall_sigma == 0.0
