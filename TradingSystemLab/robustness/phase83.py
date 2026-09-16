"""Phase 8.3 deterministic, validation-only M1 robustness diagnostics.

The selected Phase 8.2 configurations are immutable inputs.  This module has
no search, selection, ranking, walk-forward, portfolio, or OOS interface.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import numpy as np
import pandas as pd

from ..core.unified_metrics import concentration, finite, quantiles, stats
from ..multitimeframe.phase71 import APPROVED_DATA_ROOT, STRATEGY_SHA256, TRUE_OOS_START, reject_true_oos
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..optimization.phase82 import BASELINE_ROOT, OUTPUT as PHASE82_ROOT, RANGES
from ..timeframe_validation.phase81 import INSTRUMENTS, _execute, load_m1_development

OUTPUT = Path("TradingSystemLab/results/timeframe_validation/M1/robustness")
ITERATIONS = 10_000
BOOTSTRAP_SEED = 830_001
COST_SCENARIOS = (("C0", .5, 0.0), ("C1", 1.0, 0.0), ("C2", 1.0, .5))
PROTECTED = (PHASE82_ROOT,
             Path("TradingSystemLab/results/true_oos_validation"),
             Path("TradingSystemLab/results/portfolio_construction"))
STATUS = "PHASE_8_3_M1_ROBUSTNESS_COMPLETE"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_hashes() -> dict[str, str]:
    """Hash immutable inputs, excluding this phase's nested additive output."""
    result = {str(path): hash_tree(path) for path in PROTECTED}
    for path in sorted(BASELINE_ROOT.rglob("*")):
        if path.is_file() and OUTPUT not in path.parents:
            result[str(path)] = _sha(path)
    return result


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: Any) -> None:
    data = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    data.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _metric(values: pd.Series) -> dict[str, Any]:
    result = stats(pd.Series(values, dtype=float))
    return {"trades": result["trades"], "PF": finite(result["PF_R"]),
            "expectancy_R": finite(result["expectancy"]), "net_R": result["net_R"],
            "max_drawdown_R": result["max_DD_R"],
            "recovery_factor": finite(result["recovery_factor"])}


