"""Read-only, causal diagnostics for the unchanged BBW Baseline.

This module deliberately mirrors the Baseline decision path instead of adding
hooks to, or changing, the strategy.  Every timestamp in the ledger is the
time at which the decision was observable (the candle close).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .baseline import (BaselineConfig, BaselineError, BreakoutEvent, _resolve,
                       _validate, find_breakouts, find_trade_signals,
                       load_baseline_config)
from .bbw_engine import OUTPUT_NAME, file_sha256

DIAGNOSTIC_COLUMNS = ("timestamp", "stage", "direction", "result", "reason",
                      "range_high", "range_low", "atr", "bbw", "ema_trend")


@dataclass(frozen=True)
class DiagnosticRow:
    timestamp: pd.Timestamp
    stage: str
    direction: str = ""
    result: str = ""
    reason: str = ""
    range_high: float | None = None
    range_low: float | None = None
    atr: float | None = None
    bbw: float | None = None
    ema_trend: str = ""


def _bool_squeeze(bars: pd.DataFrame) -> pd.DataFrame:
    squeeze = bars["bbw_squeeze"]
    if pd.api.types.is_bool_dtype(squeeze):
        return bars
    mapped = squeeze.astype(str).str.strip().str.lower().map({"true": True, "false": False})
    if mapped.isna().any():
        raise BaselineError("bbw_squeeze must contain only TRUE/FALSE")
    bars = bars.copy()
    bars["bbw_squeeze"] = mapped
    return bars


def _h1_diagnostics(h1: pd.DataFrame, config: BaselineConfig) -> tuple[list[DiagnosticRow], dict[str, int]]:
    required = {"timestamp", "open", "high", "low", "close", "volume", "bbw",
                "bbw_squeeze", "ema50", "trend_direction", "atr14"}
    bars = _bool_squeeze(_validate(h1, required, "H1 features"))
    rows: list[DiagnosticRow] = []
    counts = {"squeeze_events": 0, "active_ranges": 0, "ranges_created": 0,
              "range_width_passed": 0, "range_width_rejected": 0,
              "breakout_candidates": 0, "breakout_long": 0, "breakout_short": 0,
              "trend_passed": 0, "trend_rejected": 0}
    active: int | None = None
    range_created = False
    width_ever_passed = False

    def finish_range(timestamp: pd.Timestamp, reason: str) -> None:
        nonlocal range_created, width_ever_passed
        if range_created and not width_ever_passed:
            counts["range_width_rejected"] += 1
            rows.append(DiagnosticRow(timestamp, "range", result="REJECTED", reason=reason))
        range_created = width_ever_passed = False

    for i, row in bars.iterrows():
        close_time = row.timestamp + pd.Timedelta(hours=1)
        if active is None and bool(row.bbw_squeeze):
            active, range_created, width_ever_passed = i, False, False
            counts["squeeze_events"] += 1
            rows.append(DiagnosticRow(close_time, "squeeze", result="STARTED", bbw=float(row.bbw)))
            continue
        if active is None:
            continue
        if row.timestamp.date() != bars.at[active, "timestamp"].date() or i - active > config.range_max_bars:
            finish_range(close_time, "day boundary or maximum range window reached")
            active = i if bool(row.bbw_squeeze) else None
            if active is not None:
                counts["squeeze_events"] += 1
                rows.append(DiagnosticRow(close_time, "squeeze", result="STARTED", bbw=float(row.bbw)))
            continue
        candidate = bars.iloc[active:i]
        if len(candidate) < config.range_min_bars:
            continue
        high, low = float(candidate.high.max()), float(candidate.low.min())
        width, atr = high - low, float(row.atr14)
        if not range_created:
            range_created = True
            counts["ranges_created"] += 1
            counts["active_ranges"] += 1
        width_ok = pd.notna(atr) and atr > 0 and config.range_atr_min * atr <= width <= config.range_atr_max * atr
        if not width_ok:
            continue
        if not width_ever_passed:
            width_ever_passed = True
            counts["range_width_passed"] += 1
            rows.append(DiagnosticRow(close_time, "range", result="PASSED", reason="ATR width filter passed",
                                      range_high=high, range_low=low, atr=atr, bbw=float(row.bbw),
                                      ema_trend=str(row.trend_direction)))
        direction = "LONG" if row.close > high else "SHORT" if row.close < low else ""
        if not direction:
            continue
        counts["breakout_candidates"] += 1
        counts[f"breakout_{direction.lower()}"] += 1
        common = dict(timestamp=close_time, direction=direction, range_high=high,
                      range_low=low, atr=atr, bbw=float(row.bbw), ema_trend=str(row.trend_direction))
        rows.append(DiagnosticRow(stage="breakout", result="CANDIDATE", reason="close outside range", **common))
        if row.trend_direction == direction:
            counts["trend_passed"] += 1
            rows.append(DiagnosticRow(stage="trend_filter", result="PASSED", reason="EMA50 direction matched", **common))
            active = None
            range_created = width_ever_passed = False
        else:
            counts["trend_rejected"] += 1
            rows.append(DiagnosticRow(stage="trend_filter", result="REJECTED", reason="EMA trend mismatch", **common))
    if active is not None:
        finish_range(bars.iloc[-1].timestamp + pd.Timedelta(hours=1), "end of data before ATR width filter passed")
    return rows, counts


def _retest_diagnostics(events: list[BreakoutEvent], m15: pd.DataFrame,
                        config: BaselineConfig) -> tuple[list[DiagnosticRow], dict[str, int]]:
    bars = _validate(m15, {"timestamp", "open", "high", "low", "close", "volume"}, "M15")
    rows: list[DiagnosticRow] = []
    counts = {"retests_started": 0, "retest_window_passed": 0,
              "retest_penetration_passed": 0, "retest_inside_close_passed": 0,
              "retest_confirmation_passed": 0}
    for event in sorted(events, key=lambda item: (item.timestamp, item.direction)):
        eligible = bars.loc[bars.timestamp.ge(event.timestamp)].head(config.retest_max_bars)
        if eligible.empty:
            rows.append(DiagnosticRow(event.timestamp, "m15_retest", event.direction, "REJECTED",
                                      "no observable M15 bars in retest window", event.range_high, event.range_low))
            continue
        counts["retests_started"] += 1
        accepted = False
        reason = "no qualifying touch within 5-30 bars"
        decision_time = eligible.iloc[-1].timestamp + pd.Timedelta(minutes=15)
        for ordinal, (_, bar) in enumerate(eligible.iterrows(), start=1):
            level = event.range_high if event.direction == "LONG" else event.range_low
            penetration = max(0.0, level - float(bar.low)) if event.direction == "LONG" else max(0.0, float(bar.high) - level)
            touched = bar.low <= level if event.direction == "LONG" else bar.high >= level
            confirms = bar.close > level if event.direction == "LONG" else bar.close < level
            inside = bar.close < level if event.direction == "LONG" else bar.close > level
            decision_time = bar.timestamp + pd.Timedelta(minutes=15)
            if penetration > config.penetration_range_pct * event.range_width + 1e-12:
                reason = "penetration > allowed"
                break
            if inside:
                reason = "close inside range"
                break
            if touched and ordinal < config.retest_min_bars:
                reason = "touch before 5-bar minimum"
                continue
            if touched and confirms:
                counts["retest_window_passed"] += 1
                counts["retest_penetration_passed"] += 1
                counts["retest_inside_close_passed"] += 1
                counts["retest_confirmation_passed"] += 1
                rows.append(DiagnosticRow(decision_time, "m15_retest", event.direction, "PASSED",
                                          "window, penetration, outside close, and confirmation passed",
                                          event.range_high, event.range_low))
                accepted = True
                break
        if not accepted:
            rows.append(DiagnosticRow(decision_time, "m15_retest", event.direction, "REJECTED", reason,
                                      event.range_high, event.range_low))
    return rows, counts


def _markdown(counts: dict[str, Any], rows: list[DiagnosticRow], csv_digest: str) -> str:
    rejected = [row for row in rows if row.result == "REJECTED"]
    lines = ["# BBW Baseline Diagnostics", "", "**Read-only diagnostic layer. Baseline strategy and parameters are unchanged; no Optimization or Robustness was performed.**", "",
             "## Funnel", "", "### Input", f"- H1 candles: {counts['h1_candles']}", f"- Data period: {counts['period_start']} — {counts['period_end']}", "",
             "### BBW", f"- Squeeze events: {counts['squeeze_events']}", f"- Active ranges: {counts['active_ranges']}", "",
             "### Range", f"- Created: {counts['ranges_created']}", f"- Passed ATR width filter: {counts['range_width_passed']}", f"- Rejected: {counts['range_width_rejected']}", "",
             "### Breakout", f"- Candidates: {counts['breakout_candidates']}", f"- LONG / SHORT: {counts['breakout_long']} / {counts['breakout_short']}", "",
             "### Trend filter", f"- Passed EMA50 direction filter: {counts['trend_passed']}", f"- Rejected: {counts['trend_rejected']}", "",
             "### M15 Retest", f"- Started: {counts['retests_started']}", f"- Passed 5-30 candle window: {counts['retest_window_passed']}", f"- Passed penetration <=20%: {counts['retest_penetration_passed']}", f"- Passed no close inside range: {counts['retest_inside_close_passed']}", f"- Passed close confirmation: {counts['retest_confirmation_passed']}", "",
             "### Execution", f"- Trade signals: {counts['trade_signals']}", f"- Actual trades: {counts['actual_trades']}", "", "## Rejections", ""]
    if not rejected:
        lines.append("No rejected stages.")
    for row in rejected:
        lines.extend([f"### Rejected {row.stage}", f"- Timestamp: {row.timestamp.isoformat()}",
                      f"- Direction: {row.direction or 'N/A'}", f"- Reason: {row.reason}", ""])
    lines.extend(["## Reproducibility", "", f"- `BASELINE_DIAGNOSTICS.csv` SHA-256: `{csv_digest}`",
                  "- H1 decisions use START-labelled candles only at H1 close; M15 decisions use them only at M15 close.",
                  "- Ranges do not cross calendar-day boundaries and TRUE OOS year 2025 is rejected.", ""])
    return "\n".join(lines)


def run_baseline_diagnostics(feature_root: Path, normalized_root: Path, baseline_root: Path,
                             output_root: Path, symbol: str,
                             config: BaselineConfig | None = None) -> dict[str, Any]:
    """Create deterministic diagnostics without writing to any input root."""
    if symbol != "CNYRUBF":
        raise BaselineError("Baseline diagnostics currently permits only CNYRUBF")
    config = config or load_baseline_config()
    feature_path = _resolve(feature_root, symbol, OUTPUT_NAME)
    m15_path = _resolve(normalized_root, symbol, "M15.csv")
    manifest_path = _resolve(normalized_root, symbol, "NORMALIZED_MANIFEST.json")
    trades_path = _resolve(baseline_root, symbol, "BASELINE_TRADES.csv")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest.get("timeframes", {}).get("M15", {}).get("sha256")
    if manifest.get("instrument") != symbol or manifest.get("timestamp_semantics") != "START" or not expected or file_sha256(m15_path) != expected:
        raise BaselineError("normalized M15 or manifest contract mismatch")
    inputs = (feature_path, m15_path, manifest_path, trades_path)
    before = {path: file_sha256(path) for path in inputs}
    h1, m15, trades = pd.read_csv(feature_path), pd.read_csv(m15_path), pd.read_csv(trades_path)
    h1_rows, counts = _h1_diagnostics(h1, config)
    events = find_breakouts(h1, config)
    retest_rows, retest_counts = _retest_diagnostics(events, m15, config)
    signals = find_trade_signals(events, m15, symbol, config)
    if len(trades) != len(signals):
        raise BaselineError("Baseline trade artifact does not match diagnostic trade-signal count")
    if signals:
        if not {"entry_time", "direction"}.issubset(trades.columns):
            raise BaselineError("Baseline trade artifact lacks entry identity columns")
        actual = [(pd.Timestamp(row.entry_time), str(row.direction)) for _, row in trades.iterrows()]
        expected_signals = [(signal.timestamp, signal.direction) for signal in signals]
        if actual != expected_signals:
            raise BaselineError("Baseline trade artifact does not match diagnostic signals")
    times = pd.to_datetime(h1["timestamp"], errors="raise")
    counts.update(retest_counts)
    counts.update({"h1_candles": len(h1), "period_start": times.iloc[0].isoformat(),
                   "period_end": (times.iloc[-1] + pd.Timedelta(hours=1)).isoformat(),
                   "trade_signals": len(signals), "actual_trades": len(trades)})
    rows = sorted(h1_rows + retest_rows, key=lambda row: (row.timestamp, row.stage, row.direction, row.result))
    frame = pd.DataFrame([asdict(row) for row in rows], columns=DIAGNOSTIC_COLUMNS)
    payload = frame.to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S",
                           float_format="%.15g", na_rep="").encode("utf-8")
    digest = sha256(payload).hexdigest()
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "BASELINE_DIAGNOSTICS.csv").write_bytes(payload)
    report = _markdown(counts, rows, digest)
    (output_root / "BASELINE_DIAGNOSTICS.md").write_text(report, encoding="utf-8", newline="\n")
    if any(file_sha256(path) != old for path, old in before.items()):
        raise BaselineError("input data mutated during diagnostics")
    return {"csv_sha256": digest, "report_sha256": sha256(report.encode()).hexdigest(), **counts}
