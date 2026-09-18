"""Deterministic, descriptive diagnostics for completed M5 trades.

This module intentionally has no strategy, market-data, or optimization import.
It reads the already completed development-period trade ledgers only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from ..core.unified_metrics import finite, stats, streaks
from ..multitimeframe.phase73 import hash_tree

VALIDATION = Path("TradingSystemLab/results/timeframe_validation/M5")
OPTIMIZATION = Path("TradingSystemLab/results/timeframe_optimization/M5")
OUTPUT = Path("TradingSystemLab/results/timeframe_diagnostics/M5")
STRATEGIES = ("T2", "T3")
CANDIDATES = {"T2": "T2_M5_candidate_v1", "T3": "T3_M5_candidate_v1"}
SCOPES = ("COMBINED", "USDRUBF", "CNYRUBF")
SESSIONS = ("Session_A", "Session_B", "Session_C")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _csv(path: Path, rows: Any, columns: list[str]) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame = frame.reindex(columns=columns)
    frame.map(finite).to_csv(path, index=False, lineterminator="\n",
                             float_format="%.12g", na_rep="")


def _session(hour: pd.Series) -> pd.Series:
    # Half-open boundaries remove any ambiguity at 10:00 and 17:00.
    return pd.Series("Session_C", index=hour.index).mask(
        (hour >= 10) & (hour < 17), "Session_A").mask(hour >= 17, "Session_B")


def _prepare(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"trade_id", "instrument", "direction", "entry_time", "exit_time", "net_R"}
    if missing := required.difference(frame.columns):
        raise ValueError(f"M5_TRADE_COLUMNS_MISSING:{','.join(sorted(missing))}")
    frame = frame.copy()
    # Preserve each ledger timestamp's written wall clock for attribution, then
    # normalize a separate representation to UTC for ordering and durations.
    entry_local = frame.entry_time.map(pd.Timestamp)
    frame["entry_time"] = pd.to_datetime(frame.entry_time, utc=True)
    frame["exit_time"] = pd.to_datetime(frame.exit_time, utc=True)
    if (frame.entry_time.dt.year >= 2025).any() or (frame.exit_time.dt.year >= 2025).any():
        raise ValueError("TRUE_OOS_TRADE_REJECTED")
    if (~frame.instrument.isin(("USDRUBF", "CNYRUBF"))).any():
        raise ValueError("UNEXPECTED_INSTRUMENT")
    frame["net_R"] = pd.to_numeric(frame.net_R, errors="raise")
    frame["hour"] = entry_local.map(lambda value: value.hour)
    frame["weekday"] = entry_local.map(lambda value: value.day_name())
    frame["entry_date"] = entry_local.map(lambda value: value.date().isoformat())
    frame["session"] = _session(frame.hour)
    frame["holding_minutes"] = (frame.exit_time - frame.entry_time).dt.total_seconds() / 60
    return frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def _scope(frame: pd.DataFrame, scope: str) -> pd.DataFrame:
    return frame if scope == "COMBINED" else frame.loc[frame.instrument.eq(scope)]


def _metrics(frame: pd.DataFrame, holding: bool = False) -> dict[str, Any]:
    metric = stats(frame.net_R)
    result = {"trades": metric["trades"], "win_rate": metric["winrate"],
              "PF": metric["PF_R"], "expectancy_R": metric["expectancy"],
              "net_R": metric["net_R"], "max_drawdown_R": metric["max_DD_R"]}
    if holding:
        result["average_holding_minutes"] = finite(frame.holding_minutes.mean()) if len(frame) else None
    return result


def _group_rows(frame: pd.DataFrame, column: str, values: Any,
                holding: bool = False) -> list[dict[str, Any]]:
    rows = []
    for scope in SCOPES:
        scoped = _scope(frame, scope)
        for value in values:
            rows.append({"scope": scope, column: value,
                         **_metrics(scoped.loc[scoped[column].eq(value)], holding)})
    return rows


def _drawdowns(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Return the five deepest peak-to-recovery (or terminal) episodes."""
    ordered = frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort")
    if ordered.empty:
        return []
    values = ordered.net_R.astype(float).tolist()
    equity = 0.0
    peak = 0.0
    start = 0
    episodes: list[tuple[float, int, int]] = []
    trough = 0.0
    for pos, value in enumerate(values):
        equity += value
        if equity < peak:
            trough = min(trough, equity - peak)
        if equity >= peak:
            if trough < 0:
                episodes.append((trough, start, pos))
            peak, start, trough = equity, pos + 1, 0.0
    if trough < 0:
        episodes.append((trough, start, len(values) - 1))
    rows = []
    for depth, first, last in sorted(episodes, key=lambda x: (x[0], x[1]))[:5]:
        part = ordered.iloc[first:last + 1]
        rows.append({"start_date": part.entry_date.iloc[0],
                     "end_date": part.exit_time.iloc[-1].date().isoformat(),
                     "trades": len(part), "net_R": float(part.net_R.sum()),
                     "max_consecutive_losses": streaks(part.net_R)[1],
                     "max_drawdown_R": depth})
    return rows


