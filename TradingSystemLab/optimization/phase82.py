"""Phase 8.2 deterministic, development-only M1 bounded optimization.

The design is intentionally small: the Phase 8.1 baseline plus every declared
one-factor perturbation.  It is not a generic search or ranking API.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from ..core.unified_metrics import concentration, finite, stats
from ..multitimeframe.phase71 import APPROVED_DATA_ROOT, COST_TICKS_PER_SIDE, STRATEGY_FILES, STRATEGY_SHA256, verify_frozen_strategies
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..strategies.trend.T2_Trend_Pullback import T2Parameters
from ..strategies.trend.T3_MTF_Trend import T3Parameters
from ..timeframe_validation.phase81 import INSTRUMENTS, _execute, load_m1_development

OUTPUT = Path("TradingSystemLab/results/timeframe_optimization/M1")
BASELINE_ROOT = Path("TradingSystemLab/results/timeframe_validation/M1")
PROTECTED = (BASELINE_ROOT,)
BASELINES = {
    "T2": {"candidate_id": "T2_candidate_v1", "parameters": {"adx_threshold": 20,
        "confirmation_window": 3, "ema_fast": 20, "ema_slow": 200, "ema_trend": 50,
        "impulse_distance_atr": .5, "max_initial_stop_atr": 2.5, "trailing_atr": 3}},
    "T3": {"candidate_id": "T3_candidate_v1", "parameters": {"adx_threshold": 20,
        "atr_average_period": 20, "breakout_period": 20, "ema_period": 75,
        "stop_atr": 2.0, "trail_atr": 3.0}},
}

# Existing configurable parameters only. Values are fixed before data is read.
RANGES: dict[str, dict[str, list[Any]]] = {
    "T2": {"ema_fast": [15, 20, 25], "ema_trend": [40, 50, 60],
           "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25],
           "impulse_distance_atr": [.3, .5, .7], "confirmation_window": [2, 3, 4],
           "max_initial_stop_atr": [2, 2.5, 3], "trailing_atr": [2, 3, 4]},
    "T3": {"ema_period": [50, 75, 100], "adx_threshold": [15, 20, 25],
           "breakout_period": [10, 20, 30], "atr_average_period": [10, 20, 30],
           "stop_atr": [1.5, 2, 2.5], "trail_atr": [2, 3, 4]},
}
MAX_CONFIGURATIONS = 5000
OPTIMIZATION_START = pd.Timestamp("2024-01-01", tz="Europe/Moscow")
OPTIMIZATION_END = pd.Timestamp("2025-01-01", tz="Europe/Moscow")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline_candidates(path: Path = BASELINE_ROOT / "manifest.json") -> dict[str, dict[str, Any]]:
    """Verify embedded Phase 8.1 inputs against its M1-only manifest.

    Parameters are embedded to ensure this phase never opens an H1 optimization
    or robustness artifact.
    """
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("phase") != "8.1" or manifest.get("timeframe") != "M1":
        raise RuntimeError("PHASE_8_1_BASELINE_PROVENANCE_INVALID")
    hashes = manifest.get("parameter_hashes", {})
    if any(hashes.get(key) != stable_hash(BASELINES[key]["parameters"]) for key in BASELINES):
        raise RuntimeError("PHASE_8_1_BASELINE_PARAMETER_HASH_MISMATCH")
    return BASELINES


def bounded_design(key: str, baseline: dict[str, Any]) -> list[dict[str, Any]]:
    """Baseline plus declared one-factor neighbors, in canonical order."""
    if any(baseline[name] not in values for name, values in RANGES[key].items()):
        raise ValueError(f"{key}_BASELINE_OUTSIDE_DECLARED_RANGES")
    rows = {stable_hash(baseline): dict(baseline)}
    for name in sorted(RANGES[key]):
        for value in RANGES[key][name]:
            candidate = {**baseline, name: value}
            rows[stable_hash(candidate)] = candidate
    design = sorted(rows.values(), key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
    if len(design) > MAX_CONFIGURATIONS:
        raise RuntimeError("M1_CONFIGURATION_LIMIT_EXCEEDED")
    return design


def validate_bounds(key: str, configs: list[dict[str, Any]]) -> None:
    for config in configs:
        if any(config[name] not in values for name, values in RANGES[key].items()):
            raise ValueError(f"{key}_PARAMETER_BOUNDS_VIOLATION")


def _metrics(configuration_id: str, trades: pd.DataFrame) -> dict[str, Any]:
    values = trades.net_R.astype(float) if len(trades) else pd.Series(dtype=float)
    metric = stats(values)
    holding = ((pd.to_datetime(trades.exit_time, utc=True) - pd.to_datetime(trades.entry_time, utc=True))
               .dt.total_seconds() / 60) if len(trades) else pd.Series(dtype=float)
    conc = concentration(values)
    return {k: finite(v) for k, v in {
        "configuration_id": configuration_id, "trades": metric["trades"], "PF": metric["PF_R"],
        "expectancy_R": metric["expectancy"], "net_R": metric["net_R"],
        "max_drawdown_R": metric["max_DD_R"], "recovery_factor": metric["recovery_factor"],
        "win_rate": metric["winrate"], "average_holding_minutes": holding.mean() if len(holding) else None,
        "losing_streak": metric["max_losing_streak"],
        "concentration_top_1": conc["top_1_positive_R_share"],
        "concentration_top_5": conc["top_5_positive_R_share"],
        "top_five_trade_dependency_net_R": conc["net_R_without_top5"],
        "top_five_trade_dependency_PF": conc["PF_R_C1_without_top5"],
    }.items()}


def _neighbors(configs: list[dict[str, Any]], position: int, key: str) -> list[int]:
    result = []
    for other, row in enumerate(configs):
        different = [name for name in RANGES[key] if row[name] != configs[position][name]]
        if len(different) == 1:
            name = different[0]; values = RANGES[key][name]
            if abs(values.index(row[name]) - values.index(configs[position][name])) == 1:
                result.append(other)
    return result


def _plateau(key: str, configs: list[dict], results: list[dict]) -> tuple[list[dict], list[dict]]:
    rows = []
    for i, result in enumerate(results):
        neighbors = _neighbors(configs, i, key)
        similar = [j for j in neighbors if results[j]["expectancy_R"] is not None and
                   result["expectancy_R"] is not None and
                   abs(results[j]["expectancy_R"] - result["expectancy_R"]) <=
                   max(.01, abs(result["expectancy_R"]) * .35)]
        robust = result["expectancy_R"] is not None and result["expectancy_R"] > 0 and len(similar) >= 2
        rows.append({"configuration_id": result["configuration_id"], "neighbor_count": len(neighbors),
                     "similar_neighbor_count": len(similar),
                     "classification": "ROBUST_PLATEAU" if robust else
                     ("LOCAL_PEAK" if result["expectancy_R"] is not None and result["expectancy_R"] > 0 else "NO_EDGE")})
    stability = []
    for name, values in RANGES[key].items():
        for value in values:
            sample = [r["expectancy_R"] for c, r in zip(configs, results)
                      if c[name] == value and r["expectancy_R"] is not None]
            stability.append({"parameter": name, "value": value, "configurations": len(sample),
                              "positive_share": sum(x > 0 for x in sample) / len(sample) if sample else None,
                              "mean_expectancy_R": sum(sample) / len(sample) if sample else None,
                              "min_expectancy_R": min(sample) if sample else None,
                              "max_expectancy_R": max(sample) if sample else None})
    return rows, stability


def _csv(path: Path, rows: Any) -> None:
    pd.DataFrame(rows).map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


_WORKER_DATA: dict | None = None


def _evaluate(task: tuple[str, dict, str]) -> dict[str, Any]:
    key, config, cid = task
    if _WORKER_DATA is None:
        raise RuntimeError("M1_WORKER_DATA_NOT_INITIALIZED")
    pieces = [_execute(key, config, alias, frame) for _, alias in INSTRUMENTS
              if (frame := _WORKER_DATA[alias][0]) is not None]
    trades = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(
        columns=["net_R", "entry_time", "exit_time"])
    if len(trades):
        trades = trades.sort_values(["exit_time", "trade_id"], kind="mergesort").reset_index(drop=True)
    return {**_metrics(cid, trades), **config}


def _run_strategy(key: str, baseline_row: dict, loaded: dict, output: Path,
                  source_hashes: list[dict]) -> dict[str, Any]:
    baseline = dict(baseline_row["parameters"]); configs = bounded_design(key, baseline)
    validate_bounds(key, configs); tasks = []
    for number, config in enumerate(configs):
        cid = f"{key}-M1-{number:04d}-{stable_hash(config)[:12]}"
        tasks.append((key, config, cid))
    global _WORKER_DATA
    _WORKER_DATA = loaded
    results = []
    with mp.get_context("fork").Pool(processes=min(8, len(tasks))) as pool:
        for completed, result in enumerate(pool.imap(_evaluate, tasks, chunksize=1), start=1):
            results.append(result)
            print(f"{key}: configuration {completed}/{len(tasks)} completed", flush=True)
    _WORKER_DATA = None
    plateau, stability = _plateau(key, configs, results)
    plateau_ids = {r["configuration_id"] for r in plateau if r["classification"] == "ROBUST_PLATEAU"}
    baseline_id = next(r["configuration_id"] for c, r in zip(configs, results) if c == baseline)
    baseline_result = next(r for r in results if r["configuration_id"] == baseline_id)
    minimum_trades = max(10, baseline_result["trades"] // 2)
    dd_limit = max(20.0, abs(baseline_result["max_drawdown_R"] or 0) * 1.5)
    eligible = [r for r in results if r["configuration_id"] in plateau_ids and r["trades"] >= minimum_trades
                and (r["expectancy_R"] or 0) > 0 and r["net_R"] > 0
                and abs(r["max_drawdown_R"] or 0) <= dd_limit
                and (r["top_five_trade_dependency_net_R"] or 0) > 0]
    # Multi-criterion ordering; PF is deliberately absent.
    selected = sorted(eligible, key=lambda r: (-r["expectancy_R"], abs(r["max_drawdown_R"]),
                                                -r["trades"], r["configuration_id"]))[0] if eligible else baseline_result
    selection = "ROBUST_PLATEAU" if selected in eligible else "BASELINE_FALLBACK_NO_QUALIFYING_PLATEAU"
    candidate_id = f"{key}_M1_candidate_v1"; parameter_hash = stable_hash({n: selected[n] for n in RANGES[key]})
    registry = {"candidate_id": candidate_id, "strategy": key, "timeframe": "M1",
                "configuration_id": selected["configuration_id"], "parameter_hash": parameter_hash,
                "parameters": {n: selected[n] for n in RANGES[key]}, "selection_status": selection,
                "source_hashes": source_hashes, "baseline_candidate_id": baseline_row["candidate_id"],
                "baseline_parameter_hash": stable_hash(baseline), "strategy_hash": STRATEGY_SHA256[key]}
    output.mkdir(parents=True, exist_ok=True)
    _json(output / "candidate_registry.json", registry)
    _csv(output / "optimization_results.csv", results); _csv(output / "plateau_analysis.csv", plateau)
    _csv(output / "parameter_stability.csv", stability)
    _csv(output / "baseline_vs_optimized.csv", [{"version": "baseline", **baseline_result},
                                                   {"version": "optimized", **selected}])
    metrics = {"candidate_id": candidate_id, "configuration_id": selected["configuration_id"],
               "selection_status": selection, "tested_configurations": len(configs),
               "robust_plateau_configurations": len(plateau_ids), **{k: selected[k] for k in
               ("trades", "PF", "expectancy_R", "net_R", "max_drawdown_R", "recovery_factor",
                "win_rate", "average_holding_minutes", "losing_streak", "concentration_top_1",
                "concentration_top_5", "top_five_trade_dependency_net_R", "top_five_trade_dependency_PF")}}
    _json(output / "metrics.json", metrics)
    (output / "final_report.md").write_text(
        f"# {candidate_id}\n\n- Tested: {len(configs)} bounded configurations\n"
        f"- Selected configuration: `{selected['configuration_id']}`\n- Selection: **{selection}**\n"
        f"- Robust plateau members: {len(plateau_ids)}\n\nSelection requires trade count, positive expectancy/net R, "
        "bounded drawdown, positive net R after removing the five best trades, and plateau membership. "
        "No maximum-PF selection was performed.\n", encoding="utf-8")
    return {"strategy": key, **metrics}


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    """Run separate T2 and T3 M1 searches and atomically verify old artifacts."""
    verify_frozen_strategies(); baselines = baseline_candidates()
    protected_before = {str(path): hash_tree(path) for path in PROTECTED}
    loaded = {alias: load_m1_development(Path(data_root), alias) for _, alias in INSTRUMENTS}
    loaded = {alias: (None if frame is None else frame.loc[
        (frame.index >= OPTIMIZATION_START) & (frame.index < OPTIMIZATION_END)], paths)
        for alias, (frame, paths) in loaded.items()}
    sources = [{"instrument": instrument, "alias": alias,
                "files": [{"name": p.name, "sha256": _sha(p)} for p in loaded[alias][1]]}
               for instrument, alias in INSTRUMENTS]
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = [_run_strategy(key, baselines[key], loaded, output / key, sources) for key in ("T2", "T3")]
    _csv(output / "comparison.csv", summaries)
    protected_after = {str(path): hash_tree(path) for path in PROTECTED}
    if protected_before != protected_after: raise RuntimeError("PROTECTED_ARTIFACT_MUTATION")
    manifest = {"phase": "8.2", "status": "PHASE_8_2_M1_OPTIMIZATION_COMPLETE", "timeframe": "M1",
        "development_period": ["2024-01-01", "2024-12-31"], "instruments": [x[0] for x in INSTRUMENTS],
        "strategies": ["T2_M1_candidate_v1", "T3_M1_candidate_v1"], "source_data_hashes": sources,
        "baseline_artifact_hashes": {str(BASELINE_ROOT): protected_before[str(BASELINE_ROOT)]},
        "strategy_hashes": {k: {"file": STRATEGY_FILES[k], "sha256": STRATEGY_SHA256[k]} for k in ("T2", "T3")},
        "parameter_hashes": {r["strategy"]: json.loads((output / r["strategy"] / "candidate_registry.json").read_text())["parameter_hash"] for r in summaries},
        "optimization_ranges": RANGES, "configurations_tested": {r["strategy"]: r["tested_configurations"] for r in summaries},
        "cost_model": {"cost_ticks_per_side": COST_TICKS_PER_SIDE, "round_trip_ticks": 2 * COST_TICKS_PER_SIDE,
                       "slippage_ticks_per_side": 0.0}, "design": "BASELINE_PLUS_ONE_FACTOR_AT_A_TIME",
        "configuration_limit_per_strategy": MAX_CONFIGURATIONS, "deterministic": True, "true_oos_blocked": True,
        "walk_forward": False, "portfolio": False, "cross_timeframe_ranking": False,
        "protected_artifact_hashes": protected_after}
    _json(output / "manifest.json", manifest)
    lines = ["# Phase 8.2 M1 Bounded Optimization", "", "Independent bounded T2 and T3 development searches; no cross-timeframe ranking or winner selection.", "",
             "| Strategy | Tested | Candidate | Configuration | Plateau members | Selection |", "|---|---:|---|---|---:|---|"]
    for row in summaries: lines.append(f"| {row['strategy']} | {row['tested_configurations']} | {row['candidate_id']} | {row['configuration_id']} | {row['robust_plateau_configurations']} | {row['selection_status']} |")
    lines += ["", "2025+ TRUE OOS, walk-forward, portfolio construction, and H1 artifacts were not accessed.", "",
              "PHASE_8_2_M1_OPTIMIZATION_COMPLETE", ""]
    (output / "m1_optimization_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": manifest["status"], "strategies": summaries}
