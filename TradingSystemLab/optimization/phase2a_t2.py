"""TradingSystemLab v2 Phase 2A: T2 M30/H1 bounded OAT optimization."""
from __future__ import annotations

from dataclasses import asdict, replace
import argparse
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import shutil
from typing import Any, Mapping

import pandas as pd

from ..baseline_v2 import (DATA_ROOT, DEVELOPMENT_START, FROZEN_TICK_SIZE,
                           INSTRUMENTS, TRUE_OOS_START, load_development)
from ..core.unified_metrics import concentration, finite, stats
from ..strategies.trend.T2_Trend_Pullback import T2Parameters, T2TrendPullback
from .experiment import stable_hash

OUTPUT_ROOT = Path("TradingSystemLab/results/optimization_v2/T2")
TIMEFRAMES = ("M30", "H1")
STRATEGY = "T2"
STRATEGY_ID = "T2_Trend_Pullback_Continuation_v1.0"
STRATEGY_HASH = "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774"
PHASE1_COMMIT = "2aae07a3d12907d1869eb603e6ac1a6fb8d851dd"
COST_MODEL = {"name": "C1", "ticks_per_side": 1, "round_trip_ticks": 2,
              "additional_slippage_ticks": 0}
PARAMETER_SPACE = {
    "ema_fast": [15, 20, 25, 30], "ema_trend": [40, 50, 60],
    "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25, 30],
    "impulse_distance_atr": [0.3, 0.5, 0.7], "confirmation_window": [2, 3, 4],
    "max_initial_stop_atr": [2.0, 2.5, 3.0], "trailing_atr": [2.0, 3.0, 4.0],
}
BASELINE = {name: getattr(T2Parameters(), name) for name in PARAMETER_SPACE}


def verify_strategy(project_root: Path = Path(".")) -> None:
    path = project_root / "TradingSystemLab/strategies/trend/T2_Trend_Pullback.py"
    if hashlib.sha256(path.read_bytes()).hexdigest() != STRATEGY_HASH:
        raise RuntimeError("T2_FROZEN_STRATEGY_HASH_MISMATCH")


