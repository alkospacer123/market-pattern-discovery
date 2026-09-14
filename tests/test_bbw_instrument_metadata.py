from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from bbw_system.instrument_metadata import (
    AUTOPROLONG_SERIES, MetadataLookupError, load_metadata, session_on,
    tick_at, trading_date_for, weekend_session_on,
)
from bbw_system.data_freeze import _series_type

PASSPORT = Path("bbw_system/config/instruments/cnyrubf.yaml")
MSK = ZoneInfo("Europe/Moscow")


@pytest.fixture(scope="module")
def metadata():
    return load_metadata(PASSPORT)


def test_tick_boundary_uses_trading_day_start_not_midnight(metadata):
    before = tick_at(metadata, datetime(2023, 9, 27, 19, 4, 59, tzinfo=MSK))
    after = tick_at(metadata, datetime(2023, 9, 27, 19, 5, tzinfo=MSK))
    assert (before["tick_size_rub_per_cny"], before["tick_value_rub_per_contract"]) == (0.01, 10)
    assert (after["tick_size_rub_per_cny"], after["tick_value_rub_per_contract"]) == (0.001, 1)
    assert tick_at(metadata, datetime(2023, 2, 1, tzinfo=MSK))["id"] == "tick_2023_old"


def test_session_regimes_and_july_expansion(metadata):
    assert session_on(metadata, date(2024, 5, 1))["trading_intervals"][0][0] == "09:00"
    assert session_on(metadata, date(2025, 1, 27))["opening_auction"] == ["08:50", "09:00"]
    july = session_on(metadata, date(2026, 7, 14))
    assert july["opening_auction"] == ["06:50", "07:00"]
    assert july["trading_intervals"][-1][-1] == "23:50"


def test_trading_date_assignment_changes_at_uts(metadata):
    assert trading_date_for(metadata, datetime(2026, 3, 20, 20, tzinfo=MSK), nonworking_dates=set()) == date(2026, 3, 23)
    assert trading_date_for(metadata, datetime(2026, 3, 23, 20, tzinfo=MSK), nonworking_dates=set()) == date(2026, 3, 23)


def test_weekend_is_explicit_and_maps_to_following_working_day(metadata):
    assert weekend_session_on(metadata, date(2025, 3, 1))["trading_date_rule"] == "following_working_day"
    assert trading_date_for(metadata, datetime(2025, 3, 1, 12, tzinfo=MSK), nonworking_dates=set()) == date(2025, 3, 3)
    with pytest.raises(MetadataLookupError):
        trading_date_for(metadata, datetime(2025, 3, 1, 12, tzinfo=MSK))


def test_storage_quarters_are_never_rollovers(metadata):
    assert metadata["identity"]["series_type"]["value"] == AUTOPROLONG_SERIES
    assert metadata["rollover"]["synthetic_rollovers"] == []
    assert metadata["rollover"]["source_partitions_are_rollovers"] is False
    series, evidence = _series_type({}, metadata)
    assert (series, evidence) == (AUTOPROLONG_SERIES, "verified instrument passport")


def test_lookup_fails_closed_outside_freeze(metadata):
    with pytest.raises(MetadataLookupError):
        tick_at(metadata, datetime(2022, 12, 31, tzinfo=MSK))
    with pytest.raises(MetadataLookupError):
        session_on(metadata, date(2026, 9, 1))
