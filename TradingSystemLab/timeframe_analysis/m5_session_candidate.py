"""Evaluate the single, pre-declared M5 main-session candidate hypothesis.

The completed candidate trade ledgers are immutable inputs.  The hypothetical
candidate differs only by rejecting entries outside weekdays [10:00, 17:00) in
the timestamp's existing trading offset; exits and trade outcomes are retained.
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
OUTPUT = Path("TradingSystemLab/results/timeframe_analysis/M5_SESSION_CANDIDATE")
BASELINES = {"T2": "T2_M5_candidate_v1", "T3": "T3_M5_candidate_v1"}
CANDIDATES = {"T2": "T2_M5_session_candidate_v1", "T3": "T3_M5_session_candidate_v1"}
INSTRUMENTS = ("USDRUBF", "CNYRUBF")
DIRECTIONS = ("LONG", "SHORT")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
SESSIONS = ("Session_A", "Session_B", "Session_C")
DEVELOPMENT = {"start": "2023-01-01", "end": "2024-12-31"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sources(validation: Path, optimization: Path) -> dict[str, str]:
    paths = [validation / key / "trades.csv" for key in BASELINES]
    paths += [optimization / key / "candidate_registry.json" for key in BASELINES]
    return {str(path): _sha(path) for path in sorted(paths, key=str)}


def _validate_inputs(validation: Path, optimization: Path) -> None:
    for key, identity in BASELINES.items():
        registry = json.loads((optimization / key / "candidate_registry.json").read_text(encoding="utf-8"))
        if registry.get("candidate_id") != identity:
            raise ValueError(f"CANDIDATE_IDENTITY_MISMATCH:{key}")


def _candidate(frame: pd.DataFrame) -> pd.DataFrame:
    # _prepare derives hour and weekday from the written timestamp offset, i.e.
    # the existing project trading timezone, rather than introducing a timezone.
    return frame.loc[frame.weekday.isin(WEEKDAYS) & frame.hour.ge(10) & frame.hour.lt(17)].copy()


def _variant_rows(scope: str, baseline: pd.DataFrame, candidate: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {"scope": scope, "variant": "BASELINE", "candidate_id": BASELINES.get(scope, "COMBINED_M5_BASELINE"),
         **_metrics(baseline)},
        {"scope": scope, "variant": "SESSION_FILTER", "candidate_id": CANDIDATES.get(scope, "COMBINED_M5_SESSION_CANDIDATE"),
         **_metrics(candidate)},
    ]


def _breakdown(baseline: pd.DataFrame, candidate: pd.DataFrame, column: str,
               values: Iterable[str]) -> list[dict[str, Any]]:
    rows = []
    for variant, frame in (("BASELINE", baseline), ("SESSION_FILTER", candidate)):
        for value in values:
            rows.append({"variant": variant, column: value, **_metrics(frame.loc[frame[column].eq(value)])})
    return rows


def _session_rows(baseline: pd.DataFrame, candidate: pd.DataFrame) -> list[dict[str, Any]]:
    rows = [{"variant": "BASELINE", "session": value,
             **_metrics(baseline.loc[baseline.session.eq(value)])} for value in SESSIONS]
    rows.append({"variant": "SESSION_FILTER", "session": "10:00-17:00", **_metrics(candidate)})
    return rows


def _holding_rows(baseline: pd.DataFrame, candidate: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for variant, frame in (("BASELINE", baseline), ("SESSION_FILTER", candidate)):
        for outcome, part in (("ALL", frame), ("WINNER", frame.loc[frame.net_R > 0]),
                              ("LOSER", frame.loc[frame.net_R < 0])):
            rows.append({"variant": variant, "outcome": outcome, "trades": len(part),
                         "average_holding_minutes": (float(part.holding_minutes.mean()) if len(part) else None),
                         "median_holding_minutes": (float(part.holding_minutes.median()) if len(part) else None)})
    return rows


def _comparison_rows(scope: str, baseline: pd.DataFrame,
                     candidate: pd.DataFrame) -> list[dict[str, Any]]:
    rows = [{**row, "analysis": "performance", "group": "ALL"}
            for row in _variant_rows(scope, baseline, candidate)]
    for analysis, column, values in (("instrument", "instrument", INSTRUMENTS),
                                     ("direction", "direction", DIRECTIONS),
                                     ("weekday", "weekday", WEEKDAYS)):
        for row in _breakdown(baseline, candidate, column, values):
            rows.append({"scope": scope, "analysis": analysis, "group": row[column], **row})
    for row in _session_rows(baseline, candidate):
        rows.append({"scope": scope, "analysis": "session", "group": row["session"], **row})
    for row in _holding_rows(baseline, candidate):
        rows.append({"scope": scope, "analysis": "holding_time", "group": row["outcome"], **row})
    return rows


def _write_strategy(target: Path, baseline: pd.DataFrame, candidate: pd.DataFrame,
                    key: str) -> list[dict[str, Any]]:
    target.mkdir(parents=True)
    summary = _variant_rows(key, baseline, candidate)
    _write_csv(target / "baseline_vs_candidate.csv", summary,
               ["scope", "variant", "candidate_id", *METRICS])
    (target / "metrics.json").write_text(json.dumps({
        "baseline_candidate_id": BASELINES[key], "session_candidate_id": CANDIDATES[key],
        "baseline": _metrics(baseline), "session_filter_candidate": _metrics(candidate),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for filename, column, values in (
        ("instrument_report.csv", "instrument", INSTRUMENTS),
        ("direction_report.csv", "direction", DIRECTIONS),
        ("weekday_report.csv", "weekday", WEEKDAYS),
    ):
        _write_csv(target / filename, _breakdown(baseline, candidate, column, values),
                   ["variant", column, *METRICS])
    _write_csv(target / "session_report.csv", _session_rows(baseline, candidate),
               ["variant", "session", *METRICS])
    _write_csv(target / "holding_time_report.csv", _holding_rows(baseline, candidate),
               ["variant", "outcome", "trades", "average_holding_minutes", "median_holding_minutes"])
    return summary


def _report(all_rows: list[dict[str, Any]]) -> str:
    lines = ["# M5 session filter candidate research", "",
             "Status: `PHASE_M5_SESSION_CANDIDATE_COMPLETE`", "",
             "## Hypothesis", "",
             "Entries are restricted to Monday–Friday, 10:00 inclusive to 17:00 exclusive, using the existing trading timezone.", "",
             "This report evaluates evidence only. It does not claim improvement, select a winner, or optimize a window.", "",
             "## Overall comparison", ""]
    for row in all_rows:
        lines.append(f"- {row['scope']} {row['variant']}: trades={row['trades']}, PF={row['PF']}, "
                     f"expectancy_R={row['expectancy_R']}, net_R={row['net_R']}, "
                     f"max_drawdown_R={row['max_drawdown_R']}, recovery_factor={row['recovery_factor']}, "
                     f"win_rate={row['win_rate']}.")
    lines += ["", "Instrument, direction, weekday, session, and holding-duration evidence is retained in the CSV artifacts.",
              "Only entry eligibility changed; strategy logic, parameters, exits, risk, stops, and trailing logic are unchanged.",
              "TRUE OOS was blocked and no winner was selected."]
    return "\n".join(lines) + "\n"


def run(validation: Path = VALIDATION, optimization: Path = OPTIMIZATION,
        output: Path = OUTPUT) -> dict[str, Any]:
    validation, optimization, output = map(Path, (validation, optimization, output))
    _validate_inputs(validation, optimization)
    before = _sources(validation, optimization)
    baselines = {key: _prepare(validation / key / "trades.csv") for key in BASELINES}
    candidates = {key: _candidate(frame) for key, frame in baselines.items()}
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    summary_rows = []
    comparison_rows = []
    for key in BASELINES:
        summary_rows += _write_strategy(output / key, baselines[key], candidates[key], key)
        comparison_rows += _comparison_rows(key, baselines[key], candidates[key])
    combined_base = pd.concat([baselines[key].assign(portfolio_strategy=key) for key in BASELINES])
    combined_candidate = pd.concat([candidates[key].assign(portfolio_strategy=key) for key in BASELINES])
    combined_base = combined_base.sort_values(["exit_time", "portfolio_strategy", "instrument", "trade_id"], kind="mergesort")
    combined_candidate = combined_candidate.sort_values(["exit_time", "portfolio_strategy", "instrument", "trade_id"], kind="mergesort")
    combined_summary = _variant_rows("COMBINED", combined_base, combined_candidate)
    summary_rows += combined_summary
    comparison_rows += _comparison_rows("COMBINED", combined_base, combined_candidate)
    _write_csv(output / "comparison.csv", comparison_rows,
               ["scope", "analysis", "group", "variant", "candidate_id", *METRICS,
                "average_holding_minutes", "median_holding_minutes"])
    manifest = {
        "phase": "M5_SESSION_CANDIDATE", "status": "PHASE_M5_SESSION_CANDIDATE_COMPLETE",
        "diagnostic_only": False, "candidate_research": True, "optimization": False,
        "parameter_changes": False, "strategy_changes": False, "winner_selection": False,
        "true_oos_access": False, "deterministic": True,
        "source_hashes": before, "baseline_candidate_ids": BASELINES,
        "session_candidate_ids": CANDIDATES, "development_period": DEVELOPMENT,
        "true_oos_cutoff": "2025-01-01",
        "session_definition": {"weekdays": list(WEEKDAYS), "start_inclusive": "10:00",
                               "end_exclusive": "17:00", "timezone": "existing_project_trading_timezone"},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "session_candidate_report.md").write_text(_report(summary_rows), encoding="utf-8")
    if before != _sources(validation, optimization):
        raise RuntimeError("SOURCE_ARTIFACTS_MODIFIED")
    return manifest
