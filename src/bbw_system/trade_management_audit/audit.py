"""Forensic, read-only reconstruction of the current BBW Baseline.

This module deliberately does not provide parameters to, or invoke, a trading
runner.  It reconstructs decisions from immutable input frames and contrasts
the observed Baseline mechanics with ``BBW_SPEC_v1.md``.  Timestamps in both
inputs are candle-open labels; a row becomes observable only at its close.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..baseline import BaselineConfig, load_baseline_config
from ..bbw_engine import OUTPUT_NAME, file_sha256


class TradeManagementAuditError(ValueError):
    """Raised when audit inputs violate the causal data contract."""


@dataclass(frozen=True)
class AuditResult:
    ranges: pd.DataFrame
    breakouts: pd.DataFrame
    retests: pd.DataFrame
    entries: pd.DataFrame
    summary: dict[str, Any]


FACT_EXPECTED = (
    ("range", "Wick high/low from H1 bars after first squeeze; 6--30 bars; 1--2 ATR inclusive.",
     "Frozen causal range, with width and horizontality/instrument caps recorded."),
    ("breakout", "H1 close strictly outside the range and matching trend_direction; known at H1 close.",
     "Close-only breakout, causal known-at timestamp, EMA direction confirmation."),
    ("retest", "Native M15 bars 5--30; touch, <=20% range penetration, and same-bar close beyond level.",
     "M15 touch/limited penetration followed by confirmation beyond the frozen level."),
    ("entry", "Confirmation M15 close is stored as entry price at its close timestamp.",
     "Next actually present M15 candle open after confirmation, with adverse slippage."),
    ("stop", "Opposite range boundary +/- fixed price offset; no stop-ratio validation.",
     "Structural boundary stop with configured offset and inclusive ATR/range-ratio validation."),
    ("position_management", "50/30/20 targets at 1R/2R/3R, but the stop never moves.",
     "After +1R move stop to entry; after +2R move it to +1R; final exit at +3R."),
    ("exit", "Independent trades, stop-first OHLC ties, no costs/slippage; residual marked at end of data.",
     "One-position reservation, stop-first unless real lower-TF ordering, explicit costs and slippage."),
)


def _validate(frame: pd.DataFrame, required: set[str], label: str) -> pd.DataFrame:
    missing = required - set(frame.columns)
    if missing:
        raise TradeManagementAuditError(f"{label} missing columns: {sorted(missing)}")
    work = frame.copy(deep=True).reset_index(drop=True)
    work["timestamp"] = pd.to_datetime(work["timestamp"], errors="raise")
    if work.empty or work.timestamp.duplicated().any() or not work.timestamp.is_monotonic_increasing:
        raise TradeManagementAuditError(f"{label} timestamps must be non-empty, unique, and increasing")
    if work.timestamp.dt.year.eq(2025).any():
        raise TradeManagementAuditError("locked TRUE OOS calendar year 2025 is present")
    return work


def reconstruct_trade_management(h1: pd.DataFrame, m15: pd.DataFrame,
                                 config: BaselineConfig | None = None) -> AuditResult:
    """Reconstruct every range, breakout, retest outcome, and effective entry.

    No input is mutated.  Rejections are terminal and deterministic: a close
    back inside the old range and excessive penetration are classified before
    an eligible confirmation, exactly as in the current Baseline.
    """
    config = config or load_baseline_config()
    h = _validate(h1, {"timestamp", "high", "low", "close", "bbw_squeeze", "trend_direction", "atr14"}, "H1")
    m = _validate(m15, {"timestamp", "open", "high", "low", "close"}, "M15")
    squeeze = h.bbw_squeeze
    if not pd.api.types.is_bool_dtype(squeeze):
        squeeze = squeeze.astype(str).str.lower().map({"true": True, "false": False})
        if squeeze.isna().any():
            raise TradeManagementAuditError("bbw_squeeze must contain only TRUE/FALSE")
        h["bbw_squeeze"] = squeeze

    range_rows: list[dict[str, Any]] = []
    breakout_rows: list[dict[str, Any]] = []
    active: int | None = None
    for i, row in h.iterrows():
        if active is None and bool(row.bbw_squeeze):
            active = i
            continue
        if active is None:
            continue
        if row.timestamp.date() != h.at[active, "timestamp"].date() or i - active > config.range_max_bars:
            active = i if bool(row.bbw_squeeze) else None
            continue
        candidate = h.iloc[active:i]
        if not len(candidate):
            continue
        high, low = float(candidate.high.max()), float(candidate.low.min())
        width, atr = high - low, float(row.atr14)
        enough = config.range_min_bars <= len(candidate) <= config.range_max_bars
        width_ok = bool(pd.notna(atr) and atr > 0 and config.range_atr_min * atr <= width <= config.range_atr_max * atr)
        range_rows.append({"decision_bar_open": row.timestamp, "range_start": candidate.timestamp.iloc[0],
                           "range_end_open": candidate.timestamp.iloc[-1], "range_high": high,
                           "range_low": low, "range_width": width, "range_bars": len(candidate),
                           "range_atr": atr, "squeeze_start": h.at[active, "timestamp"],
                           "min_width_applied": True, "max_width_atr_applied": True,
                           "max_width_instrument_pct_applied": False,
                           "range_passed": enough and width_ok})
        if not (enough and width_ok):
            continue
        direction = "LONG" if row.close > high else "SHORT" if row.close < low else None
        if direction is None:
            continue
        trend_passed = row.trend_direction == direction
        breakout_rows.append({"breakout_bar_open": row.timestamp,
                              "breakout_known_at": row.timestamp + pd.Timedelta(hours=1),
                              "direction": direction, "range_high": high, "range_low": low,
                              "range_width": width, "range_bars": len(candidate), "range_atr": atr,
                              "close": float(row.close), "close_only": True,
                              "minimum_price_confirmation": 0.0, "trend_passed": trend_passed,
                              "accepted": trend_passed,
                              "rejection_reason": None if trend_passed else "EMA_DIRECTION_FAIL"})
        if trend_passed:
            active = None

    retest_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    accepted = [row for row in breakout_rows if row["accepted"]]
    occupied: set[pd.Timestamp] = set()
    for number, event in enumerate(accepted, 1):
        eligible = m.loc[m.timestamp.ge(event["breakout_known_at"])].head(config.retest_max_bars)
        outcome, reason = "REJECTED", "RETEST_TIMEOUT"
        for ordinal, (idx, bar) in enumerate(eligible.iterrows(), 1):
            level = event["range_high"] if event["direction"] == "LONG" else event["range_low"]
            penetration = (max(0.0, level - float(bar.low)) if event["direction"] == "LONG"
                           else max(0.0, float(bar.high) - level))
            touched = bool(bar.low <= level) if event["direction"] == "LONG" else bool(bar.high >= level)
            confirms = bool(bar.close > level) if event["direction"] == "LONG" else bool(bar.close < level)
            inside = bool(bar.close < level) if event["direction"] == "LONG" else bool(bar.close > level)
            too_deep = penetration > config.penetration_range_pct * event["range_width"] + 1e-12
            if too_deep or inside:
                reason = "RETEST_TOO_DEEP" if too_deep else "CLOSE_INSIDE_RANGE"
                retest_rows.append({"breakout_id": number, "bar_open": bar.timestamp, "ordinal": ordinal,
                                    "touched": touched, "penetration": penetration, "confirmed": confirms,
                                    "status": "REJECTED", "reason": reason})
                break
            if touched:
                allowed = ordinal >= config.retest_min_bars
                status = "PASSED" if allowed and confirms else "OBSERVED"
                why = None if status == "PASSED" else ("TOO_EARLY" if not allowed else "NO_CONFIRMATION")
                retest_rows.append({"breakout_id": number, "bar_open": bar.timestamp, "ordinal": ordinal,
                                    "touched": True, "penetration": penetration, "confirmed": confirms,
                                    "status": status, "reason": why})
                if status == "PASSED":
                    outcome, reason = "PASSED", None
                    confirmation_known = bar.timestamp + pd.Timedelta(minutes=15)
                    following = m.loc[m.timestamp.gt(bar.timestamp)].head(1)
                    next_open_time = following.timestamp.iloc[0] if not following.empty else pd.NaT
                    next_open = float(following.open.iloc[0]) if not following.empty else None
                    current_entry = float(bar.close)
                    signal_admitted = confirmation_known not in occupied
                    if signal_admitted:
                        occupied.add(confirmation_known)
                    stop = (event["range_low"] - config.stop_offset if event["direction"] == "LONG"
                            else event["range_high"] + config.stop_offset)
                    entry_rows.append({"breakout_id": number, "direction": event["direction"],
                                       "confirmation_bar_open": bar.timestamp,
                                       "confirmation_known_at": confirmation_known,
                                       "current_entry_time": confirmation_known,
                                       "current_entry_price": current_entry,
                                       "expected_entry_time": next_open_time,
                                       "expected_entry_price_before_slippage": next_open,
                                       "entry_matches_core_v1": False,
                                       "structural_stop": stop,
                                       "stop_offset": config.stop_offset,
                                       "signal_admitted": signal_admitted})
                    break
        if not any(r["breakout_id"] == number for r in retest_rows):
            retest_rows.append({"breakout_id": number, "bar_open": pd.NaT, "ordinal": None,
                                "touched": False, "penetration": None, "confirmed": False,
                                "status": outcome, "reason": reason})
        elif outcome != "PASSED" and retest_rows[-1]["status"] == "OBSERVED":
            retest_rows.append({"breakout_id": number, "bar_open": pd.NaT, "ordinal": None,
                                "touched": False, "penetration": None, "confirmed": False,
                                "status": "REJECTED", "reason": "RETEST_TIMEOUT"})

    terminal = [r for r in retest_rows if r["status"] in {"PASSED", "REJECTED"}]
    reasons: dict[str, int] = {}
    for row in terminal:
        if row["status"] == "REJECTED":
            reasons[row["reason"]] = reasons.get(row["reason"], 0) + 1
    summary = {"breakouts_detected": len(breakout_rows), "breakouts_accepted": len(accepted),
               "retests_observed": sum(r["touched"] for r in retest_rows),
               "retests_passed": sum(r["status"] == "PASSED" for r in terminal),
               "retests_rejected": sum(r["status"] == "REJECTED" for r in terminal),
               "rejection_reasons": reasons, "entries": sum(r["signal_admitted"] for r in entry_rows),
               "core_v1_conformant": False,
               "material_gaps": ["ENTRY_USES_CONFIRMATION_CLOSE", "STOP_DOES_NOT_MOVE",
                                 "NO_TRANSACTION_COSTS_OR_SLIPPAGE", "NO_SINGLE_POSITION_RESERVATION"]}
    return AuditResult(pd.DataFrame(range_rows), pd.DataFrame(breakout_rows),
                       pd.DataFrame(retest_rows), pd.DataFrame(entry_rows), summary)


def _report(result: AuditResult, config_hash: str) -> str:
    lines = ["# BBW CORE v1 Trade Management Reconstruction", "",
             "**Verdict: NON-CONFORMANT.** The current Baseline implements the range/breakout/retest skeleton, "
             "but its entry and position management do not match BBW CORE v1.", "",
             "## Scope and safety", "", "Read-only forensic layer; no Baseline, Candidate, Optimization/R2, "
             "Robustness, BBW Engine, configuration, or source market data is changed. Calendar year 2025 is rejected.", "",
             "## Reconstructed counts", ""]
    for key, value in result.summary.items():
        lines.append(f"- `{key}`: `{json.dumps(value, sort_keys=True)}`")
    lines += ["", "## FACT vs EXPECTED", "", "| Stage | FACT (current Baseline) | EXPECTED (BBW CORE v1) |",
              "|---|---|---|"]
    lines += [f"| {stage} | {fact} | {expected} |" for stage, fact, expected in FACT_EXPECTED]
    lines += ["", "## Determinism", "", f"- Baseline config SHA-256: `{config_hash}`",
              "- Stable chronological ordering is used; input frames are deep-copied before analysis.", ""]
    return "\n".join(lines)


def run_trade_management_audit(feature_root: Path, normalized_root: Path, output_root: Path,
                               symbol: str = "CNYRUBF", config_path: Path | None = None) -> dict[str, Any]:
    """Audit verified files and write only new reconstruction artifacts."""
    if symbol != "CNYRUBF":
        raise TradeManagementAuditError("trade-management audit currently permits only CNYRUBF")
    config_path = config_path or Path(__file__).resolve().parents[3] / "config" / "bbw_baseline.json"
    config = load_baseline_config(config_path)
    feature_candidates = (feature_root / OUTPUT_NAME, feature_root / symbol / OUTPUT_NAME)
    m15_candidates = (normalized_root / "M15.csv", normalized_root / symbol / "M15.csv")
    manifest_candidates = (normalized_root / "NORMALIZED_MANIFEST.json",
                           normalized_root / symbol / "NORMALIZED_MANIFEST.json")
    feature = next((p for p in feature_candidates if p.is_file()), None)
    m15 = next((p for p in m15_candidates if p.is_file()), None)
    manifest_path = next((p for p in manifest_candidates if p.is_file()), None)
    if feature is None or m15 is None or manifest_path is None:
        raise TradeManagementAuditError("verified H1 features, M15 input, and normalized manifest are required")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_m15 = manifest.get("timeframes", {}).get("M15", {}).get("sha256")
    if (manifest.get("instrument") != symbol or manifest.get("timestamp_semantics") != "START"
            or not expected_m15 or file_sha256(m15) != expected_m15):
        raise TradeManagementAuditError("normalized M15 input does not match its START-labelled manifest")
    sources = (feature, m15, manifest_path, config_path)
    before = {p: file_sha256(p) for p in sources}
    result = reconstruct_trade_management(pd.read_csv(feature), pd.read_csv(m15), config)
    output_root.mkdir(parents=True, exist_ok=True)
    csv_options = {"index": False, "lineterminator": "\n", "date_format": "%Y-%m-%d %H:%M:%S",
                   "float_format": "%.15g"}
    result.ranges.to_csv(output_root / "RANGES.csv", **csv_options)
    result.breakouts.to_csv(output_root / "BREAKOUTS.csv", **csv_options)
    result.retests.to_csv(output_root / "RETESTS.csv", **csv_options)
    result.entries.to_csv(output_root / "ENTRIES.csv", **csv_options)
    summary_payload = (json.dumps(result.summary, indent=2, sort_keys=True) + "\n")
    (output_root / "SUMMARY.json").write_text(summary_payload, encoding="utf-8")
    (output_root / "REPORT.md").write_text(_report(result, before[config_path]), encoding="utf-8")
    if any(file_sha256(p) != digest for p, digest in before.items()):
        raise TradeManagementAuditError("an audit input was mutated")
    return {**result.summary, "summary_sha256": sha256(summary_payload.encode()).hexdigest()}
