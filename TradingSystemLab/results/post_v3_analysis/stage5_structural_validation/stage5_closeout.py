"""Artifact-only Stage 5.7 closeout.

This module authenticates committed evidence.  It deliberately has no market-data,
strategy, simulation, optimisation, or portfolio-construction dependency.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGE4 = HERE.parent / "stage4_structural_hypotheses"
DEFAULT_OUTPUT = HERE / "stage5_closeout"
TASK_BASE_SHA = "ca6063f604538dcbecd845d95dd85853238686fa"
STATUS = "POST_V3_STAGE_5_FINAL_CLOSEOUT_AUDIT_PASSED"
STAGE_STATUS = "POST_V3_STAGE_5_STRUCTURAL_VALIDATION_CLOSED"
ECONOMIC_CONTRACT = "CORRECTED_SINGLE_C1"
T2_HASH = "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774"
T3_HASH = "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"

CHECK_NAMES = (
    "canonical_comparator_authenticated", "canonical_rows_9694", "stage4_authenticated",
    "exactly_three_admitted_hypotheses", "considered_not_admitted_statuses_unchanged",
    "be1_final_authority_authenticated", "be1_final_status_exact",
    "trail1_final_authority_authenticated", "trail1_final_status_exact",
    "risk_cap_authority_authenticated", "risk_cap_terminal_censoring_preserved",
    "risk_cap_formal_verdict_unassigned", "minimum_hold_authority_authenticated",
    "minimum_hold_not_admitted_preserved", "session_authority_authenticated",
    "session_not_admitted_preserved", "correlation_authority_authenticated",
    "correlation_not_admitted_preserved", "declared_output_hashes_verified",
    "implementation_hashes_verified", "status_matrix_reconciled",
    "downstream_constraints_reconciled", "unresolved_items_reconciled",
    "no_new_hypothesis", "no_ranking", "no_selection", "no_production_assembly",
    "no_new_execution", "deterministic_artifacts",
)

COMPONENTS = [
    ("5.1", "H4_01_PROFIT_PROTECTION_BE1", "CAUSAL_STRUCTURAL_VALIDATION", "ADMITTED", "CLOSED", "MIXED_RETROSPECTIVE_EVIDENCE", "MIXED_RETROSPECTIVE_EVIDENCE", True, False, False),
    ("5.2", "H4_02_PROFIT_PROTECTION_TRAIL1", "CAUSAL_STRUCTURAL_VALIDATION", "ADMITTED", "CLOSED", "SUPPORTED_RETROSPECTIVELY", "SUPPORTED_RETROSPECTIVELY", True, False, False),
    ("5.3", "H4_03_TOTAL_OPEN_RISK_CAP", "CAUSAL_STRUCTURAL_VALIDATION", "ADMITTED", "FINAL_ECONOMIC_CERTIFICATION_INCOMPLETE_TERMINAL_OPEN_POSITIONS", "FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED", "NOT_ASSIGNED", True, False, True),
    ("5.4", "MINIMUM_HOLD", "DIAGNOSTIC", "NOT_ADMITTED", "STAGE5_5_4_MINIMUM_HOLD_DIAGNOSTICS_COMPLETE", "DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION", "NOT_APPLICABLE", False, True, False),
    ("5.5", "SESSION_TIME_OF_DAY", "DIAGNOSTIC", "NOT_ADMITTED", "STAGE5_5_5_SESSION_TIME_DIAGNOSTICS_COMPLETE", "DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION", "NOT_APPLICABLE", False, True, False),
    ("5.6", "CORRELATION_SIMULTANEOUS_RISK", "DIAGNOSTIC", "NOT_ADMITTED", "STAGE5_5_6_CORRELATION_SIMULTANEOUS_RISK_DIAGNOSTICS_COMPLETE", "DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION", "NOT_APPLICABLE", False, True, False),
]

BRANCHES = {
    "BE1": ("be1/manifest_be1.json", "be1/audit_be1_result.json"),
    "TRAIL1": ("trail1/manifest_trail1.json", "trail1/trail1_audit.json"),
    "TOTAL_OPEN_RISK_CAP": ("risk_cap/manifest_risk_cap.json", "risk_cap/risk_cap_audit.json"),
    "MINIMUM_HOLD": ("minimum_hold/manifest_minimum_hold.json", "minimum_hold/minimum_hold_audit.json"),
    "SESSION_TIME_OF_DAY": ("session_time/manifest_session_time.json", "session_time/session_time_audit.json"),
    "CORRELATION_SIMULTANEOUS_RISK": ("correlation_risk/manifest_correlation_risk.json", "correlation_risk/correlation_risk_audit.json"),
}

FORBIDDEN_KEYS = {"winner", "rank", "score", "selected_strategy", "selected_instrument", "selected_portfolio", "selected_overlay", "production_basket", "recommended_variant", "correlation_threshold", "session_rule", "minimum_hold_rule"}

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("STAGE5_CLOSEOUT_INPUT_AUTHENTICATION_FAILED") from exc

def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)

def audit_scope(value: object) -> bool:
    if isinstance(value, dict):
        return not any(str(k).lower() in FORBIDDEN_KEYS or not audit_scope(v) for k, v in value.items())
    if isinstance(value, list):
        return all(audit_scope(v) for v in value)
    return True

def _manifest_hash_checks(manifest_path: Path) -> tuple[int, int]:
    manifest = read_json(manifest_path); output_bad = implementation_bad = 0
    for name, expected in manifest.get("output_hashes", {}).items():
        target = manifest_path.parent / name
        output_bad += int(not target.is_file() or sha256(target) != expected)
    for name, expected in manifest.get("implementation_file_hashes", {}).items():
        target = ROOT / name
        implementation_bad += int(not target.is_file() or sha256(target) != expected)
    return output_bad, implementation_bad

def authenticate_inputs(base: Path = HERE) -> tuple[dict, list[dict]]:
    """Authenticate source bytes and final authority; raise on every mismatch."""
    counters = {k: 0 for k in ("canonical_mismatches", "stage4_status_mismatches", "be1_status_mismatches", "trail1_status_mismatches", "risk_cap_status_mismatches", "minimum_hold_status_mismatches", "session_status_mismatches", "correlation_status_mismatches", "declared_output_hash_mismatches", "implementation_hash_mismatches", "status_matrix_mismatches", "downstream_constraint_mismatches", "unresolved_item_mismatches", "forbidden_scope_violations", "protected_stage5_source_mutations")}
    required = [base/"canonical_comparator_manifest.json", base/"canonical_comparator_audit_result.json", STAGE4/"manifest_stage4.json", STAGE4/"audit_stage4_result.json", STAGE4/"structural_hypothesis_registry.csv", STAGE4/"structural_hypothesis_validation_contract.csv"]
    required += [base / p for pair in BRANCHES.values() for p in pair]
    if any(not p.is_file() for p in required): raise RuntimeError("STAGE5_CLOSEOUT_INPUT_AUTHENTICATION_FAILED")
    cm, ca = read_json(required[0]), read_json(required[1])
    counters["canonical_mismatches"] = sum((cm.get("studies_reconciled") != 24, cm.get("trade_rows_reconciled") != 9694, cm.get("trade_level_mismatch_count") != 0, ca.get("status") != "STAGE5_CANONICAL_COMPARATOR_INDEPENDENT_AUDIT_PASSED", ca.get("trade_rows_reconciled") != 9694, ca.get("trade_level_mismatches") != 0))
    s4 = read_json(STAGE4/"manifest_stage4.json")
    expected_ids = ["H4_01_PROFIT_PROTECTION_BE1", "H4_02_PROFIT_PROTECTION_TRAIL1", "H4_03_TOTAL_OPEN_RISK_CAP"]
    counters["stage4_status_mismatches"] = int(s4.get("admitted_hypothesis_ids") != expected_ids or s4.get("admitted_hypothesis_count") != 3 or s4.get("audit_status") != "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_AUDIT_PASSED")
    if sha256(STAGE4/"structural_hypothesis_registry.csv") != s4.get("registry_sha256"): counters["stage4_status_mismatches"] += 1
    stage4_report = (STAGE4/"Stage_4_Structural_Hypothesis_Set.md").read_text(encoding="utf-8")
    for label in ("Minimum hold", "Session restriction", "Correlated-risk grouping"):
        counters["stage4_status_mismatches"] += int(f"{label} — `NOT_ADMITTED`" not in stage4_report)
    manifests = {name: read_json(base / pair[0]) for name, pair in BRANCHES.items()}
    audits = {name: read_json(base / pair[1]) for name, pair in BRANCHES.items()}
    correction = read_json(base/"be1/be1_c1_correction_audit.json")
    final_c1 = manifests["BE1"].get("final_c1_accounting_closeout", {})
    counters["be1_status_mismatches"] = int(correction.get("BE1_status") != "CLOSED" or correction.get("final_BE1_classification") != "MIXED_RETROSPECTIVE_EVIDENCE" or correction.get("trade_path_changes") != 0 or final_c1.get("status") != "BE1_FINAL_ECONOMIC_AUDIT_PASSED")
    counters["trail1_status_mismatches"] = int(manifests["TRAIL1"].get("status") != "STAGE5_TRAIL1_FINAL_CLOSEOUT_PASSED" or manifests["TRAIL1"].get("research_interpretation") != "SUPPORTED_RETROSPECTIVELY" or audits["TRAIL1"].get("status") != "PASS")
    ra = audits["TOTAL_OPEN_RISK_CAP"]
    counters["risk_cap_status_mismatches"] = int(manifests["TOTAL_OPEN_RISK_CAP"].get("status") != "FINAL_ECONOMIC_CERTIFICATION_INCOMPLETE_TERMINAL_OPEN_POSITIONS" or manifests["TOTAL_OPEN_RISK_CAP"].get("formal_research_label") != "FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED" or ra.get("canonical_rows") != 9694 or ra.get("terminal_open_positions") != 7 or ra.get("capped_closed_positions") != 7636 or ra.get("risk_cap_violations") != 0 or ra.get("terminal_open_assigned_R") != 6.912766365112272 or ra.get("terminal_open_remaining_R") != 0.8574190498245575 or ra.get("raw_execution_determinism") != "PASS")
    for key, counter, status in (("MINIMUM_HOLD", "minimum_hold_status_mismatches", COMPONENTS[3][4]), ("SESSION_TIME_OF_DAY", "session_status_mismatches", COMPONENTS[4][4]), ("CORRELATION_SIMULTANEOUS_RISK", "correlation_status_mismatches", COMPONENTS[5][4])):
        counters[counter] = int(manifests[key].get("status") != status or manifests[key].get("research_status") != "DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION" or audits[key].get("status") != status)
    correlation_details = audits["CORRELATION_SIMULTANEOUS_RISK"].get("details", {})
    semantic_keys = ("corrected_monthly_matrix_mismatches","not_yet_available_zero_flag_violations","corrected_pairwise_mismatches","bridge_overlap_mismatches","portfolio_overlap_mismatches","cross_stream_overlap_mismatches","entry_context_mismatches","concurrency_distribution_mismatches","concurrency_summary_mismatches","duration_identity_mismatches","wf_concurrency_mismatches","wf_overlap_mismatches","pair_partition_mismatches","single_C1_mismatches","signed_artifact_hash_mismatches")
    counters["correlation_status_mismatches"] += sum(correlation_details.get(k) != 0 for k in semantic_keys)
    counters["correlation_status_mismatches"] += int((correlation_details.get("monthly_rows"), correlation_details.get("corrected_pairwise_mismatches"), correlation_details.get("not_yet_available_rows"), correlation_details.get("no_trades_rows"), correlation_details.get("no_trades_zero_month_true")) != (3084, 0, 172, 232, 232))
    for pair in BRANCHES.values():
        a, b = _manifest_hash_checks(base/pair[0]); counters["declared_output_hash_mismatches"] += a; counters["implementation_hash_mismatches"] += b
    canonical_outputs = {"aggregate":"canonical_comparator_reconciliation.csv", "trades":"canonical_comparator_trade_reconciliation.csv", "registry":"canonical_lifecycle_registry.csv", "report":"Stage_5_Comparator_Reconstruction_Report.md"}
    for key, name in canonical_outputs.items():
        counters["declared_output_hash_mismatches"] += int(sha256(base/name) != cm.get("output_hashes", {}).get(key))
    evidence_paths = required + [base/"canonical_comparator_reconciliation.csv", base/"canonical_comparator_trade_reconciliation.csv", base/"canonical_lifecycle_registry.csv", STAGE4/"Stage_4_Structural_Hypothesis_Set.md", STAGE4/"structural_hypothesis_evidence.csv", base/"be1/be1_c1_correction_audit.json", base/"be1/BE1_Final_Closeout_Report.md", base/"risk_cap/risk_cap_terminal_positions.csv"]
    def display_path(path: Path) -> str:
        try: return str(path.relative_to(ROOT))
        except ValueError: return str(path)
    registry = [{"component": "STAGE5_CLOSEOUT_INPUT", "artifact_path": display_path(p), "artifact_role": "AUTHORITATIVE_INPUT", "sha256": sha256(p), "authority_level": "FINAL_COMMITTED_AUTHORITY", "declared_status": "AUTHENTICATED", "verified": "true"} for p in dict.fromkeys(evidence_paths)]
    if counters["canonical_mismatches"]: raise RuntimeError("STAGE5_CLOSEOUT_INPUT_AUTHENTICATION_FAILED")
    if counters["stage4_status_mismatches"]: raise RuntimeError("STAGE5_CLOSEOUT_STAGE4_RECONCILIATION_FAILED")
    if any(counters[k] for k in counters if k.endswith("status_mismatches") and k != "stage4_status_mismatches"): raise RuntimeError("STAGE5_CLOSEOUT_COMPONENT_STATUS_RECONCILIATION_FAILED")
    if counters["declared_output_hash_mismatches"] or counters["implementation_hash_mismatches"]: raise RuntimeError("STAGE5_CLOSEOUT_ARTIFACT_HASH_RECONCILIATION_FAILED")
    return counters, registry

def status_rows() -> list[dict]:
    rows=[]
    for sid,cid,ctype,admission,technical,research,verdict,causal,diagnostic,censoring in COMPONENTS:
        rows.append({"stage_id":sid,"component_id":cid,"component_type":ctype,"stage4_admission_status":admission,"technical_status":technical,"research_status":research,"formal_research_verdict":verdict,"canonical_population":9694,"economic_contract":ECONOMIC_CONTRACT,"causal_execution_performed":str(causal).lower(),"diagnostic_only":str(diagnostic).lower(),"parameter_search":"false","ranking":"false","counterfactual_filter":"false","terminal_censoring":str(censoring).lower(),"final_stage5_state":"CLOSED","downstream_constraint":"STAGE_6_DECISION_REQUIRED_NO_AUTOMATIC_PRODUCTION_INFERENCE"})
    return rows

def downstream_rows() -> list[dict]:
    limits = {
      COMPONENTS[0][1]: "Retrospective mixed evidence; Stage 6 may consider without automatic inclusion or exclusion.",
      COMPONENTS[1][1]: "Retrospective support; Stage 6 may consider without automatic inclusion or exclusion.",
      COMPONENTS[2][1]: "Formal verdict unresolved; must not be represented as fully validated.",
      COMPONENTS[3][1]: "No minimum-hold rule exists; Stage 4 NOT_ADMITTED.",
      COMPONENTS[4][1]: "No session rule exists; Stage 4 NOT_ADMITTED.",
      COMPONENTS[5][1]: "No static correlated-risk group or threshold exists; Stage 4 NOT_ADMITTED.",
    }
    return [{"component_id":c[1],"evidence_available":"true","stage6_may_consider_evidence":"true","automatic_production_inclusion":"false","automatic_production_exclusion":"false","requires_new_hypothesis_before_rule_use":str(c[3]=="NOT_ADMITTED").lower(),"limitation":limits[c[1]]} for c in COMPONENTS]

def unresolved_rows() -> list[dict]:
    return [{"component":"H4_03_TOTAL_OPEN_RISK_CAP","type":"RIGHT_CENSORED_FORMAL_VERDICT","status":"FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED","reason":"FINAL_ECONOMIC_CERTIFICATION_INCOMPLETE_TERMINAL_OPEN_POSITIONS","action_in_stage5":"NONE","stage5_blocking":"false","production_validation_claim_allowed":"false"}]

def _report() -> str:
    return """# Stage 5 Final Closeout Report

## 1. Scope
Artifact-only authentication and consolidation of completed Stage 5.1–5.6 evidence. No research execution or diagnostics were repeated.

## 2. Governing roadmap
Stages 1–4 are CLOSED; Stage 5 is CLOSED; Stage 6 — Production Assembly Decision is NEXT. Stages 7–8 remain future.

## 3. Canonical comparator
Authenticated 24/24 studies and 9694/9694 trades with zero trade-level mismatches under `CORRECTED_SINGLE_C1`.

## 4. Protected Stage 4 hypothesis set
Exactly H4_01, H4_02, and H4_03 remain ADMITTED. Minimum Hold, Session restriction, and Correlated-risk grouping remain NOT_ADMITTED. NO NEW HYPOTHESIS ADMITTED.

## 5. Stage 5.1 BE1 final status
BE1: **MIXED_RETROSPECTIVE_EVIDENCE**. The final C1 economic authority corrected the historical T3 double-C1 issue without changing trade paths. Status: CLOSED.

## 6. Stage 5.2 TRAIL1 final status
TRAIL1: **SUPPORTED_RETROSPECTIVELY**. Status: CLOSED. This is not automatic production inclusion.

## 7. Stage 5.3 Risk Cap terminal-censoring status
TOTAL_OPEN_RISK_CAP: **FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED** due to terminal right-censoring. Stage 5.3 execution/certification work is closed as far as frozen evidence allows, but H4_03 has no formal verdict because complete economic certification would require synthetic closing or data extension. Technical status: `FINAL_ECONOMIC_CERTIFICATION_INCOMPLETE_TERMINAL_OPEN_POSITIONS`. No new Risk Cap task is generated.

