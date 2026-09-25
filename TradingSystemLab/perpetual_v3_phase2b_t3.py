"""TradingSystemLab v3 perpetual Phase 2B: T3 M30/H1 bounded OAT optimization."""
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

from .perpetual_v3_baseline import (DATA_COMMIT, DATA_ROOT, FROZEN_TICK_SIZE, INSTRUMENTS,
                                      TRUE_OOS_START, four_bar_context, load_development)
from .core.backtester import Backtester
from .core.portfolio import FixedRiskPortfolio
from .core.unified_metrics import concentration, finite, stats
from .strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters
from .optimization.experiment import stable_hash
from .optimization.phase32 import _normalize_backtester

OUTPUT_ROOT = Path("TradingSystemLab/results/perpetual_v3/optimization/T3")
TIMEFRAMES = ("M30", "H1")
STRATEGY = "T3"
STRATEGY_ID = "T3_MTF_Trend_v1.0"
STRATEGY_HASH = "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"
PHASE1_COMMIT = "f8ee11841eedb11cb6ec98debc74ad8bc8c0c8a9"
PHASE1_AUDIT_COMMIT = "a9c9815a9865a2c20fa555292de2c9924aadca96"
PHASE2A_T2_COMMIT = "7559953fd3dda8582af17f747ee38d94a93c42ad"
PHASE1_ROOT = Path("TradingSystemLab/results/perpetual_v3/baseline/T3")
COST_MODEL = {"name": "C1", "ticks_per_side": 1, "round_trip_ticks": 2,
              "additional_slippage_ticks": 0}
PARAMETER_SPACE = {
    "ema_period": [50, 75, 100, 150, 200],
    "adx_threshold": [15, 20, 25, 30],
    "breakout_period": [10, 20, 30, 40, 55],
    "atr_average_period": [10, 20, 30, 50],
    "stop_atr": [1.5, 2.0, 2.5, 3.0],
    "trail_atr": [2.0, 2.5, 3.0, 3.5, 4.0],
}
BASELINE = {name: getattr(T3Parameters(), name) for name in PARAMETER_SPACE}


def verify_strategy(project_root: Path = Path(".")) -> None:
    path = project_root / "TradingSystemLab/strategies/trend/T3_MTF_Trend.py"
    if hashlib.sha256(path.read_bytes()).hexdigest() != STRATEGY_HASH:
        raise RuntimeError("T3_FROZEN_STRATEGY_HASH_MISMATCH")


def bounded_design() -> list[dict[str, Any]]:
    rows = [dict(BASELINE)]
    for name in PARAMETER_SPACE:  # declaration order is canonical
        rows.extend({**BASELINE, name: value} for value in PARAMETER_SPACE[name]
                    if value != BASELINE[name])
    if len(rows) != 22 or len({stable_hash(row) for row in rows}) != 22:
        raise RuntimeError("T3_OAT_DESIGN_INVALID")
    return rows


def configuration_id(timeframe: str, config: Mapping[str, Any]) -> str:
    return f"T3-{timeframe}-{stable_hash(dict(config))[:12]}"


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
    for year in (2023, 2024):
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
    pieces = []
    for instrument in INSTRUMENTS:
        execution = frames[instrument]
        context = four_bar_context(execution)
        if context is execution or len(context) and context.index.max() >= TRUE_OOS_START:
            raise RuntimeError("T3_CONTEXT_CAUSALITY_VIOLATION")
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=1,
                         tick_size=FROZEN_TICK_SIZE).run(
            T3MTFTrend(replace(T3Parameters(), **config)), instrument, execution, context).trades
        trades = _normalize_backtester(raw, STRATEGY)
        trades["net_R_C1"] = trades["gross_R"] - trades["cost_R"]
        pieces.append(trades)
    trades = pd.concat(pieces, ignore_index=True)
    if len(trades):
        trades = trades.sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
        dates = pd.concat([pd.to_datetime(trades.entry_time, utc=True),
                           pd.to_datetime(trades.exit_time, utc=True)])
        if (dates >= TRUE_OOS_START.tz_convert("UTC")).any():
            raise RuntimeError("TRUE_OOS_TRADE_VIOLATION")
    return trades


_WORKER_FRAMES: Mapping[str, pd.DataFrame] | None = None


