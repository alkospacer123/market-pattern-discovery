"""Standalone D1 bounded optimization adapted directly from H1 Phase 3.2.

This module deliberately owns its OAT design and plateau analysis.  It reuses
only the audited D1 baseline's data construction and execution adapter.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping

import pandas as pd

from ..core.unified_metrics import concentration, finite, stats
from ..timeframe_validation import d1_baseline as baseline
from .experiment import stable_hash

PHASE = "D1_OPTIMIZATION"
STATUS = "PHASE_D1_OPTIMIZATION_COMPLETE"
TIMEFRAME = "D1"
METHODOLOGICAL_SOURCE = "H1_PHASE_3_2"
CANONICAL_BASELINE_MERGE = "132c64158a7a28dbe66a1e2bbd2629dc3144eb01"
BASELINE_ROOT = Path("TradingSystemLab/results/timeframe_validation/D1")
OUTPUT = Path("TradingSystemLab/results/timeframe_optimization/D1")
PARITY_COLUMNS = ["instrument", "direction", "entry_time", "exit_time", "gross_R",
                  "initial_risk_ticks", "MAE_R", "MFE_R", "net_R"]
EXPECTED_METRICS = {
    "T2": {"trades": 5, "PF_C1": 0.15481193472217664,
           "expectancy_C1": -0.5860820992494725, "net_R_C1": -2.9304104962473625,
           "max_DD_C1": -3.4671697538512944},
    "T3": {"trades": 4, "PF_C1": 0.10221688504312515,
           "expectancy_C1": -0.37138898566927836, "net_R_C1": -1.4855559426771134,
           "max_DD_C1": -1.4855559426771134},
}
SPACES: dict[str, dict[str, list[Any]]] = {
    "T2": {"ema_fast": [15, 20, 25, 30], "ema_trend": [40, 50, 60],
           "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25, 30],
           "impulse_distance_atr": [.3, .5, .7], "confirmation_window": [2, 3, 4],
           "max_initial_stop_atr": [2., 2.5, 3.], "trailing_atr": [2., 3., 4.]},
    "T3": {"ema_period": [50, 75, 100, 150, 200], "adx_threshold": [15, 20, 25, 30],
           "breakout_period": [10, 20, 30, 40, 55], "atr_average_period": [10, 20, 30, 50],
           "stop_atr": [1.5, 2., 2.5, 3.], "trail_atr": [2., 2.5, 3., 3.5, 4.]},
}
EXPECTED_COUNTS = {"T2": 19, "T3": 22}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    pd.DataFrame(rows).map(finite).to_csv(path, index=False, lineterminator="\n",
                                           float_format="%.12g", na_rep="")


def bounded_design(key: str) -> list[dict[str, Any]]:
    """H1 Phase 3.2 baseline plus every single-factor perturbation."""
    center = baseline.EXPECTED[key]["parameters"]
    rows = [dict(center)]
    for name in sorted(SPACES[key]):
        rows.extend({**center, name: value} for value in SPACES[key][name] if value != center[name])
    rows = sorted(rows, key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
    if len(rows) != EXPECTED_COUNTS[key] or sum(row == center for row in rows) != 1:
        raise RuntimeError("D1_OPTIMIZATION_OAT_DESIGN_INVALID")
    if any(sum(row[name] != center[name] for name in SPACES[key]) > 1 for row in rows):
        raise RuntimeError("D1_OPTIMIZATION_CARTESIAN_DESIGN_FORBIDDEN")
    return rows


def immediate_neighbors(configs: list[dict[str, Any]], index: int, key: str) -> list[int]:
    """Return rows differing at exactly one adjacent declared parameter level."""
    found = []
    for other_index, other in enumerate(configs):
        differing = [name for name in SPACES[key] if configs[index][name] != other[name]]
        if len(differing) == 1:
            name = differing[0]
            levels = SPACES[key][name]
            if abs(levels.index(configs[index][name]) - levels.index(other[name])) == 1:
                found.append(other_index)
    return found


def classify(configs: list[dict[str, Any]], results: list[dict[str, Any]], key: str
             ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    plateau = []
    for index, result in enumerate(results):
        neighbors = immediate_neighbors(configs, index, key)
        expectancy = result["expectancy_C1"]
        positive = expectancy is not None and expectancy > 0
        positive_neighbors = [j for j in neighbors if results[j]["expectancy_C1"] is not None
                              and results[j]["expectancy_C1"] > 0]
        threshold = max(.01, abs(expectancy) * .35) if positive else None
        stable = [j for j in positive_neighbors
                  if abs(results[j]["expectancy_C1"] - expectancy) <= threshold] if positive else []
        label = "ROBUST_PLATEAU" if positive and len(stable) >= 2 else (
            "LOCAL_SPIKE" if positive else "NO_EDGE")
        plateau.append({"configuration_id": result["configuration_id"],
                        "expectancy_C1": expectancy, "PF_C1": result["PF_C1"],
                        "neighbor_count": len(neighbors),
                        "positive_neighbor_count": len(positive_neighbors),
                        "stable_positive_neighbor_count": len(stable),
                        "stability_threshold": threshold,
                        "immediate_neighbor_ids": "|".join(results[j]["configuration_id"] for j in neighbors),
                        "classification": label})
    sensitivity = []
    for name, levels in SPACES[key].items():
        for value in levels:
            sample = [result for config, result in zip(configs, results) if config[name] == value]
            values = [row["expectancy_C1"] for row in sample if row["expectancy_C1"] is not None]
            sensitivity.append({"parameter": name, "value": value, "configurations": len(sample),
                                "positive_C1_share": sum(v > 0 for v in values) / len(values) if values else None,
                                "mean_expectancy_C1": sum(values) / len(values) if values else None})
    overall = ("ROBUST_PLATEAU" if any(row["classification"] == "ROBUST_PLATEAU" for row in plateau)
               else "LOCAL_SPIKE" if any(row["classification"] == "LOCAL_SPIKE" for row in plateau)
               else "NO_EDGE")
    return plateau, sensitivity, overall


def _slice_metrics(values: pd.Series) -> dict[str, Any]:
    metric = stats(values.astype(float))
    return {"trades": metric["trades"], "PF": metric["PF_R"],
            "expectancy": metric["expectancy"], "net_R": metric["net_R"],
            "max_DD": metric["max_DD_R"], "recovery_factor": metric["recovery_factor"],
            "win_rate": metric["winrate"]}


def metric_row(configuration_id: str, trades: pd.DataFrame) -> dict[str, Any]:
    net = trades.net_R.astype(float) if len(trades) else pd.Series(dtype=float)
    aggregate = _slice_metrics(net)
    row = {"configuration_id": configuration_id, "trades": aggregate.pop("trades"),
           **{f"{name}_C1": value for name, value in aggregate.items()}}
    years = pd.to_datetime(trades.exit_time, utc=True).dt.year if len(trades) else pd.Series(dtype=int)
    slices = [("instrument", name, trades.instrument.eq(name)) for name, _ in baseline.INSTRUMENTS]
    slices += [("year", str(year), years.eq(year)) for year in (2023, 2024)]
    slices += [("direction", direction, trades.direction.eq(direction)) for direction in ("LONG", "SHORT")]
    for kind, name, mask in slices:
        for metric, value in _slice_metrics(net[mask]).items():
            row[f"{kind}_{name}_{metric}"] = value
    row.update(concentration(net))
    return {name: finite(value) for name, value in row.items()}


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, text=True, capture_output=True).stdout.strip()


def verify_baseline_prerequisite(project_root: Path = Path("."), data_root: Path = baseline.APPROVED_DATA_ROOT
                                 ) -> tuple[dict[str, Any], dict[str, pd.DataFrame], list[dict[str, str]]]:
    """Fail closed before execution unless baseline, strategies and sources are exact."""
    manifest_path = project_root / BASELINE_ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != baseline.STATUS or manifest.get("timeframe") != TIMEFRAME:
        raise RuntimeError("D1_OPTIMIZATION_BASELINE_MANIFEST_INVALID")
    if _git("diff", "--name-only", CANONICAL_BASELINE_MERGE, "--", str(BASELINE_ROOT)):
        raise RuntimeError("D1_OPTIMIZATION_BASELINE_TREE_MISMATCH")
    baseline.verify_frozen_strategies(project_root)
    candidates = baseline.frozen_candidates(project_root / baseline.REGISTRY)
    for key in ("T2", "T3"):
        recorded = manifest["candidates"][key]
        expected = baseline.EXPECTED[key]
        if (recorded["candidate_id"] != expected["candidate_id"] or
                recorded["phase32_configuration_id"] != expected["phase32_configuration_id"] or
                recorded["parameter_hash"] != expected["parameter_hash"] or
                recorded["strategy_hash"] != baseline.STRATEGY_SHA256[key] or
                candidates[key]["parameters"] != expected["parameters"]):
            raise RuntimeError("D1_OPTIMIZATION_BASELINE_PROVENANCE_MISMATCH")
    loaded: dict[str, pd.DataFrame] = {}
    inventory = []
    for instrument, alias in baseline.INSTRUMENTS:
        frame, paths = baseline.load_h1_development(data_root, alias)
        if frame is None:
            raise RuntimeError("D1_OPTIMIZATION_SOURCE_HASH_MISMATCH")
        loaded[alias] = frame
        inventory.extend({"instrument": instrument, "alias": alias, "filename": path.name,
                          "sha256": _sha(path)} for path in paths)
    if inventory != manifest.get("source_files"):
        raise RuntimeError("D1_OPTIMIZATION_SOURCE_HASH_MISMATCH")
    return manifest, loaded, inventory


def _serialized_ledger(frame: pd.DataFrame) -> str:
    return frame[PARITY_COLUMNS].to_csv(index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def verify_center_parity(key: str, trades: pd.DataFrame, project_root: Path = Path(".")) -> None:
    committed = pd.read_csv(project_root / BASELINE_ROOT / key / "trades.csv")
    if _serialized_ledger(trades) != _serialized_ledger(committed):
        raise RuntimeError(f"D1_OPTIMIZATION_{key}_CENTER_LEDGER_PARITY_FAILURE")
    actual = metric_row("CENTER", trades)
    for name, expected in EXPECTED_METRICS[key].items():
        if actual[name] != expected:
            raise RuntimeError(f"D1_OPTIMIZATION_{key}_CENTER_METRIC_PARITY_FAILURE")


def _execute(key: str, parameters: Mapping[str, Any], loaded: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    pieces = [baseline._execute(key, dict(parameters), alias, loaded[alias])  # noqa: SLF001
              for _, alias in baseline.INSTRUMENTS]
    trades = pd.concat(pieces, ignore_index=True)
    if len(trades):
        trades = trades.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
        trades["year"] = pd.to_datetime(trades.exit_time, utc=True).dt.year
    return trades


def _run_strategy(key: str, loaded: Mapping[str, pd.DataFrame], target: Path) -> dict[str, Any]:
    target.mkdir(parents=True)
    configs = bounded_design(key)
    parameter_rows, results = [], []
    for number, config in enumerate(configs):
        parameter_hash = stable_hash(config)
        configuration_id = f"{key}-D1-{number:04d}-{parameter_hash[:12]}"
        is_center = config == baseline.EXPECTED[key]["parameters"]
        trades = _execute(key, config, loaded)
        if is_center:
            verify_center_parity(key, trades)
        parameter_rows.append({"configuration_id": configuration_id, "parameter_hash": parameter_hash,
                               "baseline_configuration": is_center, **config})
        results.append(metric_row(configuration_id, trades))
    plateau, sensitivity, overall = classify(configs, results, key)
    labels = {row["configuration_id"]: row["classification"] for row in plateau}
    for row in results:
        row["classification"] = labels[row["configuration_id"]]
    center = next(row for row, parameters in zip(results, parameter_rows)
                  if parameters["baseline_configuration"])
    counts = {label: sum(row["classification"] == label for row in plateau)
              for label in ("ROBUST_PLATEAU", "LOCAL_SPIKE", "NO_EDGE")}
    summary = {"strategy": key, "tested_configurations": len(configs),
               "baseline_configuration_id": center["configuration_id"],
               "baseline_parity": "EXACT", "overall_classification": overall, **counts}
    experiment = {"phase": PHASE, "methodological_source": METHODOLOGICAL_SOURCE,
                  "strategy": key, "design": "BASELINE_PLUS_ONE_FACTOR_AT_A_TIME",
                  "parameter_space": SPACES[key], "center": baseline.EXPECTED[key]["parameters"],
                  "tested_configurations": len(configs), "cartesian_grid": False,
                  "one_factor_at_a_time": True, "cost_scenarios": {"C1": 1.0},
                  "development_period": ["2023-01-01", "2024-12-31"], "true_oos_blocked": True}
    manifest = {**summary, "phase": PHASE, "status": STATUS, "timeframe": TIMEFRAME,
                "methodological_source": METHODOLOGICAL_SOURCE, "ranking": False,
                "selection": False, "winner_selection": False, "robustness": False,
                "walk_forward": False, "true_oos_blocked": True, "C1_only": True,
                "deterministic_execution": True}
    _json(target / "manifest.json", manifest); _json(target / "experiment.json", experiment)
    _csv(target / "parameters.csv", parameter_rows); _csv(target / "results.csv", results)
    _csv(target / "plateau_report.csv", plateau); _csv(target / "sensitivity_report.csv", sensitivity)
    _csv(target / "metrics_summary.csv", [summary])
    robust = [(parameters, result) for parameters, result in zip(parameter_rows, results)
              if result["classification"] == "ROBUST_PLATEAU"]
    details = "\n".join(f"- `{result['configuration_id']}`: " +
                         ", ".join(f"{name}={parameters[name]}" for name in SPACES[key])
                         for parameters, result in robust) or "- None."
    (target / "best_regions.md").write_text(
        f"# {key} D1 Stable Regions\n\nNo ranking or winner selection was performed.\n\n{details}\n", encoding="utf-8")
    (target / "final_report.md").write_text(
        f"# {key} D1 Optimization\n\n- OAT configurations: {len(configs)}\n"
        f"- Center parity: EXACT\n- Overall classification: **{overall}**\n"
        f"- ROBUST_PLATEAU / LOCAL_SPIKE / NO_EDGE: {counts['ROBUST_PLATEAU']} / "
        f"{counts['LOCAL_SPIKE']} / {counts['NO_EDGE']}\n\nNo candidate was ranked or selected.\n", encoding="utf-8")
    return summary


def run(data_root: Path = baseline.APPROVED_DATA_ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    baseline_manifest, loaded, inventory = verify_baseline_prerequisite(data_root=data_root)
    protected = tuple(path for path in baseline.PROTECTED_ARTIFACTS
                      if path != Path("TradingSystemLab/results/timeframe_optimization")) + (BASELINE_ROOT,)
    before = {str(path): baseline.hash_tree(path) for path in protected}
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = [_run_strategy(key, loaded, output / key) for key in ("T2", "T3")]
    after = {str(path): baseline.hash_tree(path) for path in protected}
    if before != after:
        raise RuntimeError("PROTECTED_RESEARCH_ARTIFACT_MUTATION")
    manifest = {"phase": PHASE, "status": STATUS, "timeframe": TIMEFRAME,
        "methodological_source": METHODOLOGICAL_SOURCE,
        "development_period": ["2023-01-01", "2024-12-31"], "true_oos_cutoff": "2025-01-01",
        "canonical_d1_baseline_merge": CANONICAL_BASELINE_MERGE,
        "d1_baseline_manifest_sha256": _sha(BASELINE_ROOT / "manifest.json"),
        "d1_baseline_trade_ledger_sha256": {key: _sha(BASELINE_ROOT / key / "trades.csv") for key in ("T2", "T3")},
        "baseline_parity": {"T2": "EXACT", "T3": "EXACT"}, "source_files": inventory,
        "candidates": baseline_manifest["candidates"], "parameter_spaces": SPACES,
        "tested_configurations": EXPECTED_COUNTS, "cartesian_grid": False,
        "one_factor_at_a_time": True, "cost_model": {"scenario": "C1", "ticks_per_side": 1.0,
        "round_trip_ticks": 2.0, "additional_slippage_ticks": 0.0},
        "ranking": False, "selection": False, "winner_selection": False, "robustness": False,
        "walk_forward": False, "true_oos_blocked": True, "parameter_space_expansion": False,
        "strategy_change": False, "deterministic_execution": True,
        "protected_research_unchanged": True, "strategies": {row["strategy"]: row for row in summaries}}
    _json(output / "manifest.json", manifest)
    lines = ["# D1 Standalone Optimization", "", "H1 Phase 3.2 bounded OAT methodology; C1 only.", ""]
    for row in summaries:
        lines += [f"## {row['strategy']}", f"- Tested configurations: {row['tested_configurations']}",
                  f"- Center parity: {row['baseline_parity']}",
                  f"- Overall classification: **{row['overall_classification']}**",
                  f"- ROBUST_PLATEAU / LOCAL_SPIKE / NO_EDGE: {row['ROBUST_PLATEAU']} / "
                  f"{row['LOCAL_SPIKE']} / {row['NO_EDGE']}", ""]
    lines += ["No ranking, candidate selection, Robustness, Walk Forward, or TRUE OOS was performed.", "", STATUS, ""]
    (output / "d1_optimization_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": STATUS, "strategies": summaries}
