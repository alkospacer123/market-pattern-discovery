#!/usr/bin/env python3
"""Independent fail-closed audit and mutation suite for the Stage 4 freeze."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
POST = HERE.parent
S1, S2, S3 = POST / "stage1_master_evidence", POST / "stage2_portfolio_diversification", POST / "stage3_trade_anatomy"
CANONICAL = "244a5adac2baee3bb28d697efa25299b0a1973ef"
ALLOWED = {"build_structural_hypotheses.py", "audit_structural_hypotheses.py", "structural_hypothesis_registry.csv", "structural_hypothesis_evidence.csv", "structural_hypothesis_validation_contract.csv", "manifest_stage4.json", "audit_stage4_result.json", "Stage_4_Structural_Hypothesis_Set.md"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fail(message: str) -> None:
    raise AssertionError(message)


def validate(reg: list[dict[str, str]], ev: list[dict[str, str]], con: list[dict[str, str]], manifest: dict, report: str, changed: list[str]) -> None:
    if not 1 <= len(reg) <= 5: fail("hypothesis count")
    ids = [r["hypothesis_id"] for r in reg]
    if len(ids) != len(set(ids)) or ids != manifest["admitted_hypothesis_ids"]: fail("identity set")
    if any(r["admitted_status"] != "ADMITTED" for r in reg): fail("unsupported hypothesis")
    if any(r["new_strategy_identity_required"] != "true" for r in reg): fail("old identity reusable")
    if any(not r["fixed_trigger"].strip() or not r["fixed_action"].strip() or not r["falsification_condition"].strip() for r in reg): fail("incomplete mechanics")
    evidence_ids = {r["hypothesis_id"] for r in ev}
    if evidence_ids != set(ids): fail("evidence coverage")
    for h in ids:
        sources = {e["source_stage"] for e in ev if e["hypothesis_id"] == h}
        if not any(s.startswith("Stage 3") for s in sources): fail("missing Stage 3 evidence")
        if "portfolio" in next(r["affected_layer"] for r in reg if r["hypothesis_id"] == h) and "Stage 2" not in sources: fail("missing Stage 2 evidence")
    for e in ev:
        path = ROOT / e["evidence_artifact"]
        if not path.is_file() or sha(path) != e["evidence_sha256"]: fail("evidence SHA")
    if {c["hypothesis_id"] for c in con} != set(ids): fail("contract coverage")
    for c in con:
        if c["validation_stage"] != "Stage 5" or c["causal_reexecution_required"] != "true": fail("causal Stage 5")
        if c["no_parameter_search"] != "true" or c["no_posthoc_tuning"] != "true": fail("tuning permitted")
        if not c["frozen_trigger"] or not c["frozen_action"] or "corresponding unchanged canonical" not in c["baseline_comparator"].lower(): fail("contract mechanics")
        if "test individually only" not in c["frozen_scope"]: fail("combined hypothesis")
    controls = manifest["controls"]
    required = ["no_strategy_execution", "no_backtest", "no_raw_market_data", "no_optimization", "no_ranking", "no_parameter_grid", "no_stage5", "no_production_selection", "individual_testing_only", "no_combined_variants"]
    if not all(controls.get(k) is True for k in required): fail("control disabled")
    if manifest["canonical_stage3d_commit"] != CANONICAL: fail("Stage 3D commit")
    if manifest["stage3d_manifest_sha256"] != sha(S3 / "manifest_stage3d.json") or manifest["stage3d_audit_sha256"] != sha(S3 / "audit_stage3d_result.json"): fail("Stage 3D hash")
    if manifest["stage1_evidence_hashes_used"]["manifest.json"] != sha(S1 / "manifest.json") or manifest["stage2_evidence_hashes_used"]["manifest.json"] != sha(S2 / "manifest.json"): fail("Stage 1/2 reference")
    s3m = json.loads((S3 / "manifest_stage3d.json").read_text()); s3a = json.loads((S3 / "audit_stage3d_result.json").read_text())
    if s3m["audit_status"] != "POST_V3_STAGE_3D_INDEPENDENT_CLOSEOUT_AUDIT_PASSED" or s3m["stage3_status"] != "POST_V3_STAGE_3_TRADE_ANATOMY_FAILURE_ANALYSIS_CLOSED" or s3a["status"] != s3m["audit_status"]: fail("Stage 3D status")
    if "MAE_MFE_ORDER_UNAVAILABLE" not in report or "do not prove BE or trailing would have saved any trade" not in report: fail("causal overclaim")
    if "Every hypothesis is tested individually" not in report or "No hypothesis predicts performance" not in report: fail("combination or prediction")
    if "production selection" not in report or "no parameter search" not in report.lower(): fail("guard language")
    forbidden_ids = {"H4_03_MIN_HOLD", "H4_04_SESSION", "H4_04_CORRELATED_RISK_CAP"}
    if set(ids) & forbidden_ids: fail("unsupported hypothesis")
    for text in [r["fixed_trigger"] + r["fixed_action"] for r in reg]:
        if any(x in text.lower() for x in [" grid", "sweep", "combined with", "backtest result", "ranked #", "optimize"]): fail("grid/ranking/optimization")
    if any(not p.startswith("TradingSystemLab/results/post_v3_analysis/stage4_structural_hypotheses/") for p in changed): fail("protected strategy file")


def rejected(mutator, base) -> bool:
    state = deepcopy(base)
    mutator(state)
    try:
        validate(*state)
    except (AssertionError, KeyError):
        return True
    return False


def main() -> None:
    reg, ev, con = rows("structural_hypothesis_registry.csv"), rows("structural_hypothesis_evidence.csv"), rows("structural_hypothesis_validation_contract.csv")
    manifest = json.loads((HERE / "manifest_stage4.json").read_text())
    report = (HERE / "Stage_4_Structural_Hypothesis_Set.md").read_text()
    changed_text = subprocess.run(["git", "diff", "--name-only", CANONICAL, "--"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    changed = [x for x in changed_text.splitlines() if x]
    # Untracked files are not in git diff until staged; include them explicitly.
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    changed = sorted(set(changed + untracked))
    base = [reg, ev, con, manifest, report, changed]
    validate(*base)
    muts = {
        "add_sixth_hypothesis": lambda s: s[0].extend([deepcopy(s[0][0])] * 3),
        "add_parameter_grid": lambda s: s[0][0].__setitem__("fixed_action", "parameter grid"),
        "add_two_BE_thresholds": lambda s: s[0][0].__setitem__("fixed_action", "threshold sweep"),
        "remove_evidence_reference": lambda s: s.__setitem__(1, [e for e in s[1] if e["hypothesis_id"] != s[0][0]["hypothesis_id"]]),
        "alter_stage3d_hash": lambda s: s[3].__setitem__("stage3d_manifest_sha256", "0" * 64),
        "add_unsupported_hypothesis": lambda s: s[0][0].__setitem__("admitted_status", "NOT_ADMITTED"),
        "mark_old_identity_reusable": lambda s: s[0][0].__setitem__("new_strategy_identity_required", "false"),
        "add_combined_hypothesis": lambda s: s[2][0].__setitem__("frozen_scope", "combined with risk cap"),
        "inject_backtest_result": lambda s: s[0][0].__setitem__("fixed_action", "backtest result 9R"),
        "inject_ranking": lambda s: s[0][0].__setitem__("fixed_action", "ranked #1"),
        "inject_optimization": lambda s: s[0][0].__setitem__("fixed_action", "optimize PF"),
        "inject_production_selection": lambda s: s[3]["controls"].__setitem__("no_production_selection", False),
        "remove_falsification_condition": lambda s: s[0][0].__setitem__("falsification_condition", ""),
        "claim_MAE_MFE_event_ordering": lambda s: s.__setitem__(4, s[4].replace("MAE_MFE_ORDER_UNAVAILABLE", "ORDER_KNOWN")),
        "convert_diagnostic_to_causal_claim": lambda s: s.__setitem__(4, s[4].replace("do not prove BE or trailing would have saved any trade", "prove saved trades")),
        "alter_evidence_SHA": lambda s: s[1][0].__setitem__("evidence_sha256", "0" * 64),
        "allow_posthoc_tuning": lambda s: s[2][0].__setitem__("no_posthoc_tuning", "false"),
        "modify_protected_strategy_file": lambda s: s[5].append("TradingSystemLab/strategies/t2.py"),
    }
    results = {name: rejected(fn, base) for name, fn in muts.items()}
    if len(results) != 18 or not all(results.values()): fail("mutation suite")
    manifest["audit_status"] = "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_AUDIT_PASSED"
    manifest["final_status"] = "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_CLOSED"
    manifest["mutation_tests"] = "18/18 PASS"
    (HERE / "manifest_stage4.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = {
        "status": "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_AUDIT_PASSED", "stage4_status": "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_CLOSED",
        "semantic_checks": "PASS", "canonical_prerequisites": "PASS", "evidence_hashes": "PASS", "protected_tree": "PASS",
        "admitted_hypotheses": len(reg), "mutation_tests_passed": results,
        "output_hashes": {name: sha(HERE / name) for name in sorted(ALLOWED - {"audit_stage4_result.json"})},
    }
    (HERE / "audit_stage4_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if set(p.name for p in HERE.iterdir() if p.is_file()) != ALLOWED: fail("unexpected Stage 4 artifact")
    print("18/18 PASS")
    print(result["status"])
    print(result["stage4_status"])


if __name__ == "__main__":
    main()