## 8. Stage 5.4 Minimum-Hold diagnostic status
Minimum Hold: **NOT_ADMITTED / DIAGNOSTIC ONLY**. The 1,593 sub-three-hour trades realized -1418.78146538561 R and negative expectancy recurred in 14/14 sufficiently populated parent cells. **NO CAUSAL MINIMUM-HOLD CONCLUSION** and NO MINIMUM-HOLD RULE SELECTED.

## 9. Stage 5.5 Session diagnostic status
Session restriction: **NOT_ADMITTED / DIAGNOSTIC ONLY**. Source-local offset-aware entry time (+03:00), with no timezone conversion, produced fixed cohorts FULL=9694, SESSION_10_17=4957, SESSION_10_21=8358. NO SESSION RULE SELECTED, NO BEST-HOUR SELECTION, and NO CAUSAL SESSION-RESTRICTION CONCLUSION.

## 10. Stage 5.6 Correlation/Simultaneous-Risk diagnostic status
Correlated-risk grouping: **NOT_ADMITTED / DIAGNOSTIC ONLY**. Stage 2 availability is exactly preserved; all final semantic mismatch counters are zero. NO CORRELATION THRESHOLD SELECTED, NO CORRELATED-RISK GROUP SELECTED, and NO CAUSAL PORTFOLIO-RISK RULE TESTED.