def _worker(task: tuple[dict[str, Any], str]) -> dict[str, Any]:
    if _WORKER_FRAMES is None:
        raise RuntimeError("T3_WORKER_DATA_NOT_INITIALIZED")
    config, cid = task
    return _metrics(cid, _execute(config, _WORKER_FRAMES))


def run_study(timeframe: str, data_root: Path, output: Path) -> dict[str, Any]:
    if timeframe not in TIMEFRAMES:
        raise ValueError("PHASE_2B_ALLOWS_ONLY_M30_AND_H1")
    frames, provenance = {}, []
    for instrument in INSTRUMENTS:
        frame, source = load_development(data_root, instrument, timeframe)
        frames[instrument] = frame
        provenance.append({"instrument": instrument, "source_file": str(source),
                           "first_close": frame.index.min().isoformat(),
                           "last_close": frame.index.max().isoformat(), "rows": len(frame)})
    configs = bounded_design()
    parameters = [{"configuration_id": configuration_id(timeframe, config),
                   "is_baseline": config == BASELINE, **config} for config in configs]
    tasks = [(config, configuration_id(timeframe, config)) for config in configs]
    global _WORKER_FRAMES
    _WORKER_FRAMES = frames
    with mp.get_context("fork").Pool(processes=min(8, len(tasks))) as pool:
        results = pool.map(_worker, tasks)
    _WORKER_FRAMES = None
    plateau, overall = classify(configs, results)
    sensitivity = []
    for name in PARAMETER_SPACE:
        for value in PARAMETER_SPACE[name]:
            sample = [result for config, result in zip(configs, results) if config[name] == value]
            values = [row["expectancy_C1"] for row in sample if row["expectancy_C1"] is not None]
            sensitivity.append({"parameter": name, "value": value, "configurations": len(sample),
                                "positive_C1_share": sum(x > 0 for x in values) / len(values),
                                "mean_expectancy_C1": sum(values) / len(values)})
    output.mkdir(parents=True, exist_ok=True)
    experiment = {"phase": "PHASE_2_OPTIMIZATION", "methodological_source": "original H1 Phase 3.2",
                  "strategy": STRATEGY, "strategy_id": STRATEGY_ID, "timeframe": timeframe,
                  "optimization_design": "BASELINE_PLUS_ONE_FACTOR_AT_A_TIME",
                  "baseline": BASELINE, "parameter_space": PARAMETER_SPACE,
                  "tested_configurations": 22, "instruments": list(INSTRUMENTS),
                  "cost_models": [COST_MODEL], "development_interval": ["2023-01-01", "2024-12-31"],
                  "experiment_id": f"phase2b-{timeframe}-{stable_hash({'timeframe': timeframe, 'baseline': BASELINE, 'space': PARAMETER_SPACE})[:20]}"}
    manifest = {**experiment, "frozen_strategy_hash": STRATEGY_HASH,
                "canonical_baseline_parameter_hash": stable_hash(asdict(T3Parameters())),
                "actual_source_availability": provenance, "context": "four completed execution bars; local-day reset",
                "normalized_research_tick": FROZEN_TICK_SIZE, "C1_only": True,
                "true_oos_blocked": True, "selection_objective": "PLATEAU_NOT_MAXIMUM_PF",
                "ranking": False, "candidate_selection": False, "robustness": False,
                "walk_forward": False, "true_oos_execution": False, "phase7_mtf_research": False,
                "source_data_copied": False, "data_commit": DATA_COMMIT, "phase1_reference_commit": PHASE1_COMMIT,
                "phase1_audit_reference_commit": PHASE1_AUDIT_COMMIT,
                "phase2a_t2_reference_commit": PHASE2A_T2_COMMIT, "overall": overall}
    for filename, value in (("manifest.json", manifest), ("experiment.json", experiment)):
        (output / filename).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    _csv(output / "parameters.csv", parameters)
    _csv(output / "results.csv", results)
    _csv(output / "plateau_report.csv", plateau)
    _csv(output / "sensitivity_report.csv", sensitivity)
    robust = [row for row in plateau if row["classification"] == "ROBUST_PLATEAU"]
    lines = [f"# T3 / {timeframe} Stable Regions", "", f"**Classification:** {overall}", "",
             "Complete ROBUST_PLATEAU region (not ranked; no winner selected):", ""]
    lines += [f"- `{row['configuration_id']}`" for row in robust] if robust else ["- None."]
    (output / "best_regions.md").write_text("\n".join(lines) + "\n")
    baseline = next(row for row, config in zip(results, configs) if config == BASELINE)
    (output / "final_report.md").write_text(
        f"# T3 / {timeframe} Phase 2 Optimization\n\n- Configurations: 22\n- Instruments per configuration: 4\n"
        f"- Cost: C1 only\n- Baseline trades: {baseline['trades']}\n- Baseline PF: {baseline['PF_C1']}\n"
        f"- Baseline expectancy: {baseline['expectancy_C1']}\n- Baseline Net R: {baseline['net_R_C1']}\n"
        f"- Baseline Max DD: {baseline['max_DD_C1']}\n- Overall: **{overall}**\n"
        f"- ROBUST_PLATEAU configurations: {len(robust)}\n\n"
        "Separate causal T3 context was used. No ranking or candidate selection was performed. TRUE OOS was not read. Robustness was not executed.\n")
    return {"timeframe": timeframe, "overall": overall, "robust_configurations": len(robust),
            "baseline": baseline}


