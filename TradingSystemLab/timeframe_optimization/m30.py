"""Strict M30 bounded-OAT optimization derived from H1 Phase 3.2.

This module deliberately reuses the audited M30 baseline loader and execution
function.  It never opens a 2025 file and it does not select a winner.
"""
from __future__ import annotations

import hashlib
import io
import json
import multiprocessing as mp
from pathlib import Path
import shutil
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ..core.unified_metrics import concentration, finite, stats
from ..multitimeframe.phase71 import APPROVED_DATA_ROOT, STRATEGY_SHA256, verify_frozen_strategies
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..timeframe_validation import m30_baseline as baseline

PHASE = "M30_OPTIMIZATION"
STATUS = "PHASE_M30_OPTIMIZATION_COMPLETE"
OUTPUT = Path("TradingSystemLab/results/timeframe_optimization/M30")
BASELINE_MANIFEST = Path("TradingSystemLab/results/timeframe_validation/M30/manifest.json")
DEVELOPMENT_PERIOD = ["2023-01-01", "2024-12-31"]
TRUE_OOS_CUTOFF = "2025-01-01"
LEDGER_COLUMNS = ["instrument", "direction", "entry_time", "exit_time", "gross_R",
                  "initial_risk_ticks", "MAE_R", "MFE_R", "net_R"]

# Values and declaration order are exactly those in original H1 Phase 3.2.
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
EXPECTED_METRICS = {
    "T2": {"trades": 178, "PF": 1.4875514967448944, "expectancy_R": .22257128076651778,
           "net_R": 39.617687976440166, "max_drawdown_R": -15.0847664713036},
    "T3": {"trades": 235, "PF": 2.002689330888746, "expectancy_R": .425920854548717,
           "net_R": 100.09140081894849, "max_drawdown_R": -17.864697983339333},
}

