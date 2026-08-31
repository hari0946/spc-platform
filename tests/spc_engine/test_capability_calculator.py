import pytest

from app.spc_engine.capability.capability_calculator import calculate_capability, calculate_sigma_level
from app.spc_engine.core.models import Specification


def test_two_sided_specification_computes_all_indices():
    spec = Specification(lsl=19.94, usl=20.06)
    result = calculate_capability(spec, mean=20.0, within_sigma=0.01, overall_sigma=0.012, sample_size=100)
    assert result.cp == pytest.approx((20.06 - 19.94) / (6 * 0.01))
    assert result.cpu == pytest.approx((20.06 - 20.0) / (3 * 0.01))
    assert result.cpl == pytest.approx((20.0 - 19.94) / (3 * 0.01))
    assert result.cpk == pytest.approx(min(result.cpu, result.cpl))
    assert result.pp == pytest.approx((20.06 - 19.94) / (6 * 0.012))
    assert result.ppk is not None
    assert result.warnings == []


def test_upper_only_specification():
    spec = Specification(usl=20.06)
    result = calculate_capability(spec, mean=20.0, within_sigma=0.01, overall_sigma=0.012, sample_size=100)
    assert result.cpu is not None
    assert result.cpl is None
    assert result.cp is None
    assert result.cpk == pytest.approx(result.cpu)
    assert any("LSL" in w for w in result.warnings)


def test_lower_only_specification():
    spec = Specification(lsl=19.94)
    result = calculate_capability(spec, mean=20.0, within_sigma=0.01, overall_sigma=0.012, sample_size=100)
    assert result.cpl is not None
    assert result.cpu is None
    assert result.cpk == pytest.approx(result.cpl)
    assert any("USL" in w for w in result.warnings)


def test_missing_specification_returns_none_with_warning_not_crash():
    result = calculate_capability(None, mean=20.0, within_sigma=0.01, overall_sigma=0.012, sample_size=100)
    assert result.cp is None
    assert result.cpk is None
    assert result.pp is None
    assert result.ppk is None
    assert len(result.warnings) == 1


def test_zero_sigma_returns_warning_not_crash():
    spec = Specification(lsl=19.94, usl=20.06)
    result = calculate_capability(spec, mean=20.0, within_sigma=0.0, overall_sigma=0.0, sample_size=100)
    assert result.cp is None
    assert result.cpk is None
    assert result.pp is None
    assert result.ppk is None
    assert any("zero" in w.lower() for w in result.warnings)


def test_small_sample_size_warns_but_still_computes():
    spec = Specification(lsl=19.94, usl=20.06)
    result = calculate_capability(spec, mean=20.0, within_sigma=0.01, overall_sigma=0.012, sample_size=5)
    assert result.cp is not None
    assert any("Sample size" in w for w in result.warnings)


def test_negative_sigma_raises_value_error():
    spec = Specification(lsl=19.94, usl=20.06)
    with pytest.raises(ValueError):
        calculate_capability(spec, mean=20.0, within_sigma=-0.01, overall_sigma=0.01, sample_size=100)


def test_capability_result_includes_sigma_level():
    spec = Specification(lsl=19.94, usl=20.06)
    result = calculate_capability(spec, mean=20.0, within_sigma=0.01, overall_sigma=0.012, sample_size=100)
    assert result.sigma_level_short_term == pytest.approx(3 * result.cpk)
    assert result.sigma_level_long_term == pytest.approx(3 * result.cpk - 1.5)


def test_sigma_level_six_sigma_process_is_cpk_two():
    # The textbook definition: a Cpk of 2.0 is a "six sigma" process
    # short-term, reported as 4.5 sigma long-term after the standard
    # 1.5-sigma shift.
    short_term, long_term = calculate_sigma_level(cpk=2.0)
    assert short_term == pytest.approx(6.0)
    assert long_term == pytest.approx(4.5)


def test_sigma_level_none_when_cpk_missing():
    short_term, long_term = calculate_sigma_level(cpk=None)
    assert short_term is None
    assert long_term is None