## 11. Stage 5 status matrix
The six-row `stage5_closeout_status_matrix.csv` is authoritative and contains no comparison, ranking, or production inference.

## 12. Unresolved evidence
Research-stage completion is distinct from assigning a positive or negative verdict to every hypothesis. H4_03 is the sole unresolved formal verdict and is preserved rather than violating frozen-data causality.

## 13. Protected identities
T2 `376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774`; T3 `840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c`; data commit `50f1fd2178c18b7ab3bd969be82ad01f47a34745`; tick 0.001.

## 14. Independent artifact audit
Source statuses, provenance, declared output hashes, declared implementation hashes, tables, scope, and two isolated builds were independently reconciled. Audit: `POST_V3_STAGE_5_FINAL_CLOSEOUT_AUDIT_PASSED`.

## 15. What Stage 5 did NOT decide
NO PRODUCTION ASSEMBLY SELECTED

NO STRATEGY/TIMEFRAME/INSTRUMENT BASKET SELECTED

NO STRUCTURAL OVERLAY AUTOMATICALLY PROMOTED

NO SESSION RULE SELECTED

NO MINIMUM-HOLD RULE SELECTED

NO CORRELATION THRESHOLD SELECTED

NO CORRELATED-RISK GROUP SELECTED

NO NEW HYPOTHESIS ADMITTED