# The output itself is intentionally absent.  Every prior research tree,
# including the prerequisite, is read-only for this phase.
PROTECTED = tuple(Path(p) for p in (
    "TradingSystemLab/results/optimization", "TradingSystemLab/results/robustness_validation",
    "TradingSystemLab/results/timeframe_validation", "TradingSystemLab/results/timeframe_analysis",
    "TradingSystemLab/results/timeframe_diagnostics", "TradingSystemLab/results/multitimeframe_research",
    "TradingSystemLab/results/walk_forward", "TradingSystemLab/results/true_oos_validation",
    "TradingSystemLab/results/T2_implementation_check", "TradingSystemLab/results/T3_robust"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounded_design(key: str) -> list[dict[str, Any]]:
    """Return the frozen center once plus every single-factor perturbation."""
    center = dict(baseline.EXPECTED[key]["parameters"])
    unique = {stable_hash(center): center}
    for name in sorted(SPACES[key]):
        for value in SPACES[key][name]:
            if value != center[name]:
                unique[stable_hash({**center, name: value})] = {**center, name: value}
    rows = sorted(unique.values(), key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")))
    if len(rows) != EXPECTED_COUNTS[key]:
        raise RuntimeError(f"{key}_OAT_COUNT_MISMATCH")
    return rows


def configuration_rows(key: str) -> list[dict[str, Any]]:
    center = baseline.EXPECTED[key]["parameters"]
    return [{"configuration_id": f"{key}-M30-{i:04d}-{stable_hash(cfg)[:12]}",
             "parameter_hash": stable_hash(cfg), "baseline_configuration": cfg == center, **cfg}
            for i, cfg in enumerate(bounded_design(key))]


def immediate_neighbors(configs: list[dict[str, Any]], index: int, key: str) -> list[int]:
    names = list(SPACES[key])
    found = []
    for j, other in enumerate(configs):
        differing = [name for name in names if configs[index][name] != other[name]]
        if len(differing) == 1:
            name = differing[0]
            order = SPACES[key][name]
            if abs(order.index(configs[index][name]) - order.index(other[name])) == 1:
                found.append(j)
    return found


def classify(expectancy: float | None, neighbor_expectancies: list[float | None]) -> tuple[int, int, str]:
    positive_neighbors = [x for x in neighbor_expectancies if x is not None and x > 0]
    positive = expectancy is not None and expectancy > 0
    threshold = max(.01, abs(expectancy) * .35) if positive else None
    stable = [x for x in positive_neighbors if abs(x - expectancy) <= threshold] if positive else []
    label = "ROBUST_PLATEAU" if positive and len(stable) >= 2 else ("LOCAL_SPIKE" if positive else "NO_EDGE")
    return len(positive_neighbors), len(stable), label


def _metrics(configuration_id: str, trades: pd.DataFrame) -> dict[str, Any]:
    values = trades.net_R.astype(float) if len(trades) else pd.Series(dtype=float)
    metric = stats(values)
    row = {"configuration_id": configuration_id, "trades": metric["trades"],
           "PF_C1": metric["PF_R"], "expectancy_C1": metric["expectancy"],
           "net_R_C1": metric["net_R"], "max_DD_C1": metric["max_DD_R"],
           "recovery_factor_C1": metric["recovery_factor"], "win_rate_C1": metric["winrate"]}
    for alias in ("Si", "CNY"):
        part = stats(values[trades.symbol.eq(alias)])
        row.update({f"{alias}_trades": part["trades"], f"{alias}_expectancy_C1": part["expectancy"]})
    years = pd.to_datetime(trades.exit_time, utc=True).dt.year if len(trades) else pd.Series(dtype=int)
    for year in (2023, 2024):
        part = stats(values[years.eq(year)])
        row.update({f"{year}_trades": part["trades"], f"{year}_expectancy_C1": part["expectancy"]})
    for direction in ("LONG", "SHORT"):
        part = stats(values[trades.direction.eq(direction)])
        row.update({f"{direction}_trades": part["trades"], f"{direction}_expectancy_C1": part["expectancy"]})
    conc = concentration(values)
    # Normalize the one legacy key to the requested artifact vocabulary.
    for label in ("best_trade", "top3", "top5"):
        conc[f"PF_C1_without_{label}"] = conc.pop(f"PF_R_C1_without_{label}")
    row.update(conc)
    return {k: finite(v) for k, v in row.items()}


_DATA: Mapping[str, pd.DataFrame] | None = None


def _execute_task(task: tuple[str, dict[str, Any], str]) -> dict[str, Any]:
    key, config, cid = task
    if _DATA is None:
        raise RuntimeError("M30_DATA_NOT_INITIALIZED")
    pieces = [baseline._execute(key, config, alias, _DATA[alias]) for _, alias in baseline.INSTRUMENTS]
    trades = pd.concat(pieces, ignore_index=True).sort_values(
        ["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    return _metrics(cid, trades)


def _csv(path: Path, rows: Any) -> None:
    pd.DataFrame(rows).map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _validate_prerequisites(data_root: Path) -> tuple[dict, dict[str, pd.DataFrame]]:
    manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))
    required = (manifest.get("status") == baseline.STATUS and manifest.get("timeframe") == "M30" and
                manifest.get("development_period") == DEVELOPMENT_PERIOD and
                manifest.get("true_oos_cutoff") == TRUE_OOS_CUTOFF and manifest.get("true_oos_blocked") is True)
    if not required:
        raise RuntimeError("M30_BASELINE_PROVENANCE_MISMATCH")
    verify_frozen_strategies()
    candidates = baseline.frozen_candidates()
    for key in ("T2", "T3"):
        recorded = manifest["candidates"][key]
        expected = baseline.EXPECTED[key]
        if (recorded["phase32_configuration_id"] != expected["phase32_configuration_id"] or
                recorded["parameter_hash"] != expected["parameter_hash"] or
                recorded["strategy_hash"] != STRATEGY_SHA256[key]):
            raise RuntimeError(f"{key}_BASELINE_IDENTITY_MISMATCH")
    loaded = {alias: baseline.load_m30_development(data_root, alias) for _, alias in baseline.INSTRUMENTS}
    if any(frame is None for frame, _ in loaded.values()):
        raise RuntimeError("DATA_UNAVAILABLE")
    actual_sources = []
    for instrument, alias in baseline.INSTRUMENTS:
        actual_sources.extend({"instrument": instrument, "alias": alias, "name": p.name, "sha256": _sha(p)}
                              for p in loaded[alias][1])
    if actual_sources != manifest["source_files"]:
        raise RuntimeError("M30_SOURCE_HASH_MISMATCH")
    return manifest, {alias: item[0] for alias, item in loaded.items()}


def _assert_baseline_parity(key: str, data: Mapping[str, pd.DataFrame], result: dict) -> None:
    pieces = [baseline._execute(key, baseline.EXPECTED[key]["parameters"], alias, data[alias])
              for _, alias in baseline.INSTRUMENTS]
    actual = pd.concat(pieces, ignore_index=True).sort_values(
        ["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    expected = pd.read_csv(baseline.OUTPUT / key / "trades.csv")
    # Compare the exact committed ledger representation.  The baseline contract
    # serializes floats at 12 significant digits and timezone values as text.
    serialized = io.StringIO()
    actual[LEDGER_COLUMNS].to_csv(serialized, index=False, lineterminator="\n", float_format="%.12g")
    serialized.seek(0)
    canonical_actual = pd.read_csv(serialized)
    pd.testing.assert_frame_equal(canonical_actual.reset_index(drop=True),
                                  expected[LEDGER_COLUMNS].reset_index(drop=True),
                                  check_dtype=False, check_exact=True)
    expected_metric = EXPECTED_METRICS[key]
    observed = {"trades": result["trades"], "PF": result["PF_C1"],
                "expectancy_R": result["expectancy_C1"], "net_R": result["net_R_C1"],
                "max_drawdown_R": result["max_DD_C1"]}
    if observed != expected_metric:
        raise RuntimeError(f"{key}_CENTRAL_METRIC_PARITY_FAILURE: {observed}")


def _reports(key: str, rows: list[dict], results: list[dict], target: Path,
             baseline_manifest: dict) -> dict[str, Any]:
    configs = [{name: row[name] for name in SPACES[key]} for row in rows]
    plateau = []
    for i, result in enumerate(results):
        neighbors = immediate_neighbors(configs, i, key)
        positive, stable, label = classify(result["expectancy_C1"], [results[j]["expectancy_C1"] for j in neighbors])
        plateau.append({"configuration_id": result["configuration_id"], "neighbor_count": len(neighbors),
                        "positive_neighbors": positive, "stable_neighbors": stable,
                        "classification": label, "expectancy_C1": result["expectancy_C1"], "PF_C1": result["PF_C1"]})
    sensitivity = []
    for name, values in SPACES[key].items():
        for value in values:
            sample = [res["expectancy_C1"] for cfg, res in zip(configs, results) if cfg[name] == value]
            sensitivity.append({"parameter": name, "value": value, "configurations": len(sample),
                                "positive_C1_share": sum(x > 0 for x in sample) / len(sample),
                                "mean_expectancy_C1": float(np.mean(sample)), "std_expectancy_C1": float(np.std(sample))})
    counts = {label: sum(x["classification"] == label for x in plateau)
              for label in ("ROBUST_PLATEAU", "LOCAL_SPIKE", "NO_EDGE")}
    overall = "ROBUST_PLATEAU" if counts["ROBUST_PLATEAU"] else (
        "LOCAL_SPIKE" if any(x["expectancy_C1"] > 0 for x in results) else "NO_EDGE")
    center_i = next(i for i, row in enumerate(rows) if row["baseline_configuration"])
    center, center_result = rows[center_i], results[center_i]
    target.mkdir(parents=True)
    experiment = {"phase": PHASE, "optimization_type": "BOUNDED_OAT",
        "design": "BASELINE_PLUS_ONE_FACTOR_AT_A_TIME", "methodological_source": "H1_PHASE_3_2",
        "timeframe": "M30", "development_period": DEVELOPMENT_PERIOD, "true_oos_blocked": True,
        "primary_cost_model": "H1_C1", "central_candidate_id": baseline.EXPECTED[key]["candidate_id"],
        "central_phase32_configuration_id": baseline.EXPECTED[key]["phase32_configuration_id"],
        "central_configuration_id": center["configuration_id"],
        "central_candidate_parameter_hash": baseline.EXPECTED[key]["parameter_hash"],
        "parameter_space": SPACES[key], "tested_configuration_count": len(rows), "deterministic_seed": 0,
        "source_files": baseline_manifest["source_files"]}
    manifest = {"phase": PHASE, "strategy": key, "status": STATUS, "timeframe": "M30",
                "tested_configurations": len(rows), "overall_plateau_classification": overall,
                "classification_counts": counts, "baseline_configuration_id": center["configuration_id"],
                "baseline_parity": "EXACT", "winner_selection": False, "robustness": False,
                "walk_forward": False, "true_oos_blocked": True, "deterministic": True}
    _json(target / "manifest.json", manifest); _json(target / "experiment.json", experiment)
    _csv(target / "parameters.csv", rows); _csv(target / "results.csv", results)
    _csv(target / "plateau_report.csv", plateau); _csv(target / "sensitivity_report.csv", sensitivity)
    summary = {"strategy": key, "tested_configurations": len(rows),
               "central_configuration_id": center["configuration_id"], **center_result,
               "overall_plateau_classification": overall, **{f"{k}_configurations": v for k, v in counts.items()}}
    _csv(target / "metrics_summary.csv", [summary])
    robust = [p for p in plateau if p["classification"] == "ROBUST_PLATEAU"]
    (target / "best_regions.md").write_text(
        f"# {key} M30 Stable Regions\n\n**{overall}**; {len(robust)} robust plateau configurations. "
        "Descriptive only; no winner or robustness candidate was selected.\n", encoding="utf-8")
    (target / "final_report.md").write_text(
        f"# {key} M30 Bounded OAT Optimization\n\n- Tested: {len(rows)}\n"
        f"- Central configuration: `{center['configuration_id']}`\n- Central PF / expectancy / net R: "
        f"{center_result['PF_C1']} / {center_result['expectancy_C1']} / {center_result['net_R_C1']}\n"
        f"- Classification: **{overall}**\n\nH1 Phase 3.2 methodology; C1 only; no ranking, "
        "selection, robustness, walk-forward, or TRUE OOS execution.\n", encoding="utf-8")
    return summary


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    protected_before = {str(path): hash_tree(path) for path in PROTECTED}
    baseline_manifest, data = _validate_prerequisites(Path(data_root))
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = []
    global _DATA
    _DATA = data
    for key in ("T2", "T3"):
        rows = configuration_rows(key)
        tasks = [(key, {name: row[name] for name in SPACES[key]}, row["configuration_id"]) for row in rows]
        with mp.get_context("fork").Pool(min(8, len(tasks))) as pool:
            results = pool.map(_execute_task, tasks)
        center_result = next(result for row, result in zip(rows, results) if row["baseline_configuration"])
        _assert_baseline_parity(key, data, center_result)
        summaries.append(_reports(key, rows, results, output / key, baseline_manifest))
    _DATA = None
    protected_after = {str(path): hash_tree(path) for path in PROTECTED}
    if protected_before != protected_after:
        raise RuntimeError("PROTECTED_RESEARCH_ARTIFACT_MUTATION")
    top = {"phase": PHASE, "status": STATUS, "timeframe": "M30", "development_period": DEVELOPMENT_PERIOD,
        "true_oos_cutoff": TRUE_OOS_CUTOFF, "m30_baseline_manifest_hash": _sha(BASELINE_MANIFEST),
        "m30_baseline_trade_ledger_hashes": {key: _sha(baseline.OUTPUT / key / "trades.csv") for key in ("T2", "T3")},
        "baseline_parity_status": {"T2": "EXACT", "T3": "EXACT"},
        "source_files": baseline_manifest["source_files"], "source_coverage": baseline_manifest["source_coverage"],
        "frozen_h1_candidate_ids": {key: baseline.EXPECTED[key]["candidate_id"] for key in ("T2", "T3")},
        "frozen_h1_phase32_configuration_ids": {key: baseline.EXPECTED[key]["phase32_configuration_id"] for key in ("T2", "T3")},
        "frozen_h1_candidate_parameter_hashes": {key: baseline.EXPECTED[key]["parameter_hash"] for key in ("T2", "T3")},
        "frozen_strategy_hashes": {key: STRATEGY_SHA256[key] for key in ("T2", "T3")},
        "tested_configuration_count": {key: EXPECTED_COUNTS[key] for key in ("T2", "T3")},
        "overall_plateau_classification": {x["strategy"]: x["overall_plateau_classification"] for x in summaries},
        "deterministic_execution": True, "protected_artifact_hashes": protected_after,
        "cartesian_grid": False, "one_factor_at_a_time": True, "ranking": False,
        "winner_selection": False, "robustness": False, "walk_forward": False, "true_oos_blocked": True,
        "parameter_space_expansion": False, "strategy_change": False,
        "cost_model": {"name": "H1_C1", "ticks_per_side": 1.0, "round_trip_ticks": 2.0,
                       "additional_slippage_ticks": 0.0}}
    _json(output / "manifest.json", top)
    lines = ["# M30 Bounded OAT Optimization", "", "Original H1 Phase 3.2 methodology; full 2023–2024 actual M30 data.", ""]
    for item in summaries:
        lines += [f"## {item['strategy']}", f"- Tested: {item['tested_configurations']}",
                  f"- Central configuration: `{item['central_configuration_id']}`",
                  f"- Overall classification: **{item['overall_plateau_classification']}**", ""]
    lines += ["No ranking or candidate selection. No robustness, walk-forward, or TRUE OOS run.", "", STATUS, ""]
    (output / "m30_optimization_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": STATUS, "strategies": summaries}
