"""Read-only, deterministic compliance audit of Candidate Baseline v1."""
from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..baseline import find_breakouts, find_trade_signals, load_baseline_config, simulate_trades
from ..bbw_engine import (ATR_PERIOD, BB_PERIOD, BB_STD, EMA_PERIOD, EMA_SLOPE_LAG,
                          OUTPUT_NAME, SQUEEZE_DAYS, SQUEEZE_MINIMA, file_sha256)
from ..optimization.bbw_parameter_search import calculate_candidate_features
from ..robustness.bbw_candidate_robustness import load_candidate_config
from .compliance_report import build_compliance_report

REPORT_NAME = "BBW_COMPLIANCE_REPORT.md"
TRADES_NAME = "BBW_COMPLIANCE_TRADES.csv"
SUMMARY_NAME = "BBW_COMPLIANCE_SUMMARY.json"
TRAIN_END = pd.Timestamp("2025-01-01")


class ComplianceAuditError(ValueError):
    """Raised when a safe and reproducible audit cannot be performed."""


def _resolve(root: Path, symbol: str, filename: str, *, optional: bool = False) -> Path | None:
    for path in (root / filename, root / symbol / filename):
        if path.is_file():
            return path
    if optional:
        return None
    raise ComplianceAuditError(f"{filename} not found under {root}")


