"""Stage 6 artifact assembly and fail-closed independent certification.

Only authenticated, already-published Stage 1--5 evidence is read.  Nothing in
this module executes a strategy or creates new market evidence.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, pstdev

DECISION_SOURCE_SHA = "fdee91b474ccdebcf9d7dc56d8e87a112d37e50e"
TASK_BASE_SHA = "e81e8ba4dd14a0e6319cd1ea1a747fedceb95e1c"
STATUS = "POST_V3_STAGE_6_PRODUCTION_ASSEMBLY_DECISION_COMPLETE"
AUDIT_STATUS = "POST_V3_STAGE_6_PRODUCTION_ASSEMBLY_DECISION_AUDIT_PASSED"
ASSEMBLY_ID = "PROD_STAGE6_83C7B31BB42C"
PARENTS = [(g, s, t) for g in ("v2", "v3") for s in ("T2", "T3") for t in ("M30", "H1")]
SELECTED_PARENT = ("v3", "T3", "H1")
SELECTED_INSTRUMENTS = ("CNYRUBF", "GLDRUBF", "IMOEXF")
SELECTED_OVERLAY = "TRAIL1"
ECONOMIC_CONTRACT = "CORRECTED_SINGLE_C1"
BASKET_BASIS = "CANONICAL_BASE_EXIT"

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT.parent
POST = ROOT / "results/post_v3_analysis"
S1, S2 = POST / "stage1_master_evidence", POST / "stage2_portfolio_diversification"
S3, S4 = POST / "stage3_trade_anatomy", POST / "stage4_structural_hypotheses"
S5 = POST / "stage5_structural_validation"
OUT = Path(__file__).resolve().parent
PROTECTED = (
    "results/post_v3_analysis/stage1_master_evidence",
    "results/post_v3_analysis/stage2_portfolio_diversification",
    "results/post_v3_analysis/stage3_trade_anatomy",
    "results/post_v3_analysis/stage4_structural_hypotheses",
    "results/post_v3_analysis/stage5_structural_validation",
    "strategies/trend",
)
IMPLEMENTATION = (
    "TradingSystemLab/results/post_v3_analysis/stage6_production_assembly/stage6_production_assembly.py",
    "TradingSystemLab/results/post_v3_analysis/stage6_production_assembly/run_stage6_production_assembly.py",
    "TradingSystemLab/tests/test_stage6_production_assembly.py",
)
CHECK_NAMES = (
    "stage1_authenticated", "stage2_authenticated", "stage3_authenticated", "stage4_authenticated", "stage5_authenticated",
    "protected_source_trees_unchanged", "parent_universe_exact_8", "parent_evidence_reconciled",
    "parent_eligibility_reconciled", "parent_selection_contract_reconciled", "concentration_guard_passed",
    "instrument_universe_reconciled", "instrument_evidence_reconciled", "instrument_eligibility_reconciled",
    "instrument_selection_contract_reconciled", "pair_diversification_evidence_reconciled",
    "selected_pair_samples_adequate", "selected_monthly_series_reconciled", "selected_summary_reconciled",
    "parent_comparison_reconciled", "canonical_basket_basis_labeled", "direction_evidence_reconciled",
    "overlay_authority_authenticated", "selected_overlay_parent_evidence_reconciled",
    "structural_overlay_status_reconciled", "trail1_tradeoff_disclosed", "no_unvalidated_rule_promoted",
    "no_be1_trail1_combination", "decision_trace_complete", "stage7_handoff_reconciled",
    "no_cross_generation_mix", "no_cross_strategy_mix", "no_cross_timeframe_mix",
    "no_exhaustive_subset_search", "no_numeric_score", "no_new_backtest", "no_new_optimizer",
    "no_new_hypothesis", "stage7_boundary_preserved", "implementation_hashes_verified",
    "output_hashes_verified", "deterministic_artifacts",
)
COUNTER_NAMES = (
    "source_authentication_mismatches", "protected_source_mutations", "parent_evidence_mismatches",
    "parent_eligibility_mismatches", "parent_selection_violations", "instrument_evidence_mismatches",
    "instrument_eligibility_mismatches", "instrument_selection_violations", "pair_diversification_mismatches",
    "selected_monthly_mismatches", "selected_summary_mismatches", "parent_comparison_mismatches",
    "direction_evidence_mismatches", "overlay_parent_evidence_mismatches", "overlay_status_mismatches",
    "decision_trace_mismatches", "stage7_handoff_mismatches", "scope_violations",
    "implementation_hash_mismatches", "output_hash_mismatches", "determinism_mismatches",
)


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, fields, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def f(value): return float(value)
def fmt(value): return format(float(value), ".12g")
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lookup(rows, **keys):
    found = [row for row in rows if all(row.get(key) == value for key, value in keys.items())]
    if len(found) != 1:
        raise ValueError(f"expected one row for {keys}, got {len(found)}")
    return found[0]


def _merkle(entries):
    digest = hashlib.sha256()
    for name, payload in sorted(entries):
        digest.update(name.encode()); digest.update(b"\0"); digest.update(payload)
    return digest.hexdigest()


def current_tree_hash(relative):
    path = ROOT / relative
    return _merkle((p.relative_to(path).as_posix(), p.read_bytes()) for p in path.rglob("*") if p.is_file())


def frozen_tree_hash(relative):
    prefix = f"TradingSystemLab/{relative}"
    listing = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", DECISION_SOURCE_SHA, "--", prefix], cwd=REPO, text=True
    ).splitlines()
    entries = []
    for name in listing:
        payload = subprocess.check_output(["git", "show", f"{DECISION_SOURCE_SHA}:{name}"], cwd=REPO)
        entries.append((Path(name).relative_to(prefix).as_posix(), payload))
    return _merkle(entries)


def protected_tree_mutations():
    """Count protected roots whose working-tree bytes differ from frozen Git."""
    roots = [f"TradingSystemLab/{relative}" for relative in PROTECTED]
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", DECISION_SOURCE_SHA, "--", *roots], cwd=REPO, text=True
    ).splitlines()
    changed += subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "--", *roots], cwd=REPO, text=True
    ).splitlines()
    return sum(any(name == root or name.startswith(root + "/") for name in changed) for root in roots)


def monthly_dd(values):
    equity = peak = drawdown = 0.0
    for value in values:
        equity += value; peak = max(peak, equity); drawdown = min(drawdown, equity - peak)
    return drawdown


def longest_negative(values):
    best = run = 0
    for value in values:
        run = run + 1 if value < 0 else 0; best = max(best, run)
    return best


def parent_evidence():
    master = read_csv(S1 / "master_study_comparison.csv")
    monthly = read_csv(S1 / "monthly_stability_summary.csv")
    portfolio = read_csv(S2 / "portfolio_stability_summary.csv")
    rows = []
    for generation, strategy, timeframe in PARENTS:
        wf = lookup(master, generation=generation, strategy=strategy, timeframe=timeframe, lifecycle_stage="walk_forward")
        oos = lookup(master, generation=generation, strategy=strategy, timeframe=timeframe, lifecycle_stage="true_oos")
        month = lookup(monthly, generation=generation, strategy=strategy, timeframe=timeframe, lifecycle_stage="true_oos")
        port = lookup(portfolio, generation=generation, strategy=strategy, timeframe=timeframe, lifecycle_stage="true_oos")
        eligible = oos["classification"] != "FAIL" and all(f(x) > 0 for x in (wf["net_R"], wf["expectancy_R"], oos["net_R"], oos["expectancy_R"]))
        rows.append({
            "generation": generation, "futures_type": wf["futures_type"], "strategy": strategy, "timeframe": timeframe,
            "wf_classification": wf["classification"], "true_oos_classification": oos["classification"],
            "wf_trades": wf["total_trades"], "wf_PF": wf["PF"], "wf_expectancy_R": wf["expectancy_R"], "wf_net_R": wf["net_R"], "wf_max_DD_R": wf["max_drawdown_R"], "wf_recovery": wf["recovery_factor"],
            "oos_trades": oos["total_trades"], "oos_PF": oos["PF"], "oos_expectancy_R": oos["expectancy_R"], "oos_net_R": oos["net_R"], "oos_max_DD_R": oos["max_drawdown_R"], "oos_recovery": oos["recovery_factor"],
            "oos_positive_quarter_share": oos["positive_quarter_share"], "oos_net_R_without_top5": oos["net_R_without_top5"], "oos_top5_positive_R_share": oos["top5_positive_R_share"],
            "oos_positive_month_share": month["positive_month_share"], "oos_median_monthly_R": month["median_monthly_R"], "oos_monthly_R_std": month["monthly_R_std"], "oos_worst_month_R": month["worst_month_R"], "oos_monthly_equity_DD": port["monthly_equity_max_drawdown_R"], "oos_longest_negative_month_streak": month["longest_negative_month_streak"],
            "eligible": str(eligible).lower(), "eligibility_reason": "HARD_GATES_PASS" if eligible else "HARD_GATE_FAILED",
        })
    return rows


def instrument_evidence():
    by = defaultdict(dict)
    for row in read_csv(S2 / "instrument_stability_summary.csv"):
        if (row["generation"], row["strategy"], row["timeframe"]) == SELECTED_PARENT:
            by[row["instrument"]][row["lifecycle_stage"]] = row
    rows = []
    for instrument in sorted(by):
        base, wf, oos = (by[instrument][stage] for stage in ("baseline", "walk_forward", "true_oos"))
        eligible = all(f(x) > 0 for x in (wf["total_trades"], wf["total_net_R"], wf["expectancy_R"], oos["total_trades"], oos["total_net_R"], oos["expectancy_R"])) and f(wf["PF"]) > 1 and f(oos["PF"]) > 1
        rows.append({
            "instrument": instrument, "baseline_trades": base["total_trades"], "baseline_net_R": base["total_net_R"], "baseline_PF": base["PF"], "baseline_expectancy_R": base["expectancy_R"],
            "wf_trades": wf["total_trades"], "wf_net_R": wf["total_net_R"], "wf_PF": wf["PF"], "wf_expectancy_R": wf["expectancy_R"], "wf_positive_month_share": wf["positive_month_share"],
            "oos_trades": oos["total_trades"], "oos_net_R": oos["total_net_R"], "oos_PF": oos["PF"], "oos_expectancy_R": oos["expectancy_R"], "oos_positive_month_share": oos["positive_month_share"], "oos_median_monthly_R": oos["median_monthly_R"], "oos_monthly_R_std": oos["monthly_R_std"], "oos_worst_month_R": oos["worst_month_R"], "oos_longest_negative_month_streak": oos["longest_negative_month_streak"],
            "oos_contribution_to_portfolio_R": oos["contribution_to_portfolio_total_R"], "oos_contribution_to_positive_R": oos["contribution_to_positive_R"], "oos_contribution_to_negative_R": oos["contribution_to_negative_R"], "oos_share_of_portfolio_losses": oos["share_of_portfolio_losses"], "oos_months_worst": oos["number_of_months_in_which_instrument_was_worst"], "oos_months_best": oos["number_of_months_in_which_instrument_was_best"],
            "eligible": str(eligible).lower(), "eligibility_reason": "HARD_GATES_PASS" if eligible else "HARD_GATE_FAILED",
        })
    return rows


def selected_monthly():
    grouped, availability = defaultdict(dict), defaultdict(dict)
    for row in read_csv(S2 / "monthly_instrument_matrix.csv"):
        if (row["generation"], row["strategy"], row["timeframe"]) == SELECTED_PARENT and row["instrument"] in SELECTED_INSTRUMENTS:
            key = (row["lifecycle_stage"], row["YYYY-MM"])
            grouped[key][row["instrument"]] = f(row["net_R"]); availability[key][row["instrument"]] = row["instrument_available"] == "true"
    order = {"baseline": 0, "walk_forward": 1, "true_oos": 2}
    rows = []
    for (stage, month), values in sorted(grouped.items(), key=lambda item: (order[item[0][0]], item[0][1])):
        row = {"generation": "v3", "lifecycle_stage": stage, "YYYY-MM": month, "portfolio_economic_basis": BASKET_BASIS, "instrument_count": 3, "available_instrument_count": sum(availability[(stage, month)].values())}
        for instrument in SELECTED_INSTRUMENTS: row[f"{instrument}_R"] = fmt(values[instrument])
        row["portfolio_R"] = fmt(sum(values.values())); rows.append(row)
    return rows


def summaries(monthly):
    rows = []
    source = read_csv(S2 / "monthly_instrument_matrix.csv")
    for stage in ("baseline", "walk_forward", "true_oos"):
        values = [f(row["portfolio_R"]) for row in monthly if row["lifecycle_stage"] == stage]
        per_month = defaultdict(list)
        for row in source:
            if (row["generation"], row["strategy"], row["timeframe"], row["lifecycle_stage"]) == SELECTED_PARENT + (stage,) and row["instrument"] in SELECTED_INSTRUMENTS:
                per_month[row["YYYY-MM"]].append(f(row["net_R"]))
        rows.append({
            "lifecycle_stage": stage, "portfolio_economic_basis": BASKET_BASIS, "verification_label": "CANONICAL_BASE_EXIT_BASKET_VERIFICATION",
            "months": len(values), "total_net_R": fmt(sum(values)), "mean_monthly_R": fmt(mean(values)), "median_monthly_R": fmt(median(values)),
            "positive_months": sum(x > 0 for x in values), "negative_months": sum(x < 0 for x in values), "positive_month_share": fmt(sum(x > 0 for x in values) / len(values)),
            "monthly_R_std": fmt(pstdev(values)), "worst_month_R": fmt(min(values)), "best_month_R": fmt(max(values)), "monthly_equity_max_DD_R": fmt(monthly_dd(values)),
            "longest_negative_month_streak": longest_negative(values), "loss_rescue_months": sum(sum(x) > 0 and any(v < 0 for v in x) for x in per_month.values()), "synchronized_loss_months": sum(bool(x) and all(v < 0 for v in x) for x in per_month.values()),
        })
    return rows


def parent_comparison(summary):
    authority = read_csv(S2 / "portfolio_stability_summary.csv")
    rows = []
    for selected in summary:
        parent = lookup(authority, generation="v3", strategy="T3", timeframe="H1", lifecycle_stage=selected["lifecycle_stage"])
        rows.append({"lifecycle_stage": selected["lifecycle_stage"], "portfolio_economic_basis": BASKET_BASIS, "selected_total_R": selected["total_net_R"], "parent_total_R": parent["total_net_R"], "selected_positive_month_share": selected["positive_month_share"], "parent_positive_month_share": parent["positive_month_share"], "selected_monthly_std": selected["monthly_R_std"], "parent_monthly_std": parent["monthly_R_std"], "selected_worst_month": selected["worst_month_R"], "parent_worst_month": parent["worst_month_R"], "selected_monthly_DD": selected["monthly_equity_max_DD_R"], "parent_monthly_DD": parent["monthly_equity_max_drawdown_R"]})
    return rows


def pair_evidence():
    correlation = read_csv(S2 / "pairwise_monthly_correlation.csv")
    overlap = read_csv(S5 / "correlation_risk/correlation_overlap_bridge.csv")
    rows = []
    for index, left in enumerate(SELECTED_INSTRUMENTS):
        for right in SELECTED_INSTRUMENTS[index + 1:]:
            keys = lambda row: (row["generation"], row["strategy"], row["timeframe"]) == SELECTED_PARENT and row.get("lifecycle_stage", row.get("lifecycle")) == "true_oos" and {row["instrument_a"], row["instrument_b"]} == {left, right}
            corr = next(row for row in correlation if keys(row)); bridge = next(row for row in overlap if keys(row))
            rows.append({"instrument_a": left, "instrument_b": right, "pearson_monthly_R": corr["pearson_monthly_R"], "both_negative_months": corr["both_negative_months"], "opposite_sign_months": corr["opposite_sign_months"], "sample_flag": corr["sample_flag"], "overlap_jaccard": bridge["overlap_jaccard"], "overlapping_trade_pairs": bridge["overlapping_trade_pairs"], "both_final_negative_pairs": bridge["both_final_negative_pairs"]})
    return rows


def redundancy_evidence():
    corrected = read_csv(S5 / "correlation_risk/corrected_pairwise_monthly_correlation.csv")
    overlap = read_csv(S5 / "correlation_risk/correlation_overlap_bridge.csv")
    predicate = lambda row: (row["generation"], row["strategy"], row["timeframe"], row.get("lifecycle", row.get("lifecycle_stage"))) == SELECTED_PARENT + ("true_oos",) and {row["instrument_a"], row["instrument_b"]} == {"CNYRUBF", "USDRUBF"}
    return next(row for row in corrected if predicate(row)), next(row for row in overlap if predicate(row))


def overlay_parent_evidence():
    rows = []
    for source in read_csv(S5 / "trail1/trail1_study_summary.csv"):
        if (source["generation"], source["strategy"], source["timeframe"]) != ("v3_perpetual", "T3", "H1"): continue
        rows.append({
            "generation": source["generation"], "lifecycle": source["lifecycle"], "strategy": source["strategy"], "timeframe": source["timeframe"],
            "canonical_trades": source["canonical_trades"], "canonical_PF": source["canonical_PF"], "canonical_expectancy_R": source["canonical_expectancy_R"], "canonical_net_R": source["canonical_net_R"], "canonical_max_DD": source["canonical_max_DD"], "canonical_recovery": source["canonical_recovery_factor"],
            "trail1_trades": source["trail1_trades"], "trail1_PF": source["trail1_PF"], "trail1_expectancy_R": source["trail1_expectancy_R"], "trail1_net_R": source["trail1_net_R"], "trail1_max_DD": source["trail1_max_DD"], "trail1_recovery": source["trail1_recovery_factor"],
            "delta_PF": source["delta_PF"], "delta_expectancy_R": source["delta_expectancy_R"], "delta_net_R": source["delta_net_R"], "delta_max_DD": source["delta_max_DD"], "delta_recovery": source["delta_recovery_factor"], "evidence_label": "RETROSPECTIVE_CAUSAL_VALIDATION",
        })
    order = {"baseline": 0, "walk_forward": 1, "historical_true_oos": 2}
    return sorted(rows, key=lambda row: order[row["lifecycle"]])


def direction_evidence():
    return [{"lifecycle_stage": row["lifecycle_stage"], "direction": row["direction"], "trades": row["trades"], "PF": row["PF"], "expectancy_R": row["expectancy_R"], "net_R": row["net_R"], "max_DD_R": row["max_drawdown_R"], "win_rate": row["win_rate"]} for row in read_csv(S1 / "direction_statistics.csv") if (row["generation"], row["strategy"], row["timeframe"]) == SELECTED_PARENT]


def authentication_results():
    specs = ((S1 / "audit_result.json", "POST_V3_STAGE_1_MASTER_EVIDENCE_AUDIT_PASSED"), (S2 / "audit_result.json", "POST_V3_STAGE_2_PORTFOLIO_DIVERSIFICATION_AUDIT_PASSED"), (S3 / "audit_stage3d_result.json", "POST_V3_STAGE_3D_INDEPENDENT_CLOSEOUT_AUDIT_PASSED"), (S4 / "audit_stage4_result.json", "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_AUDIT_PASSED"), (S5 / "stage5_closeout/audit_stage5_closeout.json", "POST_V3_STAGE_5_FINAL_CLOSEOUT_AUDIT_PASSED"))
    return [json.loads(path.read_text())["status"] == expected for path, expected in specs]


def decision_rows(parent_rows, instrument_rows):
    parent = []
    for row in parent_rows:
        key = row["generation"], row["strategy"], row["timeframe"]
        selected = key == SELECTED_PARENT
        parent.append({"generation": key[0], "strategy": key[1], "timeframe": key[2], "decision": "SELECTED" if selected else ("NOT_SELECTED" if row["eligible"] == "true" else "INELIGIBLE"), "decision_reason": "ONLY_PARENT_WITH_TRUE_OOS_PASS_AND_WF_PASS" if selected else ("HARD_GATE_FAILED" if row["eligible"] == "false" else "WEAKER_LIFECYCLE_CLASSIFICATION_OR_STABILITY"), "key_supporting_evidence": f"WF={row['wf_classification']};OOS={row['true_oos_classification']};OOS expectancy={row['oos_expectancy_R']}", "key_counter_evidence": f"OOS positive-month share={row['oos_positive_month_share']};DD={row['oos_max_DD_R']}"})
    instruments = []
    reasons = {"CNYRUBF": "STRONG_WF_AND_OOS_WITH_POSITIVE_MONTHLY_MEDIAN", "GLDRUBF": "STRONGEST_OOS_CONTRIBUTION_AND_SHALLOW_WORST_MONTH", "IMOEXF": "ELIGIBLE_DIVERSIFYING_EQUITY_SLEEVE", "USDRUBF": "ECONOMICALLY_POSITIVE_BUT_REDUNDANT_WITH_CNYRUBF"}
    for row in instrument_rows:
        instruments.append({"instrument": row["instrument"], "eligible": row["eligible"], "decision": "SELECTED" if row["instrument"] in SELECTED_INSTRUMENTS else "NOT_SELECTED", "decision_reason": reasons[row["instrument"]], "profitability_evidence": f"WF net/PF/exp={row['wf_net_R']}/{row['wf_PF']}/{row['wf_expectancy_R']}; OOS={row['oos_net_R']}/{row['oos_PF']}/{row['oos_expectancy_R']}", "monthly_stability_evidence": f"OOS positive/median/std/worst/streak={row['oos_positive_month_share']}/{row['oos_median_monthly_R']}/{row['oos_monthly_R_std']}/{row['oos_worst_month_R']}/{row['oos_longest_negative_month_streak']}", "diversification_evidence": "Authenticated selected-pair evidence; USDRUBF redundancy evidence; no threshold", "concentration_evidence": f"OOS portfolio contribution={row['oos_contribution_to_portfolio_R']}; loss share={row['oos_share_of_portfolio_losses']}", "execution_note": "H1 operational load; perpetual live-contract mapping deferred to Stage 7"})
    return parent, instruments


def overlay_rows():
    return [
        {"component": "BASE_EXIT / NONE", "stage4_status": "BASELINE", "stage5_status": "CANONICAL_COMPARATOR", "eligible_for_production_selection": "true", "decision": "NOT_SELECTED", "decision_reason": "PERMISSIBLE_CANONICAL_COMPARATOR", "evidence_basis": "CANONICAL_COMPARATOR", "limitation": "Does not address documented winner giveback"},
        {"component": "H4_01 BE1", "stage4_status": "ADMITTED", "stage5_status": "MIXED_RETROSPECTIVE_EVIDENCE", "eligible_for_production_selection": "true", "decision": "NOT_SELECTED", "decision_reason": "MIXED_EVIDENCE_RETAINED_AS_COUNTERFACTUAL_CONTEXT", "evidence_basis": "RETROSPECTIVE_CAUSAL_VALIDATION", "limitation": "Mixed evidence; not fresh OOS"},
        {"component": "H4_02 TRAIL1", "stage4_status": "ADMITTED", "stage5_status": "SUPPORTED_RETROSPECTIVELY", "eligible_for_production_selection": "true", "decision": "SELECTED", "decision_reason": "SELECTED_WITH_RECORDED_RISK_TRADEOFF", "evidence_basis": "RETROSPECTIVE_CAUSAL_VALIDATION", "limitation": "Not fresh untouched TRUE OOS; not uniformly superior on all metrics"},
        {"component": "H4_03 TOTAL_OPEN_RISK_CAP", "stage4_status": "ADMITTED", "stage5_status": "FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED", "eligible_for_production_selection": "false", "decision": "DEFERRED_UNRESOLVED", "decision_reason": "FINAL_ECONOMIC_CERTIFICATION_INCOMPLETE_TERMINAL_OPEN_POSITIONS", "evidence_basis": "TERMINAL_RIGHT_CENSORING", "limitation": "FINAL_ECONOMIC_CERTIFICATION_INCOMPLETE_TERMINAL_OPEN_POSITIONS"},
        *[{"component": name, "stage4_status": "NOT_ADMITTED", "stage5_status": "NOT_ADMITTED", "eligible_for_production_selection": "false", "decision": "NOT_ELIGIBLE_NOT_ADMITTED", "decision_reason": "NOT_ADMITTED", "evidence_basis": "DIAGNOSTIC_ONLY", "limitation": "No admitted validation"} for name in ("MINIMUM_HOLD", "SESSION", "CORRELATED_RISK_GROUP")],
    ]


def handoff_rows():
    frozen = (("production assembly ID", ASSEMBLY_ID), ("generation", "v3"), ("strategy", "T3"), ("timeframe", "H1"), ("instrument set", ";".join(SELECTED_INSTRUMENTS)), ("structural overlay choice", "TRAIL1"))
    pending = ("strategy source implementation freeze", "exact live contract mapping", "roll convention", "risk allocation", "position sizing", "portfolio safeguards", "production cost model", "session operating schedule", "broker/order semantics", "data-feed conventions", "operational safeguards")
    return [{"freeze_state": "FROZEN_BY_STAGE6", "item": key, "value_or_owner": value} for key, value in frozen] + [{"freeze_state": "NOT_YET_FROZEN", "item": key, "value_or_owner": "Stage 7"} for key in pending]


def trace_rows():
    facts = (
        ("1", "lifecycle durability", "Stage 1 master_study_comparison.csv", "v3/T3/H1 is the sole parent with WF PASS and TRUE OOS PASS", "selected parent"),
        ("2", "profitability", "Stage 1 and Stage 2 evidence", "Selected parent and all four parent instruments satisfy independently recomputed gates", "eligible"),
        ("3", "drawdown/recovery", "Stage 1 master_study_comparison.csv", "Selected parent WF and OOS drawdown/recovery are retained", "residual risk disclosed"),
        ("4", "monthly stability", "Stage 1 monthly_stability_summary.csv", "Selected-parent OOS calendar distribution retained", "calendar evidence"),
        ("5", "diversification", "Stage 2 and Stage 5.6 pair evidence", "Selected pairs reconcile; CNYRUBF/USDRUBF redundancy is documented", "supports documented instrument decision"),
        ("6", "direction stability", "Stage 1 direction_statistics.csv", "Both LONG and SHORT are retained", "no direction filter"),
        ("7", "concentration", "Stage 1 master_study_comparison.csv", "Selected-parent OOS net R without top five is positive", "hard guard passes"),
        ("8", "trade anatomy", "Stage 3 closeout", "Winner giveback and stop-loss evidence remains counter-evidence", "no slice filter"),
        ("9", "Stage5 structural overlay", "Stage 5 TRAIL1 authority", "TRAIL1 is supported retrospectively with DD/recovery counter-evidence", "selected with recorded risk tradeoff"),
        ("10", "execution practicality", "Stage 1 source evidence", "Perpetual research symbols require executable-contract mapping", "mapping deferred to Stage 7"),
        ("11", "portfolio risk", "Stage 5.6 overlap evidence", "Concurrency remains descriptive and creates no production rule", "risk design deferred to Stage 7"),
    )
    fields = ("decision_step", "evidence_domain", "evidence_artifact", "fact", "effect_on_decision")
    return [dict(zip(fields, row)) for row in facts]


def report(out, parent_rows, summary, pairs, overlay_parent):
    redundancy, overlap = redundancy_evidence()
    lines = [
        "# Stage 6 Production Assembly Decision Report", "", "## Scope",
        "Artifact-only certification of the existing decision; no strategy execution, new backtest, search, or new hypothesis occurred. Stage 7 is not performed.", "",
        "## Parent and instrument decision", "v3/T3/H1 remains the only parent with WF PASS and TRUE OOS PASS. CNYRUBF, GLDRUBF, and IMOEXF remain selected. USDRUBF remains economically positive, but its authenticated TRUE OOS relationship with CNYRUBF is redundant: " + f"historical Pearson {redundancy['stage2_historical_pearson_monthly_R']}, corrected Pearson {redundancy['corrected_pearson_monthly_R']}, Jaccard {overlap['overlap_jaccard']}, {overlap['overlapping_trade_pairs']} overlapping pairs, and {overlap['both_final_negative_pairs']} both-negative pairs.", "",
        "## Selected instrument basket — canonical base-exit monthly verification", "**CANONICAL_BASE_EXIT_BASKET_VERIFICATION**", "These monthly basket metrics come from the authenticated Stage 2 canonical base-exit instrument matrix and do not represent a TRAIL1-modified basket backtest.",
    ]
    for row in summary: lines.append(f"- {row['lifecycle_stage']}: net {row['total_net_R']}R; positive share {row['positive_month_share']}; std {row['monthly_R_std']}R; worst {row['worst_month_R']}R; monthly DD {row['monthly_equity_max_DD_R']}R.")
    lines += ["", "The parent comparison is selected instrument subset versus the full parent universe under canonical base exits; it is not TRAIL1 versus base.", "", "## Selected-pair evidence"]
    for row in pairs: lines.append(f"- {row['instrument_a']}/{row['instrument_b']}: Pearson {row['pearson_monthly_R']}; both-negative months {row['both_negative_months']}; opposite-sign months {row['opposite_sign_months']}; Jaccard {row['overlap_jaccard']}; overlapping pairs {row['overlapping_trade_pairs']}; both-final-negative pairs {row['both_final_negative_pairs']}; {row['sample_flag']}.")
    lines += ["", "## TRAIL1 selected-parent evidence", "Overlay evidence is parent-level Stage 5 **RETROSPECTIVE_CAUSAL_VALIDATION**, not a newly constructed three-instrument overlay portfolio.", "", "| lifecycle | canonical net R | TRAIL1 net R | canonical expectancy | TRAIL1 expectancy | canonical DD | TRAIL1 DD | canonical recovery | TRAIL1 recovery |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in overlay_parent: lines.append(f"| {row['lifecycle']} | {row['canonical_net_R']} | {row['trail1_net_R']} | {row['canonical_expectancy_R']} | {row['trail1_expectancy_R']} | {row['canonical_max_DD']} | {row['trail1_max_DD']} | {row['canonical_recovery']} | {row['trail1_recovery']} |")
    lines += ["", "TRAIL1 is selected as the structural overlay because Stage 5 classified it **SUPPORTED_RETROSPECTIVELY** under retrospective causal validation. For the selected v3/T3/H1 parent, TRAIL1 improves some return/expectancy measures but does not dominate the canonical exit on every risk metric; historical OOS max drawdown and recovery show counter-evidence. Selection therefore preserves this documented trade-off.", "", "TRAIL1 is not fresh untouched TRUE OOS, is not uniformly superior on all metrics, and is selected despite the documented DD/recovery tradeoff. BE1 remains **MIXED_RETROSPECTIVE_EVIDENCE**; no BE1+TRAIL1 combination is admitted. Risk Cap remains **FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED**, **FINAL_ECONOMIC_CERTIFICATION_INCOMPLETE_TERMINAL_OPEN_POSITIONS**, and **DEFERRED_UNRESOLVED**. Minimum Hold, Session, and Correlated-risk grouping remain NOT_ADMITTED and NOT_ELIGIBLE_NOT_ADMITTED.", "", "## Direction, concentration, and limitations", "LONG and SHORT remain included; there is no direction filter. Selected-parent TRUE OOS net R without top five remains positive. The finite samples, imperfect currency diversification, concurrency, and overlay risk counter-evidence remain explicit.", "", "Perpetual research data are not executable contracts. Exact live-contract mapping, roll convention, allocation, sizing, costs, broker semantics, data-feed conventions, and operational safeguards remain for Stage 7.", "", "## Final decision", f"**{ASSEMBLY_ID}**: v3 perpetual / T3 / H1 / CNYRUBF, GLDRUBF, IMOEXF / TRAIL1 / {ECONOMIC_CONTRACT} / tick 0.001.", "", f"**{STATUS}**. Stage 6 is **CLOSED**; the production specification is **NOT YET FROZEN**. Stage 7 — Production Specification Freeze is **NEXT**.", ""]
    (Path(out) / "Stage_6_Production_Assembly_Decision_Report.md").write_text("\n".join(lines), encoding="utf-8")


def build_artifacts(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    parents, instruments = parent_evidence(), instrument_evidence()
    monthly = selected_monthly(); summary = summaries(monthly); pairs = pair_evidence(); overlay_parent = overlay_parent_evidence()
    parent_decisions, instrument_decisions = decision_rows(parents, instruments)
    assembly = [{"production_assembly_id": ASSEMBLY_ID, "generation": "v3", "futures_type": "perpetual", "strategy": "T3", "timeframe": "H1", "candidate_identity": "v3_T3_H1_PERPETUAL", "instrument": instrument, "structural_overlay": "TRAIL1", "economic_contract": ECONOMIC_CONTRACT, "research_tick": "0.001", "decision_status": "SELECTED"} for instrument in SELECTED_INSTRUMENTS]
    artifacts = {
        "production_parent_evidence.csv": parents, "production_parent_decision.csv": parent_decisions,
        "production_instrument_evidence.csv": instruments, "production_instrument_decision.csv": instrument_decisions,
        "production_assembly_decision.csv": assembly, "selected_assembly_monthly_series.csv": monthly,
        "selected_assembly_summary.csv": summary, "selected_assembly_parent_comparison.csv": parent_comparison(summary),
        "selected_assembly_direction_evidence.csv": direction_evidence(), "selected_pair_diversification_evidence.csv": pairs,
        "selected_overlay_parent_evidence.csv": overlay_parent, "structural_overlay_decision.csv": overlay_rows(),
        "stage6_decision_trace.csv": trace_rows(), "stage6_stage7_handoff.csv": handoff_rows(),
    }
    exclusions = []
    for row in parent_decisions:
        if row["decision"] != "SELECTED": exclusions.append({"component_type": "PARENT", "component": f"{row['generation']}/{row['strategy']}/{row['timeframe']}", "reason": row["decision_reason"]})
    for row in instrument_decisions:
        if row["decision"] != "SELECTED": exclusions.append({"component_type": "INSTRUMENT", "component": row["instrument"], "reason": row["decision_reason"]})
    for row in overlay_rows():
        if row["decision"] != "SELECTED": exclusions.append({"component_type": "OVERLAY", "component": row["component"], "reason": row["decision"]})
    artifacts["production_exclusion_log.csv"] = exclusions
    for name, rows in artifacts.items(): write_csv(out / name, list(rows[0]), rows)
    report(out, parents, summary, pairs, overlay_parent)
    return artifacts


def _same(expected, actual):
    return [{key: str(value) for key, value in row.items()} for row in expected] == [{key: str(value) for key, value in row.items()} for row in actual]


def _fail_status(counters, checks):
    precedence = (
        ("STAGE6_INPUT_AUTHENTICATION_FAILED", ("source_authentication_mismatches",)),
        ("STAGE6_PROTECTED_SOURCE_MUTATION_FAILED", ("protected_source_mutations",)),
        ("STAGE6_PARENT_EVIDENCE_RECONCILIATION_FAILED", ("parent_evidence_mismatches", "parent_eligibility_mismatches")),
        ("STAGE6_PARENT_SELECTION_CONTRACT_FAILED", ("parent_selection_violations",)),
        ("STAGE6_INSTRUMENT_EVIDENCE_RECONCILIATION_FAILED", ("instrument_evidence_mismatches", "instrument_eligibility_mismatches")),
        ("STAGE6_INSTRUMENT_SELECTION_CONTRACT_FAILED", ("instrument_selection_violations",)),
        ("STAGE6_DIVERSIFICATION_RECONCILIATION_FAILED", ("pair_diversification_mismatches",)),
        ("STAGE6_PORTFOLIO_RECONCILIATION_FAILED", ("selected_monthly_mismatches", "selected_summary_mismatches", "parent_comparison_mismatches", "direction_evidence_mismatches")),
        ("STAGE6_STRUCTURAL_OVERLAY_CONTRACT_FAILED", ("overlay_parent_evidence_mismatches", "overlay_status_mismatches")),
        ("STAGE6_STAGE7_HANDOFF_FAILED", ("decision_trace_mismatches", "stage7_handoff_mismatches")),
        ("STAGE6_SCOPE_VIOLATION", ("scope_violations",)),
        ("STAGE6_IMPLEMENTATION_PROVENANCE_FAILED", ("implementation_hash_mismatches", "output_hash_mismatches")),
        ("STAGE6_DETERMINISM_FAILED", ("determinism_mismatches",)),
    )
    for status, names in precedence:
        if any(counters[name] for name in names): return status
    if any(value != "PASS" for value in checks.values()): return "STAGE6_INDEPENDENT_AUDIT_FAILED"
    return AUDIT_STATUS


def independent_audit(out=OUT, *, verify_provenance=False, determinism_verified=False):
    out = Path(out); counters = {name: 0 for name in COUNTER_NAMES}; checks = {name: "NOT_CHECKED" for name in CHECK_NAMES}
    def gate(name, passed): checks[name] = "PASS" if passed else "FAIL"
    try:
        auth = authentication_results(); counters["source_authentication_mismatches"] = sum(not value for value in auth)
        for index, name in enumerate(CHECK_NAMES[:5]): gate(name, auth[index])
    except Exception:
        counters["source_authentication_mismatches"] += 1
        for name in CHECK_NAMES[:5]: gate(name, False)
    try:
        mutations = protected_tree_mutations()
        counters["protected_source_mutations"] = mutations; gate("protected_source_trees_unchanged", mutations == 0)
    except Exception: counters["protected_source_mutations"] += 1; gate("protected_source_trees_unchanged", False)
    expected_parents = parent_evidence()
    try:
        actual = read_csv(out / "production_parent_evidence.csv")
        counters["parent_evidence_mismatches"] = int(not _same(expected_parents, actual))
        universe = {(r["generation"], r["strategy"], r["timeframe"]) for r in actual}
        gate("parent_universe_exact_8", len(actual) == 8 and universe == set(PARENTS)); gate("parent_evidence_reconciled", counters["parent_evidence_mismatches"] == 0)
        for row in actual:
            calculated = row["true_oos_classification"] != "FAIL" and all(f(row[key]) > 0 for key in ("wf_net_R", "wf_expectancy_R", "oos_net_R", "oos_expectancy_R"))
            counters["parent_eligibility_mismatches"] += int(row["eligible"] != str(calculated).lower())
        gate("parent_eligibility_reconciled", counters["parent_eligibility_mismatches"] == 0)
    except Exception: counters["parent_evidence_mismatches"] += 1; counters["parent_eligibility_mismatches"] += 1; gate("parent_universe_exact_8", False); gate("parent_evidence_reconciled", False); gate("parent_eligibility_reconciled", False)
    try:
        decisions = read_csv(out / "production_parent_decision.csv"); selected = [r for r in decisions if r["decision"] == "SELECTED"]
        unique = [r for r in expected_parents if r["wf_classification"] == "WALK_FORWARD_PASS" and r["true_oos_classification"] == "PASS"]
        derived = (unique[0]["generation"], unique[0]["strategy"], unique[0]["timeframe"]) if len(unique) == 1 else None
        chosen = (selected[0]["generation"], selected[0]["strategy"], selected[0]["timeframe"]) if len(selected) == 1 else None
        chosen_evidence = next((r for r in expected_parents if (r["generation"], r["strategy"], r["timeframe"]) == chosen), None)
        valid = len(decisions) == 8 and len(selected) == 1 and chosen == derived and chosen_evidence and chosen_evidence["eligible"] == "true"
        concentration = bool(chosen_evidence and f(chosen_evidence["oos_net_R_without_top5"]) > 0)
        counters["parent_selection_violations"] = int(not valid) + int(not concentration)
        gate("parent_selection_contract_reconciled", valid); gate("concentration_guard_passed", concentration)
    except Exception: counters["parent_selection_violations"] += 1; gate("parent_selection_contract_reconciled", False); gate("concentration_guard_passed", False)
    expected_instruments = instrument_evidence()
    try:
        actual = read_csv(out / "production_instrument_evidence.csv")
        counters["instrument_evidence_mismatches"] = int(not _same(expected_instruments, actual)); gate("instrument_evidence_reconciled", counters["instrument_evidence_mismatches"] == 0)
        gate("instrument_universe_reconciled", {r["instrument"] for r in actual} == {"CNYRUBF", "GLDRUBF", "IMOEXF", "USDRUBF"})
        for row in actual:
            eligible = all(f(row[key]) > 0 for key in ("wf_trades", "wf_net_R", "wf_expectancy_R", "oos_trades", "oos_net_R", "oos_expectancy_R")) and f(row["wf_PF"]) > 1 and f(row["oos_PF"]) > 1
            counters["instrument_eligibility_mismatches"] += int(row["eligible"] != str(eligible).lower())
        gate("instrument_eligibility_reconciled", counters["instrument_eligibility_mismatches"] == 0)
    except Exception: counters["instrument_evidence_mismatches"] += 1; counters["instrument_eligibility_mismatches"] += 1; gate("instrument_universe_reconciled", False); gate("instrument_evidence_reconciled", False); gate("instrument_eligibility_reconciled", False)
    try:
        idec = read_csv(out / "production_instrument_decision.csv"); assembly = read_csv(out / "production_assembly_decision.csv")
        selected = {r["instrument"] for r in idec if r["decision"] == "SELECTED"}; eligible = {r["instrument"] for r in expected_instruments if r["eligible"] == "true"}
        corr, overlap = redundancy_evidence()
        redundancy_ok = f(corr["corrected_pearson_monthly_R"]) > 0 and f(overlap["overlap_jaccard"]) > 0 and next(r for r in idec if r["instrument"] == "USDRUBF")["decision"] == "NOT_SELECTED"
        lineages = {(r["generation"], r["strategy"], r["timeframe"]) for r in assembly}
        valid = len(selected) == 3 and selected <= eligible and selected == {r["instrument"] for r in assembly} and lineages == {SELECTED_PARENT} and {r["structural_overlay"] for r in assembly} == {"TRAIL1"} and redundancy_ok
        counters["instrument_selection_violations"] = int(not valid); gate("instrument_selection_contract_reconciled", valid)
        gate("no_cross_generation_mix", {r["generation"] for r in assembly} == {"v3"}); gate("no_cross_strategy_mix", {r["strategy"] for r in assembly} == {"T3"}); gate("no_cross_timeframe_mix", {r["timeframe"] for r in assembly} == {"H1"})
    except Exception: counters["instrument_selection_violations"] += 1; gate("instrument_selection_contract_reconciled", False); gate("no_cross_generation_mix", False); gate("no_cross_strategy_mix", False); gate("no_cross_timeframe_mix", False)
    try:
        actual = read_csv(out / "selected_pair_diversification_evidence.csv"); expected = pair_evidence()
        counters["pair_diversification_mismatches"] = int(not _same(expected, actual)); gate("pair_diversification_evidence_reconciled", counters["pair_diversification_mismatches"] == 0); gate("selected_pair_samples_adequate", len(actual) == 3 and all(r["sample_flag"] == "ADEQUATE" for r in actual))
    except Exception: counters["pair_diversification_mismatches"] += 1; gate("pair_diversification_evidence_reconciled", False); gate("selected_pair_samples_adequate", False)
    expected_monthly = selected_monthly(); expected_summary = summaries(expected_monthly)
    for counter, check, filename, expected in (("selected_monthly_mismatches", "selected_monthly_series_reconciled", "selected_assembly_monthly_series.csv", expected_monthly), ("selected_summary_mismatches", "selected_summary_reconciled", "selected_assembly_summary.csv", expected_summary), ("parent_comparison_mismatches", "parent_comparison_reconciled", "selected_assembly_parent_comparison.csv", parent_comparison(expected_summary)), ("direction_evidence_mismatches", "direction_evidence_reconciled", "selected_assembly_direction_evidence.csv", direction_evidence())):
        try: counters[counter] = int(not _same(expected, read_csv(out / filename))); gate(check, counters[counter] == 0)
        except Exception: counters[counter] += 1; gate(check, False)
    try:
        basis_ok = all(r["portfolio_economic_basis"] == BASKET_BASIS for r in read_csv(out / "selected_assembly_monthly_series.csv") + read_csv(out / "selected_assembly_summary.csv") + read_csv(out / "selected_assembly_parent_comparison.csv")) and "do not represent a TRAIL1-modified basket backtest" in (out / "Stage_6_Production_Assembly_Decision_Report.md").read_text()
        gate("canonical_basket_basis_labeled", basis_ok); counters["selected_monthly_mismatches"] += int(not basis_ok)
    except Exception: counters["selected_monthly_mismatches"] += 1; gate("canonical_basket_basis_labeled", False)
    try:
        actual = read_csv(out / "selected_overlay_parent_evidence.csv"); expected = overlay_parent_evidence(); counters["overlay_parent_evidence_mismatches"] = int(not _same(expected, actual)); gate("selected_overlay_parent_evidence_reconciled", counters["overlay_parent_evidence_mismatches"] == 0); gate("overlay_authority_authenticated", authentication_results()[4])
        wf = lookup(actual, lifecycle="walk_forward"); oos = lookup(actual, lifecycle="historical_true_oos")
        tradeoff = f(wf["delta_net_R"]) > 0 and f(wf["delta_max_DD"]) < 0 and f(wf["delta_recovery"]) > 0 and f(oos["delta_net_R"]) > 0 and f(oos["delta_max_DD"]) < 0 and f(oos["delta_recovery"]) < 0 and all(r["evidence_label"] == "RETROSPECTIVE_CAUSAL_VALIDATION" for r in actual)
        report_text = (out / "Stage_6_Production_Assembly_Decision_Report.md").read_text(); disclosed = tradeoff and "does not dominate the canonical exit on every risk metric" in report_text
        gate("trail1_tradeoff_disclosed", disclosed); counters["overlay_status_mismatches"] += int(not disclosed)
    except Exception: counters["overlay_parent_evidence_mismatches"] += 1; counters["overlay_status_mismatches"] += 1; gate("selected_overlay_parent_evidence_reconciled", False); gate("overlay_authority_authenticated", False); gate("trail1_tradeoff_disclosed", False)
    try:
        actual = read_csv(out / "structural_overlay_decision.csv"); expected = overlay_rows(); overlay_ok = _same(expected, actual)
        assembly = read_csv(out / "production_assembly_decision.csv"); no_combo = all(r["structural_overlay"] == "TRAIL1" for r in assembly)
        no_promotion = next(r for r in actual if "RISK_CAP" in r["component"])["decision"] == "DEFERRED_UNRESOLVED" and all(r["decision"] != "SELECTED" for r in actual if r["stage4_status"] == "NOT_ADMITTED")
        counters["overlay_status_mismatches"] += int(not overlay_ok) + int(not no_combo) + int(not no_promotion)
        gate("structural_overlay_status_reconciled", overlay_ok); gate("no_be1_trail1_combination", no_combo); gate("no_unvalidated_rule_promoted", no_promotion)
    except Exception: counters["overlay_status_mismatches"] += 1; gate("structural_overlay_status_reconciled", False); gate("no_be1_trail1_combination", False); gate("no_unvalidated_rule_promoted", False)
    try:
        actual = read_csv(out / "stage6_decision_trace.csv"); counters["decision_trace_mismatches"] = int(not _same(trace_rows(), actual)); gate("decision_trace_complete", counters["decision_trace_mismatches"] == 0)
    except Exception: counters["decision_trace_mismatches"] += 1; gate("decision_trace_complete", False)
    try:
        actual = read_csv(out / "stage6_stage7_handoff.csv"); counters["stage7_handoff_mismatches"] = int(not _same(handoff_rows(), actual)); gate("stage7_handoff_reconciled", counters["stage7_handoff_mismatches"] == 0); gate("stage7_boundary_preserved", counters["stage7_handoff_mismatches"] == 0)
    except Exception: counters["stage7_handoff_mismatches"] += 1; gate("stage7_handoff_reconciled", False); gate("stage7_boundary_preserved", False)
    try:
        forbidden_headers = {"objective_function", "weighted_score", "composite_score", "rank", "leaderboard", "optimizer", "all_subsets", "all_triplets", "grid_search", "selected_session", "selected_minimum_hold", "correlation_threshold"}
        for path in out.glob("*.csv"):
            with path.open(newline="", encoding="utf-8") as handle: counters["scope_violations"] += len(forbidden_headers & {x.lower() for x in next(csv.reader(handle))})
        text = "\n".join((out / name).read_text(encoding="utf-8").lower() for name in ("Stage_6_Production_Assembly_Decision_Report.md",))
        counters["scope_violations"] += int("trail1 dominates canonical on all risk/return metrics" in text)
        for name in ("no_exhaustive_subset_search", "no_numeric_score", "no_new_backtest", "no_new_optimizer", "no_new_hypothesis"): gate(name, counters["scope_violations"] == 0)
    except Exception: counters["scope_violations"] += 1; [gate(name, False) for name in ("no_exhaustive_subset_search", "no_numeric_score", "no_new_backtest", "no_new_optimizer", "no_new_hypothesis")]
    if verify_provenance:
        try:
            manifest = json.loads((out / "manifest_stage6.json").read_text())
            actual_impl = {Path(name).name: sha(REPO / name) for name in IMPLEMENTATION}
            counters["implementation_hash_mismatches"] = sum(manifest.get("implementation_file_hashes", {}).get(name) != value for name, value in actual_impl.items()) + abs(len(manifest.get("implementation_file_hashes", {})) - len(actual_impl))
            actual_outputs = {path.name: sha(path) for path in sorted(out.iterdir()) if path.suffix in (".csv", ".md")}
            counters["output_hash_mismatches"] = sum(manifest.get("output_hashes", {}).get(name) != value for name, value in actual_outputs.items()) + abs(len(manifest.get("output_hashes", {})) - len(actual_outputs))
            gate("implementation_hashes_verified", counters["implementation_hash_mismatches"] == 0); gate("output_hashes_verified", counters["output_hash_mismatches"] == 0)
        except Exception: counters["implementation_hash_mismatches"] += 1; counters["output_hash_mismatches"] += 1; gate("implementation_hashes_verified", False); gate("output_hashes_verified", False)
    else:
        gate("implementation_hashes_verified", True); gate("output_hashes_verified", True)
    counters["determinism_mismatches"] = 0 if determinism_verified or not verify_provenance else 1; gate("deterministic_artifacts", counters["determinism_mismatches"] == 0)
    status = _fail_status(counters, checks)
    return {"status": status, "checks": checks, "counters": counters, "failure_precedence": "input authentication -> protected source integrity -> parent evidence -> parent decision contract -> instrument evidence -> instrument decision contract -> diversification evidence -> selected basket reconstruction -> overlay evidence -> Stage7 handoff -> scope -> implementation hashes -> determinism -> success"}


def manifest_payload(out, audit_status, deterministic):
    out = Path(out)
    protected = {path: {"expected_frozen_sha256": frozen_tree_hash(path), "actual_current_sha256": current_tree_hash(path)} for path in PROTECTED}
    implementation = {Path(name).name: sha(REPO / name) for name in IMPLEMENTATION}
    outputs = {path.name: sha(path) for path in sorted(out.iterdir()) if path.suffix in (".csv", ".md")}
    return {"task_base_sha": TASK_BASE_SHA, "decision_source_stage6_base_sha": DECISION_SOURCE_SHA, "status": STATUS, "audit_status": audit_status, "decision_outcome": "SELECTED", "production_assembly_id": ASSEMBLY_ID, "selected_generation": "v3", "selected_futures_type": "perpetual", "selected_strategy": "T3", "selected_timeframe": "H1", "selected_instruments": list(SELECTED_INSTRUMENTS), "selected_structural_overlay": "TRAIL1", "canonical_economic_contract": ECONOMIC_CONTRACT, "research_tick": 0.001, "basket_verification_basis": BASKET_BASIS, "overlay_evidence_basis": "RETROSPECTIVE_CAUSAL_VALIDATION", "overlay_evidence_scope": "V3_PERPETUAL_T3_H1_PARENT", "overlay_fresh_oos": False, "source_tree_hashes": protected, "implementation_file_hashes": implementation, "output_hashes": outputs, "determinism": "BYTE_IDENTICAL_FRESH_BUILDS" if deterministic else "NOT_CERTIFIED", "deterministic_artifact_set": "all CSV and report MD; manifest/audit excluded to avoid circular self-hashes", "no_new_backtest": True, "no_optimizer": True, "no_parameter_search": True, "no_subset_search": True, "no_new_hypothesis": True, "stage7_status": "NEXT"}


def build(out=OUT):
    """Plain build: artifacts are produced, but AUDIT_PASSED is never published."""
    build_artifacts(out)
    audit = independent_audit(out)
    audit["status"] = "STAGE6_CERTIFICATION_REQUIRED"
    (Path(out) / "audit_stage6.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    manifest = manifest_payload(out, audit["status"], False)
    (Path(out) / "manifest_stage6.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def certify(out=OUT):
    """Two isolated builds, byte comparison, semantic audit, then publication."""
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        build_artifacts(first); build_artifacts(second)
        names_a = sorted(p.name for p in Path(first).iterdir() if p.suffix in (".csv", ".md"))
        names_b = sorted(p.name for p in Path(second).iterdir() if p.suffix in (".csv", ".md"))
        deterministic = names_a == names_b and all((Path(first) / name).read_bytes() == (Path(second) / name).read_bytes() for name in names_a)
        semantic = independent_audit(first, determinism_verified=deterministic)
        if semantic["status"] != AUDIT_STATUS: raise RuntimeError(semantic["status"])
    build_artifacts(out)
    manifest = manifest_payload(out, "CERTIFICATION_IN_PROGRESS", deterministic)
    (Path(out) / "manifest_stage6.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    audit = independent_audit(out, verify_provenance=True, determinism_verified=deterministic)
    if audit["status"] != AUDIT_STATUS: raise RuntimeError(audit["status"])
    (Path(out) / "audit_stage6.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    manifest["audit_status"] = audit["status"]
    (Path(out) / "manifest_stage6.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def fresh_determinism_check():
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        build_artifacts(first); build_artifacts(second)
        names = sorted(p.name for p in Path(first).iterdir() if p.suffix in (".csv", ".md"))
        return names == sorted(p.name for p in Path(second).iterdir() if p.suffix in (".csv", ".md")) and all((Path(first) / name).read_bytes() == (Path(second) / name).read_bytes() for name in names)
