"""Deterministic, read-only hypothesis analysis of completed M5 trades.

This module deliberately operates on ledgers, not candles or strategy code.  Its
subsets are counterfactual summaries of already-closed trades, not backtests.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from ..timeframe_diagnostics.m5_full import METRICS, _metrics, _prepare, _write_csv

DIAGNOSTICS = Path("TradingSystemLab/results/timeframe_diagnostics/M5_FULL")
VALIDATION = Path("TradingSystemLab/results/timeframe_validation/M5")
OUTPUT = Path("TradingSystemLab/results/timeframe_analysis/M5_CANDIDATES")
CANDIDATES = {"T2": "T2_M5_candidate_v1", "T3": "T3_M5_candidate_v1"}
DEVELOPMENT = {"start": "2023-01-01", "end": "2024-12-31"}
SESSIONS = ("Session_A", "Session_B", "Session_C")
INSTRUMENTS = ("USDRUBF", "CNYRUBF")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sources(diagnostics: Path, validation: Path) -> dict[str, str]:
    paths = [p for p in diagnostics.rglob("*") if p.is_file()]
    paths += [validation / strategy / "trades.csv" for strategy in CANDIDATES]
    return {str(path): _sha(path) for path in sorted(paths, key=str)}


def _validate_provenance(diagnostics: Path, validation: Path) -> dict[str, Any]:
    manifest = json.loads((diagnostics / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("phase") != "M5_FULL_DIAGNOSTIC":
        raise ValueError("DIAGNOSTIC_PHASE_MISMATCH")
    if manifest.get("candidate_identities") != CANDIDATES:
        raise ValueError("CANDIDATE_IDENTITIES_MISMATCH")
    if manifest.get("development_period") != DEVELOPMENT:
        raise ValueError("DEVELOPMENT_PERIOD_MISMATCH")
    if manifest.get("true_oos_cutoff") != "2025-01-01" or manifest.get("true_oos_access") is not False:
        raise ValueError("TRUE_OOS_CONTRACT_MISMATCH")
    recorded = manifest.get("source_artifact_hashes", {})
    for strategy in CANDIDATES:
        ledger = validation / strategy / "trades.csv"
        expected = recorded.get(str(ledger))
        if expected is None or expected != _sha(ledger):
            raise ValueError(f"SOURCE_HASH_MISMATCH:{strategy}")
    return manifest


def _row(analysis: str, hypothesis_id: str, scope: str, label: str,
         frame: pd.DataFrame) -> dict[str, Any]:
    return {"analysis": analysis, "hypothesis_id": hypothesis_id, "scope": scope,
            "label": label, **_metrics(frame)}


def _session_rows(frame: pd.DataFrame, scope: str) -> list[dict[str, Any]]:
    definitions = (
        ("M5_SESSION_KEEP_B", "Keep only Session_B", ("Session_B",)),
        ("M5_SESSION_REMOVE_C", "Remove Session_C", ("Session_A", "Session_B")),
        ("M5_SESSION_KEEP_B_A", "Keep Session_B + Session_A", ("Session_B", "Session_A")),
    )
    return [_row("session_filter", identity, scope, label,
                 frame.loc[frame.session.isin(sessions)])
            for identity, label, sessions in definitions]


def _holding_rows(frame: pd.DataFrame, scope: str) -> list[dict[str, Any]]:
    buckets = (("M5_HOLD_000_015", "0-15 min", 0, 15),
               ("M5_HOLD_015_030", "15-30 min", 15, 30),
               ("M5_HOLD_030_060", "30-60 min", 30, 60),
               ("M5_HOLD_060_120", "60-120 min", 60, 120),
               ("M5_HOLD_120_PLUS", "120+ min", 120, float("inf")))
    return [_row("holding_time", identity, scope, label,
                 frame.loc[(frame.holding_minutes >= low) & (frame.holding_minutes < high)])
            for identity, label, low, high in buckets]


def _instrument_session_rows(frame: pd.DataFrame, scope: str) -> list[dict[str, Any]]:
    return [{"analysis": "instrument_session", "hypothesis_id": f"M5_{instrument}_{session}",
             "scope": scope, "label": f"{instrument} / {session}", "instrument": instrument,
             "session": session, **_metrics(frame.loc[frame.instrument.eq(instrument) &
                                                       frame.session.eq(session)])}
            for instrument in INSTRUMENTS for session in SESSIONS]


def _time_rows(frame: pd.DataFrame, scope: str) -> list[dict[str, Any]]:
    dimensions: tuple[tuple[str, list[Any]], ...] = (
        ("hour", list(range(24))),
        ("weekday", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
        ("month", [f"{n:02d}-{pd.Timestamp(2000, n, 1).month_name()}" for n in range(1, 13)]),
        ("quarter", [f"{year}-Q{quarter}" for year in (2023, 2024) for quarter in range(1, 5)]),
    )
    rows = []
    for dimension, values in dimensions:
        for value in values:
            part = frame.loc[frame[dimension].eq(value)]
            rows.append({"analysis": "time_slice", "hypothesis_id": f"M5_TIME_{dimension.upper()}_{value}",
                         "scope": scope, "label": str(value), "time_dimension": dimension,
                         "time_value": value, "descriptive_class":
                         ("positive" if part.net_R.sum() > 0 else "negative" if part.net_R.sum() < 0 else "flat"),
                         **_metrics(part)})
    # These two pre-declared hour hypotheses expose the requested evidence but
    # are not recommendations. Their membership is recorded for auditability.
    hour_net = frame.groupby("hour", sort=True).net_R.sum()
    negative = tuple(int(x) for x in hour_net[hour_net < 0].index)
    positive = tuple(int(x) for x in hour_net[hour_net > 0].index)
    nonnegative = tuple(int(x) for x in hour_net[hour_net >= 0].index)
    for identity, label, hours in (
            ("M5_TIME_REMOVE_OBSERVED_NEGATIVE_HOURS", "Remove observed negative hours", nonnegative),
            ("M5_TIME_KEEP_OBSERVED_PROFITABLE_HOURS", "Keep observed profitable hour set", positive)):
        rows.append({"analysis": "time_hypothesis", "hypothesis_id": identity, "scope": scope,
                     "label": label, "time_dimension": "hour_set", "time_value": ";".join(map(str, hours)),
                     "descriptive_class": "hypothetical_in_sample_subset",
                     "excluded_values": ";".join(map(str, negative)),
                     **_metrics(frame.loc[frame.hour.isin(hours)])})
    return rows


def _write_rows(path: Path, rows: list[dict[str, Any]], extras: list[str] | None = None) -> None:
    columns = ["analysis", "hypothesis_id", "scope", "label", *(extras or []), *METRICS]
    _write_csv(path, rows, columns)


def _fmt(value: Any) -> str:
    return "DATA_UNAVAILABLE" if value is None else f"{value:.6g}" if isinstance(value, float) else str(value)


def _report(frames: dict[str, pd.DataFrame], portfolio: pd.DataFrame) -> str:
    sessions = {r["hypothesis_id"]: r for r in _session_rows(portfolio, "portfolio")}
    holds = {r["label"]: r for r in _holding_rows(portfolio, "portfolio")}
    inst = {(r["instrument"], r["session"]): r for r in _instrument_session_rows(portfolio, "portfolio")}
    total = _metrics(portfolio)
    b, no_c = sessions["M5_SESSION_KEEP_B"], sessions["M5_SESSION_REMOVE_C"]
    session_c = _metrics(portfolio.loc[portfolio.session.eq("Session_C")])
    short = _metrics(portfolio.loc[portfolio.holding_minutes < 60])
    long = _metrics(portfolio.loc[portfolio.holding_minutes >= 60])
    cny_c, usd_c = inst[("CNYRUBF", "Session_C")], inst[("USDRUBF", "Session_C")]
    return "\n".join([
        "# M5 candidate hypothesis analysis", "",
        "Status: `PHASE_M5_CANDIDATE_ANALYSIS_COMPLETE`", "",
        "This is deterministic, read-only descriptive analysis of already-completed development trades. "
        "It is not a backtest, optimization, ranking, candidate selection, or strategy change. Hour subsets are "
        "in-sample descriptions and require independent future development before any promotion decision.", "",
        "## Questions", "",
        "### 1. Is Session_B the main source of profitability?", "",
        f"Portfolio Session_B has net_R {_fmt(b['net_R'])}, PF {_fmt(b['PF'])}, and {b['trades']} trades, "
        f"versus total net_R {_fmt(total['net_R'])}. This is the largest positive session contribution "
        "when compared with the complete session rows; it is evidence of concentration, not a filter decision.", "",
        "### 2. How much performance comes from Session_C losses?", "",
        f"Session_C contributes net_R {_fmt(session_c['net_R'])} across {session_c['trades']} trades. "
        f"The hypothetical portfolio without Session_C has net_R {_fmt(no_c['net_R'])}; the arithmetic net_R "
        f"difference is {_fmt(no_c['net_R'] - total['net_R'])} R.", "",
        "### 3. Are short-duration trades the main degradation source?", "",
        f"Trades below 60 minutes contribute net_R {_fmt(short['net_R'])} across {short['trades']} trades "
        f"(PF {_fmt(short['PF'])}); 60+ minute trades contribute net_R {_fmt(long['net_R'])} across "
        f"{long['trades']} trades (PF {_fmt(long['PF'])}). Bucket-level results are retained in comparison.csv.", "",
        "### 4. Is the effect different between USDRUBF and CNYRUBF?", "",
        f"In Session_C, USDRUBF net_R is {_fmt(usd_c['net_R'])} ({usd_c['trades']} trades) and CNYRUBF "
        f"net_R is {_fmt(cny_c['net_R'])} ({cny_c['trades']} trades). The six instrument/session cells "
        "show whether the session effect is shared or instrument-specific.", "",
        "### 5. Which hypotheses deserve promotion to future candidates?", "",
        "No candidate is promoted or selected in this phase. The session, duration, instrument/session, and "
        "time-window hypotheses are documented as evidence-bearing hypotheses for a separately governed future "
        "development phase. Session concentration and sub-60-minute degradation merit prospective validation; "
        "instrument/session interactions merit validation as a possible moderator. Data-derived profitable-hour "
        "sets are explicitly exploratory and carry the highest in-sample overfitting risk.", "",
        "## Holding bucket reference", "",
        *[f"- {label}: trades={row['trades']}, net_R={_fmt(row['net_R'])}, PF={_fmt(row['PF'])}"
          for label, row in holds.items()], "",
        "No strategy rules, entries, exits, stops, trailing logic, parameters, or research frameworks were modified.",
    ]) + "\n"


def run(diagnostics: Path = DIAGNOSTICS, validation: Path = VALIDATION,
        output: Path = OUTPUT) -> dict[str, Any]:
    diagnostics, validation, output = map(Path, (diagnostics, validation, output))
    _validate_provenance(diagnostics, validation)
    before = _sources(diagnostics, validation)
    frames = {strategy: _prepare(validation / strategy / "trades.csv") for strategy in CANDIDATES}
    portfolio = pd.concat([frames[s].assign(portfolio_strategy=s) for s in CANDIDATES], ignore_index=True)
    portfolio = portfolio.sort_values(["exit_time", "portfolio_strategy", "instrument", "trade_id"],
                                      kind="mergesort").reset_index(drop=True)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    all_rows: list[dict[str, Any]] = []
    for strategy, frame in frames.items():
        target = output / strategy
        target.mkdir()
        session_rows = _session_rows(frame, strategy)
        holding_rows = _holding_rows(frame, strategy)
        interaction_rows = _instrument_session_rows(frame, strategy)
        time_rows = _time_rows(frame, strategy)
        _write_rows(target / "session_filter_analysis.csv", session_rows)
        _write_rows(target / "holding_time_analysis.csv", holding_rows)
        _write_rows(target / "instrument_session_analysis.csv", interaction_rows, ["instrument", "session"])
        _write_rows(target / "time_analysis.csv", time_rows,
                    ["time_dimension", "time_value", "descriptive_class", "excluded_values"])
        all_rows.extend(session_rows + holding_rows + interaction_rows + time_rows)
    all_rows.extend(_session_rows(portfolio, "portfolio") + _holding_rows(portfolio, "portfolio") +
                    _instrument_session_rows(portfolio, "portfolio") + _time_rows(portfolio, "portfolio"))
    _write_rows(output / "comparison.csv", all_rows,
                ["instrument", "session", "time_dimension", "time_value", "descriptive_class", "excluded_values"])
    unavailable = sorted(set().union(*(set(("hour", "weekday", "month", "quarter", "holding_minutes",
                                             "session", "instrument")) - set(frame.columns)
                                         for frame in frames.values())))
    manifest = {
        "phase": "M5_CANDIDATE_ANALYSIS", "status": "PHASE_M5_CANDIDATE_ANALYSIS_COMPLETE",
        "diagnostic_only": True, "optimization": False, "strategy_changes": False,
        "parameter_changes": False, "true_oos_blocked": True, "deterministic": True,
        "candidate_selection": False, "ranking": False, "backtest_execution": False,
        "candidate_ids": CANDIDATES, "development_period": DEVELOPMENT,
        "true_oos_cutoff": "2025-01-01", "source_artifact_hashes": before,
        "unavailable_fields": unavailable,
        "bucket_definitions": {"holding_minutes": ["[0,15)", "[15,30)", "[30,60)", "[60,120)", "[120,infinity)"],
                               "sessions": {"Session_A": "[00:00,10:00)", "Session_B": "[10:00,17:00)",
                                            "Session_C": "[17:00,24:00)"}},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "candidate_analysis_report.md").write_text(_report(frames, portfolio), encoding="utf-8")
    if before != _sources(diagnostics, validation):
        raise RuntimeError("SOURCE_ARTIFACTS_MODIFIED")
    return manifest
