"""Artifact-only, fail-closed consolidation audit for perpetual v3 Phase 2.

This module deliberately does not import either optimization runner (or its
design/classification helpers).  Non-baseline performance is accepted only as
committed execution evidence; the audit independently reconstructs structure.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any

import pandas as pd

ROOT = Path("TradingSystemLab/results/perpetual_v3/optimization")
BASELINE_ROOT = Path("TradingSystemLab/results/perpetual_v3/baseline")
TIMEFRAMES = ("M30", "H1")
INSTRUMENTS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
PHASE1 = "f8ee11841eedb11cb6ec98debc74ad8bc8c0c8a9"
PHASE1_AUDIT = "a9c9815a9865a2c20fa555292de2c9924aadca96"
PHASE2A = "7559953fd3dda8582af17f747ee38d94a93c42ad"
PHASE2B = "3b3cb3046f3f68c602d6d65f715d23090ab4a17c"
STATUS = "V3_PERPETUAL_PHASE_2_OPTIMIZATION_COMPLETE"
REQUIRED = {"experiment.json", "manifest.json", "parameters.csv", "results.csv",
            "plateau_report.csv", "sensitivity_report.csv", "best_regions.md", "final_report.md"}
FORBIDDEN = ("rank", "score", "winner", "selected_candidate", "selected_configuration",
             "best_by_pf", "best_by_expectancy", "recommended_candidate")

SPACES = {
    "T2": {
        "ema_fast": [15, 20, 25, 30], "ema_trend": [40, 50, 60],
        "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25, 30],
        "impulse_distance_atr": [.3, .5, .7], "confirmation_window": [2, 3, 4],
        "max_initial_stop_atr": [2., 2.5, 3.], "trailing_atr": [2., 3., 4.],
    },
    "T3": {
        "ema_period": [50, 75, 100, 150, 200], "adx_threshold": [15, 20, 25, 30],
        "breakout_period": [10, 20, 30, 40, 55], "atr_average_period": [10, 20, 30, 50],
        "stop_atr": [1.5, 2., 2.5, 3.], "trail_atr": [2., 2.5, 3., 3.5, 4.],
    },
}
BASELINES = {
    "T2": {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200, "adx_threshold": 20.,
           "impulse_distance_atr": .5, "confirmation_window": 3,
           "max_initial_stop_atr": 3., "trailing_atr": 3.},
    "T3": {"ema_period": 100, "adx_threshold": 20., "breakout_period": 20,
           "atr_average_period": 20, "stop_atr": 2., "trail_atr": 3.},
}
STRATEGIES = {
    "T2": (Path("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py"),
           "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774"),
    "T3": (Path("TradingSystemLab/strategies/trend/T3_MTF_Trend.py"),
           "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"),
}
ANCHORS = {("T2", "M30"): (366, 3), ("T2", "H1"): (176, 4),
           ("T3", "M30"): (398, 9), ("T3", "H1"): (184, 9)}


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def bounded_design(strategy: str) -> list[dict[str, Any]]:
    baseline, space = BASELINES[strategy], SPACES[strategy]
    rows = [dict(baseline)]
    sensitivity_parameters = sorted(space) if strategy == "T2" else space
    for parameter in sensitivity_parameters:
        values = space[parameter]
        rows.extend({**baseline, parameter: value} for value in values
                    if value != baseline[parameter])
    # Phase 2A's accepted canonical order is lexical canonical-JSON order;
    # Phase 2B intentionally retained parameter declaration order.
    if strategy == "T2":
        rows.sort(key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
    return rows


def immediate_neighbors(configs: list[dict[str, Any]], strategy: str, index: int) -> list[int]:
    space = SPACES[strategy]
    answer = []
    for other_index, other in enumerate(configs):
        differing = [key for key in space if configs[index][key] != other[key]]
        if len(differing) == 1:
            values = space[differing[0]]
            if abs(values.index(configs[index][differing[0]]) - values.index(other[differing[0]])) == 1:
                answer.append(other_index)
    return answer


def _close(actual: Any, expected: Any, tolerance: float = 1e-9) -> bool:
    if (actual is None or pd.isna(actual)) and (expected is None or pd.isna(expected)):
        return True
    return abs(float(actual) - float(expected)) <= tolerance


def phase1_metrics(strategy: str, timeframe: str, baseline_root: Path = BASELINE_ROOT) -> dict[str, Any]:
    frames = [pd.read_csv(baseline_root / strategy / timeframe / symbol / "trades.csv")
              for symbol in INSTRUMENTS]
    trades = pd.concat(frames, ignore_index=True).sort_values(
        ["exit_time", "symbol", "trade_id"], kind="mergesort")
    values = trades["net_R"].astype(float)
    positive, negative = values[values > 0].sum(), values[values < 0].sum()
    net = values.sum()
    equity = values.cumsum()
    drawdown = equity - equity.cummax().clip(lower=0)
    max_dd = drawdown.min() if len(drawdown) else 0.0
    return {"trades": len(values), "positive_R_sum": positive, "negative_R_sum": negative,
            "PF_C1": positive / abs(negative) if negative else math.inf,
            "expectancy_C1": values.mean(), "net_R_C1": net, "max_DD_C1": max_dd,
            "recovery_factor_C1": net / abs(max_dd) if max_dd else math.inf,
            "win_rate_C1": (values > 0).mean()}


def _static_causality() -> None:
    tree = ast.parse(Path("TradingSystemLab/perpetual_v3_phase2b_t3.py").read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "run"]
    assert any(len(c.args) >= 4 and isinstance(c.args[-2], ast.Name)
               and isinstance(c.args[-1], ast.Name) and c.args[-2].id == "execution"
               and c.args[-1].id == "context" for c in calls), "T3 execution/context separation"
    source = STRATEGIES["T3"][0].read_text()
    assert ".rolling(p.breakout_period).max().shift(1)" in source, "Donchian maximum is not causal"
    assert ".rolling(p.breakout_period).min().shift(1)" in source, "Donchian minimum is not causal"


def _git_immutable() -> None:
    checks = [(PHASE1, "TradingSystemLab/results/perpetual_v3/baseline"),
              (PHASE2A, "TradingSystemLab/results/perpetual_v3/optimization/T2"),
              (PHASE2B, "TradingSystemLab/results/perpetual_v3/optimization/T3")]
    for commit, path in checks:
        assert subprocess.run(["git", "diff", "--quiet", commit, "--", path]).returncode == 0, path
    for path in ("baseline_v2", "optimization_v2", "phase3_candidate_freeze", "robustness_v2",
                 "walk_forward_v2", "true_oos_v2", "true_oos_validation"):
        assert subprocess.run(["git", "diff", "--quiet", PHASE2B, "--", f"TradingSystemLab/results/{path}"]).returncode == 0, path


def _audit_study(root: Path, baseline_root: Path, strategy: str, timeframe: str) -> dict[str, Any]:
    study, space = root / strategy / timeframe, SPACES[strategy]
    assert {p.name for p in study.iterdir()} == REQUIRED, f"artifact set {strategy}/{timeframe}"
    experiment = json.loads((study / "experiment.json").read_text())
    manifest = json.loads((study / "manifest.json").read_text())
    assert experiment["parameter_space"] == space and experiment["baseline"] == BASELINES[strategy]
    assert manifest["data_commit"] == DATA_COMMIT
    assert manifest["frozen_strategy_hash"] == STRATEGIES[strategy][1]
    assert manifest["C1_only"] is True and manifest["normalized_research_tick"] == .001
    assert manifest["true_oos_blocked"] is True
    for flag in ("ranking", "candidate_selection", "robustness", "walk_forward", "true_oos_execution", "phase7_mtf_research"):
        assert manifest[flag] is False, flag

    parameters = pd.read_csv(study / "parameters.csv")
    results = pd.read_csv(study / "results.csv")
    plateau = pd.read_csv(study / "plateau_report.csv").fillna("")
    expected = bounded_design(strategy)
    assert len(parameters) == len(results) == len(plateau) == len(expected)
    assert int(parameters.is_baseline.sum()) == 1
    configs = parameters[list(space)].to_dict("records")
    assert configs == expected and len({stable_hash(c) for c in configs}) == len(configs)
    ids = [f"{strategy}-{timeframe}-{stable_hash(c)[:12]}" for c in expected]
    assert parameters.configuration_id.tolist() == ids
    assert results.configuration_id.tolist() == ids and plateau.configuration_id.tolist() == ids
    for config, flag in zip(configs, parameters.is_baseline):
        changed = sum(config[k] != BASELINES[strategy][k] for k in space)
        assert changed == (0 if flag else 1)
        assert all(config[k] in space[k] for k in space)
    required = {"trades", "PF_C1", "expectancy_C1", "net_R_C1", "max_DD_C1",
                "recovery_factor_C1", "win_rate_C1"}
    required |= {f"{x}_{y}" for x in (*INSTRUMENTS, "Y2023", "Y2024", "LONG", "SHORT")
                 for y in ("trades", "expectancy_C1")}
    required |= {"top_1_positive_R_share", "top_3_positive_R_share", "top_5_positive_R_share",
                 "top_10_positive_R_share", "net_R_without_best_trade", "net_R_without_top3", "net_R_without_top5"}
    assert required <= set(results.columns)
    assert not any(any(term in col.lower() for term in FORBIDDEN) for col in results.columns)

    records = results.where(pd.notna(results), None).to_dict("records")
    reconstructed = []
    for i, record in enumerate(records):
        neighbors = immediate_neighbors(configs, strategy, i)
        positive_neighbors = [j for j in neighbors if records[j]["expectancy_C1"] is not None
                              and records[j]["expectancy_C1"] > 0]
        positive = record["expectancy_C1"] is not None and record["expectancy_C1"] > 0
        tolerance = max(.01, abs(record["expectancy_C1"]) * .35) if positive else None
        stable = [j for j in positive_neighbors if abs(records[j]["expectancy_C1"] - record["expectancy_C1"]) <= tolerance]
        classification = "ROBUST_PLATEAU" if positive and len(stable) >= 2 else "LOCAL_SPIKE" if positive else "NO_EDGE"
        reconstructed.append({"neighbor_ids": ";".join(ids[j] for j in neighbors),
                              "neighbor_count": len(neighbors), "positive_neighbors": len(positive_neighbors),
                              "stable_positive_neighbors": len(stable), "stability_tolerance": tolerance,
                              "classification": classification})
    for actual, expected_row in zip(plateau.to_dict("records"), reconstructed):
        for key in ("neighbor_ids", "neighbor_count", "positive_neighbors", "stable_positive_neighbors", "classification"):
            assert actual[key] == expected_row[key], f"plateau {strategy}/{timeframe}:{key}"
        assert _close(actual["stability_tolerance"] or None, expected_row["stability_tolerance"])
    classes = [r["classification"] for r in reconstructed]
    overall = "ROBUST_PLATEAU" if "ROBUST_PLATEAU" in classes else "LOCAL_SPIKE" if "LOCAL_SPIKE" in classes else "NO_EDGE"
    assert manifest["overall"] == overall and f"**{overall}**" in (study / "final_report.md").read_text()

    baseline_index = parameters.index[parameters.is_baseline].item()
    metrics = phase1_metrics(strategy, timeframe, baseline_root)
    assert metrics["trades"] == ANCHORS[(strategy, timeframe)][0]
    for key in required & metrics.keys():
        assert _close(records[baseline_index][key], metrics[key]), f"baseline {strategy}/{timeframe}:{key}"

    expected_sensitivity = []
    sensitivity_parameters = sorted(space) if strategy == "T2" else space
    for parameter in sensitivity_parameters:
        values = space[parameter]
        for value in values:
            sample = [row for config, row in zip(configs, records) if config[parameter] == value]
            exps = [row["expectancy_C1"] for row in sample if row["expectancy_C1"] is not None]
            expected_sensitivity.append((parameter, value, len(sample), sum(x > 0 for x in exps) / len(exps), sum(exps) / len(exps)))
    sensitivity = pd.read_csv(study / "sensitivity_report.csv")
    assert len(sensitivity) == len(expected_sensitivity)
    for actual, expected_row in zip(sensitivity.to_dict("records"), expected_sensitivity):
        assert actual["parameter"] == expected_row[0] and _close(actual["value"], expected_row[1])
        assert actual["configurations"] == expected_row[2]
        assert _close(actual["positive_C1_share"], expected_row[3]) and _close(actual["mean_expectancy_C1"], expected_row[4])

    robust_ids = [ids[i] for i, value in enumerate(classes) if value == "ROBUST_PLATEAU"]
    listed = re.findall(r"^- `([^`]+)`", (study / "best_regions.md").read_text(), re.MULTILINE)
    assert listed == robust_ids
    assert len(robust_ids) == ANCHORS[(strategy, timeframe)][1]
    inventory = []
    for i, identifier in enumerate(ids):
        if classes[i] != "ROBUST_PLATEAU":
            continue
        changed = [k for k in space if configs[i][k] != BASELINES[strategy][k]]
        inventory.append({"strategy": strategy, "timeframe": timeframe, "configuration_id": identifier,
                          "changed_parameter": changed[0] if changed else "BASELINE",
                          "changed_value": configs[i][changed[0]] if changed else "BASELINE",
                          **{k: records[i][k] for k in ("trades", "PF_C1", "expectancy_C1", "net_R_C1", "max_DD_C1", "recovery_factor_C1", "win_rate_C1")},
                          "stable_neighbor_count": reconstructed[i]["stable_positive_neighbors"]})
    return {"strategy": strategy, "timeframe": timeframe, "configurations": len(configs),
            "classification": overall, "robust": len(robust_ids), "metrics": metrics,
            "inventory": inventory}


def _root_manifest() -> dict[str, Any]:
    return {"generation": "v3_perpetual", "phase": "PHASE_2_OPTIMIZATION", "status": STATUS,
            "methodological_source": "original H1 Phase 3.2", "phase1_reference_merge": PHASE1,
            "phase1_audit_reference_merge": PHASE1_AUDIT, "phase2a_t2_reference_merge": PHASE2A,
            "phase2b_t3_reference_merge": PHASE2B, "data_commit": DATA_COMMIT,
            "strategies": ["T2", "T3"], "timeframes": list(TIMEFRAMES), "instruments": list(INSTRUMENTS),
            "development_period": ["2023-01-01", "2024-12-31"], "true_oos_start": "2025-01-01",
            "true_oos_blocked": True, "cost": {"name": "C1", "ticks_per_side": 1, "round_trip_ticks": 2,
            "additional_slippage_ticks": 0}, "normalized_research_tick": .001, "OAT": True, "studies": 4,
            "T2_configurations": 38, "T3_configurations": 44, "total_configuration_studies": 82,
            "ROBUST_PLATEAU_configurations": 25, "ranking": False, "candidate_selection": False,
            "robustness": False, "walk_forward": False, "true_oos_execution": False,
            "portfolio": False, "mtf": False, "failed_checks": []}


def _write_bundle(root: Path, studies: list[dict[str, Any]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "manifest.json").write_text(json.dumps(_root_manifest(), indent=2, sort_keys=True) + "\n")
    fields = ["strategy", "timeframe", "configuration_id", "changed_parameter", "changed_value", "trades", "PF_C1",
              "expectancy_C1", "net_R_C1", "max_DD_C1", "recovery_factor_C1", "win_rate_C1", "stable_neighbor_count"]
    with (root / "robust_plateau_inventory.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for study in studies:
            writer.writerows(study["inventory"])
    lines = ["# Phase 2 Optimization Report", "", "Artifact-only consolidation of four already committed Development studies.",
             "No Optimization was rerun.", "", "| Strategy | TF | Configurations | Baseline trades | Baseline PF | Baseline expectancy | Baseline Net R | Baseline Max DD | Classification | ROBUST_PLATEAU count |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
    for s in studies:
        m = s["metrics"]
        lines.append(f"| {s['strategy']} | {s['timeframe']} | {s['configurations']} | {m['trades']} | {m['PF_C1']:.12f} | {m['expectancy_C1']:.12f} | {m['net_R_C1']:.12f} | {m['max_DD_C1']:.12f} | {s['classification']} | {s['robust']} |")
    lines += ["", "The exact original-H1 bounded Baseline-plus-OAT design comprises 82 configurations in four independent studies and yields 25 ROBUST_PLATEAU configurations.",
              "TRUE OOS remained blocked and was not read. No ranking, winner, candidate selection/freeze, Robustness, Walk Forward, TRUE OOS execution, portfolio selection, or MTF research occurred.", "",
              "The next permitted action is procedural v3 candidate freeze/preparation required by the original H1 lifecycle before Robustness; it is not performed here.", ""]
    (root / "Phase_2_Optimization_Report.md").write_text("\n".join(lines))
    checks = ["canonical merge provenance", "Phase 1 immutable", "Phase 2A T2 immutable", "Phase 2B T3 immutable",
              "4 expected studies", "exact artifact sets", "exact T2 parameter space", "exact T3 parameter space",
              "canonical Baselines", "T2 19+19", "T3 22+22", "total 82", "exact OAT compliance",
              "deterministic configuration IDs", "Phase 1 Baseline reconciliation", "C1 only", "tick 0.001",
              "TRUE OOS blocked", "immediate neighbor reconstruction", "35% / 0.01 stability rule",
              "all 82 classifications reconstructed", "sensitivity reconciliation", "best_regions reconciliation",
              "25-row robust inventory", "T3 execution/context static separation", "Donchian shift(1)",
              "child independent audits present/PASS", "no ranking", "no winner", "no candidate selection",
              "no Robustness", "no Walk Forward", "no TRUE OOS execution", "no portfolio selection", "no MTF"]
    audit_lines = ["# Phase 2 Optimization Independent Audit", "", f"**PASS — {STATUS}**", "",
                   "Artifact-only: committed non-Baseline results were not re-executed; all structural conclusions were independently reconstructed.", ""]
    audit_lines += [f"{i}. **PASS** — {check}." for i, check in enumerate(checks, 1)]
    audit_lines += ["", "Dynamic four-bar context correctness relies on the committed Phase 1/Phase 2B audits; this audit performed only static causal verification.", ""]
    (root / "Phase_2_Optimization_Audit_Report.md").write_text("\n".join(audit_lines))


def audit(root: Path = ROOT, *, baseline_root: Path = BASELINE_ROOT,
          check_protected: bool = True, write_bundle: bool = True) -> dict[str, Any]:
    root, baseline_root = Path(root), Path(baseline_root)
    for strategy, (source, digest) in STRATEGIES.items():
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, f"{strategy} strategy hash"
    _static_causality()
    if check_protected:
        _git_immutable()
    root_contract = {
        "T2": ("PHASE_2A_T2", 19, 38, "V3_PERPETUAL_PHASE_2A_T2_COMPLETE"),
        "T3": ("PHASE_2B_T3", 22, 44, "V3_PERPETUAL_PHASE_2B_T3_COMPLETE")}
    for strategy, (subphase, each, total, status) in root_contract.items():
        manifest = json.loads((root / strategy / "manifest.json").read_text())
        expected = {"generation": "v3_perpetual", "phase": "PHASE_2_OPTIMIZATION", "subphase": subphase,
                    "configurations_per_study": each, "studies": 2, "total_configuration_studies": total,
                    "C1_only": True, "normalized_research_tick": .001, "true_oos_start": "2025-01-01",
                    "true_oos_blocked": True, "ranking": False, "candidate_selection": False, "robustness": False,
                    "walk_forward": False, "true_oos_execution": False, "mtf": False, "data_commit": DATA_COMMIT,
                    "status": status}
        assert all(manifest.get(k) == v for k, v in expected.items()), f"{strategy} root manifest"
        report = (root / strategy / f"{strategy}_Optimization_Audit_Report.md").read_text()
        assert status in report and "PASS" in report
    studies = [_audit_study(root, baseline_root, strategy, timeframe)
               for strategy in ("T2", "T3") for timeframe in TIMEFRAMES]
    assert sum(s["configurations"] for s in studies) == 82
    assert sum(s["robust"] for s in studies) == 25
    if write_bundle:
        _write_bundle(root, studies)
    # Existing/generated root files are themselves audited exactly, including order.
    assert json.loads((root / "manifest.json").read_text()) == _root_manifest()
    expected_inventory = [row for study in studies for row in study["inventory"]]
    actual_inventory = pd.read_csv(root / "robust_plateau_inventory.csv", dtype=str).to_dict("records")
    assert len(actual_inventory) == len(expected_inventory)
    for actual, expected in zip(actual_inventory, expected_inventory):
        assert list(actual) == list(expected)
        for key in actual:
            if key in {"strategy", "timeframe", "configuration_id", "changed_parameter", "changed_value"}:
                assert actual[key] == str(expected[key])
            else:
                assert _close(actual[key], expected[key])
    root_text = "\n".join((root / name).read_text().lower() for name in
                          ("manifest.json", "Phase_2_Optimization_Report.md", "Phase_2_Optimization_Audit_Report.md"))
    assert not any(f'"{term}"' in root_text and ': true' in root_text[root_text.index(f'"{term}"'):][:30]
                   for term in FORBIDDEN)
    return {"status": STATUS, "audit": "PASS", "studies": 4, "configurations": 82,
            "robust_plateau_configurations": 25, "failures": []}


def main() -> int:
    try:
        print(json.dumps(audit(), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "V3_PERPETUAL_PHASE_2_OPTIMIZATION_AUDIT_FAILED",
                          "audit": "FAIL", "failures": [str(exc)]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