def bounded_design() -> list[dict[str, Any]]:
    """Return the baseline and all unique one-factor deviations."""
    rows = [dict(BASELINE)]
    for name in sorted(PARAMETER_SPACE):
        rows.extend({**BASELINE, name: value} for value in PARAMETER_SPACE[name]
                    if value != BASELINE[name])
    rows.sort(key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
    if len(rows) != 19 or len({stable_hash(row) for row in rows}) != 19:
        raise RuntimeError("T2_OAT_DESIGN_INVALID")
    return rows


def configuration_id(timeframe: str, config: Mapping[str, Any]) -> str:
    return f"T2-{timeframe}-{stable_hash(dict(config))[:12]}"


def neighbors(configs: list[dict[str, Any]], index: int) -> list[int]:
    found = []
    for other_index, other in enumerate(configs):
        differing = [name for name in PARAMETER_SPACE if configs[index][name] != other[name]]
        if len(differing) == 1:
            values = PARAMETER_SPACE[differing[0]]
            if abs(values.index(configs[index][differing[0]]) - values.index(other[differing[0]])) == 1:
                found.append(other_index)
    return found


def classify(configs: list[dict[str, Any]], results: list[dict[str, Any]]) -> tuple[list[dict], str]:
    rows = []
    for index, result in enumerate(results):
        adjacent = neighbors(configs, index)
        positive = result["expectancy_C1"] is not None and result["expectancy_C1"] > 0
        positive_neighbors = [j for j in adjacent if results[j]["expectancy_C1"] is not None
                              and results[j]["expectancy_C1"] > 0]
        tolerance = max(0.01, abs(result["expectancy_C1"]) * 0.35) if positive else None
        stable = [j for j in positive_neighbors
                  if abs(results[j]["expectancy_C1"] - result["expectancy_C1"]) <= tolerance]
        classification = ("ROBUST_PLATEAU" if positive and len(stable) >= 2 else
                          "LOCAL_SPIKE" if positive else "NO_EDGE")
        rows.append({"configuration_id": result["configuration_id"],
                     "neighbor_ids": ";".join(results[j]["configuration_id"] for j in adjacent),
                     "neighbor_count": len(adjacent), "positive_neighbors": len(positive_neighbors),
                     "stable_positive_neighbors": len(stable), "stability_tolerance": tolerance,
                     "expectancy_C1": result["expectancy_C1"], "PF_C1": result["PF_C1"],
                     "classification": classification})
    overall = ("ROBUST_PLATEAU" if any(r["classification"] == "ROBUST_PLATEAU" for r in rows)
               else "LOCAL_SPIKE" if any(r["classification"] == "LOCAL_SPIKE" for r in rows)
               else "NO_EDGE")
    return rows, overall


def _metrics(configuration: str, trades: pd.DataFrame) -> dict[str, Any]:
    values = trades.net_R_C1.astype(float) if len(trades) else pd.Series(dtype=float)
    summary = stats(values)
    row = {"configuration_id": configuration, "trades": summary["trades"],
           "PF_C1": summary["PF_R"], "expectancy_C1": summary["expectancy"],
           "net_R_C1": summary["net_R"], "max_DD_C1": summary["max_DD_R"],
           "recovery_factor_C1": summary["recovery_factor"], "win_rate_C1": summary["winrate"]}
    for instrument in INSTRUMENTS:
        metric = stats(values[trades.symbol.eq(instrument)])
        row.update({f"{instrument}_trades": metric["trades"],
                    f"{instrument}_expectancy_C1": metric["expectancy"]})
    years = pd.to_datetime(trades.exit_time, utc=True).dt.year if len(trades) else pd.Series(dtype=int)
    for year in range(2020, 2025):
        metric = stats(values[years.eq(year)])
        row.update({f"Y{year}_trades": metric["trades"],
                    f"Y{year}_expectancy_C1": metric["expectancy"]})
    for direction in ("LONG", "SHORT"):
        metric = stats(values[trades.direction.eq(direction)])
        row.update({f"{direction}_trades": metric["trades"],
                    f"{direction}_expectancy_C1": metric["expectancy"]})
    row.update(concentration(values))
    return {key: finite(value) for key, value in row.items()}


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    pd.DataFrame(rows).map(finite).to_csv(path, index=False, lineterminator="\n",
                                          float_format="%.12g", na_rep="")


def _execute(config: Mapping[str, Any], frames: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    strategy = T2TrendPullback(replace(T2Parameters(), **config))
    pieces = [strategy.run(frames[instrument], instrument, tick_size=FROZEN_TICK_SIZE)
              for instrument in INSTRUMENTS]
    trades = pd.concat(pieces, ignore_index=True)
    if len(trades):
        trades = trades.sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
        if (pd.to_datetime(trades.entry_time, utc=True) >= TRUE_OOS_START.tz_convert("UTC")).any():
            raise RuntimeError("TRUE_OOS_TRADE_VIOLATION")
    return trades


_WORKER_FRAMES: Mapping[str, pd.DataFrame] | None = None


def _worker(task: tuple[dict[str, Any], str]) -> dict[str, Any]:
    if _WORKER_FRAMES is None:
        raise RuntimeError("T2_WORKER_DATA_NOT_INITIALIZED")
    config, cid = task
    return _metrics(cid, _execute(config, _WORKER_FRAMES))


def run_study(timeframe: str, data_root: Path, output: Path) -> dict[str, Any]:
    if timeframe not in TIMEFRAMES:
        raise ValueError("PHASE_2A_ALLOWS_ONLY_M30_AND_H1")
    frames, provenance = {}, []
    for instrument in INSTRUMENTS:
        frame, source = load_development(data_root, instrument, timeframe)
        frames[instrument] = frame
        provenance.append({"instrument": instrument, "source_file": str(source),
                           "first_close": frame.index.min().isoformat(),
                           "last_close": frame.index.max().isoformat(), "rows": len(frame)})
    configs = bounded_design()
    parameters, tasks = [], []
    for config in configs:
        cid = configuration_id(timeframe, config)
        parameters.append({"configuration_id": cid, "is_baseline": config == BASELINE, **config})
        tasks.append((config, cid))
    # Fork workers inherit the immutable admitted frames. Pool.map preserves
    # canonical configuration order and does not copy source data into Git.
    global _WORKER_FRAMES
    _WORKER_FRAMES = frames
    with mp.get_context("fork").Pool(processes=min(8, len(tasks))) as pool:
        results = pool.map(_worker, tasks)
    _WORKER_FRAMES = None
    plateau, overall = classify(configs, results)
    sensitivity = []
    for name in sorted(PARAMETER_SPACE):
        for value in PARAMETER_SPACE[name]:
            sample = [result for config, result in zip(configs, results) if config[name] == value]
            expectancies = [row["expectancy_C1"] for row in sample if row["expectancy_C1"] is not None]
            sensitivity.append({"parameter": name, "value": value, "configurations": len(sample),
                                "positive_C1_share": sum(x > 0 for x in expectancies) / len(expectancies),
                                "mean_expectancy_C1": sum(expectancies) / len(expectancies)})
    output.mkdir(parents=True, exist_ok=True)
    experiment = {"phase": "PHASE_2_OPTIMIZATION", "methodological_source": "original H1 Phase 3.2",
                  "strategy": STRATEGY, "strategy_id": STRATEGY_ID, "timeframe": timeframe,
                  "optimization_design": "BASELINE_PLUS_ONE_FACTOR_AT_A_TIME",
                  "baseline": BASELINE, "parameter_space": PARAMETER_SPACE,
                  "tested_configurations": 19, "instruments": list(INSTRUMENTS),
                  "cost_models": [COST_MODEL], "development_interval": ["2020-01-01", "2024-12-31"],
                  "experiment_id": f"phase2a-{timeframe}-{stable_hash({'timeframe': timeframe, 'baseline': BASELINE, 'space': PARAMETER_SPACE})[:20]}"}
    manifest = {**experiment, "frozen_strategy_hash": STRATEGY_HASH,
                "canonical_baseline_parameter_hash": stable_hash(asdict(T2Parameters())),
                "actual_source_availability": provenance,
                "normalized_research_tick": FROZEN_TICK_SIZE, "C1_only": True,
                "true_oos_blocked": True, "selection_objective": "PLATEAU_NOT_MAXIMUM_PF",
                "ranking": False, "candidate_selection": False, "robustness": False,
                "walk_forward": False, "true_oos_execution": False, "phase7_mtf_research": False,
                "source_data_copied": False, "phase1_reference_commit": PHASE1_COMMIT,
                "overall": overall}
    for filename, value in (("manifest.json", manifest), ("experiment.json", experiment)):
        (output / filename).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    _csv(output / "parameters.csv", parameters); _csv(output / "results.csv", results)
    _csv(output / "plateau_report.csv", plateau); _csv(output / "sensitivity_report.csv", sensitivity)
    robust = [row for row in plateau if row["classification"] == "ROBUST_PLATEAU"]
    region_lines = ["# T2 / " + timeframe + " Stable Regions", "", f"**Classification:** {overall}", "",
                    "Complete ROBUST_PLATEAU region (not ranked; no winner selected):", ""]
    region_lines += ([f"- `{row['configuration_id']}`" for row in robust] if robust else ["- None."])
    (output / "best_regions.md").write_text("\n".join(region_lines) + "\n")
    recommendation = {"ROBUST_PLATEAU": "ROBUST_CANDIDATE", "LOCAL_SPIKE": "CONTINUE_RESEARCH", "NO_EDGE": "NO_EDGE"}[overall]
    (output / "final_report.md").write_text(
        f"# T2 / {timeframe} Phase 2 Optimization\n\n- Configurations: 19\n- Instruments per configuration: 6\n"
        f"- Cost: C1 only\n- Overall: **{overall}**\n- Recommendation: **{recommendation}**\n\n"
        "The complete stable region is reported without ranking or candidate selection. TRUE OOS was not read.\n")
    return {"timeframe": timeframe, "overall": overall, "robust_configurations": len(robust),
            "recommendation": recommendation}


def run(data_root: Path = DATA_ROOT, output: Path = OUTPUT_ROOT) -> dict[str, Any]:
    verify_strategy()  # Must precede every market-data open.
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    studies = [run_study(timeframe, Path(data_root), output / timeframe) for timeframe in TIMEFRAMES]
    (output / "manifest.json").write_text(json.dumps({"phase": "PHASE_2_OPTIMIZATION", "strategy": "T2",
        "timeframes": list(TIMEFRAMES), "studies": 2, "configurations_per_study": 19,
        "total_configuration_studies": 38, "candidate_selection": False,
        "true_oos_blocked": True}, indent=2, sort_keys=True) + "\n")
    lines = ["# T2 Phase 2A Optimization Report", "", "Two independent bounded OAT studies; no ranking or candidate selection.", "",
             "| Timeframe | Configurations | Overall | Robust region size | Recommendation |", "|---|---:|---|---:|---|"]
    lines += [f"| {row['timeframe']} | 19 | {row['overall']} | {row['robust_configurations']} | {row['recommendation']} |" for row in studies]
    lines += ["", "T2 Phase 2A only. T3, robustness, walk-forward, TRUE OOS, portfolio selection, and Phase 7 were not executed.", ""]
    (output / "T2_Optimization_Report.md").write_text("\n".join(lines))
    return {"status": "T2_PHASE_2A_EXECUTED", "studies": studies}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(); print(json.dumps(run(args.data_root, args.output), sort_keys=True))


if __name__ == "__main__": main()
