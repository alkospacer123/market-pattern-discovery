"""Frozen-candidate M30 robustness replay using the original H1 diagnostics.

Candidate identity is resolved from hard-coded IDs before any market-data loader
is called.  This module is deliberately descriptive: it contains no search,
ranking, robustness gate, or walk-forward operation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import numpy as np
import pandas as pd

from ..core.unified_metrics import concentration, finite, stats
from ..multitimeframe.phase71 import APPROVED_DATA_ROOT, STRATEGY_SHA256, reject_true_oos, verify_frozen_strategies
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..timeframe_validation import m30_baseline

PHASE = "M30_ROBUSTNESS"
STATUS = "PHASE_M30_ROBUSTNESS_COMPLETE"
OUTPUT = Path("TradingSystemLab/results/timeframe_analysis/M30_ROBUSTNESS")
BASELINE = Path("TradingSystemLab/results/timeframe_validation/M30")
OPTIMIZATION = Path("TradingSystemLab/results/timeframe_optimization/M30")
DEVELOPMENT_PERIOD = ["2023-01-01", "2024-12-31"]
TRUE_OOS_CUTOFF = "2025-01-01"
BOOTSTRAP_SEED = 330_2025
BOOTSTRAP_ITERATIONS = 10_000
PREDECLARED_CONFIGURATION_IDS = {
    "T2": "T2-M30-0008-2b0494cdd24b",
    "T3": "T3-M30-0020-816e9e819790",
}
FROZEN = {
    "T2": {"candidate_id": "T2_M30_candidate_v1", "parent_candidate_id": "T2_candidate_v1",
           "parameter_hash": "2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00",
           "parameters": {"adx_threshold": 20, "confirmation_window": 3, "ema_fast": 20,
             "ema_slow": 200, "ema_trend": 50, "impulse_distance_atr": .5,
             "max_initial_stop_atr": 2.5, "trailing_atr": 3}},
    "T3": {"candidate_id": "T3_M30_candidate_v1", "parent_candidate_id": "T3_candidate_v1",
           "parameter_hash": "816e9e819790e1523aa5408bc1437119fae03f840c9e672c74f9974983e429c3",
           "parameters": {"adx_threshold": 25, "atr_average_period": 20, "breakout_period": 20,
             "ema_period": 75, "stop_atr": 2.0, "trail_atr": 3.0}},
}
EXPECTED_REPLAY = {
    "T2": {"trades": 178, "PF": 1.4875514967448944, "expectancy_R": .22257128076651778,
           "net_R": 39.617687976440166, "max_drawdown_R": -15.0847664713036},
    "T3": {"trades": 190, "PF": 2.39563875011, "expectancy_R": .530481219958,
           "net_R": 100.791431792, "max_drawdown_R": -8.94922459666},
}
FLAGS = {"optimization": False, "ranking": False, "candidate_selection": False,
         "parameter_change": False, "strategy_change": False, "filter_search": False,
         "walk_forward": False, "true_oos_access": False, "portfolio": False}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: Any) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def lock_candidate_registry(optimization: Path) -> dict[str, dict]:
    """Validate only the predeclared IDs; this intentionally precedes data access."""
    registry = {}
    for key, contract in FROZEN.items():
        root = optimization / key
        parameters = pd.read_csv(root / "parameters.csv")
        selected = parameters.loc[parameters.configuration_id.eq(PREDECLARED_CONFIGURATION_IDS[key])]
        if len(selected) != 1:
            raise RuntimeError(f"{key}_PREDECLARED_CONFIGURATION_MISSING")
        row = selected.iloc[0]
        actual = {name: row[name].item() for name in contract["parameters"]}
        if row.parameter_hash != contract["parameter_hash"] or actual != contract["parameters"] or stable_hash(actual) != contract["parameter_hash"]:
            raise RuntimeError(f"{key}_FROZEN_PARAMETER_PROVENANCE_MISMATCH")
        plateau = pd.read_csv(root / "plateau_report.csv")
        classification = plateau.loc[plateau.configuration_id.eq(PREDECLARED_CONFIGURATION_IDS[key]), "classification"]
        if len(classification) != 1 or classification.iloc[0] != "ROBUST_PLATEAU":
            raise RuntimeError(f"{key}_NOT_ROBUST_PLATEAU")
        registry[key] = {"strategy": key, **contract,
            "optimization_configuration_id": PREDECLARED_CONFIGURATION_IDS[key],
            "strategy_hash": STRATEGY_SHA256[key], "selection_locked_before_validation": True,
            "optimization_classification": "ROBUST_PLATEAU",
            "source_optimization_artifact_hashes": {name: _sha(root / name) for name in
                ("parameters.csv", "plateau_report.csv", "results.csv", "manifest.json")}}
    return registry


def _validate_prerequisites(baseline: Path, optimization: Path) -> tuple[dict, dict]:
    bm = json.loads((baseline / "manifest.json").read_text(encoding="utf-8"))
    om = json.loads((optimization / "manifest.json").read_text(encoding="utf-8"))
    if (bm.get("phase"), bm.get("status"), bm.get("timeframe"), bm.get("development_period"),
            bm.get("true_oos_cutoff"), bm.get("true_oos_blocked")) != (
            "M30_BASELINE", "PHASE_M30_BASELINE_COMPLETE", "M30", DEVELOPMENT_PERIOD, TRUE_OOS_CUTOFF, True):
        raise RuntimeError("M30_BASELINE_PREREQUISITE_INVALID")
    required = (om.get("phase") == "M30_OPTIMIZATION" and om.get("status") == "PHASE_M30_OPTIMIZATION_COMPLETE"
        and om.get("timeframe") == "M30" and om.get("development_period") == DEVELOPMENT_PERIOD
        and om.get("true_oos_cutoff") == TRUE_OOS_CUTOFF and om.get("true_oos_blocked") is True
        and om.get("one_factor_at_a_time") is True and om.get("cartesian_grid") is False
        and om.get("winner_selection") is False and om.get("robustness") is False
        and om.get("walk_forward") is False)
    if not required:
        raise RuntimeError("M30_OPTIMIZATION_PREREQUISITE_INVALID")
    if bm.get("source_files") != om.get("source_files"):
        raise RuntimeError("M30_BASELINE_OPTIMIZATION_SOURCE_MISMATCH")
    return bm, om


def _metric(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float)
    summary = stats(values)
    holding = ((pd.to_datetime(frame.exit_time, utc=True) - pd.to_datetime(frame.entry_time, utc=True)).dt.total_seconds() / 60
               if len(frame) else pd.Series(dtype=float))
    return {name: finite(value) for name, value in {
        "trades": summary["trades"], "PF": summary["PF_R"], "expectancy_R": summary["expectancy"],
        "net_R": summary["net_R"], "max_drawdown_R": summary["max_DD_R"],
        "recovery_factor": summary["recovery_factor"], "win_rate": summary["winrate"],
        "average_holding_minutes": holding.mean() if len(holding) else None,
        "max_winning_streak": summary["max_winning_streak"], "max_losing_streak": summary["max_losing_streak"],
        "average_MAE_R": frame.MAE_R.astype(float).mean() if len(frame) else None,
        "average_MFE_R": frame.MFE_R.astype(float).mean() if len(frame) else None}.items()}


def _bootstrap(values: pd.Series) -> dict:
    data = np.asarray(values, dtype=float); rng = np.random.default_rng(BOOTSTRAP_SEED)
    means = np.empty(BOOTSTRAP_ITERATIONS)
    for start in range(0, BOOTSTRAP_ITERATIONS, 1000):
        stop = min(start + 1000, BOOTSTRAP_ITERATIONS)
        means[start:stop] = rng.choice(data, size=(stop - start, len(data)), replace=True).mean(axis=1)
    q = np.quantile(means, [.025, .05, .5, .95, .975])
    return {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED, "sample_trades": len(data),
        "bootstrap_mean_R": float(means.mean()), "p2.5": q[0], "p5": q[1], "p50": q[2],
        "p95": q[3], "p97.5": q[4], "probability_mean_R_gt_0": float((means > 0).mean()),
        "interpretation": "DIAGNOSTIC_ONLY_IID_TRADE_BOOTSTRAP"}


def _mae_mfe(frame: pd.DataFrame) -> list[dict]:
    rows = []
    for scope, mask in (("ALL", pd.Series(True, index=frame.index)), ("WINNERS", frame.net_R.gt(0)), ("LOSERS", frame.net_R.lt(0))):
        for name in ("MAE_R", "MFE_R"):
            values = pd.to_numeric(frame.loc[mask, name], errors="coerce").dropna()
            rows.append({"scope": scope, "metric": name, "count": len(values),
                "mean": values.mean() if len(values) else None, "median": values.median() if len(values) else None,
                "p75": values.quantile(.75) if len(values) else None, "p90": values.quantile(.9) if len(values) else None})
    return rows


def _drawdown(frame: pd.DataFrame) -> list[dict]:
    if frame.empty: return []
    ordered = frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    curve = pd.concat([pd.Series([0.0]), ordered.net_R.astype(float).cumsum().reset_index(drop=True)], ignore_index=True)
    drawdown = curve - curve.cummax(); trough_curve = int(drawdown.idxmin()); peak_value = curve.cummax().iloc[trough_curve]
    start_curve = int(curve.iloc[:trough_curve + 1][curve.iloc[:trough_curve + 1].eq(peak_value)].index[0])
    recovery_candidates = drawdown.index[(drawdown.index > trough_curve) & drawdown.ge(0)]
    recovery_curve = int(recovery_candidates[0]) if len(recovery_candidates) else None
    timestamp = lambda curve_index: pd.Timestamp(ordered.iloc[max(curve_index - 1, 0)].exit_time)
    start, trough = timestamp(start_curve), timestamp(trough_curve)
    end = timestamp(recovery_curve) if recovery_curve is not None else pd.Timestamp(ordered.iloc[-1].exit_time)
    return [{"max_drawdown_R": float(drawdown.iloc[trough_curve]), "drawdown_start": start.isoformat(),
        "trough": trough.isoformat(), "recovery": end.isoformat() if recovery_curve is not None else "UNRECOVERED",
        "duration_minutes": (end - start).total_seconds() / 60}]


def _dependence(frame: pd.DataFrame) -> list[dict]:
    dates = pd.to_datetime(frame.exit_time, utc=True); naive = dates.dt.tz_localize(None)
    definitions = (("leave_one_quarter_out", naive.dt.to_period("Q").astype(str)),
                   ("leave_one_year_out", dates.dt.year.astype(str)))
    return [{"analysis": analysis, "omitted_period": period, **_metric(frame.loc[labels.ne(period)])}
            for analysis, labels in definitions for period in sorted(labels.unique())]


def _parity(key: str, metric: dict, optimization: Path) -> None:
    committed = pd.read_csv(optimization / key / "results.csv")
    row = committed.loc[committed.configuration_id.eq(PREDECLARED_CONFIGURATION_IDS[key])]
    if len(row) != 1: raise RuntimeError(f"{key}_OPTIMIZATION_RESULT_MISSING")
    expected = EXPECTED_REPLAY[key]
    mapping = {"trades": "trades", "PF": "PF_C1", "expectancy_R": "expectancy_C1",
               "net_R": "net_R_C1", "max_drawdown_R": "max_DD_C1"}
    for name, column in mapping.items():
        if name == "trades": ok = metric[name] == expected[name] == int(row.iloc[0][column])
        else: ok = np.isclose(metric[name], expected[name], rtol=0, atol=5e-10) and np.isclose(metric[name], row.iloc[0][column], rtol=0, atol=5e-10)
        if not ok: raise RuntimeError(f"{key}_OPTIMIZATION_REPLAY_PARITY_FAILURE_{name}")


def _reports(target: Path, key: str, trades: pd.DataFrame, baseline_trades: pd.DataFrame) -> dict:
    target.mkdir(parents=True); overall = _metric(trades)
    _csv(target / "trades.csv", trades); _json(target / "metrics.json", overall)
    group = lambda column, value: _metric(trades.loc[trades[column].eq(value)])
    _csv(target / "yearly_report.csv", [{"year": year, **group("year", year)} for year in (2023, 2024)])
    _csv(target / "instrument_report.csv", [{"instrument": name, **group("instrument", name)} for name, _ in m30_baseline.INSTRUMENTS])
    _csv(target / "direction_report.csv", [{"direction": side, **group("direction", side)} for side in ("LONG", "SHORT")])
    dates = pd.to_datetime(trades.exit_time, utc=True).dt.tz_localize(None).dt.to_period("M")
    _csv(target / "monthly_report.csv", [{"month": str(month), **_metric(trades.loc[dates.eq(month)])}
        for month in pd.period_range("2023-01", "2024-12", freq="M")])
    _csv(target / "concentration_report.csv", [concentration(trades.net_R.astype(float))])
    _csv(target / "drawdown_report.csv", _drawdown(trades)); _csv(target / "mae_mfe_report.csv", _mae_mfe(trades))
    _csv(target / "bootstrap_report.csv", [_bootstrap(trades.net_R.astype(float))])
    _csv(target / "leave_one_period_out.csv", _dependence(trades))
    _csv(target / "baseline_vs_candidate.csv", [
        {"version": "baseline", "candidate_id": FROZEN[key]["parent_candidate_id"], **_metric(baseline_trades)},
        {"version": "candidate", "candidate_id": FROZEN[key]["candidate_id"], **overall}])
    (target / "final_report.md").write_text(
        f"# {FROZEN[key]['candidate_id']} robustness\n\nC1-only descriptive H1-methodology diagnostics on full 2023–2024 development data. "
        "The candidate was frozen before validation; no selection, gate, filter, optimization, TRUE OOS, or walk-forward occurred.\n", encoding="utf-8")
    return overall


def _protected_paths(output: Path) -> tuple[Path, ...]:
    fixed = [Path(p) for p in ("TradingSystemLab/results/T2_implementation_check", "TradingSystemLab/results/T3_robust",
        "TradingSystemLab/results/robustness_validation", "TradingSystemLab/results/multitimeframe_research",
        "TradingSystemLab/results/timeframe_validation", "TradingSystemLab/results/timeframe_optimization",
        "TradingSystemLab/results/walk_forward", "TradingSystemLab/results/true_oos_validation")]
    analysis = Path("TradingSystemLab/results/timeframe_analysis")
    siblings = [p for p in analysis.iterdir() if p != output] if analysis.exists() else []
    return tuple(fixed + siblings)


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT,
        baseline: Path = BASELINE, optimization: Path = OPTIMIZATION) -> dict[str, Any]:
    """Run the frozen replay. Registry locking happens before the sole data read."""
    verify_frozen_strategies(); output, baseline, optimization = map(Path, (output, baseline, optimization))
    bm, om = _validate_prerequisites(baseline, optimization)
    registry = lock_candidate_registry(optimization)  # MUST precede loading market data.
    protected = _protected_paths(output); before = {str(path): hash_tree(path) for path in protected}
    loaded = {alias: m30_baseline.load_m30_development(Path(data_root), alias) for _, alias in m30_baseline.INSTRUMENTS}
    if any(frame is None for frame, _ in loaded.values()): raise RuntimeError("M30_DEVELOPMENT_DATA_MISSING")
    sources = [{"instrument": instrument, "alias": alias, "name": path.name, "sha256": _sha(path)}
               for instrument, alias in m30_baseline.INSTRUMENTS for path in loaded[alias][1]]
    if sources != bm["source_files"] or sources != om["source_files"]: raise RuntimeError("M30_SOURCE_SNAPSHOT_MISMATCH")
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True); summaries = []
    for key in ("T2", "T3"):
        def execute(parameters: dict) -> pd.DataFrame:
            pieces = [m30_baseline._execute(key, parameters, alias, loaded[alias][0]) for _, alias in m30_baseline.INSTRUMENTS]
            result = pd.concat(pieces, ignore_index=True).sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
            reject_true_oos(result.entry_time); reject_true_oos(result.exit_time)
            result["year"] = pd.to_datetime(result.exit_time, utc=True).dt.year
            return result
        candidate = execute(registry[key]["parameters"]); metric = _metric(candidate); _parity(key, metric, optimization)
        baseline_trades = execute(m30_baseline.EXPECTED[key]["parameters"])
        overall = _reports(output / key, key, candidate, baseline_trades)
        if key == "T2" and not candidate.equals(baseline_trades): raise RuntimeError("T2_BASELINE_CANDIDATE_EQUALITY_FAILURE")
        summaries.append({"strategy": key, "candidate_id": registry[key]["candidate_id"], **overall})
    _json(output / "candidate_registry.json", registry); _csv(output / "comparison.csv", summaries)
    after = {str(path): hash_tree(path) for path in protected}
    if before != after: raise RuntimeError("PROTECTED_RESEARCH_ARTIFACT_MUTATION")
    manifest = {"phase": PHASE, "status": STATUS, "timeframe": "M30", "development_period": DEVELOPMENT_PERIOD,
        "true_oos_cutoff": TRUE_OOS_CUTOFF, "true_oos_blocked": True,
        "candidate_selection_precedes_validation": True,
        "candidate_ids": {k: registry[k]["candidate_id"] for k in registry},
        "parent_candidate_ids": {k: registry[k]["parent_candidate_id"] for k in registry},
        "optimization_configuration_ids": PREDECLARED_CONFIGURATION_IDS,
        "parameter_hashes": {k: registry[k]["parameter_hash"] for k in registry},
        "strategy_hashes": STRATEGY_SHA256,
        "optimization_artifact_hashes": {k: registry[k]["source_optimization_artifact_hashes"] for k in registry},
        "baseline_artifact_hash": hash_tree(baseline), "source_files": sources,
        "source_coverage": bm["source_coverage"],
        "cost_model": {"name": "H1_C1", "ticks_per_side": 1.0, "round_trip_ticks": 2.0, "additional_slippage_ticks": 0.0},
        "bootstrap": {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED,
                      "interpretation": "DIAGNOSTIC_ONLY_IID_TRADE_BOOTSTRAP"},
        "deterministic_execution": True, "execution": {"T2": "DIRECT_CLOSED_M30", "T3": "CLOSED_M30_WITH_CAUSAL_FOUR_M30_CONTEXT"},
        "protected_artifact_hashes": after, **FLAGS}
    _json(output / "manifest.json", manifest)
    lines = ["# M30 Frozen-Candidate Robustness Validation", "", f"Status: `{STATUS}`", "",
        "Original H1 robustness methodology, C1 only. Diagnostic evidence; no robustness gate or candidate selection.", "",
        "| Strategy | Trades | PF | Expectancy R | Net R | Max DD R |", "|---|---:|---:|---:|---:|---:|"]
    lines += ["| " + " | ".join(str(row[x]) for x in ("strategy", "trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")) + " |" for row in summaries]
    (output / "robustness_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest
