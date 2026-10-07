from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from TradingSystemLab.stage8_robot import production_history as history
from TradingSystemLab.stage8_robot.production_history import (
    BOOTSTRAP_DATA_COMMIT,
    BOOTSTRAP_FILES,
    MIN_OVERLAP_BARS,
    ProductionHistoryError,
    merge_h1_history,
    update_h1_history,
    validated_finam_tail,
    verify_bootstrap_checkout,
)


def frame(start: str, count: int, *, base: float = 100.0) -> pd.DataFrame:
    index = pd.date_range(start, periods=count, freq="h", tz="Europe/Moscow")
    rows = []
    for i in range(count):
        value = base + i / 100
        rows.append([value, value + 0.02, value - 0.02, value + 0.01])
    return pd.DataFrame(rows, index=index, columns=["Open", "High", "Low", "Close"])


def finam_response(source: pd.DataFrame) -> dict:
    bars = []
    for stamp, row in source.iterrows():
        utc = stamp.tz_convert("UTC")
        bars.append(
            {
                "timestamp": utc.isoformat().replace("+00:00", "Z"),
                "open": {"value": str(row.Open)},
                "high": {"value": str(row.High)},
                "low": {"value": str(row.Low)},
                "close": {"value": str(row.Close)},
            }
        )
    return {"bars": bars}


def future_schedule(day: str = "2026-01-07") -> dict:
    return {
        "sessions": [
            {
                "type": "CORE_TRADING",
                "interval": {
                    "start_time": f"{day}T04:00:00Z",
                    "end_time": f"{day}T20:00:00Z",
                },
            }
        ]
    }


def test_merge_requires_exact_overlap_and_extends_only_after_cache_end():
    base = frame("2026-01-01 10:00", 60)
    tail = base.iloc[-40:].copy()
    extension = frame(
        (base.index[-1] + pd.Timedelta(hours=1)).isoformat(), 5,
        base=200.0,
    )
    tail = pd.concat([tail, extension])
    merged = merge_h1_history(base, tail)
    assert len(merged) == len(base) + 5
    assert merged.index[-1] == extension.index[-1]
    assert merged.loc[base.index[-1], "Close"] == base.iloc[-1].Close


def test_merge_fails_on_overlap_mismatch_or_lost_continuity():
    base = frame("2026-01-01 10:00", 60)
    tail = base.iloc[-40:].copy()
    tail.iloc[-1, tail.columns.get_loc("Close")] += 1
    with pytest.raises(ProductionHistoryError, match="H1_HISTORY_OVERLAP_MISMATCH"):
        merge_h1_history(base, tail)

    stale = frame("2026-01-01 10:00", MIN_OVERLAP_BARS)
    disconnected = frame("2026-02-15 10:00", MIN_OVERLAP_BARS)
    with pytest.raises(ProductionHistoryError, match="H1_HISTORY_CONTINUITY_LOST"):
        merge_h1_history(stale, disconnected)


def test_validated_finam_tail_uses_prior_watermark_before_new_session():
    source = frame("2026-01-05 07:00", 40)
    watermark = source.index[-1].tz_convert("UTC").to_pydatetime()
    observed = datetime(2026, 1, 7, 3, 43, tzinfo=timezone.utc)
    tail, expected = validated_finam_tail(
        finam_response(source),
        schedule=future_schedule(),
        now=observed,
        prior_expected=watermark,
    )
    assert expected == watermark
    assert tail.index[-1] == source.index[-1]


