import pytest

from app.spc_engine.core.exceptions import InsufficientDataError
from app.spc_engine.statistics.descriptive_stats import calculate_descriptive_statistics


def test_basic_statistics():
    result = calculate_descriptive_statistics([1.0, 2.0, 3.0, 4.0, 5.0])
    assert result.mean == 3.0
    assert result.minimum == 1.0
    assert result.maximum == 5.0
    assert result.median == 3.0
    assert result.range_ == 4.0
    assert result.count == 5


def test_single_observation():
    result = calculate_descriptive_statistics([42.0])
    assert result.mean == 42.0
    assert result.minimum == 42.0
    assert result.maximum == 42.0
    assert result.range_ == 0.0
    assert result.count == 1


def test_all_identical_observations():
    result = calculate_descriptive_statistics([5.0] * 10)
    assert result.mean == 5.0
    assert result.range_ == 0.0


def test_empty_dataset_raises():
    with pytest.raises(InsufficientDataError):
        calculate_descriptive_statistics([])
