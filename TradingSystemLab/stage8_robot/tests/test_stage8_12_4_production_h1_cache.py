from __future__ import annotations

from decimal import Decimal

import pandas as pd
import pytest

import TradingSystemLab.stage8_robot.production_h1_cache as cache_mod
from TradingSystemLab.stage8_robot.production_h1_cache import (
    ProductionH1Cache,
    ProductionH1CacheError,
    initialize_cache,
)
from TradingSystemLab.stage8_robot.production_history import MOSCOW
from TradingSystemLab.stage8_robot.specification import INSTRUMENTS


def frame(rows):
    return pd.DataFrame(
        [[Decimal(str(v)) for v in values] for _, *values in rows],
        index=pd.DatetimeIndex(
            [pd.Timestamp(stamp, tz=MOSCOW) for stamp, *_ in rows],
            name="OpenTime",
        ),
        columns=("Open", "High", "Low", "Close"),
        dtype=object,
    )


SEEDS = {
    instrument: frame([
        ("2026-09-15 20:00:00", 100, 101, 99, 100),
        ("2026-09-15 21:00:00", 100, 102, 100, 101),
        ("2026-09-15 22:00:00", 101, 103, 100, 102),
    ])
    for instrument in INSTRUMENTS
}


def test_cache_initializes_once_from_exact_seed_and_reopens(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cache_mod,
        "load_stage5_seed_open_h1",
        lambda _root, instrument: SEEDS[instrument].copy(),
    )
    path = initialize_cache(tmp_path, tmp_path / "data")
    assert path.is_file()

    cache = ProductionH1Cache(tmp_path)
    try:
        assert cache.latest_open("USDRUBF") == pd.Timestamp(
            "2026-09-15 22:00:00", tz=MOSCOW
        )
        assert cache.frame("USDRUBF").equals(SEEDS["USDRUBF"])
    finally:
        cache.close()

    assert initialize_cache(tmp_path, tmp_path / "different-data-root") == path


def test_cache_requires_exact_overlap_then_appends_and_survives_restart(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        cache_mod,
        "load_stage5_seed_open_h1",
        lambda _root, instrument: SEEDS[instrument].copy(),
    )
    initialize_cache(tmp_path, tmp_path / "data")
    live = frame([
        ("2026-09-15 21:00:00", 100, 102, 100, 101),
        ("2026-09-15 22:00:00", 101, 103, 100, 102),
        ("2026-09-15 23:00:00", 102, 104, 101, 103),
        ("2026-09-16 00:00:00", 103, 105, 102, 104),
    ])
    cache = ProductionH1Cache(tmp_path)
    try:
        assert cache.merge_finam("USDRUBF", live) == 2
        assert cache.merge_finam("USDRUBF", live) == 0
        assert cache.latest_open("USDRUBF") == pd.Timestamp(
            "2026-09-16 00:00:00", tz=MOSCOW
        )
    finally:
        cache.close()

    reopened = ProductionH1Cache(tmp_path)
    try:
        result = reopened.frame("USDRUBF")
        assert len(result) == 5
        assert result.iloc[-1].Close == Decimal("104")
    finally:
        reopened.close()


def test_cache_rejects_overlap_conflict_missing_overlap_and_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cache_mod,
        "load_stage5_seed_open_h1",
        lambda _root, instrument: SEEDS[instrument].copy(),
    )
    initialize_cache(tmp_path, tmp_path / "data")
    cache = ProductionH1Cache(tmp_path)
    try:
        conflicting = frame([
            ("2026-09-15 21:00:00", 100, 102, 100, 101),
            ("2026-09-15 22:00:00", 101, 103, 100, 999),
        ])
        with pytest.raises(
            ProductionH1CacheError, match="H1_CACHE_OHLC_MISMATCH"
        ):
            cache.merge_finam("USDRUBF", conflicting)

        no_overlap = frame([
            ("2026-10-20 10:00:00", 100, 101, 99, 100),
            ("2026-10-20 11:00:00", 100, 101, 99, 100),
        ])
        with pytest.raises(
            ProductionH1CacheError, match="H1_CACHE_NO_OVERLAP"
        ):
            cache.merge_finam("USDRUBF", no_overlap)

        duplicate = frame([
            ("2026-09-15 22:00:00", 101, 103, 100, 102),
            ("2026-09-15 23:00:00", 102, 104, 101, 103),
        ])
        duplicate = pd.concat([duplicate, duplicate.iloc[[-1]]])
        with pytest.raises(
            ProductionH1CacheError, match="H1_CACHE_LIVE_INVALID"
        ):
            cache.merge_finam("USDRUBF", duplicate)
    finally:
        cache.close()


def test_cache_identity_is_bound_to_frozen_production_and_data_authority(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        cache_mod,
        "load_stage5_seed_open_h1",
        lambda _root, instrument: SEEDS[instrument].copy(),
    )
    initialize_cache(tmp_path, tmp_path / "data")
    path = cache_mod.cache_path(tmp_path)

    import json
    import sqlite3

    db = sqlite3.connect(path)
    try:
        raw = db.execute(
            "SELECT value FROM metadata WHERE key='identity'"
        ).fetchone()[0]
        identity = json.loads(raw)
        assert identity["stage5_data_commit"] == cache_mod.STAGE5_DATA_COMMIT
        assert identity["seed_sha256"] == cache_mod.SEED_SHA256
        assert identity["instruments"] == list(INSTRUMENTS)
    finally:
        db.close()
