from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from bbw_system.baseline import (
    BaselineConfig, BreakoutEvent, TradeSignal, find_breakouts,
    find_trade_signals, form_range, run_baseline, simulate_trades, trade_levels,
)
from bbw_system.baseline_cli import main
from bbw_system.bbw_engine import OUTPUT_NAME


def h1_fixture() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02 00:00", periods=8, freq="h")
    return pd.DataFrame({
        "timestamp": timestamps, "open": [5] * 6 + [9, 11],
        "high": [10] * 6 + [11, 13], "low": [0] * 6 + [8, 10],
        "close": [5] * 6 + [11, 12], "volume": [1] * 8,
        "bbw": [.1] * 8, "bbw_squeeze": [True] + [False] * 7,
        "ema50": [4] * 8, "trend_direction": ["LONG"] * 8, "atr14": [10] * 8,
    })


def m15_fixture(rows: int = 20) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02 07:00", periods=rows, freq="15min")
    # Breakout closes at 07:00. The fifth native bar touches and confirms.
    low = [11, 11, 11, 11, 9] + [11] * (rows - 5)
    close = [12, 12, 12, 12, 11] + [12] * (rows - 5)
    return pd.DataFrame({"timestamp": timestamps, "open": close, "high": [13] * rows,
                         "low": low, "close": close, "volume": [1] * rows})


def test_range_uses_wicks_and_inclusive_atr_filter() -> None:
    config = BaselineConfig()
    bars = h1_fixture().iloc[:6]
    assert form_range(bars, 10, config) == (10.0, 0.0, 10.0)
    assert form_range(bars, 4, config) is None
    assert form_range(bars.iloc[:5], 10, config) is None


def test_breakout_requires_close_and_matching_trend() -> None:
    frame = h1_fixture()
    events = find_breakouts(frame, BaselineConfig())
    assert events == [BreakoutEvent(pd.Timestamp("2024-01-02 07:00"), "LONG", 10, 0, 10)]
    wick_only = frame.iloc[:7].copy(); wick_only.loc[6, "close"] = 10
    assert find_breakouts(wick_only, BaselineConfig()) == []
    wrong_trend = frame.iloc[:7].copy(); wrong_trend.loc[6, "trend_direction"] = "SHORT"
    assert find_breakouts(wrong_trend, BaselineConfig()) == []


def test_retest_window_penetration_confirmation_and_close_time() -> None:
    event = BreakoutEvent(pd.Timestamp("2024-01-02 07:00"), "LONG", 10, 0, 10)
    signals = find_trade_signals([event], m15_fixture(), "CNYRUBF", BaselineConfig())
    assert signals[0].timestamp == pd.Timestamp("2024-01-02 08:15")
    assert signals[0].entry_price == 11
    deep = m15_fixture(); deep.loc[4, "low"] = 7
    assert find_trade_signals([event], deep, "CNYRUBF", BaselineConfig()) == []
    inside = m15_fixture(); inside.loc[4, "close"] = 9
    assert find_trade_signals([event], inside, "CNYRUBF", BaselineConfig()) == []


def test_stop_tp_and_partial_trade_simulator_stop_first() -> None:
    signal = TradeSignal(pd.Timestamp("2024-01-02 08:15"), "CNYRUBF", "LONG", 11, 10, 0, 10)
    assert trade_levels(signal, BaselineConfig()) == (-4, 26, 41, 56)
    bars = m15_fixture()
    bars.loc[6, ["high", "low", "close"]] = [30, -5, 12]
    trade = simulate_trades([signal], bars, BaselineConfig()).iloc[0]
    assert trade.exit_reason == "STOP"
    assert trade.result_R == -1  # stop wins an ambiguous stop+TP1 candle


def test_prefix_causality_and_stability() -> None:
    base_h1, base_m15 = h1_fixture(), m15_fixture()
    expected_event = find_breakouts(base_h1.iloc[:7], BaselineConfig())
    changed_h1 = base_h1.copy(); changed_h1.loc[7, ["high", "low", "close"]] = [999, -999, -500]
    assert find_breakouts(changed_h1, BaselineConfig())[:1] == expected_event
    expected_signal = find_trade_signals(expected_event, base_m15.iloc[:5], "CNYRUBF", BaselineConfig())
    changed_m15 = base_m15.copy(); changed_m15.loc[10:, "close"] = 999
    assert find_trade_signals(expected_event, changed_m15, "CNYRUBF", BaselineConfig()) == expected_signal


def write_bundle(root: Path) -> tuple[Path, Path]:
    feature_root, normalized = root / "features", root / "normalized" / "CNYRUBF"
    feature_root.mkdir(parents=True); normalized.mkdir(parents=True)
    h1_fixture().to_csv(feature_root / OUTPUT_NAME, index=False)
    payload = m15_fixture().to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S").encode()
    (normalized / "M15.csv").write_bytes(payload)
    manifest = {"instrument": "CNYRUBF", "timestamp_semantics": "START",
                "timeframes": {"M15": {"sha256": hashlib.sha256(payload).hexdigest()}}}
    (normalized / "NORMALIZED_MANIFEST.json").write_text(json.dumps(manifest))
    return feature_root, root / "normalized"


def test_runner_cli_is_deterministic_and_inputs_are_read_only(tmp_path: Path) -> None:
    features, normalized = write_bundle(tmp_path)
    sources = [features / OUTPUT_NAME, normalized / "CNYRUBF" / "M15.csv"]
    before = [path.read_bytes() for path in sources]
    first = run_baseline(features, normalized, tmp_path / "out1", "CNYRUBF")
    second = run_baseline(features, normalized, tmp_path / "out2", "CNYRUBF")
    assert first["sha256"] == second["sha256"]
    assert (tmp_path / "out1" / "BASELINE_TRADES.csv").read_bytes() == (tmp_path / "out2" / "BASELINE_TRADES.csv").read_bytes()
    assert (tmp_path / "out1" / "BASELINE_REPORT.md").is_file()
    assert [path.read_bytes() for path in sources] == before
    assert main(["--feature-root", str(features), "--normalized-root", str(normalized),
                 "--output-root", str(tmp_path / "cli"), "--symbol", "CNYRUBF"]) == 0


def test_true_oos_is_rejected() -> None:
    frame = h1_fixture(); frame["timestamp"] = pd.date_range("2025-01-01", periods=8, freq="h")
    with pytest.raises(ValueError, match="TRUE OOS"):
        find_breakouts(frame, BaselineConfig())
