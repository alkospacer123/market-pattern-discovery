from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
import pytest

from TradingSystemLab.stage8_robot.production_history import (
    MOSCOW,
    SEED_FILES,
    SEED_SHA256,
    STAGE5_DATA_COMMIT,
    MIN_CACHE_OVERLAP_BARS,
    ProductionHistoryError,
    close_index_for_frozen_t3,
    finam_completed_open_h1,
    load_stage5_seed_open_h1,
    splice_seed_and_finam_open_h1,
    splice_cache_and_finam_open_h1,
    update_production_h1,
)


def frame(rows):
    index = pd.DatetimeIndex(
        [pd.Timestamp(stamp, tz=MOSCOW) for stamp, *_ in rows],
        name="OpenTime",
    )
    return pd.DataFrame(
        [[Decimal(str(v)) for v in values] for _, *values in rows],
        index=index,
        columns=("Open", "High", "Low", "Close"),
        dtype=object,
    )


def test_stage5_seed_authority_constants_are_exact():
    assert STAGE5_DATA_COMMIT == "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
    assert SEED_FILES == {
        "USDRUBF": "forever/USDRUBF/USDRUBF_H1.csv",
        "CNYRUBF": "forever/CNYRUBF/CNYRUBF_H1.csv",
        "GLDRUBF": "forever/GLDRUBF/GLDRUBF_H1.csv",
        "IMOEXF": "forever/IMOEXF/IMOEXF_H1.csv",
    }
    assert SEED_SHA256 == {
        "USDRUBF": "f0ca366d816a6213742271242e87c53d1e23f5a5fc4655df0123217df418a226",
        "CNYRUBF": "a3815b88a11aa5878b8bd104140f002859349c2c8d7f6ff0476a0d4c4d9a612e",
        "GLDRUBF": "12a626ba6cc47fce2f392d4a6ce3bdb8a3c1aad074306a73ab480fcfbb83b87e",
        "IMOEXF": "119878c12f602924296ab27b5b9f3cf51fa54f1a9370793892edbea58003e110",
    }


def test_seed_loader_preserves_research_open_time_and_exact_hash(tmp_path, monkeypatch):
    root = tmp_path / "data"
    source = root / "forever/USDRUBF/USDRUBF_H1.csv"
    source.parent.mkdir(parents=True)
    source.write_text(
        "Datetime;Open;High;Low;Close;Volume\n"
        "2026-09-15 21:00:00;84.36;84.38;84.33;84.35;1\n"
        "2026-09-15 22:00:00;84.35;84.40;84.34;84.39;2\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setitem(SEED_SHA256, "USDRUBF", digest)

    loaded = load_stage5_seed_open_h1(root, "USDRUBF")
    assert str(loaded.index.tz) == MOSCOW
    assert loaded.index[0] == pd.Timestamp("2026-09-15 21:00:00", tz=MOSCOW)
    assert loaded.loc[loaded.index[0], "Close"] == Decimal("84.35")

    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ProductionHistoryError, match="SEED_SHA256_MISMATCH"):
        load_stage5_seed_open_h1(root, "USDRUBF")


def test_finam_completed_h1_keeps_open_timestamp_and_rest_decimal_schema():
    observed = datetime(2026, 10, 7, 8, 30, tzinfo=timezone.utc)
    windows = [
        (
            datetime(2026, 10, 7, 6, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc),
        )
    ]
    response = {
        "bars": [
            {
                "timestamp": "2026-10-07T06:00:00Z",
                "open": {"value": "100"},
                "high": {"value": "102"},
                "low": {"value": "99"},
                "close": {"value": "101"},
            },
            {
                "timestamp": "2026-10-07T07:00:00Z",
                "open": {"value": "101"},
                "high": {"value": "103"},
                "low": {"value": "100"},
                "close": {"value": "102"},
            },
            {
                "timestamp": "2026-10-07T08:00:00Z",
                "open": {"value": "102"},
                "high": {"value": "104"},
                "low": {"value": "101"},
                "close": {"value": "103"},
            },
        ]
    }
    loaded = finam_completed_open_h1(response, observed, windows)
    assert list(loaded.index) == [
        pd.Timestamp("2026-10-07 09:00:00", tz=MOSCOW),
        pd.Timestamp("2026-10-07 10:00:00", tz=MOSCOW),
    ]
    assert loaded.iloc[-1].Close == Decimal("102")

    malformed = {"bars": [dict(response["bars"][0], close=101)]}
    with pytest.raises(ProductionHistoryError, match="FINAM_H1_INVALID"):
        finam_completed_open_h1(malformed, observed, windows)


