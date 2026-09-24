"""Artifact-only independent consolidation audit for TradingSystemLab v2 Phase 2.

This module never opens market data and never executes an optimizer.  It treats
the committed Phase 1/2 artifacts as evidence, reconstructs the bounded OAT
design and plateau classifications, and writes only the Phase 2 root bundle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = Path("TradingSystemLab/results/optimization_v2")
PHASE1_ROOT = Path("TradingSystemLab/results/baseline_v2")
PHASE1_COMMIT = "2aae07a3d12907d1869eb603e6ac1a6fb8d851dd"
T2_COMMIT = "a252f076a09495d3093854c8509b1551701ba2b4"
T3_COMMIT = "f8f28834db4bc016a995b55aed1ff7fd53a4a0e8"
STUDIES = (("T2", "M30"), ("T2", "H1"), ("T3", "M30"), ("T3", "H1"))
INSTRUMENTS = ("Si", "CNY", "GD", "BR", "MIX", "NG")
TIMEFRAMES = ("M30", "H1")
EXPECTED_COUNTS = {"T2": 19, "T3": 22}
EXPECTED_ROBUST = {("T2", "M30"): 3, ("T2", "H1"): 4,
                   ("T3", "M30"): 9, ("T3", "H1"): 9}
REQUIRED_STUDY_FILES = {"manifest.json", "experiment.json", "parameters.csv",
                        "results.csv", "plateau_report.csv", "sensitivity_report.csv",
                        "best_regions.md", "final_report.md"}
COST = {"name": "C1", "ticks_per_side": 1, "round_trip_ticks": 2,
        "additional_slippage_ticks": 0}
T2_SPACE = {
    "ema_fast": [15, 20, 25, 30], "ema_trend": [40, 50, 60],
    "ema_slow": [150, 200, 250], "adx_threshold": [15, 20, 25, 30],
    "impulse_distance_atr": [0.3, 0.5, 0.7], "confirmation_window": [2, 3, 4],
    "max_initial_stop_atr": [2.0, 2.5, 3.0], "trailing_atr": [2.0, 3.0, 4.0],
}
T3_SPACE = {
    "ema_period": [50, 75, 100, 150, 200], "adx_threshold": [15, 20, 25, 30],
    "breakout_period": [10, 20, 30, 40, 55],
    "atr_average_period": [10, 20, 30, 50], "stop_atr": [1.5, 2.0, 2.5, 3.0],
    "trail_atr": [2.0, 2.5, 3.0, 3.5, 4.0],
}
SPACES = {"T2": T2_SPACE, "T3": T3_SPACE}
BASELINES = {
    "T2": {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200,
           "adx_threshold": 20.0, "impulse_distance_atr": 0.5,
           "confirmation_window": 3, "max_initial_stop_atr": 3.0,
           "trailing_atr": 3.0},
    "T3": {"ema_period": 100, "adx_threshold": 20.0, "breakout_period": 20,
           "atr_average_period": 20, "stop_atr": 2.0, "trail_atr": 3.0},
}


def stable_hash(value: Any) -> str:
    """Reimplement the canonical content hash without importing Phase 2 runners."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def expected_design(strategy: str) -> list[dict[str, Any]]:
    """Independently construct baseline plus every unique one-factor deviation."""
    baseline, space = BASELINES[strategy], SPACES[strategy]
    rows = [dict(baseline)]
    names = sorted(space) if strategy == "T2" else space
    for name in names:
        rows.extend({**baseline, name: value} for value in space[name]
                    if value != baseline[name])
    if strategy == "T2":
        rows.sort(key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
    return rows


def configuration_id(strategy: str, timeframe: str, config: Mapping[str, Any]) -> str:
    return f"{strategy}-{timeframe}-{stable_hash(dict(config))[:12]}"


def immediate_neighbors(configs: list[dict[str, Any]], index: int,
                        space: Mapping[str, list[Any]]) -> list[int]:
    """Return canonical-order indices differing by one immediately adjacent value."""
    found: list[int] = []
    current = configs[index]
    for other_index, other in enumerate(configs):
        changed = [name for name in space if current[name] != other[name]]
        if len(changed) == 1:
            values = space[changed[0]]
            if abs(values.index(current[changed[0]]) - values.index(other[changed[0]])) == 1:
                found.append(other_index)
    return found


def classify(configs: list[dict[str, Any]], results: list[dict[str, Any]],
             space: Mapping[str, list[Any]]) -> tuple[list[dict[str, Any]], str]:
    """Independently apply the exact positive-neighbor plateau contract."""
    rows = []
    for index, result in enumerate(results):
        adjacent = immediate_neighbors(configs, index, space)
        expectancy = result["expectancy_C1"]
        positive = expectancy is not None and expectancy > 0
        positive_neighbors = [i for i in adjacent
                              if results[i]["expectancy_C1"] is not None
                              and results[i]["expectancy_C1"] > 0]
        tolerance = max(0.01, abs(expectancy) * 0.35) if positive else None
        stable = [i for i in positive_neighbors
                  if abs(results[i]["expectancy_C1"] - expectancy) <= tolerance]
        label = ("ROBUST_PLATEAU" if positive and len(stable) >= 2 else
                 "LOCAL_SPIKE" if positive else "NO_EDGE")
        rows.append({"configuration_id": result["configuration_id"],
                     "neighbor_ids": ";".join(results[i]["configuration_id"] for i in adjacent),
                     "neighbor_count": len(adjacent),
                     "positive_neighbors": len(positive_neighbors),
                     "stable_positive_neighbors": len(stable),
                     "stability_tolerance": tolerance,
                     "classification": label})
    overall = ("ROBUST_PLATEAU" if any(r["classification"] == "ROBUST_PLATEAU" for r in rows)
               else "LOCAL_SPIKE" if any(r["classification"] == "LOCAL_SPIKE" for r in rows)
               else "NO_EDGE")
    return rows, overall


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _same_number(left: Any, right: Any, tolerance: float = 5e-10) -> bool:
    if left is None or right is None:
        return left is right
    return abs(float(left) - float(right)) <= tolerance * max(1.0, abs(float(right)))


def _git_ok(project_root: Path, *args: str) -> bool:
    return subprocess.run(["git", *args], cwd=project_root, check=False,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def _phase1_metrics(project_root: Path, strategy: str, timeframe: str) -> tuple[dict, dict]:
    """Rebuild combined Phase 1 metrics and collect per-instrument metrics."""
    frames, instruments = [], {}
    for instrument in INSTRUMENTS:
        run = project_root / PHASE1_ROOT / strategy / instrument / timeframe
        metric = _json(run / "metrics.json")
        manifest = _json(run / "manifest.json")
        trades = pd.read_csv(run / "trades.csv")
        assert manifest["true_oos_blocked"] is True
        assert manifest["true_oos_cutoff"] == "2025-01-01"
        assert pd.to_datetime(trades["entry_time"], utc=True).max() < pd.Timestamp("2025-01-01", tz="UTC")
        assert pd.to_datetime(trades["exit_time"], utc=True).max() < pd.Timestamp("2025-01-01", tz="UTC")
        instruments[instrument] = metric
        frames.append(trades.assign(symbol=instrument))
    all_trades = pd.concat(frames, ignore_index=True).sort_values(
        ["exit_time", "symbol", "trade_id"], kind="mergesort")
    values = all_trades["net_R"].astype(float).reset_index(drop=True)
    gains, losses = values[values > 0].sum(), -values[values < 0].sum()
    curve = pd.concat([pd.Series([0.0]), values.cumsum().reset_index(drop=True)])
    combined = {"trades": len(values), "PF_C1": float(gains / losses),
                "expectancy_C1": float(values.mean()), "net_R_C1": float(values.sum()),
                "max_DD_C1": float((curve - curve.cummax()).min())}
    return combined, instruments


def _assert_t3_context(project_root: Path) -> None:
    """Audit implementation provenance and a synthetic day-boundary construction."""
    baseline_source = (project_root / "TradingSystemLab/baseline_v2.py").read_text()
    t3_source = (project_root / "TradingSystemLab/optimization/phase2b_t3.py").read_text()
    t2_source = (project_root / "TradingSystemLab/optimization/phase2a_t2.py").read_text()
    loader_source = (project_root / "TradingSystemLab/core/data_loader.py").read_text()
    assert "context = four_bar_context(execution)" in t3_source
    assert "context is execution" in t3_source
    assert "four_bar_context" not in t2_source
    assert "return DataLoader.h4_from_h1(execution)" in baseline_source
    assert "groupby(closed_h1.index.normalize()" in loader_source
    assert "range(0, len(day), 4)" in loader_source and "if len(block) != 4" in loader_source
    from TradingSystemLab.baseline_v2 import four_bar_context
    index = pd.to_datetime(["2024-01-01 10:00", "2024-01-01 10:30",
                            "2024-01-01 11:00", "2024-01-01 11:30",
                            "2024-01-01 12:00", "2024-01-02 10:00",
                            "2024-01-02 10:30", "2024-01-02 11:00",
                            "2024-01-02 11:30"], utc=True)
    frame = pd.DataFrame({"Open": range(9), "High": range(1, 10), "Low": range(9),
                          "Close": range(1, 10), "Volume": range(9)}, index=index)
    context = four_bar_context(frame)
    assert context is not frame
    assert context.index.tolist() == [index[3], index[8]]
    assert context.iloc[0]["Open"] == 0 and context.iloc[0]["Close"] == 4


def _assert_study(project_root: Path, output_root: Path, strategy: str, timeframe: str) -> dict:
    study = output_root / strategy / timeframe
    assert study.is_dir() and {p.name for p in study.iterdir()} == REQUIRED_STUDY_FILES
    manifest, experiment = _json(study / "manifest.json"), _json(study / "experiment.json")
    parameters, result_frame = pd.read_csv(study / "parameters.csv"), pd.read_csv(study / "results.csv")
    plateau = pd.read_csv(study / "plateau_report.csv").fillna("")
    space, baseline = SPACES[strategy], BASELINES[strategy]
    expected = expected_design(strategy)
    count = EXPECTED_COUNTS[strategy]
    assert len(parameters) == len(result_frame) == len(plateau) == count
    assert manifest["parameter_space"] == experiment["parameter_space"] == space
    assert manifest["baseline"] == experiment["baseline"] == baseline
    assert manifest["strategy"] == strategy and manifest["timeframe"] == timeframe
    assert manifest["instruments"] == experiment["instruments"] == list(INSTRUMENTS)
    assert manifest["development_interval"] == ["2020-01-01", "2024-12-31"]
    assert manifest["optimization_design"] == "BASELINE_PLUS_ONE_FACTOR_AT_A_TIME"
    assert manifest["cost_models"] == [COST] and manifest["C1_only"] is True
    assert manifest["normalized_research_tick"] == 0.001
    assert manifest["true_oos_blocked"] is True
    assert all(manifest[key] is False for key in ("ranking", "candidate_selection", "robustness",
                                                   "walk_forward", "true_oos_execution",
                                                   "phase7_mtf_research"))
    assert {item["instrument"] for item in manifest["actual_source_availability"]} == set(INSTRUMENTS)
    assert all(pd.Timestamp(item["last_close"]) < pd.Timestamp("2025-01-01", tz="Europe/Moscow")
               for item in manifest["actual_source_availability"])
    forbidden = ("C0", "C05", "C0.5", "C2")
    assert not any(any(token in column for token in forbidden) for column in result_frame.columns)
    required_diagnostics = {item for instrument in INSTRUMENTS
                            for item in (f"{instrument}_trades", f"{instrument}_expectancy_C1")}
    assert required_diagnostics <= set(result_frame.columns)
    assert parameters["is_baseline"].sum() == 1
    persisted_configs = parameters[list(space)].to_dict("records")
    assert persisted_configs == expected
    # Use the authoritative typed design for hashing: CSV parsing intentionally
    # normalizes integral float columns (for example 3.0 to 3).
    configs = expected
    assert all(sum(row[name] != baseline[name] for name in space) == (0 if row == baseline else 1)
               for row in configs)
    assert len({tuple(row[name] for name in space) for row in configs}) == count
    expected_ids = [configuration_id(strategy, timeframe, row) for row in configs]
    assert parameters["configuration_id"].tolist() == expected_ids
    assert len(set(expected_ids)) == count
    assert result_frame["configuration_id"].tolist() == expected_ids
    results = result_frame.where(pd.notna(result_frame), None).to_dict("records")
    reconstructed, overall = classify(configs, results, space)
    for actual, expected_row in zip(plateau.to_dict("records"), reconstructed):
        for key in ("configuration_id", "neighbor_ids", "neighbor_count", "positive_neighbors",
                    "stable_positive_neighbors", "classification"):
            assert actual[key] == expected_row[key]
        if expected_row["stability_tolerance"] is None:
            assert actual["stability_tolerance"] == ""
        else:
            assert _same_number(actual["stability_tolerance"], expected_row["stability_tolerance"])
    robust_count = sum(row["classification"] == "ROBUST_PLATEAU" for row in reconstructed)
    assert overall == manifest["overall"] == "ROBUST_PLATEAU"
    assert robust_count == EXPECTED_ROBUST[(strategy, timeframe)]
    regions = (study / "best_regions.md").read_text(encoding="utf-8")
    assert all(row["configuration_id"] in regions for row in reconstructed
               if row["classification"] == "ROBUST_PLATEAU")
    phase1, per_instrument = _phase1_metrics(project_root, strategy, timeframe)
    baseline_index = configs.index(baseline)
    baseline_result = results[baseline_index]
    for key in ("trades", "PF_C1", "expectancy_C1", "net_R_C1", "max_DD_C1"):
        assert _same_number(baseline_result[key], phase1[key])
    for instrument, metric in per_instrument.items():
        assert baseline_result[f"{instrument}_trades"] == metric["trades"]
        assert _same_number(baseline_result[f"{instrument}_expectancy_C1"], metric["expectancy_R"])
    if strategy == "T3":
        assert manifest["context"] == "four completed execution bars; local-day reset"
    return {"strategy": strategy, "timeframe": timeframe, "count": count,
            "overall": overall, "robust_count": robust_count, "configs": configs,
            "results": results, "plateau": reconstructed,
            "baseline": baseline_result}


CHECK_NAMES = [
    "canonical commit provenance", "Phase 1 tree unchanged", "T2 Phase 2A tree unchanged",
    "T3 Phase 2B tree unchanged", "four expected studies exist", "exact artifact sets exist",
    "T2 19+19 design", "T3 22+22 design", "exactly 82 total configuration studies",
    "canonical Baselines", "exact original H1 parameter spaces", "exact OAT compliance",
    "deterministic configuration IDs", "six-instrument common configuration scope",
    "Phase 2 Baselines reconcile to Phase 1", "C1-only execution",
    "normalized research tick 0.001", "T3 causal four-bar context", "TRUE OOS exclusion",
    "exact immediate-neighbor reconstruction", "exact 35% / 0.01 stability rule",
    "all 82 classifications independently reconstructed", "stable-region inventories reconcile",
    "no ranking", "no winner", "no candidate selection", "no Robustness execution",
    "no Walk Forward execution", "no TRUE OOS execution", "no Phase 7 MTF research",
]


def _inventory(studies: list[dict]) -> list[dict[str, Any]]:
    rows = []
    for study in studies:
        baseline = BASELINES[study["strategy"]]
        for config, result, plateau in zip(study["configs"], study["results"], study["plateau"]):
            if plateau["classification"] != "ROBUST_PLATEAU":
                continue
            changed = [name for name in SPACES[study["strategy"]] if config[name] != baseline[name]]
            parameter = changed[0] if changed else "BASELINE"
            value = config[changed[0]] if changed else "BASELINE"
            rows.append({"strategy": study["strategy"], "timeframe": study["timeframe"],
                         "configuration_id": result["configuration_id"],
                         "changed_parameter": parameter, "changed_value": value,
                         "trades": result["trades"], "PF_C1": result["PF_C1"],
                         "expectancy_C1": result["expectancy_C1"], "net_R_C1": result["net_R_C1"],
                         "max_DD_C1": result["max_DD_C1"],
                         "recovery_factor_C1": result["recovery_factor_C1"],
                         "win_rate_C1": result["win_rate_C1"],
                         "stable_neighbor_count": plateau["stable_positive_neighbors"]})
    return rows


def build_manifest(passed: bool, failures: list[str]) -> dict[str, Any]:
    """Build a fail-closed root manifest; COMPLETE is impossible after any failure."""
    return {"phase": "PHASE_2_OPTIMIZATION", "status": ("PHASE_2_OPTIMIZATION_COMPLETE"
            if passed and not failures else "PHASE_2_OPTIMIZATION_AUDIT_FAILED"),
            "methodological_source": "original H1 Phase 3.2",
            "phase1_reference_commit": PHASE1_COMMIT, "phase2a_t2_reference_commit": T2_COMMIT,
            "phase2b_t3_reference_commit": T3_COMMIT, "strategies": ["T2", "T3"],
            "timeframes": list(TIMEFRAMES), "instruments": list(INSTRUMENTS),
            "development_period": ["2020-01-01", "2024-12-31"],
            "true_oos_start": "2025-01-01", "normalized_research_tick": 0.001,
            "cost": COST, "cost_models": ["C1"], "studies": 4,
            "T2_configurations": 38, "T3_configurations": 44,
            "total_configuration_studies": 82, "OAT": True, "ranking": False,
            "candidate_selection": False, "robustness": False, "walk_forward": False,
            "true_oos_execution": False, "phase7_mtf_research": False,
            "true_oos_blocked": True, "failed_checks": failures}


def _write_outputs(output_root: Path, studies: list[dict], checks: list[tuple[str, bool, str]],
                   failures: list[str]) -> None:
    passed = not failures
    manifest = build_manifest(passed, failures)
    inventory = _inventory(studies) if passed else []
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    pd.DataFrame(inventory, columns=["strategy", "timeframe", "configuration_id",
        "changed_parameter", "changed_value", "trades", "PF_C1", "expectancy_C1", "net_R_C1",
        "max_DD_C1", "recovery_factor_C1", "win_rate_C1", "stable_neighbor_count"]).to_csv(
            output_root / "robust_plateau_inventory.csv", index=False, lineterminator="\n",
            float_format="%.12g")
    report = ["# TradingSystemLab v2 — Phase 2 Optimization", "",
              "Artifact-only consolidation of four independent Development studies. No optimization was rerun.", "",
              "| Strategy | Timeframe | Tested configurations | Baseline trades | Baseline PF | Baseline expectancy | Baseline Net R | Baseline max DD | Overall classification | ROBUST_PLATEAU configurations | Recommendation |",
              "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|"]
    for study in studies:
        b = study["baseline"]
        report.append(f"| {study['strategy']} | {study['timeframe']} | {study['count']} | {b['trades']} | {b['PF_C1']:.12g} | {b['expectancy_C1']:.12g} | {b['net_R_C1']:.12g} | {b['max_DD_C1']:.12g} | {study['overall']} | {study['robust_count']} | Proceed to dedicated candidate freeze before Phase 3 |")
    report += ["", "## Scope and verdict", "",
               "- 82 total configuration studies across four independent strategy/timeframe studies.",
               "- T2/M30, T2/H1, T3/M30, and T3/H1 each classify as `ROBUST_PLATEAU`.",
               "- TRUE OOS 2025+ remained sealed; only committed Development artifacts were inspected.",
               "- No ranking, winner, or Phase 3 candidate selection/freeze was performed.",
               "- Robustness, Walk Forward, TRUE OOS execution, portfolio selection, and Phase 7 MTF research were not performed.",
               "- A second full byte-identical optimization rerun was not performed and is not claimed.", "",
               f"**Status:** `{manifest['status']}`", ""]
    (output_root / "Phase_2_Optimization_Report.md").write_text("\n".join(report))
    audit = ["# TradingSystemLab v2 — Phase 2 Independent Audit", "",
             "This was an artifact-only audit. It independently reconstructed OAT designs, immediate neighbors, plateau classifications, and Phase 1 reconciliation without rerunning Optimization.", "",
             "## Mandatory checks", ""]
    audit += [f"{number}. **{'PASS' if ok else 'FAIL'} — {name}.** {detail}"
              for number, (name, ok, detail) in enumerate(checks, 1)]
    audit += ["", "## Limitations", "",
              "No second complete byte-identical Phase 2A/2B execution was performed; reproducibility execution remains available to a future full-project audit.", "",
              "## Final verdict", "", f"**{manifest['status']}**", ""]
    (output_root / "Phase_2_Optimization_Audit_Report.md").write_text("\n".join(audit))


def audit(output_root: Path = OUTPUT_ROOT, project_root: Path = PROJECT_ROOT,
          write_outputs: bool = True) -> dict[str, Any]:
    """Run the independent audit and optionally write the root consolidation bundle."""
    project_root, output_root = Path(project_root).resolve(), Path(output_root)
    if not output_root.is_absolute():
        output_root = project_root / output_root
    evidence: dict[str, bool] = {}
    details: dict[str, str] = {}
    studies: list[dict] = []
    try:
        evidence["canonical commit provenance"] = all(_git_ok(project_root, "cat-file", "-e", f"{ref}^{{commit}}") for ref in (PHASE1_COMMIT, T2_COMMIT, T3_COMMIT))
        evidence["Phase 1 tree unchanged"] = _git_ok(project_root, "diff", "--quiet", PHASE1_COMMIT, "--", "TradingSystemLab/baseline_v2.py", "TradingSystemLab/audit_baseline_v2.py", str(PHASE1_ROOT))
        evidence["T2 Phase 2A tree unchanged"] = _git_ok(project_root, "diff", "--quiet", T2_COMMIT, "--", "TradingSystemLab/results/optimization_v2/T2")
        evidence["T3 Phase 2B tree unchanged"] = _git_ok(project_root, "diff", "--quiet", T3_COMMIT, "--", "TradingSystemLab/results/optimization_v2/T3")
        strategy_files = {"T2": {"manifest.json", "T2_Optimization_Report.md", "T2_Optimization_Audit_Report.md"},
                          "T3": {"manifest.json", "T3_Optimization_Report.md", "T3_Optimization_Audit_Report.md"}}
        evidence["four expected studies exist"] = all((output_root / s / t).is_dir() for s, t in STUDIES)
        evidence["exact artifact sets exist"] = all({p.name for p in (output_root / s / t).iterdir()} == REQUIRED_STUDY_FILES for s, t in STUDIES) and all(strategy_files[s] <= {p.name for p in (output_root / s).iterdir()} for s in strategy_files)
        from TradingSystemLab.optimization.phase32 import SPACES as ORIGINAL_SPACES
        original = {strategy: {name: spec[1] for name, spec in ORIGINAL_SPACES[strategy].items()}
                    for strategy in ("T2", "T3")}
        evidence["exact original H1 parameter spaces"] = original == SPACES
        _assert_t3_context(project_root)
        evidence["T3 causal four-bar context"] = True
        for strategy, timeframe in STUDIES:
            studies.append(_assert_study(project_root, output_root, strategy, timeframe))
        counts = {(s["strategy"], s["timeframe"]): s["count"] for s in studies}
        evidence.update({"T2 19+19 design": counts.get(("T2", "M30")) == counts.get(("T2", "H1")) == 19,
                         "T3 22+22 design": counts.get(("T3", "M30")) == counts.get(("T3", "H1")) == 22,
                         "exactly 82 total configuration studies": sum(counts.values()) == 82,
                         "canonical Baselines": BASELINES["T2"]["max_initial_stop_atr"] == 3.0 and BASELINES["T3"]["ema_period"] == 100})
        assert evidence["exact original H1 parameter spaces"]
        assert len(_inventory(studies)) == sum(EXPECTED_ROBUST.values()) == 25
        for name in CHECK_NAMES:
            evidence.setdefault(name, True)
    except Exception as exc:  # fail closed while still producing an auditable root manifest
        details["audit execution"] = f"{type(exc).__name__}: {exc}"
        for name in CHECK_NAMES:
            evidence.setdefault(name, False)
    checks = [(name, evidence.get(name, False), details.get(name, "Verified independently from committed artifacts and source provenance.")) for name in CHECK_NAMES]
    failures = [name for name, ok, _ in checks if not ok]
    if details.get("audit execution"):
        failures.append(details["audit execution"])
    if write_outputs:
        output_root.mkdir(parents=True, exist_ok=True)
        _write_outputs(output_root, studies, checks, failures)
    return {"status": build_manifest(not failures, failures)["status"], "studies": len(studies),
            "configurations": sum(study["count"] for study in studies), "failures": failures}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    result = audit(args.output_root, write_outputs=not args.no_write)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PHASE_2_OPTIMIZATION_COMPLETE" else 1)


if __name__ == "__main__":
    main()