def _distribution(frame: pd.DataFrame) -> list[dict[str, Any]]:
    positive = frame.loc[frame.net_R > 0].sort_values(
        ["net_R", "exit_time", "instrument", "trade_id"], ascending=[False, True, True, True], kind="mergesort").head(5)
    negative = frame.loc[frame.net_R < 0].sort_values(
        ["net_R", "exit_time", "instrument", "trade_id"], kind="mergesort").head(5)
    rows = []
    for category, selected in (("TOP_POSITIVE", positive), ("BOTTOM_NEGATIVE", negative)):
        for rank, (_, row) in enumerate(selected.iterrows(), 1):
            rows.append({"category": category, "rank": rank, "trade_id": row.trade_id,
                         "net_R": row.net_R, "instrument": row.instrument,
                         "direction": row.direction, "session": row.session,
                         "weekday": row.weekday, "holding_minutes": row.holding_minutes,
                         "entry_time": row.entry_time.isoformat(), "exit_time": row.exit_time.isoformat()})
    return rows


def _write_strategy(target: Path, strategy: str, frame: pd.DataFrame) -> dict[str, Any]:
    target.mkdir(parents=True)
    hour = _group_rows(frame, "hour", range(24), True)
    _csv(target / "hour_report.csv", hour, ["scope", "hour", "trades", "win_rate", "PF",
         "expectancy_R", "net_R", "max_drawdown_R", "average_holding_minutes"])
    session_rows = []
    for scope in SCOPES:
        scoped = _scope(frame, scope)
        session_rows.append({"scope": scope, "session": "Full_Session", **_metrics(scoped)})
        session_rows.extend({"scope": scope, "session": session,
                             **_metrics(scoped.loc[scoped.session.eq(session)])}
                            for session in SESSIONS)
    _csv(target / "session_report.csv", session_rows,
         ["scope", "session", "trades", "win_rate", "PF", "expectancy_R", "net_R", "max_drawdown_R"])
    _csv(target / "weekday_report.csv", _group_rows(frame, "weekday", WEEKDAYS),
         ["scope", "weekday", "trades", "win_rate", "PF", "expectancy_R", "net_R"])
    _csv(target / "direction_report.csv", _group_rows(frame, "direction", ("LONG", "SHORT")),
         ["scope", "direction", "trades", "PF", "expectancy_R", "net_R", "win_rate"])
    instrument_session = []
    for instrument in ("USDRUBF", "CNYRUBF"):
        for session in SESSIONS:
            part = frame.loc[frame.instrument.eq(instrument) & frame.session.eq(session)]
            instrument_session.append({"instrument": instrument, "session": session, **_metrics(part)})
    _csv(target / "instrument_session_report.csv", instrument_session,
         ["instrument", "session", "trades", "PF", "expectancy_R", "net_R"])
    dd = []
    for scope in SCOPES:
        dd.extend({"scope": scope, **row} for row in _drawdowns(_scope(frame, scope)))
    _csv(target / "drawdown_period_report.csv", dd,
         ["scope", "start_date", "end_date", "trades", "net_R", "max_consecutive_losses", "max_drawdown_R"])
    _csv(target / "trade_distribution_report.csv", _distribution(frame),
         ["category", "rank", "trade_id", "net_R", "instrument", "direction", "session",
          "weekday", "holding_minutes", "entry_time", "exit_time"])
    summary = _metrics(frame, True)
    lines = [f"# {CANDIDATES[strategy]} M5 diagnostic report", "",
             "Descriptive analysis of completed trades only; no rules, parameters, or execution were changed.", "",
             "## Combined portfolio", "",
             f"- Trades: {summary['trades']}", f"- Net R: {summary['net_R']:.6f}",
             f"- Expectancy R: {summary['expectancy_R']:.6f}", "",
             "Reports include combined, USDRUBF, and CNYRUBF scopes. Session boundaries are half-open: "
             "Session A [10:00,17:00), Session B [17:00,24:00), and Session C [00:00,10:00).", "",
             "These outputs are diagnostic and must not be interpreted as session or rule selection."]
    (target / "diagnostic_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def run(validation: Path = VALIDATION, optimization: Path = OPTIMIZATION,
        output: Path = OUTPUT) -> dict[str, Any]:
    """Analyze immutable trade artifacts without loading candles or strategies."""
    validation, optimization, output = Path(validation), Path(optimization), Path(output)
    inputs = {str(validation / key / "trades.csv"): _sha(validation / key / "trades.csv") for key in STRATEGIES}
    inputs.update({str(optimization / key / "candidate_registry.json"):
                   _sha(optimization / key / "candidate_registry.json") for key in STRATEGIES})
    source_before = {str(validation): hash_tree(validation), str(optimization): hash_tree(optimization)}
    frames = {key: _prepare(validation / key / "trades.csv") for key in STRATEGIES}
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = {key: _write_strategy(output / key, key, frames[key]) for key in STRATEGIES}
    comparison = [{"candidate": CANDIDATES[key], **summaries[key]} for key in STRATEGIES]
    _csv(output / "comparison.csv", comparison,
         ["candidate", "trades", "win_rate", "PF", "expectancy_R", "net_R",
          "max_drawdown_R", "average_holding_minutes"])
    manifest = {"phase": "M5_DIAGNOSTIC", "status": "PHASE_M5_DIAGNOSTIC_COMPLETE",
                "source_artifacts_hashes": inputs, "candidates_analyzed": list(CANDIDATES.values()),
                "timeframe": "M5", "optimization_performed": False, "strategy_modified": False,
                "parameters_modified": False, "true_oos_accessed": False, "deterministic": True,
                "analysis_source": "completed development-period trades.csv",
                "session_boundaries": {"Session_A": "[10:00,17:00)",
                                       "Session_B": "[17:00,24:00)", "Session_C": "[00:00,10:00)"}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = ["# M5 diagnostic analysis", "", "Status: `PHASE_M5_DIAGNOSTIC_COMPLETE`", "",
              "This phase analyzes completed trade artifacts only. It performs no optimization, ranking, "
              "filtering, strategy modification, parameter modification, or TRUE OOS access.", "",
              "Both candidate reports cover USDRUBF, CNYRUBF, and their combined portfolio. "
              "All classifications use entry timestamps from the immutable trade ledgers."]
    (output / "m5_diagnostic_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    source_after = {str(validation): hash_tree(validation), str(optimization): hash_tree(optimization)}
    if source_before != source_after:
        raise RuntimeError("SOURCE_ARTIFACTS_MODIFIED")
    return manifest