def test_splice_requires_exact_overlap_and_appends_only_new_bars():
    seed = frame([
        ("2026-09-15 20:00:00", 100, 101, 99, 100),
        ("2026-09-15 21:00:00", 100, 102, 100, 101),
        ("2026-09-15 22:00:00", 101, 103, 100, 102),
    ])
    live = frame([
        ("2026-09-15 21:00:00", 100, 102, 100, 101),
        ("2026-09-15 22:00:00", 101, 103, 100, 102),
        ("2026-09-15 23:00:00", 102, 104, 101, 103),
    ])
    merged = splice_seed_and_finam_open_h1(seed, live)
    assert list(merged.index) == [
        pd.Timestamp("2026-09-15 20:00:00", tz=MOSCOW),
        pd.Timestamp("2026-09-15 21:00:00", tz=MOSCOW),
        pd.Timestamp("2026-09-15 22:00:00", tz=MOSCOW),
        pd.Timestamp("2026-09-15 23:00:00", tz=MOSCOW),
    ]

    conflicting = live.copy()
    conflicting.loc[pd.Timestamp("2026-09-15 22:00:00", tz=MOSCOW), "Close"] = Decimal("999")
    with pytest.raises(ProductionHistoryError, match="H1_SPLICE_OHLC_MISMATCH"):
        splice_seed_and_finam_open_h1(seed, conflicting)

    missing = live.drop(pd.Timestamp("2026-09-15 22:00:00", tz=MOSCOW))
    with pytest.raises(ProductionHistoryError, match="H1_SPLICE_TIMESTAMP_MISMATCH"):
        splice_seed_and_finam_open_h1(seed, missing)


def test_close_index_matches_frozen_research_loader_semantics():
    open_h1 = frame([
        ("2026-09-15 22:00:00", 100, 101, 99, 100),
        ("2026-09-15 23:00:00", 100, 102, 100, 101),
    ])
    closed = close_index_for_frozen_t3(open_h1)
    assert list(closed.index) == [
        pd.Timestamp("2026-09-15 23:00:00", tz=MOSCOW),
        pd.Timestamp("2026-09-16 00:00:00", tz=MOSCOW),
    ]
    assert all(dtype.kind == "f" for dtype in closed.dtypes)


def test_finam_history_retains_prior_days_and_excludes_current_incomplete_bar():
    observed = datetime(2026, 10, 7, 8, 30, tzinfo=timezone.utc)
    windows = [
        (
            datetime(2026, 10, 7, 6, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc),
        )
    ]
    response = {
        "bars": [
            {
                "timestamp": "2026-09-15T18:00:00Z",
                "open": {"value": "100"},
                "high": {"value": "102"},
                "low": {"value": "99"},
                "close": {"value": "101"},
            },
            {
                "timestamp": "2026-10-07T06:00:00Z",
                "open": {"value": "101"},
                "high": {"value": "103"},
                "low": {"value": "100"},
                "close": {"value": "102"},
            },
            {
                "timestamp": "2026-10-07T07:00:00Z",
                "open": {"value": "102"},
                "high": {"value": "104"},
                "low": {"value": "101"},
                "close": {"value": "103"},
            },
            {
                "timestamp": "2026-10-07T08:00:00Z",
                "open": {"value": "103"},
                "high": {"value": "105"},
                "low": {"value": "102"},
                "close": {"value": "104"},
            },
        ]
    }
    loaded = finam_completed_open_h1(response, observed, windows)
    assert list(loaded.index) == [
        pd.Timestamp("2026-09-15 21:00:00", tz=MOSCOW),
        pd.Timestamp("2026-10-07 09:00:00", tz=MOSCOW),
        pd.Timestamp("2026-10-07 10:00:00", tz=MOSCOW),
    ]
    assert pd.Timestamp("2026-10-07 11:00:00", tz=MOSCOW) not in loaded.index


def test_finam_history_closed_day_keeps_prior_history_and_rejects_current_day_bar():
    observed = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)
    prior_only = {
        "bars": [
            {
                "timestamp": "2026-10-09T18:00:00Z",
                "open": {"value": "100"},
                "high": {"value": "101"},
                "low": {"value": "99"},
                "close": {"value": "100"},
            }
        ]
    }
    loaded = finam_completed_open_h1(prior_only, observed, [])
    assert list(loaded.index) == [
        pd.Timestamp("2026-10-09 21:00:00", tz=MOSCOW)
    ]

    current_bar = {
        "bars": [
            *prior_only["bars"],
            {
                "timestamp": "2026-10-11T08:00:00Z",
                "open": {"value": "100"},
                "high": {"value": "101"},
                "low": {"value": "99"},
                "close": {"value": "100"},
            },
        ]
    }
    with pytest.raises(
        ProductionHistoryError,
        match="FINAM_H1_OUTSIDE_CURRENT_SCHEDULE",
    ):
        finam_completed_open_h1(current_bar, observed, [])