def test_update_cold_start_bootstraps_then_persists_cache(tmp_path, monkeypatch):
    base = frame("2026-01-01 10:00", 60)
    tail = base.iloc[-40:].copy()
    extension = frame(
        (base.index[-1] + pd.Timedelta(hours=1)).isoformat(), 3, base=200
    )
    source = pd.concat([tail, extension])
    expected = source.index[-1].tz_convert("UTC").to_pydatetime()

    calls = {"verify": 0, "load": 0}

    def fake_verify(root):
        calls["verify"] += 1

    def fake_load(root, instrument):
        calls["load"] += 1
        return base.copy()

    monkeypatch.setattr(history, "verify_bootstrap_checkout", fake_verify)
    monkeypatch.setattr(history, "load_bootstrap_h1", fake_load)

    merged, watermark = update_h1_history(
        runtime_root=tmp_path / "runtime",
        data_root=tmp_path / "data",
        instrument="USDRUBF",
        finam_response=finam_response(source),
        schedule=future_schedule("2026-01-10"),
        now=datetime(2026, 1, 10, 3, 0, tzinfo=timezone.utc),
        prior_expected=expected,
    )
    assert watermark == expected
    assert merged.index[-1] == source.index[-1]
    assert calls == {"verify": 1, "load": 1}

    # A second update must trust only the authenticated rolling cache plus FINAM
    # overlap; the static bootstrap checkout is no longer re-read.
    next_extension = frame(
        (source.index[-1] + pd.Timedelta(hours=1)).isoformat(), 2, base=300
    )
    second_source = pd.concat([merged.iloc[-40:], next_extension])
    monkeypatch.setattr(
        history,
        "verify_bootstrap_checkout",
        lambda *_: (_ for _ in ()).throw(AssertionError("bootstrap reread")),
    )
    monkeypatch.setattr(
        history,
        "load_bootstrap_h1",
        lambda *_: (_ for _ in ()).throw(AssertionError("bootstrap reread")),
    )
    second_expected = second_source.index[-1].tz_convert("UTC").to_pydatetime()
    merged2, watermark2 = update_h1_history(
        runtime_root=tmp_path / "runtime",
        data_root=tmp_path / "data",
        instrument="USDRUBF",
        finam_response=finam_response(second_source),
        schedule=future_schedule("2026-01-11"),
        now=datetime(2026, 1, 11, 3, 0, tzinfo=timezone.utc),
        prior_expected=second_expected,
    )
    assert watermark2 == second_expected
    assert merged2.index[-1] == next_extension.index[-1]


def test_cache_tamper_fails_closed(tmp_path, monkeypatch):
    base = frame("2026-01-01 10:00", 60)
    tail = base.iloc[-40:].copy()
    expected = tail.index[-1].tz_convert("UTC").to_pydatetime()
    monkeypatch.setattr(history, "verify_bootstrap_checkout", lambda *_: None)
    monkeypatch.setattr(history, "load_bootstrap_h1", lambda *_: base.copy())
    update_h1_history(
        runtime_root=tmp_path,
        data_root=tmp_path,
        instrument="USDRUBF",
        finam_response=finam_response(tail),
        schedule=future_schedule("2026-01-10"),
        now=datetime(2026, 1, 10, 3, 0, tzinfo=timezone.utc),
        prior_expected=expected,
    )
    data_path = tmp_path / "state" / "production-h1" / "USDRUBF.csv"
    data_path.write_text(data_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ProductionHistoryError, match="H1_CACHE_AUTHORITY_MISMATCH"):
        history._load_cache(tmp_path, "USDRUBF")


def test_bootstrap_checkout_requires_commit_clean_tree_and_exact_blobs(tmp_path, monkeypatch):
    root = tmp_path / "data"
    root.mkdir()
    expected_rows = {
        relative: f"100644 {blob} 0\t{relative}"
        for relative, blob in BOOTSTRAP_FILES.values()
    }

    def good_run(command, check, capture_output, text):
        args = command[3:]
        if args == ["rev-parse", "HEAD"]:
            out = BOOTSTRAP_DATA_COMMIT + "\n"
        elif args == ["status", "--porcelain", "--untracked-files=all"]:
            out = ""
        elif args[:3] == ["ls-files", "-s", "--"]:
            out = expected_rows[args[3]] + "\n"
        else:
            raise AssertionError(args)
        return SimpleNamespace(stdout=out)

    monkeypatch.setattr(history.subprocess, "run", good_run)
    verify_bootstrap_checkout(root)

    def bad_commit(command, check, capture_output, text):
        if command[3:] == ["rev-parse", "HEAD"]:
            return SimpleNamespace(stdout="0" * 40 + "\n")
        return good_run(command, check, capture_output, text)

    monkeypatch.setattr(history.subprocess, "run", bad_commit)
    with pytest.raises(ProductionHistoryError, match="BOOTSTRAP_DATA_COMMIT_MISMATCH"):
        verify_bootstrap_checkout(root)
