from __future__ import annotations

import hashlib
from datetime import timedelta
from decimal import Decimal

import pandas as pd
import pytest

import TradingSystemLab.stage8_robot.production_history as history
import TradingSystemLab.stage8_robot.production_history_store as store_module
from TradingSystemLab.stage8_robot.production_history_store import (
    ProductionHistoryStore,
    ProductionHistoryStoreError,
    initialize_history_store,
)
from TradingSystemLab.stage8_robot.specification import INSTRUMENTS


def _seed_file(path, *, extra=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    start = pd.Timestamp("2026-08-01T00:00:00", tz="Europe/Moscow")
    lines = ["Datetime;Open;High;Low;Close;Volume"]
    for index in range(900 + extra):
        stamp = (start + pd.Timedelta(hours=index)).tz_localize(None)
        base = Decimal("100") + Decimal(index) / Decimal("1000")
        lines.append(
            f"{stamp.isoformat(sep=' ')};"
            f"{base};{base + 1};{base - 1};{base + Decimal('0.5')};1"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _data_root(tmp_path, monkeypatch):
    root = tmp_path / "market-pattern-data"
    hashes = {}
    for instrument in INSTRUMENTS:
        source = root / "forever" / instrument / f"{instrument}_H1.csv"
        _seed_file(source)
        hashes[instrument] = hashlib.sha256(source.read_bytes()).hexdigest()
    monkeypatch.setattr(history, "SEED_SHA256", hashes)
    monkeypatch.setattr(store_module, "SEED_SHA256", hashes)
    return root


def test_history_store_initializes_once_from_exact_pinned_seed(tmp_path, monkeypatch):
    root = _data_root(tmp_path, monkeypatch)
    runtime = tmp_path / "runtime"
    target = initialize_history_store(runtime, root)
    assert target.is_file()
    assert initialize_history_store(runtime, root) == target
    store = ProductionHistoryStore(runtime)
    try:
        for instrument in INSTRUMENTS:
            frame = store.close_frame(instrument)
            assert len(frame) == 900
            assert str(frame.index.tz) == "Europe/Moscow"
    finally:
        store.close()


def test_history_store_extends_only_through_exact_overlap(tmp_path, monkeypatch):
    root = _data_root(tmp_path, monkeypatch)
    runtime = tmp_path / "runtime"
    initialize_history_store(runtime, root)
    store = ProductionHistoryStore(runtime)
    try:
        instrument = "USDRUBF"
        existing = store._open_frame(instrument)
        tail = existing.iloc[-3:].copy()
        new_stamp = existing.index[-1] + timedelta(hours=1)
        new_row = pd.DataFrame(
            [[Decimal("200"), Decimal("201"), Decimal("199"), Decimal("200.5")]],
            index=pd.DatetimeIndex([new_stamp], name="OpenTime"),
            columns=history.OHLC,
            dtype=object,
        )
        live = pd.concat([tail, new_row])
        store.merge_live(instrument, live)
        merged = store._open_frame(instrument)
        assert len(merged) == 901
        assert merged.index[-1] == new_stamp

        mismatch = live.copy()
        mismatch.loc[tail.index[-1], "Close"] = Decimal("999")
        with pytest.raises(
            ProductionHistoryStoreError,
            match="STAGE8_12_4_HISTORY_OVERLAP_OHLC_MISMATCH",
        ):
            store.merge_live(instrument, mismatch)

        far = live.iloc[-1:].copy()
        far.index = far.index + timedelta(days=40)
        with pytest.raises(
            ProductionHistoryStoreError,
            match="STAGE8_12_4_HISTORY_OVERLAP_REQUIRED",
        ):
            store.merge_live(instrument, far)
    finally:
        store.close()


def test_history_store_identity_is_bound_to_seed_authority(tmp_path, monkeypatch):
    root = _data_root(tmp_path, monkeypatch)
    runtime = tmp_path / "runtime"
    initialize_history_store(runtime, root)
    changed = dict(store_module.SEED_SHA256)
    changed["USDRUBF"] = "0" * 64
    monkeypatch.setattr(store_module, "SEED_SHA256", changed)
    with pytest.raises(
        ProductionHistoryStoreError,
        match="STAGE8_12_4_HISTORY_STORE_IDENTITY_INVALID",
    ):
        ProductionHistoryStore(runtime)