def _finam_response_from_frame(open_h1: pd.DataFrame) -> dict:
    bars = []
    for stamp, row in open_h1.iterrows():
        utc = stamp.tz_convert("UTC")
        bars.append({
            "timestamp": utc.isoformat().replace("+00:00", "Z"),
            "open": {"value": str(row.Open)},
            "high": {"value": str(row.High)},
            "low": {"value": str(row.Low)},
            "close": {"value": str(row.Close)},
        })
    return {"bars": bars}


def _hourly_frame(start: str, count: int) -> pd.DataFrame:
    rows = []
    stamp = pd.Timestamp(start, tz=MOSCOW)
    for index in range(count):
        value = Decimal("100") + Decimal(index) / Decimal("100")
        rows.append((
            (stamp + pd.Timedelta(hours=index)).strftime("%Y-%m-%d %H:%M:%S"),
            value,
            value + Decimal("0.02"),
            value - Decimal("0.02"),
            value + Decimal("0.01"),
        ))
    return frame(rows)


def test_rolling_cache_preserves_authenticated_continuity_after_seed_window(tmp_path, monkeypatch):
    seed = _hourly_frame("2026-09-14 10:00:00", 80)
    first_live = seed.iloc[-40:].copy()
    first_extension = _hourly_frame("2026-09-17 18:00:00", 4)
    first_live = pd.concat([first_live, first_extension])

    monkeypatch.setattr(
        "TradingSystemLab.stage8_robot.production_history.load_stage5_seed_open_h1",
        lambda root, instrument: seed.copy(),
    )
    first_closed = update_production_h1(
        runtime_root=tmp_path / "runtime",
        data_root=tmp_path / "data",
        instrument="USDRUBF",
        finam_response=_finam_response_from_frame(first_live),
        observed_at=datetime(2026, 9, 19, 0, tzinfo=timezone.utc),
        trading_windows=[],
    )
    assert first_closed.index[-1] == first_extension.index[-1] + pd.Timedelta("1h")

    cached_open_end = first_extension.index[-1]
    second_prefix = pd.concat([seed, first_extension]).loc[
        lambda value: value.index <= cached_open_end
    ].iloc[-40:]
    second_extension = _hourly_frame(
        (cached_open_end + pd.Timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        3,
    )
    second_live = pd.concat([second_prefix, second_extension])

    monkeypatch.setattr(
        "TradingSystemLab.stage8_robot.production_history.load_stage5_seed_open_h1",
        lambda *_: (_ for _ in ()).throw(AssertionError("static seed must not be reread")),
    )
    second_closed = update_production_h1(
        runtime_root=tmp_path / "runtime",
        data_root=tmp_path / "data",
        instrument="USDRUBF",
        finam_response=_finam_response_from_frame(second_live),
        observed_at=datetime(2026, 9, 20, 0, tzinfo=timezone.utc),
        trading_windows=[],
    )
    assert second_closed.index[-1] == second_extension.index[-1] + pd.Timedelta("1h")


def test_rolling_cache_rejects_tamper_and_lost_overlap(tmp_path, monkeypatch):
    seed = _hourly_frame("2026-09-14 10:00:00", 80)
    live = seed.iloc[-40:].copy()
    monkeypatch.setattr(
        "TradingSystemLab.stage8_robot.production_history.load_stage5_seed_open_h1",
        lambda root, instrument: seed.copy(),
    )
    update_production_h1(
        runtime_root=tmp_path,
        data_root=tmp_path / "data",
        instrument="USDRUBF",
        finam_response=_finam_response_from_frame(live),
        observed_at=datetime(2026, 9, 19, 0, tzinfo=timezone.utc),
        trading_windows=[],
    )
    cache_path = tmp_path / "state" / "production-h1" / "USDRUBF.csv"
    cache_path.write_text(cache_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ProductionHistoryError, match="H1_CACHE_AUTHORITY_MISMATCH"):
        update_production_h1(
            runtime_root=tmp_path,
            data_root=tmp_path / "data",
            instrument="USDRUBF",
            finam_response=_finam_response_from_frame(live),
            observed_at=datetime(2026, 9, 19, 0, tzinfo=timezone.utc),
            trading_windows=[],
        )


def test_cache_splice_requires_sufficient_overlap_and_cached_last_bar():
    cached = _hourly_frame("2026-09-14 10:00:00", 80)
    too_short = cached.iloc[-(MIN_CACHE_OVERLAP_BARS - 1):].copy()
    with pytest.raises(
        ProductionHistoryError, match="H1_CACHE_OVERLAP_INSUFFICIENT"
    ):
        splice_cache_and_finam_open_h1(cached, too_short)

    missing_last = cached.iloc[-(MIN_CACHE_OVERLAP_BARS + 2):-1].copy()
    assert len(missing_last) >= MIN_CACHE_OVERLAP_BARS
    with pytest.raises(
        ProductionHistoryError, match="H1_CACHE_CONTINUITY_LOST"
    ):
        splice_cache_and_finam_open_h1(cached, missing_last)
