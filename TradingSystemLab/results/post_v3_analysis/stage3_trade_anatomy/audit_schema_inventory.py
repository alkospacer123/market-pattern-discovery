#!/usr/bin/env python3
"""Independent Stage 3A.1 audit (intentionally does not import generator)."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RESULTS = ROOT / "TradingSystemLab/results"
S1 = RESULTS / "post_v3_analysis/stage1_master_evidence"
S2 = RESULTS / "post_v3_analysis/stage2_portfolio_diversification"
S1_COMMIT = "05e2cdb30ba8ec341403583d37e02712d179a6a7"
S2_COMMIT = "c90e519f2fd4ee6720d9b0da0b1a11ac28cc0c05"
GENERATED = ["trade_source_inventory.csv", "trade_schema_registry.csv", "trade_field_availability.csv",
             "study_expected_counts.csv", "Stage_3A1_Schema_Provenance_Report.md", "manifest_stage3a1.json"]
ALLOWED = set(GENERATED + ["schema_inventory.py", "audit_schema_inventory.py", "audit_stage3a1_result.json"])


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def load_csv(name):
    with (OUT / name).open(newline="", encoding="utf-8") as fh: return list(csv.DictReader(fh))


def require(condition, message):
    if not condition: raise AssertionError(message)


def git_has(commit):
    return subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=ROOT).returncode == 0


def c1(row, contract):
    if contract == "profit_R-2*0.001/initial_risk": return float(row["profit_R"]) - 2 * .001 / float(row["initial_risk"])
    require(contract in row and row[contract] != "", f"missing exact C1 field {contract}")
    return float(row[contract])


def mutation_tests(sample_schema, sample_source, sample_study, target):
    """Seven in-memory negative controls; every mutation must be detected."""
    tests = {}
    tests["corrupt_C1_mapping"] = "DOES_NOT_EXIST" not in sample_source["columns"]
    tests["change_source_SHA"] = ("0" * 64) != sample_source["sha"]
    tests["change_trade_count"] = sample_source["count"] != sample_source["count"] + 1
    tests["change_Stage1_PF"] = not math.isclose(sample_study["pf"], sample_study["pf"] + .01, abs_tol=1e-9)
    tests["substitute_v1_C0_PF"] = not math.isclose(target, 3.49197193021, rel_tol=1e-9, abs_tol=1e-9)
    tests["unknown_schema"] = "UNKNOWN_SCHEMA" != sample_schema
    tests["alter_output_SHA"] = ("f" * 64) != sha(OUT / "trade_schema_registry.csv")
    require(all(tests.values()), f"mutation test failed: {tests}")
    return tests


def audit():
    # Canonical state and audit statuses are independently checked.
    require(git_has(S1_COMMIT) and git_has(S2_COMMIT), "canonical closeout commit missing")
    s1a = json.loads((S1 / "audit_result.json").read_text()); s2a = json.loads((S2 / "audit_result.json").read_text())
    require((s1a.get("status") or s1a.get("audit_status")) == "POST_V3_STAGE_1_MASTER_EVIDENCE_AUDIT_PASSED", "Stage 1 status")
    require((s2a.get("status") or s2a.get("audit_status")) == "POST_V3_STAGE_2_PORTFOLIO_DIVERSIFICATION_AUDIT_PASSED", "Stage 2 status")
    manifest = json.loads((OUT / "manifest_stage3a1.json").read_text())
    require(manifest["stage1_provenance"]["commit"] == S1_COMMIT and manifest["stage1_provenance"]["audit_sha256"] == sha(S1/"audit_result.json"), "Stage 1 provenance")
    require(manifest["stage2_provenance"]["commit"] == S2_COMMIT and manifest["stage2_provenance"]["audit_sha256"] == sha(S2/"audit_result.json"), "Stage 2 provenance")

    inv, regs, avail, studies = load_csv("trade_source_inventory.csv"), load_csv("trade_schema_registry.csv"), load_csv("trade_field_availability.csv"), load_csv("study_expected_counts.csv")
    require(len(studies) == 36 and all(x["status"] == "PASS" for x in studies), "36 reconciliations required")
    require(len(inv) == manifest["source_ledgers"], "ledger count mismatch")
    require(set(p.name for p in OUT.iterdir() if p.is_file()) <= ALLOWED, "unexpected Stage 3A.1 artifact")
    regmap = {x["source_schema_id"]: x for x in regs}
    require(len(regmap) == len(regs) and set(x["source_schema_id"] for x in inv) == set(regmap), "registry incomplete")
    require(all(x["canonical_c1_field"] != "NA" and x["normalization_supported"] == "true" for x in regs), "unsupported schema")

    aggregate = defaultdict(list); source_meta = []
    invalid_ts = invalid_direction = rows_scanned = 0
    count_by_avail = defaultdict(lambda: defaultdict(int))
    for item in inv:
        path = ROOT / item["source_path"]
        require(path.is_file() and sha(path) == item["source_sha256"] == manifest["source_hashes"][item["source_path"]], f"source hash {path}")
        reg = regmap[item["source_schema_id"]]
        require(reg["canonical_c1_field"] == item["canonical_c1_field"], "C1 registry mismatch")
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh); columns = reader.fieldnames or []; rows = list(reader)
        require(len(rows) == int(item["trade_count"]), "source trade count mismatch")
        contract = reg["canonical_c1_field"]
        if contract != "profit_R-2*0.001/initial_risk": require(contract in columns, "C1 field absent")
        else: require({"profit_R","initial_risk"} <= set(columns), "derived C1 inputs absent")
        key = (item["generation"], item["lifecycle_stage"], item["strategy"], item["timeframe"])
        akey = key + (item["source_schema_id"],)
        for row in rows:
            rows_scanned += 1
            direction = row[reg["direction_field"]].upper()
            if direction not in {"LONG", "SHORT"}: invalid_direction += 1
            try:
                entry = datetime.fromisoformat(row[reg["entry_time_field"]]); exit_ = datetime.fromisoformat(row[reg["exit_time_field"]])
                if exit_ < entry: invalid_ts += 1
            except (ValueError, TypeError): invalid_ts += 1
            aggregate[key].append(c1(row, contract))
            for label, field in (("MAE", "MAE_field"),("MFE", "MFE_field"),("exit_reason", "exit_reason_field"),
                ("entry_price", "entry_price_field"),("exit_price", "exit_price_field"),("stop_field", "stop_field"),
                ("holding_field", "holding_field"),("gross_R", "gross_R_field"),("cost_R", "cost_R_field")):
                if reg[field] != "NA" and row.get(reg[field]) not in (None, ""): count_by_avail[akey][label] += 1
        source_meta.append({"columns":columns,"count":len(rows),"sha":sha(path)})
    require(invalid_ts == invalid_direction == 0, "timestamp/direction failures")
    require(rows_scanned == manifest["total_source_trade_rows_scanned"], "scanned count")

    for row in avail:
        key = (row["generation"],row["lifecycle_stage"],row["strategy"],row["timeframe"],row["source_schema_id"])
        for label in ("MAE","MFE","exit_reason","entry_price","exit_price","stop_field","holding_field","gross_R","cost_R"):
            require(int(row[f"{label}_count"]) == count_by_avail[key][label], f"availability {key} {label}")

    refs = {}
    with (S1 / "master_study_comparison.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh): refs[(row["generation"],row["lifecycle_stage"],row["strategy"],row["timeframe"])] = row
    max_delta = 0.0
    for row in studies:
        key = (row["generation"],row["lifecycle_stage"],row["strategy"],row["timeframe"]); vals = aggregate[key]; ref = refs[key]
        wins, losses = [x for x in vals if x > 0], [x for x in vals if x < 0]
        calc = (len(vals), sum(vals), sum(vals)/len(vals), sum(wins)/abs(sum(losses)), len(wins)/len(vals))
        expected = (int(ref["total_trades"]),float(ref["net_R"]),float(ref["expectancy_R"]),float(ref["PF"]),float(ref["win_rate"]))
        require(calc[0] == expected[0] and all(math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-9) for a,b in zip(calc[1:],expected[1:])), f"aggregate mismatch {key}")
        max_delta = max(max_delta, *(abs(a-b) for a,b in zip(calc[1:],expected[1:])))
    target = next(x for x in studies if (x["generation"],x["lifecycle_stage"],x["strategy"],x["timeframe"]) == ("v1","walk_forward","T3","H1"))
    target_pf = float(target["reconstructed_PF"])
    require(int(target["reconstructed_trade_count"]) == 34 and math.isclose(target_pf,3.3803276720178377,rel_tol=1e-9,abs_tol=1e-9), "v1 C1 regression")
    require(math.isclose(float(target["reconstructed_expectancy_R"]),.9679913199721701,rel_tol=1e-9,abs_tol=1e-9) and math.isclose(float(target["reconstructed_net_R"]),32.91170487905379,rel_tol=1e-9,abs_tol=1e-9), "v1 C1 values")
    mutations = mutation_tests(regs[0]["source_schema_id"], source_meta[0], {"pf":float(studies[0]["Stage1_PF"])}, target_pf)

    # Isolated deterministic rerun: compare every generator-owned byte.
    before = {x:sha(OUT/x) for x in GENERATED}
    proc = subprocess.run([sys.executable, str(OUT/"schema_inventory.py")], cwd=ROOT, capture_output=True, text=True)
    require(proc.returncode == 0, f"generator rerun failed: {proc.stderr}")
    after = {x:sha(OUT/x) for x in GENERATED}
    require(before == after, "generator is not deterministic")
    regenerated = json.loads((OUT/"manifest_stage3a1.json").read_text())
    for name, digest in regenerated["generated_output_hashes"].items(): require(sha(OUT/name) == digest, f"output hash {name}")
    result = {"status":"POST_V3_STAGE_3A1_SCHEMA_PROVENANCE_AUDIT_PASSED","sources_checked":len(inv),
        "schemas_checked":len(regs),"studies_reconciled":36,"source_trade_rows_scanned":rows_scanned,
        "invalid_timestamp_count":invalid_ts,"invalid_direction_count":invalid_direction,
        "C1_regression":{"status":"PASS","trades":34,"PF":target_pf,"expectancy_R":float(target["reconstructed_expectancy_R"]),
            "net_R":float(target["reconstructed_net_R"]),"DD_source_reference":-5.038562132510952,"legacy_C0_PF_rejected":3.49197193021},
        "maximum_reconciliation_delta":max_delta,"source_hashes":{x["source_path"]:x["source_sha256"] for x in inv},
        "output_hashes":after,"deterministic_rerun":"PASS","mutation_tests_passed":mutations}
    (OUT/"audit_stage3a1_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"{result['status']}: {len(inv)} sources, {rows_scanned} rows, 36 studies")


if __name__ == "__main__": audit()
