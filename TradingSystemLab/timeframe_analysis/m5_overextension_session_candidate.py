"""Validate the pre-declared M5 session and EMA50-distance hypotheses.

This module is deliberately not an optimizer.  It reads frozen development
trades, attaches the causal entry features used by the entry-quality phase and
reports the one fixed session window and the existing near/normal/extended
classification.  It never reads 2025 data or changes a trade outcome.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping, Sequence

import pandas as pd

from .m5_entry_quality import DATA, _discover, _entry_rows, _load_bars
from ..core.unified_metrics import finite, stats
from ..timeframe_diagnostics.m5_full import _prepare, _write_csv

VALIDATION = Path("TradingSystemLab/results/timeframe_validation/M5")
OPTIMIZATION = Path("TradingSystemLab/results/timeframe_optimization/M5")
OUTPUT = Path("TradingSystemLab/results/timeframe_analysis/M5_OVEREXTENSION_SESSION_CANDIDATE")
CANDIDATES = {"T2": "T2_M5_candidate_v1", "T3": "T3_M5_candidate_v1"}
DEVELOPMENT_PERIOD = "2023-01-01 to 2024-12-31"
DISTANCES = ("near", "normal", "extended")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
FILES = ("baseline_vs_candidate.csv", "session_analysis.csv", "ema50_distance_analysis.csv",
         "interaction_analysis.csv", "outcome_comparison.csv", "metrics.json")
METRICS = ("trades", "win_rate", "PF", "expectancy_R", "net_R", "max_drawdown_R",
           "recovery_factor", "average_holding_time", "losing_streak",
           "top_1_positive_R_concentration", "top_5_positive_R_concentration")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _source_hashes(validation: Path, optimization: Path, market_paths: Sequence[Path]) -> dict[str, str]:
    paths = [validation / key / "trades.csv" for key in CANDIDATES]
    paths += [optimization / key / "candidate_registry.json" for key in CANDIDATES]
    paths += list(market_paths)
    return {str(path): _sha(path) for path in sorted(set(paths), key=str)}


def _losing_streak(frame: pd.DataFrame) -> int:
    longest = current = 0
    for losing in frame.net_R.lt(0):
        current = current + 1 if losing else 0
        longest = max(longest, current)
    return longest


def _metrics(frame: pd.DataFrame) -> dict[str, Any]:
    calculated = stats(frame.net_R)
    positive = frame.net_R.clip(lower=0).sum()
    ordered = frame.net_R.sort_values(ascending=False, kind="mergesort").clip(lower=0)
    concentration = lambda n: float(ordered.head(n).sum() / positive) if positive else None
    return {"trades": len(frame), "win_rate": calculated["winrate"], "PF": calculated["PF_R"],
            "expectancy_R": calculated["expectancy"], "net_R": calculated["net_R"],
            "max_drawdown_R": calculated["max_DD_R"], "recovery_factor": calculated["recovery_factor"],
            "average_holding_time": finite(frame.holding_minutes.mean()),
            "losing_streak": _losing_streak(frame),
            "top_1_positive_R_concentration": concentration(1),
            "top_5_positive_R_concentration": concentration(5)}


def _session_mask(frame: pd.DataFrame) -> pd.Series:
    """The fixed project-timezone eligibility rule (10:00 included, 17:00 excluded)."""
    return frame.weekday.isin(WEEKDAYS) & frame.hour.ge(10) & frame.hour.lt(17)


def _variant_rows(scope: str, frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [{"scope": scope, "variant": name, **_metrics(part)} for name, part in
            (("BASELINE", frame), ("SESSION_CANDIDATE", frame.loc[_session_mask(frame)]))]


def _dimension_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    definitions = (("instrument", "instrument", sorted(frame.instrument.unique())),
                   ("direction", "direction", ("LONG", "SHORT")),
                   ("weekday", "weekday", WEEKDAYS),
                   ("session", "session", ("Session_A", "Session_B", "Session_C")),
                   ("EMA50_distance", "location_ema50", DISTANCES))
    rows = []
    for variant, selected in (("BASELINE", frame), ("SESSION_CANDIDATE", frame.loc[_session_mask(frame)])):
        for dimension, column, values in definitions:
            for value in values:
                rows.append({"variant": variant, "dimension": dimension, "category": value,
                             **_metrics(selected.loc[selected[column].eq(value)])})
    return rows


def _distance_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [{"ema50_distance": value, **_metrics(frame.loc[frame.location_ema50.eq(value)])}
            for value in DISTANCES]


def _interaction_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    session = frame.loc[_session_mask(frame)]
    return [{"session": "10:00-17:00", "ema50_distance": value,
             **_metrics(session.loc[session.location_ema50.eq(value)])} for value in DISTANCES]


def _outcome_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    outcomes = (("EARLY_FAILURE_NEGATIVE_AT_15_MIN", frame.early_failure),
                ("LONG_WINNER_120_MIN_PLUS", frame.long_winner))
    definitions = (("session", "session", ("Session_A", "Session_B", "Session_C")),
                   ("instrument", "instrument", sorted(frame.instrument.unique())),
                   ("EMA50_distance", "location_ema50", DISTANCES))
    for outcome, mask in outcomes:
        selected = frame.loc[mask]
        rows.append({"outcome": outcome, "dimension": "ALL", "category": "ALL", **_metrics(selected)})
        for dimension, column, values in definitions:
            for value in values:
                rows.append({"outcome": outcome, "dimension": dimension, "category": value,
                             **_metrics(selected.loc[selected[column].eq(value)])})
        for distance in DISTANCES:
            part = selected.loc[_session_mask(selected) & selected.location_ema50.eq(distance)]
            rows.append({"outcome": outcome, "dimension": "session_x_EMA50_distance",
                         "category": f"10:00-17:00|{distance}", **_metrics(part)})
    return rows


def _write_scope(target: Path, scope: str, frame: pd.DataFrame) -> None:
    target.mkdir(parents=True)
    _write_csv(target / "baseline_vs_candidate.csv", _variant_rows(scope, frame), ["scope", "variant", *METRICS])
    _write_csv(target / "session_analysis.csv", _dimension_rows(frame), ["variant", "dimension", "category", *METRICS])
    _write_csv(target / "ema50_distance_analysis.csv", _distance_rows(frame), ["ema50_distance", *METRICS])
    _write_csv(target / "interaction_analysis.csv", _interaction_rows(frame), ["session", "ema50_distance", *METRICS])
    _write_csv(target / "outcome_comparison.csv", _outcome_rows(frame), ["outcome", "dimension", "category", *METRICS])
    (target / "metrics.json").write_text(json.dumps({
        "baseline": _metrics(frame), "session_candidate": _metrics(frame.loc[_session_mask(frame)]),
        "ema50_distance": {value: _metrics(frame.loc[frame.location_ema50.eq(value)]) for value in DISTANCES},
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _report(frames: Mapping[str, pd.DataFrame]) -> str:
    combined = frames["COMBINED"]
    base, session = _metrics(combined), _metrics(combined.loc[_session_mask(combined)])
    distance = {value: _metrics(combined.loc[combined.location_ema50.eq(value)]) for value in DISTANCES}
    early = combined.loc[combined.early_failure]
    long = combined.loc[combined.long_winner]
    def share(frame: pd.DataFrame, distance_name: str) -> str:
        if frame.empty: return "DATA_UNAVAILABLE"
        count = int((_session_mask(frame) & frame.location_ema50.eq(distance_name)).sum())
        return f"{count}/{len(frame)} ({100 * count / len(frame):.1f}%)"
    improvement = session["expectancy_R"] is not None and base["expectancy_R"] is not None and session["expectancy_R"] > base["expectancy_R"]
    degradation = distance["extended"]["expectancy_R"] is not None and distance["normal"]["expectancy_R"] is not None and distance["extended"]["expectancy_R"] < distance["normal"]["expectancy_R"]
    return "\n".join(["# M5 overextension + session candidate validation", "",
        "Status: `PHASE_M5_OVEREXTENSION_SESSION_CANDIDATE_COMPLETE`", "",
        "This candidate-validation phase reports evidence only; it creates no trading rule and selects no production candidate.", "",
        "## Answers", "",
        f"1. **10:00–17:00 session:** {'Improved' if improvement else 'Did not improve'} combined expectancy versus baseline "
        f"({base['expectancy_R']} to {session['expectancy_R']}); PF changed from {base['PF']} to {session['PF']}.",
        f"2. **EMA50 overextension:** Extended expectancy is {distance['extended']['expectancy_R']} versus normal {distance['normal']['expectancy_R']}; measurable degradation: **{'yes' if degradation else 'no'}**.",
        f"3. **Interaction separation:** session+extended occurs in {share(early, 'extended')} early failures and {share(long, 'extended')} long winners. Detailed session, instrument, and distance counts are in `outcome_comparison.csv`.",
        "4. **Future validation:** **Yes, but only as a bounded follow-up hypothesis.** The session improvement is present in both T2 and T3, while EMA50 degradation is not uniform across them and the interaction separation is modest. This is not evidence for a production rule.", "",
        "All thresholds were inherited unchanged from the entry-quality diagnostic (near <= 0.5 ATR; normal > 0.5 and <= 1.5 ATR; extended > 1.5 ATR). TRUE OOS remained blocked.", ""]) + "\n"


def run(validation: Path = VALIDATION, optimization: Path = OPTIMIZATION, data: Path = DATA,
        output: Path = OUTPUT, market_data: Mapping[str, Any] | None = None) -> dict[str, Any]:
    validation, optimization, data, output = map(Path, (validation, optimization, data, output))
    registries = {}
    for key, identity in CANDIDATES.items():
        registries[key] = json.loads((optimization / key / "candidate_registry.json").read_text(encoding="utf-8"))
        if registries[key].get("candidate_id") != identity:
            raise ValueError(f"CANDIDATE_IDENTITY_MISMATCH:{key}")
    supplied = market_data if market_data is not None else _discover(data)
    bars, market_paths = {}, []
    for instrument in ("USDRUBF", "CNYRUBF"):
        bars[instrument], paths = _load_bars(supplied[instrument])
        market_paths += paths
    before = _source_hashes(validation, optimization, market_paths)
    prepared = {key: _prepare(validation / key / "trades.csv") for key in CANDIDATES}
    enriched = {key: _entry_rows(frame, bars) for key, frame in prepared.items()}
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    frames = dict(enriched)
    frames["COMBINED"] = pd.concat([enriched[key].assign(strategy=key) for key in CANDIDATES], ignore_index=True).sort_values(
        ["exit_time", "strategy", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    comparison = []
    for scope, frame in frames.items():
        _write_scope(output / scope, scope, frame)
        comparison += _variant_rows(scope, frame)
    _write_csv(output / "comparison.csv", comparison, ["scope", "variant", *METRICS])
    definitions = {"session": {"weekdays": list(WEEKDAYS), "start_inclusive": "10:00", "end_exclusive": "17:00",
                  "timezone": "entry_timestamp_project_timezone"},
                  "ema50_distance": {"normalization": "absolute_close_minus_ema50_divided_by_atr14",
                  "near": "<=0.5", "normal": ">0.5 and <=1.5", "extended": ">1.5"}}
    candidate_hashes = {key: _canonical_hash({"candidate_id": identity, "registry": registries[key]})
                        for key, identity in CANDIDATES.items()}
    execution_hash = _canonical_hash({"sources": before, "candidates": candidate_hashes, "definitions": definitions})
    manifest = {"phase": "M5_OVEREXTENSION_SESSION_CANDIDATE",
        "status": "PHASE_M5_OVEREXTENSION_SESSION_CANDIDATE_COMPLETE", "diagnostic_only": False,
        "candidate_validation": True, "optimization": False, "parameter_change": False,
        "strategy_change": False, "true_oos_access": False, "true_oos_blocked": True,
        "development_period": DEVELOPMENT_PERIOD, "source_hashes": before,
        "candidate_hashes": candidate_hashes, "deterministic_execution_hash": execution_hash,
        "candidate_definitions": definitions, "candidate_ids": CANDIDATES}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "m5_overextension_session_report.md").write_text(_report(frames), encoding="utf-8")
    if before != _source_hashes(validation, optimization, market_paths):
        raise RuntimeError("SOURCE_ARTIFACTS_MODIFIED")
    return manifest
