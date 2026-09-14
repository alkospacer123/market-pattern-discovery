"""Causal, deterministic indicator layer for the CNYRUBF H1 BBW system.

This module deliberately contains no setup, signal, execution, or backtest logic.
Input timestamps are START-labelled; a row's features become observable only when
that H1 candle closes.  Every window below is backward-looking and inclusive.
"""
from __future__ import annotations

import json
from decimal import Decimal, ROUND_CEILING
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

BB_PERIOD = 10
BB_STD = 2.0
EMA_PERIOD = 50
EMA_SLOPE_LAG = 10
ATR_PERIOD = 14
SQUEEZE_DAYS = 10
SQUEEZE_MINIMA = 6
OUTPUT_NAME = "CNYRUBF_H1_BBW_FEATURES.csv"
OUTPUT_COLUMNS = (
    "timestamp", "open", "high", "low", "close", "volume", "bb_middle",
    "bb_upper", "bb_lower", "bbw", "bbw_threshold", "bbw_squeeze",
    "ema50", "ema_slope", "trend_direction", "atr14",
)


class BBWEngineError(ValueError):
    """Raised when the normalized-input contract is not satisfied."""


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ceil_3(value: float) -> float:
    """Round upward to three decimals without binary-float surprises."""
    return float(Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_CEILING))


def _squeeze_thresholds(timestamp: pd.Series, bbw: pd.Series) -> pd.Series:
    """Six-minimum mean over observations seen in the latest 10 trading dates.

    A trading day is an explicit calendar date in the normalized timestamp (no
    exchange calendar is inferred).  The current, already-closed bar is included;
    no later bar from its day is visible.  This feature intentionally crosses day
    boundaries because its approved definition explicitly spans ten trading days.
    """
    result = pd.Series(np.nan, index=bbw.index, dtype="float64")
    dates = timestamp.dt.date
    seen_dates: list[object] = []
    values_by_date: dict[object, list[float]] = {}
    for index in bbw.index:
        day = dates.at[index]
        if not seen_dates or seen_dates[-1] != day:
            seen_dates.append(day)
            values_by_date[day] = []
        value = bbw.at[index]
        if pd.notna(value):
            values_by_date[day].append(float(value))
        if len(seen_dates) < SQUEEZE_DAYS:
            continue
        values = [item for date in seen_dates[-SQUEEZE_DAYS:] for item in values_by_date[date]]
        if len(values) >= SQUEEZE_MINIMA:
            result.at[index] = _ceil_3(float(np.mean(sorted(values)[:SQUEEZE_MINIMA])))
    return result


