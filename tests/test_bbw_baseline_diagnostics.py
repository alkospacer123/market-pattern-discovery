from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from bbw_system.baseline import BaselineError, run_baseline
from bbw_system.baseline_diagnostics import DIAGNOSTIC_COLUMNS, run_baseline_diagnostics
from bbw_system.baseline_diagnostics_cli import main
from test_bbw_baseline import write_bundle


def _prepared(tmp_path: Path) -> tuple[Path, Path, Path]:
    features, normalized = write_bundle(tmp_path)
    baseline = tmp_path / "baseline"
    run_baseline(features, normalized, baseline, "CNYRUBF")
    return features, normalized, baseline


def test_diagnostics_funnel_and_rejection_ledger(tmp_path: Path) -> None:
    features, normalized, baseline = _prepared(tmp_path)
    result = run_baseline_diagnostics(features, normalized, baseline, tmp_path / "diagnostics", "CNYRUBF")

    assert {key: result[key] for key in (
        "h1_candles", "squeeze_events", "active_ranges", "ranges_created",
        "range_width_passed", "range_width_rejected", "breakout_candidates",
        "breakout_long", "breakout_short", "trend_passed", "trend_rejected",
        "retests_started", "retest_window_passed", "retest_penetration_passed",
        "retest_inside_close_passed", "retest_confirmation_passed",
        "trade_signals", "actual_trades",
    )} == {
        "h1_candles": 8, "squeeze_events": 1, "active_ranges": 1, "ranges_created": 1,
        "range_width_passed": 1, "range_width_rejected": 0, "breakout_candidates": 1,
        "breakout_long": 1, "breakout_short": 0, "trend_passed": 1, "trend_rejected": 0,
        "retests_started": 1, "retest_window_passed": 1, "retest_penetration_passed": 1,
        "retest_inside_close_passed": 1, "retest_confirmation_passed": 1,
        "trade_signals": 1, "actual_trades": 1,
    }
    ledger = pd.read_csv(tmp_path / "diagnostics" / "BASELINE_DIAGNOSTICS.csv")
    assert tuple(ledger.columns) == DIAGNOSTIC_COLUMNS
    assert set(ledger.stage) == {"squeeze", "range", "breakout", "trend_filter", "m15_retest"}
    report = (tmp_path / "diagnostics" / "BASELINE_DIAGNOSTICS.md").read_text()
    assert "Baseline strategy and parameters are unchanged" in report
    assert "Trade signals: 1" in report and "Actual trades: 1" in report


def test_repeat_hashes_and_read_only_inputs(tmp_path: Path) -> None:
    features, normalized, baseline = _prepared(tmp_path)
    inputs = [features / "CNYRUBF_H1_BBW_FEATURES.csv",
              normalized / "CNYRUBF" / "M15.csv",
              normalized / "CNYRUBF" / "NORMALIZED_MANIFEST.json",
              baseline / "BASELINE_TRADES.csv"]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    first = run_baseline_diagnostics(features, normalized, baseline, tmp_path / "one", "CNYRUBF")
    second = run_baseline_diagnostics(features, normalized, baseline, tmp_path / "two", "CNYRUBF")
    assert first["csv_sha256"] == second["csv_sha256"]
    assert first["report_sha256"] == second["report_sha256"]
    assert (tmp_path / "one" / "BASELINE_DIAGNOSTICS.md").read_bytes() == (tmp_path / "two" / "BASELINE_DIAGNOSTICS.md").read_bytes()
    assert before == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    assert main(["--feature-root", str(features), "--normalized-root", str(normalized),
                 "--baseline-root", str(baseline), "--output-root", str(tmp_path / "cli"),
                 "--symbol", "CNYRUBF"]) == 0


def test_rejected_trend_has_observable_timestamp_and_reason(tmp_path: Path) -> None:
    features, normalized, baseline = _prepared(tmp_path)
    feature_path = features / "CNYRUBF_H1_BBW_FEATURES.csv"
    frame = pd.read_csv(feature_path)
    frame.loc[6, "trend_direction"] = "SHORT"
    frame.to_csv(feature_path, index=False)
    # The unchanged Baseline now has no signal/trade; provide its corresponding artifact.
    run_baseline(features, normalized, baseline, "CNYRUBF")
    result = run_baseline_diagnostics(features, normalized, baseline, tmp_path / "out", "CNYRUBF")
    ledger = pd.read_csv(tmp_path / "out" / "BASELINE_DIAGNOSTICS.csv")
    rejected = ledger[(ledger.stage == "trend_filter") & (ledger.result == "REJECTED")].iloc[0]
    assert result["trend_rejected"] == 1
    assert rejected.timestamp == "2024-01-02 07:00:00"
    assert rejected.direction == "LONG"
    assert rejected.reason == "EMA trend mismatch"


def test_locked_future_data_fails_closed(tmp_path: Path) -> None:
    features, normalized, baseline = _prepared(tmp_path)
    feature_path = features / "CNYRUBF_H1_BBW_FEATURES.csv"
    frame = pd.read_csv(feature_path)
    frame["timestamp"] = pd.date_range("2025-01-01", periods=len(frame), freq="h")
    frame.to_csv(feature_path, index=False)
    with pytest.raises(BaselineError, match="TRUE OOS"):
        run_baseline_diagnostics(features, normalized, baseline, tmp_path / "out", "CNYRUBF")