def reconcile_phase1(studies: list[dict[str, Any]]) -> None:
    for study in studies:
        pieces = [pd.read_csv(PHASE1_ROOT / study["timeframe"] / symbol / "trades.csv")
                  for symbol in INSTRUMENTS]
        trades = pd.concat(pieces, ignore_index=True).sort_values(
            ["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
        expected = _metrics("phase1", trades.rename(columns={"net_R": "net_R_C1"}))
        for key in ("trades", "PF_C1", "expectancy_C1", "net_R_C1", "max_DD_C1",
                    "recovery_factor_C1", "win_rate_C1"):
            actual = study["baseline"][key]
            if pd.isna(expected[key]) and pd.isna(actual):
                continue
            if abs(float(expected[key]) - float(actual)) > 1e-10:
                raise RuntimeError(f"PHASE1_BASELINE_RECONCILIATION_FAILED:{study['timeframe']}:{key}")


def run(data_root: Path = DATA_ROOT, output: Path = OUTPUT_ROOT) -> dict[str, Any]:
    verify_strategy()  # before any market-data open
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    studies = [run_study(tf, Path(data_root), output / tf) for tf in TIMEFRAMES]
    reconcile_phase1(studies)
    manifest = {"generation": "v3_perpetual", "phase": "PHASE_2_OPTIMIZATION", "subphase": "PHASE_2B_T3",
        "strategy": "T3", "strategy_source_hash": STRATEGY_HASH, "timeframes": list(TIMEFRAMES),
        "instruments": list(INSTRUMENTS), "development_period": ["2023-01-01", "2024-12-31"],
        "data_commit": DATA_COMMIT, "phase1_reference_merge": PHASE1_COMMIT,
        "phase1_audit_reference_merge": PHASE1_AUDIT_COMMIT, "phase2a_t2_reference_merge": PHASE2A_T2_COMMIT,
        "optimization_design": "BASELINE_PLUS_ONE_FACTOR_AT_A_TIME", "configurations_per_study": 22,
        "studies": 2, "total_configuration_studies": 44, "C1_only": True,
        "normalized_research_tick": FROZEN_TICK_SIZE, "true_oos_start": "2025-01-01",
        "true_oos_blocked": True, "ranking": False, "candidate_selection": False,
        "robustness": False, "walk_forward": False, "true_oos_execution": False, "mtf": False,
        "status": "V3_PERPETUAL_PHASE_2B_T3_COMPLETE"}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    lines = ["# T3 Phase 2B Optimization Report", "", "Two independent bounded OAT studies; no ranking or candidate selection.", "",
        "| Timeframe | Configurations | Baseline trades | Baseline PF | Baseline expectancy | Baseline Net R | Baseline Max DD | Overall classification | ROBUST_PLATEAU count |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|"]
    for row in studies:
        b = row["baseline"]
        lines.append(f"| {row['timeframe']} | 22 | {b['trades']} | {b['PF_C1']} | {b['expectancy_C1']} | {b['net_R_C1']} | {b['max_DD_C1']} | {row['overall']} | {row['robust_configurations']} |")
    lines += ["", "T3 Phase 2B only. Robustness, walk-forward, TRUE OOS, candidate freezing, and Phase 2 consolidation were not executed.", ""]
    (output / "T3_Optimization_Report.md").write_text("\n".join(lines))
    return {"status": manifest["status"], "studies": studies}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    print(json.dumps(run(args.data_root, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