def calculate_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Calculate approved BBW-engine features from ordered H1 OHLCV candles."""
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(frame.columns)
    if missing:
        raise BBWEngineError(f"missing normalized columns: {sorted(missing)}")
    work = frame.loc[:, ["timestamp", "open", "high", "low", "close", "volume"]].copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="raise")
    for column in ("open", "high", "low", "close", "volume"):
        work[column] = pd.to_numeric(work[column], errors="raise")
    if work.empty:
        raise BBWEngineError("normalized H1 dataset is empty")
    if work["timestamp"].duplicated().any() or not work["timestamp"].is_monotonic_increasing:
        raise BBWEngineError("normalized H1 timestamps must be unique and increasing")
    if work["timestamp"].dt.year.eq(2025).any():
        raise BBWEngineError("locked TRUE OOS calendar year 2025 is present")

    close = work["close"].astype("float64")
    middle = close.rolling(BB_PERIOD, min_periods=BB_PERIOD).mean()
    deviation = close.rolling(BB_PERIOD, min_periods=BB_PERIOD).std(ddof=0)
    work["bb_middle"] = middle
    work["bb_upper"] = middle + BB_STD * deviation
    work["bb_lower"] = middle - BB_STD * deviation
    work["bbw"] = (work["bb_upper"] - work["bb_lower"]) / middle
    work["bbw_threshold"] = _squeeze_thresholds(work["timestamp"], work["bbw"])
    work["bbw_squeeze"] = (work["bbw"] < work["bbw_threshold"]).fillna(False)

    work["ema50"] = close.ewm(span=EMA_PERIOD, adjust=False, min_periods=EMA_PERIOD).mean()
    work["ema_slope"] = work["ema50"] - work["ema50"].shift(EMA_SLOPE_LAG)
    minimum = close.abs() * 0.001
    work["trend_direction"] = np.select(
        [work["ema_slope"] > minimum, work["ema_slope"] < -minimum],
        ["LONG", "SHORT"], default="FLAT",
    )

    previous_close = close.shift(1)
    true_range = pd.concat([
        work["high"] - work["low"],
        (work["high"] - previous_close).abs(),
        (work["low"] - previous_close).abs(),
    ], axis=1).max(axis=1)
    # Wilder ATR: seed with the first 14-TR arithmetic mean, then recurse.
    atr = pd.Series(np.nan, index=work.index, dtype="float64")
    if len(work) >= ATR_PERIOD:
        atr.iloc[ATR_PERIOD - 1] = true_range.iloc[:ATR_PERIOD].mean()
        for index in range(ATR_PERIOD, len(work)):
            atr.iloc[index] = (atr.iloc[index - 1] * (ATR_PERIOD - 1) + true_range.iloc[index]) / ATR_PERIOD
    work["atr14"] = atr
    return work.loc[:, OUTPUT_COLUMNS]


def _resolve_input(input_root: Path, symbol: str) -> tuple[Path, Path]:
    roots = (input_root / symbol, input_root)
    for root in roots:
        csv_path, manifest_path = root / "H1.csv", root / "NORMALIZED_MANIFEST.json"
        if csv_path.is_file() and manifest_path.is_file():
            return csv_path, manifest_path
    raise BBWEngineError(f"normalized H1.csv and NORMALIZED_MANIFEST.json not found under {input_root}")


def _csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S", float_format="%.15g").encode("utf-8")


def _report(source: Path, features: pd.DataFrame, output_hash: str) -> str:
    counts = features["trend_direction"].value_counts().reindex(["LONG", "SHORT", "FLAT"], fill_value=0)
    first, last = features["timestamp"].iloc[0], features["timestamp"].iloc[-1]
    calculated = int(features[["bbw", "ema50", "atr14"]].notna().all(axis=1).sum())
    return "\n".join([
        "# BBW Engine Report", "", "**Scope:** indicator features only; no Baseline or trading logic.", "",
        f"- Source: `{source.resolve()}` (normalized CNYRUBF H1 OHLCV, START-labelled)",
        f"- Period: {first.isoformat()} — {last.isoformat()}", f"- Candles: {len(features)}",
        f"- Fully calculated rows (BBW, EMA, ATR available): {calculated}",
        f"- BBW parameters: period={BB_PERIOD}, std={BB_STD:g}, population standard deviation (ddof=0)",
        f"- EMA parameters: period={EMA_PERIOD}, slope lag={EMA_SLOPE_LAG}, flat threshold=0.1% of current close",
        f"- ATR parameters: period={ATR_PERIOD}, Wilder smoothing", f"- Squeeze count: {int(features['bbw_squeeze'].sum())}",
        f"- Trend distribution: LONG={counts['LONG']}, SHORT={counts['SHORT']}, FLAT={counts['FLAT']}",
        f"- Output SHA-256: `{output_hash}`", "",
        "Squeeze thresholds use only closed observations available through each row, over the latest 10 observed trading dates; the six lowest available BBW values are averaged and rounded upward to three decimals.",
        "Calendar year 2025 is rejected as locked TRUE OOS. The source is read-only and its hash is verified before and after processing.", "",
    ])


def run_bbw_engine(input_root: Path, output_root: Path, symbol: str) -> dict[str, Any]:
    """Verify normalized input, write deterministic feature CSV and report."""
    if symbol != "CNYRUBF":
        raise BBWEngineError("BBW Engine currently permits only CNYRUBF")
    source, manifest_path = _resolve_input(input_root, symbol)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("instrument") != symbol or manifest.get("timestamp_semantics") != "START":
        raise BBWEngineError("normalized manifest instrument or timestamp semantics mismatch")
    expected = manifest.get("timeframes", {}).get("H1", {}).get("sha256")
    source_hash = file_sha256(source)
    if not expected or source_hash != expected:
        raise BBWEngineError("normalized H1 hash does not match its manifest")
    features = calculate_features(pd.read_csv(source))
    payload = _csv_bytes(features)
    output_hash = sha256(payload).hexdigest()
    output_root.mkdir(parents=True, exist_ok=True)
    output_file = output_root / OUTPUT_NAME
    output_file.write_bytes(payload)
    (output_root / "BBW_ENGINE_REPORT.md").write_text(_report(source, features, output_hash), encoding="utf-8")
    if file_sha256(source) != source_hash:
        raise BBWEngineError("normalized source mutated during BBW Engine execution")
    return {"output_file": str(output_file), "sha256": output_hash, "rows": len(features)}
