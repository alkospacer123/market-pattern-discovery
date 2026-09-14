from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bbw_system.bbw_engine import (
    BBWEngineError,
    OUTPUT_COLUMNS,
    OUTPUT_NAME,
    calculate_features,
    run_bbw_engine,
)
from bbw_system.bbw_engine_cli import main


def candles(rows: int = 100, *, start: str = "2024-01-01") -> pd.DataFrame:
    timestamp = pd.date_range(start, periods=rows, freq="h")
    close = pd.Series(np.arange(rows, dtype=float) + 100.0)
    return pd.DataFrame({
        "timestamp": timestamp,
        "open": close - 0.25,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": np.arange(rows) + 1,
    })


def normalized_bundle(root: Path, frame: pd.DataFrame) -> Path:
    target = root / "CNYRUBF"
    target.mkdir(parents=True)
    payload = frame.to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S").encode()
    (target / "H1.csv").write_bytes(payload)
    manifest = {
        "instrument": "CNYRUBF", "timestamp_semantics": "START",
        "timeframes": {"H1": {"sha256": hashlib.sha256(payload).hexdigest()}},
    }
    (target / "NORMALIZED_MANIFEST.json").write_text(json.dumps(manifest))
    return target


def test_bbw_formula_uses_population_standard_deviation() -> None:
    source = candles(20)
    result = calculate_features(source)
    values = source.close.iloc[:10]
    middle = values.mean()
    deviation = values.std(ddof=0)
    assert result.loc[9, "bb_middle"] == pytest.approx(middle)
    assert result.loc[9, "bb_upper"] == pytest.approx(middle + 2 * deviation)
    assert result.loc[9, "bb_lower"] == pytest.approx(middle - 2 * deviation)
    assert result.loc[9, "bbw"] == pytest.approx(4 * deviation / middle)
    assert pd.isna(result.loc[8, "bbw"])


def test_ema_and_slope_and_trend_direction() -> None:
    source = candles(80)
    result = calculate_features(source)
    expected = source.close.ewm(span=50, adjust=False, min_periods=50).mean()
    pd.testing.assert_series_equal(result.ema50, expected, check_names=False)
    assert result.loc[60, "ema_slope"] == pytest.approx(expected.iloc[60] - expected.iloc[50])
    assert result.loc[60, "trend_direction"] == "LONG"
    assert (result.loc[:58, "trend_direction"] == "FLAT").all()


def test_wilder_atr() -> None:
    source = candles(20)
    source.loc[14, ["open", "high", "low", "close"]] += 10
    result = calculate_features(source)
    previous = source.close.shift(1)
    tr = pd.concat([(source.high - source.low), (source.high - previous).abs(), (source.low - previous).abs()], axis=1).max(axis=1)
    seed = tr.iloc[:14].mean()
    assert pd.isna(result.loc[12, "atr14"])
    assert result.loc[13, "atr14"] == pytest.approx(seed)
    assert result.loc[14, "atr14"] == pytest.approx((seed * 13 + tr.iloc[14]) / 14)


def test_features_have_no_lookahead_and_threshold_waits_for_ten_days() -> None:
    source = candles(24 * 12)
    complete = calculate_features(source)
    prefix = calculate_features(source.iloc[:250])
    pd.testing.assert_frame_equal(complete.iloc[:250].reset_index(drop=True), prefix.reset_index(drop=True))
    assert complete.loc[24 * 8, "bbw_threshold"] != complete.loc[24 * 8, "bbw_threshold"]  # NaN
    assert pd.notna(complete.loc[24 * 9, "bbw_threshold"])


def test_run_is_deterministic_writes_files_and_preserves_source(tmp_path: Path) -> None:
    bundle = normalized_bundle(tmp_path / "normalized", candles(24 * 12))
    source = bundle / "H1.csv"
    before = source.read_bytes()
    first = run_bbw_engine(tmp_path / "normalized", tmp_path / "out1", "CNYRUBF")
    second = run_bbw_engine(tmp_path / "normalized", tmp_path / "out2", "CNYRUBF")
    assert first["sha256"] == second["sha256"]
    assert (tmp_path / "out1" / OUTPUT_NAME).read_bytes() == (tmp_path / "out2" / OUTPUT_NAME).read_bytes()
    assert (tmp_path / "out1" / "BBW_ENGINE_REPORT.md").is_file()
    assert source.read_bytes() == before
    output = pd.read_csv(tmp_path / "out1" / OUTPUT_NAME)
    assert tuple(output.columns) == OUTPUT_COLUMNS


def test_cli_and_fail_closed_contracts(tmp_path: Path) -> None:
    normalized_bundle(tmp_path / "normalized", candles())
    assert main(["--input-root", str(tmp_path / "normalized"), "--output-root", str(tmp_path / "out"), "--symbol", "CNYRUBF"]) == 0
    assert (tmp_path / "out" / OUTPUT_NAME).is_file()
    with pytest.raises(BBWEngineError, match="TRUE OOS"):
        calculate_features(candles(20, start="2025-01-01"))
    with pytest.raises(BBWEngineError, match="only CNYRUBF"):
        run_bbw_engine(tmp_path / "normalized", tmp_path / "bad", "OTHER")
