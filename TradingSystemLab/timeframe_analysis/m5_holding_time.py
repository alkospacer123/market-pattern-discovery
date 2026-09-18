"""Causal, read-only holding-time analysis of frozen M5 trade ledgers.

Final MAE/MFE are available, but intratrade paths are not. Time-to-event
outputs therefore report unavailable rather than inventing future information.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Iterable

import pandas as pd

from ..timeframe_diagnostics.m5_full import METRICS, _metrics, _prepare, _write_csv

VALIDATION = Path("TradingSystemLab/results/timeframe_validation/M5")
OPTIMIZATION = Path("TradingSystemLab/results/timeframe_optimization/M5")
DIAGNOSTICS = Path("TradingSystemLab/results/timeframe_diagnostics/M5_FULL")
OUTPUT = Path("TradingSystemLab/results/timeframe_analysis/M5_HOLDING_TIME")
CANDIDATES = {"T2": "T2_M5_candidate_v1", "T3": "T3_M5_candidate_v1"}
DEVELOPMENT = {"start": "2023-01-01", "end": "2024-12-31"}
INSTRUMENTS = ("USDRUBF", "CNYRUBF")
SESSIONS = ("Session_A", "Session_B", "Session_C")
DIRECTIONS = ("LONG", "SHORT")
HOLDING_BUCKETS = (("0-5 min", 0, 5), ("5-15 min", 5, 15),
                   ("15-30 min", 15, 30), ("30-60 min", 30, 60),
                   ("60-120 min", 60, 120), ("120+ min", 120, float("inf")))
EVENT_BUCKETS = ("0-5 min", "5-15 min", "15-30 min", "30-60 min", "60+ min")
DURATION_COLUMNS = ["trades", "average_minutes", "median_minutes", "minimum_minutes",
                    "maximum_minutes", "percentile_25_minutes", "percentile_75_minutes"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_hashes(*roots: Path) -> dict[str, str]:
    return {str(path): _sha(path) for root in roots
            for path in sorted(root.rglob("*"), key=str) if path.is_file()}


def _validate_provenance(diagnostics: Path, validation: Path) -> None:
    manifest = json.loads((diagnostics / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("phase") != "M5_FULL_DIAGNOSTIC":
        raise ValueError("DIAGNOSTIC_PHASE_MISMATCH")
    if manifest.get("candidate_identities") != CANDIDATES:
        raise ValueError("CANDIDATE_IDENTITIES_MISMATCH")
    if manifest.get("development_period") != DEVELOPMENT:
        raise ValueError("DEVELOPMENT_PERIOD_MISMATCH")
    if manifest.get("true_oos_cutoff") != "2025-01-01" or manifest.get("true_oos_access") is not False:
        raise ValueError("TRUE_OOS_CONTRACT_MISMATCH")
    for strategy in CANDIDATES:
        ledger = validation / strategy / "trades.csv"
        if manifest.get("source_artifact_hashes", {}).get(str(ledger)) != _sha(ledger):
            raise ValueError(f"SOURCE_HASH_MISMATCH:{strategy}")


def _bucket_rows(frame: pd.DataFrame, **dimensions: Any) -> list[dict[str, Any]]:
    rows = []
    for label, low, high in HOLDING_BUCKETS:
        part = frame.loc[(frame.holding_minutes >= low) & (frame.holding_minutes < high)]
        mae = pd.to_numeric(part.MAE_R, errors="coerce") if "MAE_R" in part else pd.Series(dtype=float)
        mfe = pd.to_numeric(part.MFE_R, errors="coerce") if "MFE_R" in part else pd.Series(dtype=float)
        rows.append({**dimensions, "holding_bucket": label, **_metrics(part),
                     "average_MAE_R": mae.mean(), "average_MFE_R": mfe.mean(),
                     "average_final_R": part.net_R.mean()})
    return rows


def _duration(frame: pd.DataFrame, outcome: str) -> dict[str, Any]:
    part = frame.loc[frame.net_R > 0] if outcome == "WINNING" else frame.loc[frame.net_R < 0]
    values = part.holding_minutes
    return {"outcome": outcome, "trades": len(part), "average_minutes": values.mean(),
            "median_minutes": values.median(), "minimum_minutes": values.min(),
            "maximum_minutes": values.max(), "percentile_25_minutes": values.quantile(.25),
            "percentile_75_minutes": values.quantile(.75)}


def _duration_rows(frame: pd.DataFrame, **dimensions: Any) -> list[dict[str, Any]]:
    return [{**dimensions, **_duration(frame, outcome)} for outcome in ("WINNING", "LOSING")]


def _event_unavailable(event: str, eligible: int) -> list[dict[str, Any]]:
    reason = "INTRATRADE_PATH_NOT_PRESENT_IN_FROZEN_TRADE_LEDGER"
    return [{"event": event, "time_bucket": bucket, "trades": None, "eligible_trades": eligible,
             "status": "DATA_UNAVAILABLE", "reason": reason} for bucket in EVENT_BUCKETS]


def _write_dimension(path: Path, frame: pd.DataFrame, column: str, values: Iterable[str]) -> None:
    rows = [row for value in values for row in _bucket_rows(frame.loc[frame[column].eq(value)], **{column: value})]
    _write_csv(path, rows, [column, "holding_bucket", *METRICS,
                            "average_MAE_R", "average_MFE_R", "average_final_R"])


def _write_strategy(target: Path, frame: pd.DataFrame) -> None:
    target.mkdir(parents=True)
    buckets = _bucket_rows(frame)
    _write_csv(target / "holding_distribution.csv", buckets, ["holding_bucket", *METRICS])
    _write_csv(target / "winner_loser_duration.csv", _duration_rows(frame), ["outcome", *DURATION_COLUMNS])
    _write_csv(target / "mae_mfe_by_duration.csv", buckets,
               ["holding_bucket", "trades", "average_MAE_R", "average_MFE_R", "average_final_R"])
    event_cols = ["event", "time_bucket", "trades", "eligible_trades", "status", "reason"]
    _write_csv(target / "time_to_profit.csv", _event_unavailable("FIRST_POSITIVE_EXCURSION", int((frame.net_R > 0).sum())), event_cols)
    _write_csv(target / "time_to_mae.csv", _event_unavailable("MAXIMUM_ADVERSE_EXCURSION", int((frame.net_R < 0).sum())), event_cols)
    rows = []
    for value in INSTRUMENTS:
        part = frame.loc[frame.instrument.eq(value)]
        rows += [{"row_type": "HOLDING_BUCKET", **row} for row in _bucket_rows(part, instrument=value)]
        rows += [{"row_type": "DURATION", **row} for row in _duration_rows(part, instrument=value)]
    _write_csv(target / "instrument_report.csv", rows,
               ["row_type", "instrument", "holding_bucket", "outcome", *METRICS,
                *DURATION_COLUMNS[1:], "average_MAE_R", "average_MFE_R", "average_final_R"])
    _write_dimension(target / "session_report.csv", frame, "session", SESSIONS)
    _write_dimension(target / "direction_report.csv", frame, "direction", DIRECTIONS)


def _report(frames: dict[str, pd.DataFrame], portfolio: pd.DataFrame) -> str:
    short = _metrics(portfolio.loc[portfolio.holding_minutes < 60])
    long = _metrics(portfolio.loc[portfolio.holding_minutes >= 60])
    lines = ["# M5 holding-time candidate analysis", "",
             "Status: `PHASE_M5_HOLDING_TIME_ANALYSIS_COMPLETE`", "",
             "This is deterministic, read-only evidence collection over completed 2023–2024 trades. It is not a strategy modification, optimization, candidate selection, parameter search, or new backtest.", "",
             "## Questions and evidence", "",
             "### 1. Are losing trades failing immediately after entry?", "",
             f"- Portfolio trades below 60 minutes: {short['trades']} trades, net_R={short['net_R']:.6g}, PF={short['PF'] if short['PF'] is not None else 'DATA_UNAVAILABLE'}.",
             "- Final outcomes show strong short-duration degradation, but the allowed ledgers cannot establish how soon within each trade the loss developed.", "",
             "### 2. Do profitable trades require time to develop?", "",
             f"- Portfolio trades of 60 minutes or longer: {long['trades']} trades, net_R={long['net_R']:.6g}, PF={long['PF'] if long['PF'] is not None else 'DATA_UNAVAILABLE'}." ]
    for strategy, frame in frames.items():
        durations = {row["outcome"]: row for row in _duration_rows(frame)}
        lines.append(f"- {strategy}: winner median duration={durations['WINNING']['median_minutes']:.6g} minutes; loser median duration={durations['LOSING']['median_minutes']:.6g} minutes.")
    lines += ["", "Winner durations are longer than loser durations in both candidate ledgers. This supports a duration association, while timestamped excursions would be required to prove when profits first developed.", "",
              "### 3–5. Candidate, instrument, and session differences", "",
              "| Scope | <60 min trades | <60 min net_R | 60+ min trades | 60+ min net_R |", "|---|---:|---:|---:|---:|"]
    for label, frame in [*frames.items(), *((value, portfolio.loc[portfolio.instrument.eq(value)]) for value in INSTRUMENTS),
                         *((value, portfolio.loc[portfolio.session.eq(value)]) for value in SESSIONS)]:
        left, right = _metrics(frame.loc[frame.holding_minutes < 60]), _metrics(frame.loc[frame.holding_minutes >= 60])
        lines.append(f"| {label} | {left['trades']} | {left['net_R']:.6g} | {right['trades']} | {right['net_R']:.6g} |")
    lines += ["", "These are descriptive cells, not proposed filters. Full instrument, session, direction, and holding-bucket metrics are preserved in the CSV reports.", "",
              "## Intratrade timing limitation", "",
              "The frozen trade ledgers provide final MAE and MFE values, but not timestamped intratrade excursions. Therefore first-positive-excursion time and time-to-maximum-MAE cannot be calculated causally from the allowed inputs. The corresponding files explicitly report `DATA_UNAVAILABLE`; no candle data was read and no timing was inferred from final outcomes.", "",
              "The evidence distinguishes duration-associated outcomes, but cannot by itself establish whether MFE appeared early, whether losses failed immediately, or whether an exit-management or entry-quality mechanism caused the association.", ""]
    return "\n".join(lines)


def run(diagnostics: Path = DIAGNOSTICS, validation: Path = VALIDATION,
        optimization: Path = OPTIMIZATION, output: Path = OUTPUT) -> dict[str, Any]:
    diagnostics, validation, optimization, output = map(Path, (diagnostics, validation, optimization, output))
    _validate_provenance(diagnostics, validation)
    before = _source_hashes(validation, optimization, diagnostics)
    frames = {strategy: _prepare(validation / strategy / "trades.csv") for strategy in CANDIDATES}
    portfolio = pd.concat([frame.assign(portfolio_strategy=strategy) for strategy, frame in frames.items()], ignore_index=True)
    portfolio = portfolio.sort_values(["exit_time", "portfolio_strategy", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for strategy, frame in frames.items():
        _write_strategy(output / strategy, frame)
    comparison = [dict(scope=strategy, **row) for strategy, frame in frames.items() for row in _bucket_rows(frame)]
    comparison += [dict(scope="portfolio", **row) for row in _bucket_rows(portfolio)]
    _write_csv(output / "comparison.csv", comparison, ["scope", "holding_bucket", *METRICS,
                                                         "average_MAE_R", "average_MFE_R", "average_final_R"])
    manifest = {"phase": "M5_HOLDING_TIME_ANALYSIS", "status": "PHASE_M5_HOLDING_TIME_ANALYSIS_COMPLETE",
                "diagnostic_only": True, "optimization": False, "strategy_changes": False,
                "parameter_changes": False, "candidate_selection": False, "true_oos_access": False,
                "true_oos_blocked": True, "deterministic": True, "candidate_ids": CANDIDATES,
                "development_period": DEVELOPMENT, "true_oos_cutoff": "2025-01-01",
                "source_hashes": before,
                "holding_bucket_definitions": ["[0,5)", "[5,15)", "[15,30)", "[30,60)", "[60,120)", "[120,infinity)"],
                "intratrade_timing_status": "DATA_UNAVAILABLE",
                "intratrade_timing_reason": "INTRATRADE_PATH_NOT_PRESENT_IN_FROZEN_TRADE_LEDGER"}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "holding_time_candidate_report.md").write_text(_report(frames, portfolio), encoding="utf-8")
    if before != _source_hashes(validation, optimization, diagnostics):
        raise RuntimeError("SOURCE_ARTIFACTS_MODIFIED")
    return manifest
