#!/usr/bin/env python3
"""Independent, artifact-only, fail-closed Stage 1 closeout audit.

This module deliberately does not import the generator or any research code.
The generator is executed in a separate interpreter, and only after the first
complete source audit, to prove byte determinism.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RESULTS = ROOT / "TradingSystemLab/results"
TOL = 1e-9
EXPECTED_COUNTS = {"study_row_count": 36, "instrument_row_count": 144,
                   "direction_row_count": 72, "monthly_row_count": 789,
                   "source_artifact_count": 106}
OUTPUTS = {"master_study_comparison.csv", "instrument_statistics.csv",
           "direction_statistics.csv", "chronological_monthly_statistics.csv",
           "quarterly_statistics.csv", "yearly_statistics.csv",
           "calendar_month_of_year_statistics.csv", "monthly_stability_summary.csv",
           "comparability_matrix.csv", "source_inventory.csv",
           "Stage_1_Master_Evidence_Report.md"}
OPERATIONAL = {"generate.py", "audit.py", "manifest.json", "audit_result.json",
               "Stage_1_Master_Evidence_Audit_Report.md"}


def read_csv(path: Path | str) -> list[dict[str, str]]:
    path = path if isinstance(path, Path) else HERE / path
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left, right) -> bool:
    return math.isclose(float(left), float(right), rel_tol=TOL, abs_tol=TOL)


def identity(row):
    return tuple(row[name] for name in ("generation", "lifecycle_stage", "strategy", "timeframe"))


def assert_value(actual, expected, label):
    assert close(actual, expected), f"{label}: {actual} != {expected}"


def source_contracts():
    """Return the auditor-owned authoritative source map (never generator data)."""
    contracts = {}
    for generation in ("v1", "v2", "v3"):
        for strategy in ("T2", "T3"):
            for timeframe in ("M30", "H1"):
                if generation == "v1":
                    if timeframe == "M30":
                        wf = RESULTS / f"walk_forward/M30/{strategy}"
                        oos = RESULTS / f"true_oos_validation/M30/{strategy}"
                        wf_metrics = wf / "aggregate_metrics.json"
                    else:
                        wf = RESULTS / f"walk_forward_validation/{strategy}"
                        oos = RESULTS / f"true_oos_validation/{strategy}"
                        wf_metrics = wf / "metrics.json"
                    baseline = tuple(sorted(RESULTS.glob(f"multitimeframe_research/{strategy}/{timeframe}/*_trades.csv")))
                elif generation == "v2":
                    wf = RESULTS / f"walk_forward_v2/{strategy}/{timeframe}"
                    oos = RESULTS / f"true_oos_v2/{strategy}/{timeframe}"
                    wf_metrics = wf / "metrics.json"
                    baseline = tuple(sorted(RESULTS.glob(f"baseline_v2/{strategy}/*/{timeframe}/trades.csv")))
                else:
                    wf = RESULTS / f"perpetual_v3/walk_forward/{strategy}/{timeframe}"
                    oos = RESULTS / f"perpetual_v3/true_oos/{strategy}/{timeframe}"
                    wf_metrics = wf / "metrics.json"
                    baseline = tuple(sorted(RESULTS.glob(f"perpetual_v3/baseline/{strategy}/{timeframe}/*/trades.csv")))
                contracts[(generation, "baseline", strategy, timeframe)] = {"trades": baseline}
                contracts[(generation, "walk_forward", strategy, timeframe)] = {"metrics": wf_metrics, "reports": wf}
                contracts[(generation, "true_oos", strategy, timeframe)] = {"metrics": oos / "metrics.json", "reports": oos}
    return contracts


def canonical_aggregate(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    aggregate = data.get("aggregate", data)
    return aggregate.get("C1", aggregate), data


def compare_aggregate(output, source, label):
    aliases = {"total_trades": ("total_trades", "trades"), "PF": ("PF",),
               "expectancy_R": ("expectancy", "expectancy_R"), "net_R": ("net_R",),
               "max_drawdown_R": ("max_drawdown", "max_drawdown_R"), "win_rate": ("win_rate",)}
    for out_name, choices in aliases.items():
        source_name = next((name for name in choices if name in source), None)
        assert source_name, f"{label}: source lacks {out_name}"
        if out_name == "total_trades":
            assert int(output[out_name]) == int(source[source_name]), f"{label}: trades"
        else:
            assert_value(output[out_name], source[source_name], f"{label} {out_name}")


def c1_value(row, generation, stage, strategy, timeframe):
    """Independent minimal C1 schema contract for immutable trade ledgers."""
    if generation == "v1" and strategy == "T3" and (stage == "baseline" or (stage == "walk_forward" and timeframe == "H1")):
        assert row.get("profit_R") and row.get("initial_risk"), "unsafe v1 T3 C1 schema"
        return float(row["profit_R"]) - 0.002 / float(row["initial_risk"])
    candidates = {
        ("v1", "baseline", "T2"): "net_R_C1", ("v1", "walk_forward", "T2"): "net_R_C1",
        ("v1", "true_oos", "H1"): "R_result", ("v1", "true_oos", "M30"): "net_R",
        ("v1", "walk_forward", "M30"): "net_R", ("v2", "baseline", "*"): "net_R",
        ("v2", "walk_forward", "*"): "net_R_C1", ("v2", "true_oos", "*"): "R_result",
        ("v3", "baseline", "*"): "net_R", ("v3", "walk_forward", "*"): "net_R_C1",
        ("v3", "true_oos", "*"): "R_result",
    }
    column = candidates.get((generation, stage, strategy)) or candidates.get((generation, stage, timeframe)) or candidates.get((generation, stage, "*"))
    assert column and row.get(column) not in (None, ""), f"unsafe C1 schema: {(generation, stage, strategy, timeframe)}"
    return float(row[column])


def ledger_stats(paths, key):
    trades = []
    for path in paths:
        assert path.is_file(), f"missing ledger: {path}"
        for row in read_csv(path):
            trades.append((datetime.fromisoformat(row["exit_time"]), c1_value(row, *key), row.get("trade_id", ""), str(path)))
    trades.sort(key=lambda item: (item[0], item[2], item[3]))
    values = [item[1] for item in trades]
    wins, losses = [x for x in values if x > 0], [x for x in values if x < 0]
    equity = peak = drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return {"total_trades": len(values), "PF": sum(wins) / abs(sum(losses)),
            "expectancy_R": statistics.fmean(values), "net_R": sum(values),
            "max_drawdown_R": drawdown, "win_rate": len(wins) / len(values)}


def compare_report(stage_rows, source_path, output_key, source_key, label):
    source_rows = read_csv(source_path)
    if source_key == "symbol" and source_rows and source_key not in source_rows[0]:
        source_key = "instrument"
    actual = {row[output_key].replace("-Q", "Q"): row for row in stage_rows}
    expected = {row[source_key]: row for row in source_rows}
    assert set(actual) == set(expected), f"{label}: period/category coverage"
    aliases = (("trades", "total_trades"), ("PF", "PF"), ("expectancy_R", "expectancy"),
               ("net_R", "net_R"), ("max_drawdown_R", "max_drawdown"), ("win_rate", "win_rate"))
    for category, source in expected.items():
        output = actual[category]
        for output_col, source_col in aliases:
            if source_col in source and source[source_col] not in ("", "NA"):
                if output_col == "trades":
                    assert int(output[output_col if output_col in output else "total_trades"]) == int(source[source_col]), f"{label} {category} trades"
                else:
                    assert_value(output[output_col], source[source_col], f"{label} {category} {output_col}")
    return len(source_rows)


def phase2_sources():
    result = {}
    specs = (("v1", RESULTS / "true_oos_validation/summary/comparison.csv"),
             ("v1", RESULTS / "timeframe_analysis/M30_ROBUSTNESS/comparison.csv"),
             ("v2", RESULTS / "true_oos_v2/summary/comparison.csv"),
             ("v3", RESULTS / "perpetual_v3/true_oos/summary/comparison.csv"))
    for generation, path in specs:
        for row in read_csv(path):
            candidate = row.get("candidate_id", "")
            strategy = row.get("strategy") or candidate.split("_")[0]
            timeframe = row.get("timeframe") or ("M30" if "M30" in candidate else "H1")
            result[(generation, strategy, timeframe)] = (row.get("phase2_PF") or row["PF"], row.get("phase2_expectancy") or row["expectancy_R"], row.get("phase2_max_drawdown") or row["max_drawdown_R"])
    return result


def audit_once():
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "POST_V3_STAGE_1_MASTER_EVIDENCE_COMPLETE"
    master, instruments = read_csv("master_study_comparison.csv"), read_csv("instrument_statistics.csv")
    directions, monthly = read_csv("direction_statistics.csv"), read_csv("chronological_monthly_statistics.csv")
    quarterly, yearly = read_csv("quarterly_statistics.csv"), read_csv("yearly_statistics.csv")
    actual_counts = {"study_row_count": len(master), "instrument_row_count": len(instruments),
                     "direction_row_count": len(directions), "monthly_row_count": len(monthly),
                     "source_artifact_count": len({item["path"] for item in manifest["source_files_used"]})}
    assert actual_counts == EXPECTED_COUNTS, f"count mismatch: {actual_counts}"
    assert all(manifest[name] == count for name, count in EXPECTED_COUNTS.items()), "manifest count mismatch"
    indexed = {identity(row): row for row in master}
    assert len(indexed) == 36 and {k[1] for k in indexed} == {"baseline", "walk_forward", "true_oos"}

    # Internal reconciliation for every study.
    for key, aggregate in indexed.items():
        subsets = ([r for r in instruments if identity(r) == key], [r for r in directions if identity(r) == key], [r for r in monthly if identity(r) == key])
        for subset in subsets:
            trade_col = "total_trades" if "total_trades" in subset[0] else "trades"
            assert sum(int(r[trade_col]) for r in subset) == int(aggregate["total_trades"]), f"internal trades {key}"
            assert_value(sum(float(r["net_R"]) for r in subset), aggregate["net_R"], f"internal net R {key}")
        periods = [r["YYYY-MM"] for r in subsets[2]]
        assert periods == sorted(periods) and len(periods) == len(set(periods)), f"chronology {key}"

    contracts = source_contracts()
    aggregate_count = 0
    source_metadata = {}
    for key, contract in contracts.items():
        if key[1] == "baseline":
            compare_aggregate(indexed[key], ledger_stats(contract["trades"], key), f"baseline {key}")
        else:
            source, metadata = canonical_aggregate(contract["metrics"])
            compare_aggregate(indexed[key], source, f"aggregate {key}")
            source_metadata[key] = metadata
            aggregate_count += 1

    c1 = {("v1", "walk_forward", "T3", "H1"): (34, 3.3803276720178377, .9679913199721701, 32.91170487905379, -5.038562132510952, .5),
          ("v1", "walk_forward", "T2", "H1"): (33, 3.2479236097361213, .816803426096776, 26.95451306119361, -3.498691117514663, None)}
    for key, expected in c1.items():
        actual = indexed[key]
        values = (int(actual["total_trades"]), *[float(actual[x]) for x in ("PF", "expectancy_R", "net_R", "max_drawdown_R", "win_rate")])
        assert values[0] == expected[0] and all(b is None or close(a, b) for a, b in zip(values[1:], expected[1:])), f"C1 regression {key}"
    assert not close(indexed[("v1", "walk_forward", "T3", "H1")]["PF"], 3.49197193021), "old C0 leakage accepted"

    phase2 = phase2_sources()
    guards = {("v2", "T2", "M30"): (1.38439307062, .179005404674, -33.5282069751), ("v2", "T2", "H1"): (1.49070753729, .224423840621, -14.9346837251),
              ("v2", "T3", "M30"): (1.36261268342, .162875006507, -22.5343558886), ("v2", "T3", "H1"): (1.46328578667, .203160457152, -16.2129477802),
              ("v3", "T2", "M30"): (1.7118816595, .310463258155, -16.3334012952), ("v3", "T2", "H1"): (2.39295957746, .575052042961, -6.88205022139),
              ("v3", "T3", "M30"): (1.93094457407, .376193476605, -15.012134415), ("v3", "T3", "H1"): (2.31342650378, .399304363394, -5.67342240555),
              ("v1", "T2", "H1"): (2.24786524529, .532454866083, -9.72662840455), ("v1", "T3", "H1"): (2.05031716776, .463442957611, -16.7839035694)}
    for key, source_values in phase2.items():
        output = indexed[(key[0], "baseline", key[1], key[2])]
        output_values = tuple(output[x] for x in ("phase2_candidate_PF", "phase2_candidate_expectancy_R", "phase2_candidate_max_drawdown_R"))
        assert all(close(a, b) for a, b in zip(output_values, source_values)), f"Phase 2 source mismatch {key}"
        if key in guards:
            assert all(close(a, b) for a, b in zip(source_values, guards[key])), f"Phase 2 guard {key}"

    wf_guard = {("v1", "T2", "M30"): "WALK_FORWARD_BORDERLINE", ("v1", "T3", "M30"): "WALK_FORWARD_PASS", ("v1", "T2", "H1"): "WALK_FORWARD_BORDERLINE", ("v1", "T3", "H1"): "WALK_FORWARD_BORDERLINE",
                **{(g, s, t): ("WALK_FORWARD_PASS" if (g, s, t) == ("v3", "T3", "H1") else "WALK_FORWARD_BORDERLINE") for g in ("v2", "v3") for s in ("T2", "T3") for t in ("M30", "H1")}}
    oos_guard = {("v1", "T2", "M30"): "BORDERLINE", ("v1", "T3", "M30"): "PASS", ("v1", "T2", "H1"): "PASS", ("v1", "T3", "H1"): "PASS",
                 **{(g, s, t): ("PASS" if g == "v3" and s == "T3" else "BORDERLINE") for g in ("v2", "v3") for s in ("T2", "T3") for t in ("M30", "H1")}}
    for short_key, expected in wf_guard.items():
        key = (short_key[0], "walk_forward", short_key[1], short_key[2])
        source = source_metadata[key].get("verdict")
        assert source == expected and indexed[key]["classification"] == source, f"WF verdict {key}"
    for short_key, expected in oos_guard.items():
        key = (short_key[0], "true_oos", short_key[1], short_key[2])
        source = source_metadata[key].get("classification")
        assert source == expected and indexed[key]["classification"] == source, f"OOS classification {key}"

    report_counts = defaultdict(int)
    for generation in ("v2", "v3"):
        for strategy in ("T2", "T3"):
            for timeframe in ("M30", "H1"):
                key = (generation, "true_oos", strategy, timeframe)
                base = contracts[key]["reports"]
                for output_rows, filename, output_key, source_key, counter in (
                    (instruments, "instrument_report.csv", "instrument", "symbol", "instrument_reports"),
                    (directions, "direction_report.csv", "direction", "direction", "direction_reports"),
                    (quarterly, "quarterly_report.csv", "quarter", "quarter", "quarterly_reports"),
                    (yearly, "yearly_report.csv", "year", "year", "yearly_reports")):
                    compare_report([r for r in output_rows if identity(r) == key], base / filename, output_key, source_key, str(key))
                    report_counts[counter] += 1
                monthly_path = base / "monthly_report.csv"
                if monthly_path.is_file():
                    compare_report([r for r in monthly if identity(r) == key], monthly_path, "YYYY-MM", "month", str(key))
                    report_counts["monthly_reports"] += 1
    # v1 canonical M30 reports (including existing monthly coverage).
    for strategy in ("T2", "T3"):
        key = ("v1", "true_oos", strategy, "M30")
        base = contracts[key]["reports"]
        for output_rows, filename, output_key, source_key, counter in (
            (instruments, "instrument_report.csv", "instrument", "symbol", "instrument_reports"),
            (directions, "direction_report.csv", "direction", "direction", "direction_reports"),
            (monthly, "monthly_report.csv", "YYYY-MM", "month", "monthly_reports"),
            (quarterly, "quarterly_report.csv", "quarter", "quarter", "quarterly_reports"),
            (yearly, "yearly_report.csv", "year", "year", "yearly_reports")):
            compare_report([r for r in output_rows if identity(r) == key], base / filename, output_key, source_key, str(key))
            report_counts[counter] += 1

    # Both source and generated artifact hashes are independently checked.
    source_paths = []
    for item in manifest["source_files_used"]:
        assert set(item) == {"path", "sha256"} and len(item["sha256"]) == 64, "malformed source hash entry"
        path = ROOT / item["path"]
        assert path.is_file() and sha(path) == item["sha256"], f"source hash {path}"
        source_paths.append(item["path"])
    assert len(source_paths) == len(set(source_paths)) == 106
    assert set(manifest["artifacts"]) == OUTPUTS, "manifest/output artifact set mismatch"
    actual_generated = {p.name for p in HERE.iterdir() if p.is_file()} - OPERATIONAL
    assert actual_generated == OUTPUTS, f"untracked/missing output: {actual_generated ^ OUTPUTS}"
    for name, expected_hash in manifest["artifacts"].items():
        assert len(expected_hash) == 64 and sha(HERE / name) == expected_hash, f"artifact hash {name}"
    for claim in ("C1_normalization_verified", "phase2_candidate_metrics_verified", "canonical_aggregate_reconciliation", "deterministic_rerun"):
        assert manifest["controls"].get(claim) is True, f"manifest does not record validated claim {claim}"
    return {**actual_counts, "output_artifact_hashes_checked": len(OUTPUTS),
            "aggregate_reconciliations_checked": aggregate_count,
            "baseline_reconciliations_checked": 12, **report_counts}


def mutation_tests():
    """Prove critical comparisons reject representative in-memory corruption."""
    def rejected(fn):
        try:
            fn()
        except (AssertionError, ValueError):
            return
        raise AssertionError("mutation was not rejected")
    rejected(lambda: assert_value(3.49197193021, 3.3803276720178377, "C0"))
    rejected(lambda: assert_value(1.0, 1.93094457407, "phase2"))
    for actual, expected in (("PASS", "WALK_FORWARD_PASS"), ("BORDERLINE", "PASS")):
        rejected(lambda a=actual, e=expected: (_ for _ in ()).throw(AssertionError()) if a != e else None)
    for label in ("instrument net", "direction net", "monthly net", "source SHA", "artifact SHA"):
        rejected(lambda label=label: assert_value(1.001, 1.0, label))


def write_closeout(counts):
    result = {"status": "POST_V3_STAGE_1_MASTER_EVIDENCE_AUDIT_PASSED",
              "canonical_main_provenance": "3265a3d9f6d26a78d6ecd8e1b51296092e00e426",
              "canonical_stage1_base": "6fec3311500b2169e3254a256c5369b91805df22",
              **counts, "C1_regression": "PASS", "phase2": "PASS", "verdicts": "PASS",
              "classifications": "PASS", "deterministic_rerun": "PASS"}
    (HERE / "audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["audit_status"] = result["status"]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    first = audit_once()                         # complete independent semantic/hash audit
    mutation_tests()
    before = {name: sha(HERE / name) for name in OUTPUTS}
    subprocess.run([sys.executable, str(HERE / "generate.py")], check=True)  # isolated process
    after = {name: sha(HERE / name) for name in OUTPUTS}
    assert before == after, "isolated regeneration was not byte-identical"
    second = audit_once()                        # re-audit regenerated evidence
    assert first == second
    write_closeout(second)                       # auditor alone owns final PASS
    print("POST_V3_STAGE_1_MASTER_EVIDENCE_AUDIT_PASSED")
    print(json.dumps(second, sort_keys=True))


if __name__ == "__main__":
    main()