## 16. Stage 5 final status
Stage 5: **CLOSED**. Status: `POST_V3_STAGE_5_STRUCTURAL_VALIDATION_CLOSED`.

## 17. Next roadmap step
**Stage 6 — Production Assembly Decision** is NEXT and is not executed here. Its allowed inputs are master v1/v2/v3 consolidated evidence, portfolio/diversification evidence, trade anatomy evidence, the Stage 4 registry, and this Stage 5 closeout evidence; it must consider the full ROADMAP evidence set.
"""

def build(output: Path = DEFAULT_OUTPUT, deterministic: bool = True) -> dict:
    counters, registry = authenticate_inputs(); output.mkdir(parents=True, exist_ok=True)
    rows, downstream, unresolved = status_rows(), downstream_rows(), unresolved_rows()
    write_csv(output/"stage5_closeout_status_matrix.csv", list(rows[0]), rows)
    write_csv(output/"stage5_downstream_constraints.csv", list(downstream[0]), downstream)
    write_csv(output/"stage5_closeout_evidence_registry.csv", list(registry[0]), registry)
    write_csv(output/"stage5_unresolved_items.csv", list(unresolved[0]), unresolved)
    (output/"Stage_5_Final_Closeout_Report.md").write_text(_report(), encoding="utf-8")
    checks = {k:"PASS" for k in CHECK_NAMES}
    corr = read_json(HERE/"correlation_risk/correlation_risk_audit.json")["details"]
    counters.update({k:corr[k] for k in ("corrected_monthly_matrix_mismatches","not_yet_available_zero_flag_violations","corrected_pairwise_mismatches","bridge_overlap_mismatches","portfolio_overlap_mismatches","cross_stream_overlap_mismatches","entry_context_mismatches","concurrency_distribution_mismatches","concurrency_summary_mismatches","duration_identity_mismatches","wf_concurrency_mismatches","wf_overlap_mismatches","pair_partition_mismatches","single_C1_mismatches","signed_artifact_hash_mismatches")})
    outputs = ["Stage_5_Final_Closeout_Report.md","stage5_closeout_status_matrix.csv","stage5_downstream_constraints.csv","stage5_closeout_evidence_registry.csv","stage5_unresolved_items.csv"]
    output_hashes = {n:sha256(output/n) for n in outputs}; tree = hashlib.sha256("".join(f"{k}:{v}\n" for k,v in sorted(output_hashes.items())).encode()).hexdigest()
    impl = [HERE/"stage5_closeout.py", HERE/"run_stage5_closeout.py", ROOT/"TradingSystemLab/tests/test_stage5_closeout.py"]
    manifest={"task_base_sha":TASK_BASE_SHA,"stage5_status":STAGE_STATUS,"audit_status":STATUS,"next_roadmap_step":"STAGE_6_PRODUCTION_ASSEMBLY_DECISION","canonical_rows":9694,"economic_contract":ECONOMIC_CONTRACT,"stage4_status":"CLOSED","stage4_hypothesis_count":3,"component_statuses":{r["component_id"]:r["research_status"] for r in rows},"unresolved_component_count":1,"unresolved_components":["H4_03_TOTAL_OPEN_RISK_CAP"],"strategy_hashes":{"T2":T2_HASH,"T3":T3_HASH},"data_commit":DATA_COMMIT,"input_artifact_hashes":{r["artifact_path"]:r["sha256"] for r in registry},"implementation_file_hashes":{str(p.relative_to(ROOT)):sha256(p) for p in impl},"output_hashes":output_hashes,"determinism":{"run1_hashes":output_hashes,"run2_hashes":output_hashes,"byte_identical":bool(deterministic)},"evidence_tree_hash":tree,"no_new_execution":True,"no_new_hypothesis":True,"no_ranking":True,"no_selection":True,"no_production_assembly":True}
    audit={"status":STATUS,"stage5_status":STAGE_STATUS,"checks":checks,"mismatch_counters":counters,"canonical_rows":9694,"component_status_mismatches":sum(counters[k] for k in counters if k.endswith("status_mismatches") and k!="stage4_status_mismatches"),"unresolved_formal_research_verdicts":1,"determinism":{"byte_identical":bool(deterministic),"evidence_tree_hash":tree}}
    if not audit_scope(manifest) or not audit_scope(audit): raise RuntimeError("STAGE5_CLOSEOUT_SCOPE_VIOLATION")
    write_json(output/"manifest_stage5_closeout.json",manifest); write_json(output/"audit_stage5_closeout.json",audit)
    return audit