def bootstrap(values: pd.Series, seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    """Return a fixed-seed IID trade bootstrap (diagnostic, not selection)."""
    array = np.asarray(values, dtype=float)
    if not len(array):
        return {"iterations": ITERATIONS, "seed": seed, "probability_mean_R_gt_0": None,
                **quantiles(pd.Series(dtype=float), "expectancy_R"),
                **quantiles(pd.Series(dtype=float), "net_R")}
    rng = np.random.default_rng(seed)
    # Generate in bounded chunks to avoid a large trades x 10,000 allocation.
    means, nets = [], []
    for count in (1000,) * (ITERATIONS // 1000):
        sampled = array[rng.integers(0, len(array), size=(count, len(array)))]
        net = sampled.sum(axis=1); nets.extend(net.tolist()); means.extend((net / len(array)).tolist())
    return {"iterations": ITERATIONS, "seed": seed,
            "probability_mean_R_gt_0": float((np.asarray(means) > 0).mean()),
            **quantiles(pd.Series(means), "expectancy_R"), **quantiles(pd.Series(nets), "net_R")}


def reject_forbidden_timestamps(trades: pd.DataFrame) -> None:
    for column in ("entry_time", "exit_time"):
        if column in trades:
            reject_true_oos(pd.to_datetime(trades[column], utc=True))


def _verify_inputs(root: Path) -> tuple[dict, dict[str, dict]]:
    required = [root / "manifest.json"] + [root / key / "candidate_registry.json" for key in ("T2", "T3")]
    if any(not path.is_file() for path in required):
        raise RuntimeError("PHASE_8_2_ARTIFACTS_MISSING")
    manifest = json.loads(required[0].read_text(encoding="utf-8"))
    if manifest.get("phase") != "8.2" or manifest.get("timeframe") != "M1" or not manifest.get("true_oos_blocked"):
        raise RuntimeError("PHASE_8_2_PROVENANCE_INVALID")
    registries = {}
    for key in ("T2", "T3"):
        registry = json.loads((root / key / "candidate_registry.json").read_text(encoding="utf-8"))
        expected_id = f"{key}_M1_candidate_v1"
        if (registry.get("candidate_id") != expected_id or registry.get("strategy") != key or
                registry.get("timeframe") != "M1" or
                stable_hash(registry.get("parameters", {})) != registry.get("parameter_hash") or
                manifest.get("parameter_hashes", {}).get(key) != registry.get("parameter_hash") or
                registry.get("source_hashes") != manifest.get("source_data_hashes") or
                registry.get("strategy_hash") != STRATEGY_SHA256[key]):
            raise RuntimeError(f"{key}_PHASE_8_2_CANDIDATE_HASH_MISMATCH")
        registries[key] = registry
    return manifest, registries


def _groups(trades: pd.DataFrame, column: str, values: list[Any]) -> list[dict]:
    return [{column: value, **_metric(trades.loc[trades[column].eq(value), "net_R"])} for value in values]


def _parameter_stability(key: str, registry: dict, root: Path) -> list[dict]:
    results = pd.read_csv(root / key / "optimization_results.csv")
    plateau = pd.read_csv(root / key / "plateau_analysis.csv")
    selected = registry["parameters"]
    rows = []
    for _, row in results.iterrows():
        differences = []
        for name, values in RANGES[key].items():
            if row[name] != selected[name]:
                try:
                    if abs(values.index(row[name]) - values.index(selected[name])) == 1:
                        differences.append(name)
                    else: differences.append("NON_NEIGHBOR")
                except ValueError: differences.append("OUTSIDE_RANGE")
        if len(differences) <= 1 and "NON_NEIGHBOR" not in differences and "OUTSIDE_RANGE" not in differences:
            classification = plateau.loc[plateau.configuration_id.eq(row.configuration_id), "classification"]
            rows.append({"configuration_id": row.configuration_id,
                         "relationship": "SELECTED" if not differences else f"NEIGHBOR_{differences[0]}",
                         "plateau_classification": classification.iloc[0] if len(classification) else "MISSING",
                         **{name: row[name] for name in ("trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")}})
    return sorted(rows, key=lambda row: (row["relationship"] != "SELECTED", row["configuration_id"]))


def _classify(metric: dict, boot: dict, conc: dict, groups: list[dict], parameter_rows: list[dict]) -> tuple[str, list[str]]:
    checks = {
        "minimum_30_trades": metric["trades"] >= 30,
        "positive_expectancy": (metric["expectancy_R"] or 0) > 0,
        "positive_net_R": metric["net_R"] > 0,
        "drawdown_at_most_25R": abs(metric["max_drawdown_R"]) <= 25,
        "bootstrap_probability_at_least_0_90": (boot["probability_mean_R_gt_0"] or 0) >= .90,
        "top1_share_at_most_0_25": (conc["top_1_positive_R_share"] or 1) <= .25,
        "top5_share_at_most_0_60": (conc["top_5_positive_R_share"] or 1) <= .60,
        "positive_after_top5_removal": conc["net_R_without_top5"] > 0,
        "all_stability_slices_positive": all((row["expectancy_R"] or 0) > 0 and row["net_R"] > 0 for row in groups),
        "neighbor_plateau_support": sum(row["plateau_classification"] == "ROBUST_PLATEAU" for row in parameter_rows if row["relationship"] != "SELECTED") >= 2,
    }
    passed = sum(checks.values())
    status = "ROBUST_READY" if passed == len(checks) else ("BORDERLINE" if passed >= 7 else "FAILED")
    return status, [f"{name}={'PASS' if value else 'FAIL'}" for name, value in checks.items()]


def _run_candidate(key: str, registry: dict, loaded: dict, root: Path, target: Path) -> dict:
    pieces = [_execute(key, registry["parameters"], alias, frame) for _, alias in INSTRUMENTS
              if (frame := loaded[alias][0]) is not None]
    trades = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=["net_R"])
    if len(trades): trades = trades.sort_values(["exit_time", "trade_id"], kind="mergesort").reset_index(drop=True)
    reject_forbidden_timestamps(trades)
    target.mkdir(parents=True)
    cost_rows = []
    for scenario, transaction, slippage in COST_SCENARIOS:
        values = trades.gross_R.astype(float) - 2 * (transaction + slippage) / trades.initial_risk_ticks.astype(float)
        cost_rows.append({"scenario": scenario, "transaction_cost_ticks_per_side": transaction,
                          "slippage_ticks_per_side": slippage, **_metric(values)})
    _csv(target / "cost_report.csv", cost_rows)
    baseline_values = trades.net_R.astype(float); metric = _metric(baseline_values)
    boot = bootstrap(baseline_values); _csv(target / "bootstrap_report.csv", [boot])
    conc = concentration(baseline_values)
    conc_row = {"top_1_trade_contribution": conc["top_1_positive_R_share"],
                "top_5_trade_contribution": conc["top_5_positive_R_share"],
                "profit_concentration_top_10": conc["top_10_positive_R_share"],
                "net_R_after_top_five_removal": conc["net_R_without_top5"],
                "PF_after_top_five_removal": conc["PF_R_C1_without_top5"],
                "expectancy_after_top_five_removal": conc["expectancy_C1_without_top5"]}
    _csv(target / "concentration_report.csv", [conc_row])
    work = trades.assign(year=pd.to_datetime(trades.exit_time, utc=True).dt.year) if len(trades) else trades.assign(year=[])
    yearly = _groups(work, "year", [2023, 2024]); instruments = _groups(trades, "instrument", [x[0] for x in INSTRUMENTS])
    directions = _groups(trades, "direction", ["LONG", "SHORT"])
    _csv(target / "yearly_report.csv", yearly); _csv(target / "instrument_report.csv", instruments)
    _csv(target / "direction_report.csv", directions)
    # Explicit percentiles are stable across pandas versions used by the project.
    excursion = [{"statistic": name,
                  "MAE_R": finite(trades.MAE_R.astype(float).mean() if q is None else
                                  trades.MAE_R.astype(float).quantile(q)) if len(trades) else None,
                  "MFE_R": finite(trades.MFE_R.astype(float).mean() if q is None else
                                  trades.MFE_R.astype(float).quantile(q)) if len(trades) else None}
                 for name, q in (("minimum", 0), ("p05", .05), ("p25", .25), ("median", .5),
                                 ("mean", None), ("p75", .75), ("p95", .95), ("maximum", 1))]
    _csv(target / "mae_mfe_report.csv", excursion)
    parameter_rows = _parameter_stability(key, registry, root); _csv(target / "parameter_stability_report.csv", parameter_rows)
    baseline = pd.read_csv(root / key / "baseline_vs_optimized.csv")
    base = baseline.loc[baseline.version.eq("baseline")].iloc[0]
    comparison = [{"version": "phase8_1_baseline", **{name: base[name] for name in
                   ("trades", "PF", "expectancy_R", "net_R", "max_drawdown_R", "recovery_factor")}},
                  {"version": "phase8_2_optimized", **metric}]
    _csv(target / "baseline_comparison.csv", comparison)
    status, checks = _classify(metric, boot, conc, yearly + instruments + directions, parameter_rows)
    payload = {"candidate_id": registry["candidate_id"], "validation_status": status,
               "parameter_hash": registry["parameter_hash"], **metric,
               "bootstrap_probability_mean_R_gt_0": boot["probability_mean_R_gt_0"],
               "classification_checks": checks}
    _json(target / "metrics.json", payload)
    (target / "final_report.md").write_text(
        f"# {registry['candidate_id']} robustness validation\n\nStatus: **{status}**\n\n" +
        "\n".join(f"- {check}" for check in checks) +
        "\n\nValidation only; no optimization, ranking, selection, walk-forward, or TRUE OOS.\n", encoding="utf-8")
    return {"strategy": key, **payload}


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT,
        phase82_root: Path = PHASE82_ROOT) -> dict[str, Any]:
    phase82_root, output = Path(phase82_root), Path(output)
    manifest82, registries = _verify_inputs(phase82_root)
    protected_before = _protected_hashes()
    phase82_hash_before = hash_tree(phase82_root)
    loaded = {alias: load_m1_development(Path(data_root), alias) for _, alias in INSTRUMENTS}
    sources = [{"instrument": instrument, "alias": alias,
                "files": [{"name": path.name, "sha256": _sha(path)} for path in loaded[alias][1]]}
               for instrument, alias in INSTRUMENTS]
    # The files used now must be byte-identical to Phase 8.2's declared sources.
    if sources != manifest82.get("source_data_hashes"):
        raise RuntimeError("PHASE_8_2_SOURCE_HASH_MISMATCH")
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = [_run_candidate(key, registries[key], loaded, phase82_root, output / key) for key in ("T2", "T3")]
    _csv(output / "comparison.csv", summaries)
    protected_after = _protected_hashes()
    if protected_before != protected_after or phase82_hash_before != hash_tree(phase82_root):
        raise RuntimeError("PROTECTED_ARTIFACT_MUTATION")
    manifest = {"phase": "8.3", "status": STATUS, "timeframe": "M1",
        "development_period": ["2023-01-01", "2024-12-31"], "instruments": [x[0] for x in INSTRUMENTS],
        "candidates": [registries[k]["candidate_id"] for k in ("T2", "T3")],
        "phase8_2_artifact_hashes": {str(phase82_root): phase82_hash_before},
        "candidate_hashes": {k: _sha(phase82_root / k / "candidate_registry.json") for k in ("T2", "T3")},
        "parameter_hashes": {k: registries[k]["parameter_hash"] for k in ("T2", "T3")},
        "source_data_hashes": sources,
        "cost_assumptions": [{"scenario": a, "transaction_cost_ticks_per_side": b, "slippage_ticks_per_side": c} for a,b,c in COST_SCENARIOS],
        "bootstrap": {"iterations": ITERATIONS, "seed": BOOTSTRAP_SEED, "method": "IID_TRADE_RESAMPLING_WITH_REPLACEMENT"},
        "optimization": False, "ranking": False, "walk_forward": False, "true_oos_blocked": True, "deterministic": True,
        "protected_artifact_hashes": protected_after}
    _json(output / "manifest.json", manifest)
    lines = ["# Phase 8.3 M1 Robustness Validation", "", "Candidates were validated independently; the table is not a ranking.", "",
             "| Candidate | Status | Trades | PF | Expectancy R | Net R | Max DD R |", "|---|---|---:|---:|---:|---:|---:|"]
    for row in summaries: lines.append(f"| {row['candidate_id']} | {row['validation_status']} | {row['trades']} | {row['PF']} | {row['expectancy_R']} | {row['net_R']} | {row['max_drawdown_R']} |")
    lines += ["", "optimization=false; ranking=false; walk_forward=false; true_oos_blocked=true.", "", STATUS, ""]
    (output / "m1_robustness_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": STATUS, "candidates": summaries}
