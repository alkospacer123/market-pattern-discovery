from __future__ import annotations

import csv
from datetime import timedelta
from pathlib import Path

import pandas as pd
import pytest

import TradingSystemLab.stage8_robot.production_history as history
from TradingSystemLab.stage8_robot.production_history import (
    ProductionHistoryCache,
    ProductionHistoryError,
    _phase5_frame_sha,
    _read_seed_source,
    initialize_history_cache,
)
from TradingSystemLab.stage8_robot.specification import INSTRUMENTS


def _write_seed(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    start = pd.Timestamp("2024-12-01T00:00:00", tz="Europe/Moscow")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["<DATE>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<VOL>"])
        for index in range(900):
            opened = start + pd.Timedelta(hours=index)
            base = 100 + index / 1000
            writer.writerow([
                opened.tz_localize(None).isoformat(sep=" "),
                f"{base:.3f}",
                f"{base + 1:.3f}",
                f"{base - 1:.3f}",
                f"{base + 0.5:.3f}",
                "1",
            ])
        writer.writerow([
            "2026-09-16 01:00:00",
            "200.000", "201.000", "199.000", "200.500", "1",
        ])


def _prepare_root(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "market-pattern-data"
    for instrument in INSTRUMENTS:
        _write_seed(root / "forever" / instrument / f"{instrument}_H1.csv")
    _, oos = _read_seed_source(
        root / "forever" / INSTRUMENTS[0] / f"{INSTRUMENTS[0]}_H1.csv"
    )
    authority = {
        instrument: (len(oos), _phase5_frame_sha(oos))
        for instrument in INSTRUMENTS
    }
    monkeypatch.setattr(history, "PHASE5_H1_AUTHORITY", authority)
    return root


def _rest_bar(opened, values):
    return {
        "timestamp": opened.isoformat().replace("+00:00", "Z"),
        "open": {"value": values[0]},
        "high": {"value": values[1]},
        "low": {"value": values[2]},
        "close": {"value": values[3]},
    }


def test_seed_is_phase5_bound_and_repository_external(tmp_path, monkeypatch):
    data_root = _prepare_root(tmp_path, monkeypatch)
    runtime_root = tmp_path / "runtime"
    target = initialize_history_cache(runtime_root, data_root)
    assert target.is_file()
    cache = ProductionHistoryCache(runtime_root)
    try:
        for instrument in INSTRUMENTS:
            frame = cache.frame(instrument)
            assert len(frame) == 900
            assert frame.index.max() < history.PHASE5_AUTHORITY_END
        assert initialize_history_cache(runtime_root, data_root) == target
    finally:
        cache.close()


def test_seed_hash_mismatch_fails_closed(tmp_path, monkeypatch):
    data_root = _prepare_root(tmp_path, monkeypatch)
    wrong = dict(history.PHASE5_H1_AUTHORITY)
    rows, _ = wrong["USDRUBF"]
    wrong["USDRUBF"] = (rows, "0" * 64)
    monkeypatch.setattr(history, "PHASE5_H1_AUTHORITY", wrong)
    with pytest.raises(
        ProductionHistoryError,
        match="STAGE8_12_4_PHASE5_H1_AUTHORITY_MISMATCH",
    ):
        initialize_history_cache(tmp_path / "runtime", data_root)


def test_finam_overlap_extends_cache_and_normalizes_decimals(tmp_path, monkeypatch):
    data_root = _prepare_root(tmp_path, monkeypatch)
    runtime_root = tmp_path / "runtime"
    initialize_history_cache(runtime_root, data_root)
    cache = ProductionHistoryCache(runtime_root)
    try:
        instrument = "USDRUBF"
        latest = cache.latest_open(instrument)
        assert latest is not None
        existing = cache._bar(instrument, latest.isoformat())
        new_open = latest + timedelta(hours=1)
        now = latest + timedelta(hours=2)
        schedule = {
            "sessions": [{
                "type": "CORE_TRADING",
                "interval": {
                    "start_time": latest.isoformat().replace("+00:00", "Z"),
                    "end_time": (latest + timedelta(hours=4)).isoformat().replace("+00:00", "Z"),
                },
            }]
        }
        response = {
            "bars": [
                _rest_bar(latest, tuple(value + ".000" if "." not in value else value for value in existing)),
                _rest_bar(new_open, ("150.000", "151.000", "149.000", "150.500")),
            ]
        }
        expected = cache.merge_finam_tail(
            instrument=instrument,
            response=response,
            schedule=schedule,
            now=now,
        )
        assert expected == new_open
        assert cache.latest_open(instrument) == new_open
        assert len(cache.frame(instrument)) == 901
    finally:
        cache.close()


def test_finam_overlap_mismatch_and_missing_overlap_fail_closed(tmp_path, monkeypatch):
    data_root = _prepare_root(tmp_path, monkeypatch)
    runtime_root = tmp_path / "runtime"
    initialize_history_cache(runtime_root, data_root)
    cache = ProductionHistoryCache(runtime_root)
    try:
        instrument = "USDRUBF"
        latest = cache.latest_open(instrument)
        existing = cache._bar(instrument, latest.isoformat())
        now = latest + timedelta(hours=1)
        schedule = {
            "sessions": [{
                "type": "CORE_TRADING",
                "interval": {
                    "start_time": latest.isoformat().replace("+00:00", "Z"),
                    "end_time": (latest + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
                },
            }]
        }
        bad = list(existing)
        bad[3] = "999"
        with pytest.raises(
            ProductionHistoryError,
            match="STAGE8_12_4_H1_OVERLAP_MISMATCH",
        ):
            cache.merge_finam_tail(
                instrument=instrument,
                response={"bars": [_rest_bar(latest, tuple(bad))]},
                schedule=schedule,
                now=now,
            )

        far = latest + timedelta(days=31)
        no_overlap_schedule = {
            "sessions": [{
                "type": "CORE_TRADING",
                "interval": {
                    "start_time": far.isoformat().replace("+00:00", "Z"),
                    "end_time": (far + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
                },
            }]
        }
        with pytest.raises(
            ProductionHistoryError,
            match="STAGE8_12_4_H1_CACHE_OVERLAP_REQUIRED",
        ):
            cache.merge_finam_tail(
                instrument=instrument,
                response={
                    "bars": [
                        _rest_bar(far, ("160", "161", "159", "160.5"))
                    ]
                },
                schedule=no_overlap_schedule,
                now=far + timedelta(hours=1),
            )
    finally:
        cache.close()
