from datetime import datetime, timedelta, timezone

import pytest

from app.spc_engine.core.enums import SubgroupMethod
from app.spc_engine.core.exceptions import IncompatibleContextError, InvalidSubgroupSizeError
from app.spc_engine.core.models import MeasurementRecord
from app.spc_engine.subgrouping.subgroup_engine import form_subgroups


def _records(values, machine_id="M1", start=None, interval_seconds=60):
    start = start or datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        MeasurementRecord(
            row_number=i + 1,
            value=v,
            event_timestamp=start + timedelta(seconds=interval_seconds * i),
            machine_id=machine_id,
        )
        for i, v in enumerate(values)
    ]


def test_fixed_size_forms_complete_chunks_only():
    records = _records([1, 2, 3, 4, 5, 6, 7])  # 7 values, size 3 -> 2 full subgroups, 1 dropped
    subgroups = form_subgroups(records, SubgroupMethod.FIXED_SIZE, subgroup_size=3, maximum_time_gap_seconds=3600)
    assert len(subgroups) == 2
    assert [sg.count for sg in subgroups] == [3, 3]
    assert subgroups[0].values == [1, 2, 3]
    assert subgroups[1].values == [4, 5, 6]


def test_consecutive_breaks_on_time_gap():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    # Monotonically increasing timestamps, but with a 5-hour gap between the
    # 2nd and 3rd record (all others 60s apart).
    timestamps = [
        start,
        start + timedelta(seconds=60),
        start + timedelta(seconds=60) + timedelta(hours=5),
        start + timedelta(seconds=60) + timedelta(hours=5) + timedelta(seconds=60),
        start + timedelta(seconds=60) + timedelta(hours=5) + timedelta(seconds=120),
    ]
    records = [
        MeasurementRecord(row_number=i + 1, value=float(i), event_timestamp=ts, machine_id="M1")
        for i, ts in enumerate(timestamps)
    ]
    subgroups = form_subgroups(records, SubgroupMethod.CONSECUTIVE, subgroup_size=5, maximum_time_gap_seconds=3600)
    # Gap forces a subgroup close after 2 records, even though target size is 5.
    assert subgroups[0].count == 2
    assert subgroups[1].count == 3


def test_subgroup_size_one_forms_singletons():
    records = _records([1, 2, 3])
    subgroups = form_subgroups(records, SubgroupMethod.CONSECUTIVE, subgroup_size=1, maximum_time_gap_seconds=3600)
    assert len(subgroups) == 3
    assert all(sg.count == 1 for sg in subgroups)


def test_incompatible_context_raises():
    records = _records([1, 2, 3], machine_id="M1")
    records[1] = MeasurementRecord(
        row_number=2, value=2, event_timestamp=records[1].event_timestamp, machine_id="M2"
    )
    with pytest.raises(IncompatibleContextError):
        form_subgroups(records, SubgroupMethod.FIXED_SIZE, subgroup_size=3, maximum_time_gap_seconds=3600)


def test_existing_id_requires_hint_on_every_record():
    records = _records([1, 2, 3])
    with pytest.raises(InvalidSubgroupSizeError):
        form_subgroups(records, SubgroupMethod.EXISTING_ID, subgroup_size=3, maximum_time_gap_seconds=3600)


def test_existing_id_groups_by_hint():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records = [
        MeasurementRecord(row_number=1, value=1, event_timestamp=start, machine_id="M1", subgroup_hint="A"),
        MeasurementRecord(row_number=2, value=2, event_timestamp=start, machine_id="M1", subgroup_hint="A"),
        MeasurementRecord(row_number=3, value=3, event_timestamp=start, machine_id="M1", subgroup_hint="B"),
    ]
    subgroups = form_subgroups(records, SubgroupMethod.EXISTING_ID, subgroup_size=2, maximum_time_gap_seconds=3600)
    assert len(subgroups) == 2
    sizes = sorted(sg.count for sg in subgroups)
    assert sizes == [1, 2]