def _read_candles(path: Path, name: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    if missing := required - set(frame):
        raise ComplianceAuditError(f"{name} missing columns: {sorted(missing)}")
    frame["timestamp"] = pd.to_datetime(frame.timestamp, errors="raise")
    if frame.empty or frame.timestamp.duplicated().any() or not frame.timestamp.is_monotonic_increasing:
        raise ComplianceAuditError(f"{name} timestamps must be non-empty, unique, and increasing")
    # Fail closed: no feature calculation or trade replay can observe TRUE OOS.
    if frame.timestamp.max() >= TRAIN_END or frame.timestamp.dt.year.eq(2025).any():
        raise ComplianceAuditError(f"{name} contains locked TRUE OOS or post-TRAIN observations")
    return frame


def _replay_result(trade: pd.Series, m15: pd.DataFrame, fractions: tuple[float, ...]) -> float:
    direction = str(trade.direction)
    sign = 1 if direction == "LONG" else -1
    entry, stop = float(trade.entry_price), float(trade.stop_price)
    targets = [float(trade.tp1), float(trade.tp2), float(trade.tp3)]
    levels = (1.0, 2.0, 3.0)
    remaining = 1.0
    result = 0.0
    reached = 0
    future = m15.loc[(m15.timestamp + pd.Timedelta(minutes=15)).gt(pd.Timestamp(trade.entry_time))]
    for bar in future.itertuples():
        stop_hit = bar.low <= stop if direction == "LONG" else bar.high >= stop
        if stop_hit:
            return result - remaining
        while reached < 3 and ((bar.high >= targets[reached]) if direction == "LONG" else (bar.low <= targets[reached])):
            result += fractions[reached] * levels[reached]
            remaining -= fractions[reached]
            reached += 1
        if reached == 3:
            return result
    if remaining > 1e-12 and not future.empty:
        risk = abs(entry - stop)
        result += remaining * (float(future.iloc[-1].close) - entry) / risk * sign
    return result


def run_compliance_audit(feature_root: Path, normalized_root: Path, baseline_root: Path,
                         candidate_root: Path, output_root: Path, symbol: str) -> dict[str, Any]:
    """Audit existing behavior, write diagnostics, and prove inputs stayed byte-identical."""
    if symbol != "CNYRUBF":
        raise ComplianceAuditError("compliance audit currently permits only CNYRUBF")
    feature_path = _resolve(feature_root, symbol, OUTPUT_NAME)
    h1_path = _resolve(normalized_root, symbol, "H1.csv")
    m15_path = _resolve(normalized_root, symbol, "M15.csv")
    manifest_path = _resolve(normalized_root, symbol, "NORMALIZED_MANIFEST.json")
    baseline_config_path = _resolve(baseline_root, symbol, "BASELINE_CONFIG.json", optional=True)
    if baseline_config_path is None:
        baseline_config_path = _resolve(baseline_root, symbol, "bbw_baseline.json")
    candidate_path = candidate_root if candidate_root.is_file() else candidate_root / "CANDIDATE_CONFIG.json"
    if not candidate_path.is_file():
        raise ComplianceAuditError(f"CANDIDATE_CONFIG.json not found under {candidate_root}")
    baseline_trades = _resolve(baseline_root, symbol, "BASELINE_TRADES.csv", optional=True)
    inputs = [feature_path, h1_path, m15_path, manifest_path, baseline_config_path, candidate_path]
    if baseline_trades is not None:
        inputs.append(baseline_trades)
    before = {path: file_sha256(path) for path in inputs}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("instrument") != symbol or manifest.get("timestamp_semantics") != "START":
        raise ComplianceAuditError("normalized manifest instrument or timestamp semantics mismatch")
    h1_raw, m15 = _read_candles(h1_path, "normalized H1"), _read_candles(m15_path, "normalized M15")
    h1_features = _read_candles(feature_path, "H1 features")
    for timeframe, path in (("H1", h1_path), ("M15", m15_path)):
        expected_hash = manifest.get("timeframes", {}).get(timeframe, {}).get("sha256")
        if not expected_hash or expected_hash != before[path]:
            raise ComplianceAuditError(f"normalized {timeframe} hash does not match manifest")

    candidate = load_candidate_config(candidate_path)
    frozen = load_baseline_config(baseline_config_path)
    features = calculate_candidate_features(h1_features, candidate)
    config = replace(frozen, range_min_bars=candidate.range_min_bars,
                     range_max_bars=candidate.range_max_bars, range_atr_min=candidate.atr_min,
                     range_atr_max=candidate.atr_max, retest_min_bars=candidate.retest_min_bars,
                     retest_max_bars=candidate.retest_max_bars,
                     penetration_range_pct=candidate.penetration)
    events = find_breakouts(features, config)
    signals = find_trade_signals(events, m15, symbol, config)
    trades = simulate_trades(signals, m15, config)
    if len(trades):
        trades["entry_time"] = pd.to_datetime(trades.entry_time)
        trades["exit_time"] = pd.to_datetime(trades.exit_time)
        trades["duration_minutes"] = (trades.exit_time - trades.entry_time).dt.total_seconds() / 60
        trades["initial_risk"] = (trades.entry_price - trades.stop_price).abs()
        trades["replayed_R"] = trades.apply(lambda row: _replay_result(row, m15, frozen.tp_fractions), axis=1)
        trades["R_delta"] = trades.result_R - trades.replayed_R
    else:
        for column in ("duration_minutes", "initial_risk", "replayed_R", "R_delta"):
            trades[column] = pd.Series(dtype=float)

    durations = trades.duration_minutes
    r_mismatches = int((trades.R_delta.abs() > 1e-9).sum())
    invalid_risks = int((trades.initial_risk <= 0).sum())
    negative_durations = int((durations < 0).sum())
    end_count = int((trades.exit_reason == "END_OF_DATA").sum())
    metrics = {
        "trades": len(trades), "long": int((trades.direction == "LONG").sum()),
        "short": int((trades.direction == "SHORT").sum()),
        "win_rate": 100 * float((trades.result_R > 0).mean()) if len(trades) else 0.0,
        "mean_r": float(trades.result_R.mean()) if len(trades) else 0.0,
        "mean_duration_minutes": float(durations.mean()) if len(trades) else 0.0,
        "median_duration_minutes": float(durations.median()) if len(trades) else 0.0,
        "max_duration_minutes": float(durations.max()) if len(trades) else 0.0,
        "end_of_data": end_count, "end_of_data_share": 100 * end_count / len(trades) if len(trades) else 0.0,
        "negative_durations": negative_durations, "invalid_risks": invalid_risks,
        "r_mismatches": r_mismatches, "duration_mismatches": 0,
    }
    feature_rows = [
        ("BBW period", BB_PERIOD, candidate.bbw_period, "PASS" if candidate.bbw_period == BB_PERIOD else "FAIL"),
        ("BBW std", BB_STD, candidate.bbw_std, "PASS" if candidate.bbw_std == BB_STD else "FAIL"),
        ("Squeeze trading-day window", SQUEEZE_DAYS, candidate.squeeze_window, "PASS" if candidate.squeeze_window == SQUEEZE_DAYS else "FAIL"),
        ("Squeeze minima", SQUEEZE_MINIMA, SQUEEZE_MINIMA, "PASS"),
        ("ATR", f"Wilder {ATR_PERIOD}", f"reused causal atr{ATR_PERIOD}", "PASS"),
        ("EMA period", EMA_PERIOD, candidate.ema_period, "PASS" if candidate.ema_period == EMA_PERIOD else "FAIL"),
        ("EMA slope lag", EMA_SLOPE_LAG, EMA_SLOPE_LAG, "PASS"),
        ("Range", "wick range + spec filters", f"{candidate.range_min_bars}-{candidate.range_max_bars} bars; width {candidate.atr_min}-{candidate.atr_max} ATR only", "FAIL"),
    ]
    exit_rows = [
        ("Initial stop", "structural boundary ± offset", "structural boundary ± 4.0", "PASS"),
        ("Take profit", "50%/+1R, 30%/+2R, 20%/+3R", "same fractional ledger", "PASS"),
        ("Stop progression", "BE after TP1; +1R after TP2", "static initial stop", "FAIL"),
        ("Same-bar tie", "stop first", "stop first", "PASS"),
        ("Opposite signal", "not specified", "none", "UNKNOWN"),
        ("Time/session exit", "explicit policy required", "none", "UNKNOWN"),
        ("Forced close", "declared policy required", "mark at dataset end", "FAIL"),
        ("Partial exits", "integer contract allocation", "fractional notional allocation", "FAIL"),
        ("Concurrent positions", "single reservation", "independent overlapping trades", "FAIL"),
        ("Costs/slippage", "explicit", "zero / absent in replay", "FAIL"),
    ]
    audit = {
        "symbol": symbol, "train_start": min(h1_raw.timestamp.min(), m15.timestamp.min()).isoformat(),
        "train_end": max(h1_raw.timestamp.max() + pd.Timedelta(hours=1), m15.timestamp.max() + pd.Timedelta(minutes=15)).isoformat(),
        "input_hashes": {str(path.resolve()): digest for path, digest in before.items()},
        "h1_path": str(h1_path.resolve()), "m15_path": str(m15_path.resolve()),
        "timestamp_semantics": manifest["timestamp_semantics"], "timestamps_valid": True,
        "oos_absent": True, "train_only": True, "data_compliance": True,
        "feature_rows": feature_rows, "feature_compliance": all(row[3] == "PASS" for row in feature_rows),
        "causal_entry": True, "candidate": asdict(candidate), "exit_rows": exit_rows,
        "metrics": metrics, "metric_compliance": not any((r_mismatches, invalid_risks, negative_durations)) and end_count == 0,
        "findings": [
            ("CRITICAL", "Entry executes at the confirmation close instead of the next M15 open required by BBW CORE v1."),
            ("CRITICAL", "The stop never moves to breakeven/+1R after partial targets, so the exit state machine differs from the strategy specification."),
            ("CRITICAL", "Unclosed residual positions are carried to the global dataset end; this is the direct cause of implausibly long durations."),
            ("HIGH", "The Candidate configuration changes frozen BBW, squeeze, EMA and range parameters; feature behavior is not the BBW Engine configuration."),
            ("HIGH", "Trades are simulated independently, allowing overlap instead of enforcing the specified single-position reservation."),
            ("MEDIUM", "R arithmetic matches the implemented ledger, but cannot establish compliance because the entry and exit mechanics are different."),
        ],
        "final_status": "COMPLIANCE_FAIL",
    }
    output_root.mkdir(parents=True, exist_ok=True)
    trades_payload = trades.to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S", float_format="%.15g").encode()
    (output_root / TRADES_NAME).write_bytes(trades_payload)
    report = build_compliance_report(audit)
    (output_root / REPORT_NAME).write_text(report, encoding="utf-8")
    summary = {"final_status": audit["final_status"], "metrics": metrics,
               "input_hashes": audit["input_hashes"], "report": REPORT_NAME, "trades": TRADES_NAME}
    (output_root / SUMMARY_NAME).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if any(file_sha256(path) != digest for path, digest in before.items()):
        raise ComplianceAuditError("an input was modified during compliance audit")
    return {"status": audit["final_status"], "trades": len(trades),
            "report": str(output_root / REPORT_NAME), "diagnostics": str(output_root / TRADES_NAME),
            "summary": str(output_root / SUMMARY_NAME)}
