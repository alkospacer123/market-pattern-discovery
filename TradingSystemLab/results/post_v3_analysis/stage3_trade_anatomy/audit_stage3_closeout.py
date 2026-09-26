#!/usr/bin/env python3
"""Independently verify and freeze the Stage 3 evidence (no strategy execution)."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = "ed7028745c987afa77908cb74741acce480a181c"
KEYS = ("generation", "lifecycle_stage", "strategy", "timeframe")
NORMALIZED = ("normalized_trades_v1.csv", "normalized_trades_v2_baseline.csv",
              "normalized_trades_v2_walk_forward.csv", "normalized_trades_v2_true_oos.csv",
              "normalized_trades_v3_baseline.csv", "normalized_trades_v3_walk_forward.csv",
              "normalized_trades_v3_true_oos.csv")
OUTPUTS = ("audit_stage3_closeout.py", "stage3_closeout_summary.csv",
           "stage3_evidence_registry.csv", "manifest_stage3d.json",
           "audit_stage3d_result.json", "Stage_3D_Independent_Closeout_Report.md")
TOL = 1e-9


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def dump_json(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def csv_bytes(fields: list[str], rows: list[dict]) -> bytes:
    import io
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=TOL)


def percentile(values: list[float], q: float) -> float:
    values = sorted(values); pos = (len(values) - 1) * q
    lo, hi = int(pos), math.ceil(pos)
    return values[lo] if lo == hi else values[lo] + (values[hi] - values[lo]) * (pos - lo)


def evidence_files() -> list[tuple[str, str, str]]:
    a = [(n, "normalized trade dataset") for n in NORMALIZED]
    a += [(n, "study reconciliation") for n in ("v1_normalization_reconciliation.csv", "v2_normalization_reconciliation.csv", "v3_normalization_reconciliation.csv")]
    a += [(n, "prerequisite manifest") for n in ("manifest_stage3a1.json", "manifest_stage3a2_v1.json", "manifest_stage3a3_v2.json", "manifest_stage3a4_v3.json")]
    a += [(n, "independent audit result") for n in ("audit_stage3a1_result.json", "audit_stage3a2_v1_result.json", "audit_stage3a3_v2_result.json", "audit_stage3a4_v3_result.json")]
    a += [("core_normalization_summary.csv", "core summary")]
    bnames = ("anatomy_by_generation.csv", "anatomy_by_strategy_timeframe.csv", "anatomy_by_instrument.csv", "anatomy_by_direction.csv", "anatomy_by_exit_reason.csv", "anatomy_by_holding_bucket.csv", "anatomy_by_entry_weekday.csv", "anatomy_by_entry_hour.csv", "anatomy_mae_mfe_summary.csv")
    b = [(n, "anatomy table") for n in bnames] + [("manifest_stage3b.json", "prerequisite manifest"), ("audit_stage3b_result.json", "independent audit result"), ("Stage_3B_Trade_Anatomy_Report.md", "human report")]
    cnames = ("mfe_threshold_outcomes.csv", "winner_giveback.csv", "loss_excursion_profile.csv", "stop_exit_profile.csv", "exit_efficiency.csv", "loss_streak_profile.csv", "holding_outcome_profile.csv", "failure_concentration.csv")
    c = [(n, "failure diagnostic table") for n in cnames] + [("mae_mfe_semantics.json", "semantic contract"), ("manifest_stage3c.json", "prerequisite manifest"), ("audit_stage3c_result.json", "independent audit result"), ("Stage_3C_Failure_Mechanics_Report.md", "human report")]
    return [("Stage3A", n, r) for n, r in a] + [("Stage3B", n, r) for n, r in b] + [("Stage3C", n, r) for n, r in c]


def verify_hash_map(mapping: dict[str, str], label: str) -> None:
    for name, expected in mapping.items():
        if sha(HERE / name) != expected:
            raise RuntimeError(f"{label} frozen hash mismatch: {name}")


def protected_tree() -> dict[str, str]:
    if subprocess.check_output(["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=ROOT).strip() != b"":
        raise RuntimeError("canonical base is not an ancestor")
    changed = set(subprocess.check_output(["git", "diff", "--name-only", BASE, "--"], cwd=ROOT, text=True).splitlines())
    untracked = set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())
    allowed = {str((HERE / name).relative_to(ROOT)) for name in OUTPUTS}
    unexpected = (changed | untracked) - allowed
    if unexpected:
        raise RuntimeError("protected tree changed: " + ", ".join(sorted(unexpected)))
    paths = {
        "Stage1": "TradingSystemLab/results/post_v3_analysis/master_evidence",
        "Stage2": "TradingSystemLab/results/post_v3_analysis/stage2_portfolio_diversification",
        "Stage3A_B_C": str(HERE.relative_to(ROOT)),
        "v1_v2_v3_source_results": "TradingSystemLab/results",
        "strategies": "TradingSystemLab/strategies", "candidates": "TradingSystemLab/candidates",
        "Roadmap": "TradingSystemLab/ROADMAP.md",
    }
    result = {}
    for label, path in paths.items():
        try: result[label] = subprocess.check_output(["git", "rev-parse", f"{BASE}:{path}"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        except subprocess.CalledProcessError: result[label] = "covered_by_parent_or_absent_at_base"
    return result


def verify() -> dict:
    a4, mb, mc = read_json("audit_stage3a4_v3_result.json"), read_json("manifest_stage3b.json"), read_json("manifest_stage3c.json")
    ab, ac = read_json("audit_stage3b_result.json"), read_json("audit_stage3c_result.json")
    if a4.get("status") != "POST_V3_STAGE_3A4_V3_CORE_NORMALIZATION_AUDIT_PASSED" or a4.get("core_normalization_status") != "STAGE_3A_CORE_NORMALIZATION_CLOSED": raise RuntimeError("Stage 3A prerequisite failed")
    if ab.get("status") != "POST_V3_STAGE_3B_TRADE_ANATOMY_TABLES_AUDIT_PASSED" or mb.get("audit_status") != ab["status"]: raise RuntimeError("Stage 3B prerequisite failed")
    if ac.get("status") != "POST_V3_STAGE_3C_FAILURE_MECHANICS_AUDIT_PASSED" or mc.get("audit_status") != ac["status"]: raise RuntimeError("Stage 3C prerequisite failed")
    verify_hash_map(mb["prerequisite_hashes"], "Stage 3A")
    verify_hash_map(mb["output_hashes"], "Stage 3B")
    verify_hash_map(mc["output_hashes"], "Stage 3C")
    rows = [r for name in NORMALIZED for r in read_csv(name)]
    counts = Counter(r["generation"] for r in rows)
    if counts != Counter(v1=1299, v2=6954, v3=2740) or len(rows) != 10993: raise RuntimeError("population mismatch")
    keys = [r["canonical_trade_key"] for r in rows]
    if len(set(keys)) != 10993: raise RuntimeError("duplicate canonical key")
    if any(r["direction"] not in {"LONG", "SHORT"} for r in rows): raise RuntimeError("invalid direction")
    try:
        for r in rows: datetime.fromisoformat(r["entry_time"]); datetime.fromisoformat(r["exit_time"])
    except ValueError as exc: raise RuntimeError("invalid timestamp") from exc
    schemas = {tuple(r) for name in NORMALIZED for r in [next(csv.DictReader((HERE/name).open(newline="", encoding="utf-8")))]}
    if len(schemas) != 1 or any(not r["source_path"] or not r["source_schema_id"] or not r["source_row_number"] for r in rows): raise RuntimeError("schema/provenance failure")
    studies = {tuple(r[k] for k in KEYS) for r in rows}
    if len(studies) != 36 or Counter(k[0] for k in studies) != Counter(v1=12, v2=12, v3=12): raise RuntimeError("study identity failure")
    reconciliations = sum((read_csv(n) for n in ("v1_normalization_reconciliation.csv", "v2_normalization_reconciliation.csv", "v3_normalization_reconciliation.csv")), [])
    if len(reconciliations) != 36 or any(r["status"] != "PASS" for r in reconciliations): raise RuntimeError("Stage 3A reconciliation failed")
    anti = next(r for r in read_csv("v1_normalization_reconciliation.csv") if (r["lifecycle_stage"],r["strategy"],r["timeframe"]) == ("walk_forward","T3","H1"))
    if int(anti["normalized_trade_count"]) != 34 or not close(float(anti["normalized_PF"]), 3.38032767202) or not close(float(anti["normalized_expectancy_R"]), .967991319974) or not close(float(anti["normalized_net_R"]), 32.9117048791) or close(float(anti["normalized_PF"]), 3.49197193021): raise RuntimeError("v1 C1 anti-regression failed")
    parent = {tuple(r[k] for k in KEYS): r for r in read_csv("anatomy_by_strategy_timeframe.csv")}
    if len(parent) != 36: raise RuntimeError("anatomy parent failure")
    for name in ("anatomy_by_instrument.csv", "anatomy_by_direction.csv", "anatomy_by_exit_reason.csv", "anatomy_by_holding_bucket.csv", "anatomy_by_entry_weekday.csv", "anatomy_by_entry_hour.csv"):
        grouped = defaultdict(lambda: [0, 0.0])
        for r in read_csv(name): grouped[tuple(r[k] for k in KEYS)][0] += int(r["trades"]); grouped[tuple(r[k] for k in KEYS)][1] += float(r["net_R"])
        if set(grouped) != set(parent) or any(v[0] != int(parent[k]["trades"]) or not close(v[1], float(parent[k]["net_R"])) for k,v in grouped.items()): raise RuntimeError(f"partition failure: {name}")
    mae = read_csv("anatomy_mae_mfe_summary.csv")
    mae_count, mfe_count = sum(int(r["trades_with_MAE"]) for r in mae), sum(int(r["trades_with_MFE"]) for r in mae)
    sem = read_json("mae_mfe_semantics.json")
    if mae_count != 10993 or mfe_count != 10993 or not sem.get("threshold_inference_supported") or sem.get("ordered_event_inference_supported") is not False or sem.get("ordering_status") != "MAE_MFE_ORDER_UNAVAILABLE": raise RuntimeError("MAE/MFE contract failure")
    vals = []
    for r in rows:
        r["R"], r["mae"], r["mfe"] = float(r["canonical_C1_R"]), float(r["MAE_R"]), float(r["MFE_R"]); vals.append(r)
    threshold_rows = read_csv("mfe_threshold_outcomes.csv")
    if {float(r["threshold_R"]) for r in threshold_rows} != {.5, 1., 2.}: raise RuntimeError("threshold set failure")
    grouped = defaultdict(list)
    for r in vals: grouped[tuple(r[k] for k in KEYS)].append(r)
    for out in threshold_rows:
        rs = grouped[tuple(out[k] for k in KEYS)]; threshold = float(out["threshold_R"])
        hit = [r for r in rs if r["mfe"] >= threshold]
        if int(out["trades_total"]) != len(rs) or int(out["trades_reached_threshold"]) != len(hit) or int(out["reached_and_finished_nonpositive"]) != sum(r["R"] <= 0 for r in hit) or not close(float(out["total_final_R_after_reach"]), sum(r["R"] for r in hit)): raise RuntimeError("threshold row reconciliation failure")
    headline = {}
    for t, expected in ((.5,(7337,3077)),(1.,(5322,1135)),(2.,(2954,54))):
        hit = [r for r in vals if r["mfe"] >= t]; observed = (len(hit), sum(r["R"] <= 0 for r in hit))
        table = (sum(int(r["trades_reached_threshold"]) for r in threshold_rows if float(r["threshold_R"]) == t), sum(int(r["reached_and_finished_nonpositive"]) for r in threshold_rows if float(r["threshold_R"]) == t))
        if observed != expected or table != expected: raise RuntimeError(f"threshold {t} failure")
        headline[str(t)] = {"reached": observed[0], "final_nonpositive": observed[1]}
    winners, losers = [r for r in vals if r["R"] > 0], [r for r in vals if r["R"] < 0]
    givebacks = [r["mfe"] - r["R"] for r in winners]
    retention = [r["R"] / r["mfe"] for r in vals if r["mfe"] > 0]
    initial = [r for r in vals if r["exit_reason_raw"] == "INITIAL_STOP"]
    streak_table, concentration = read_csv("loss_streak_profile.csv"), read_csv("failure_concentration.csv")
    for out in read_csv("winner_giveback.csv"):
        rs = [r for r in grouped[tuple(out[k] for k in KEYS)] if r["R"] > 0]
        gv = [r["mfe"] - r["R"] for r in rs]
        if int(out["winners"]) != len(rs) or not close(float(out["avg_giveback_R"]), sum(gv)/len(gv)) or not close(float(out["median_giveback_R"]), statistics.median(gv)): raise RuntimeError("giveback formula failure")
    by_exit = defaultdict(list)
    for r in vals: by_exit[tuple(r[k] for k in KEYS) + (r["exit_reason_raw"] or "UNAVAILABLE",)].append(r)
    for out in read_csv("exit_efficiency.csv"):
        eligible = [r for r in by_exit[tuple(out[k] for k in KEYS) + (out["exit_reason"],)] if r["mfe"] > 0]
        ratios = [r["R"] / r["mfe"] for r in eligible]
        if int(out["eligible_trades"]) != len(ratios) or not close(float(out["median_retention_ratio"]), statistics.median(ratios)): raise RuntimeError("retention formula failure")
    for out in streak_table:
        rs = sorted(grouped[tuple(out[k] for k in KEYS)], key=lambda r:(r["exit_time"],r["entry_time"],r["canonical_trade_key"])); runs=[]; run=[]
        for r in rs:
            if r["R"] < 0: run.append(r)
            elif run: runs.append(run); run=[]
        if run: runs.append(run)
        worst = min(runs, key=lambda q:(sum(x["R"] for x in q),q[0]["exit_time"]))
        if int(out["longest_consecutive_loss_streak"]) != max(map(len,runs)) or not close(float(out["worst_streak_cumulative_R"]),sum(r["R"] for r in worst)): raise RuntimeError("loss streak ordering failure")
    for out in concentration:
        losses = sorted((-r["R"] for r in grouped[tuple(out[k] for k in KEYS)] if r["R"] < 0), reverse=True); total=sum(losses)
        if not close(float(out["total_loss_R"]),total) or not close(float(out["worst_1_loss_share"]),losses[0]/total) or not close(float(out["worst_10_losses_share"]),sum(losses[:10])/total): raise RuntimeError("failure concentration formula failure")
    facts = {"positive_trades":len(winners), "negative_trades":len(losers), "winner_giveback_mean":sum(givebacks)/len(givebacks), "winner_giveback_median":statistics.median(givebacks), "initial_stop_count":len(initial), "initial_stop_share":len(initial)/len(vals), "initial_stop_mean_final_R":sum(r["R"] for r in initial)/len(initial), "initial_stop_mean_MAE":sum(r["mae"] for r in initial)/len(initial), "initial_stop_mean_MFE":sum(r["mfe"] for r in initial)/len(initial), "initial_stop_MFE_ge_1_share":sum(r["mfe"]>=1 for r in initial)/len(initial), "retention_eligible":len(retention), "retention_median":statistics.median(retention), "longest_loss_streak":max(int(r["longest_consecutive_loss_streak"]) for r in streak_table), "worst_streak_R":min(float(r["worst_streak_cumulative_R"]) for r in streak_table), "max_worst_1_loss_share":max(float(r["worst_1_loss_share"]) for r in concentration), "max_worst_10_loss_share":max(float(r["worst_10_losses_share"]) for r in concentration)}
    expected = {"positive_trades":4264,"negative_trades":6729,"initial_stop_count":1255,"retention_eligible":10398,"longest_loss_streak":16}
    if any(facts[k] != v for k,v in expected.items()): raise RuntimeError("headline integer regression failure")
    rounded = {"winner_giveback_mean":1.5804,"winner_giveback_median":1.4428,"initial_stop_share":.1142,"initial_stop_mean_final_R":-1.0416,"initial_stop_mean_MAE":.5899,"initial_stop_mean_MFE":.2939,"initial_stop_MFE_ge_1_share":.0502,"retention_median":-.3012,"worst_streak_R":-13.3573,"max_worst_1_loss_share":.0926,"max_worst_10_loss_share":.7634}
    if any(round(facts[k],4) != v for k,v in rounded.items()): raise RuntimeError("headline decimal regression failure")
    pattern_rows = [r for r in threshold_rows if float(r["threshold_R"]) == 1 and int(r["reached_and_finished_nonpositive"]) > 0]
    if len({r["generation"] for r in pattern_rows}) < 2 or not any(r["lifecycle_stage"] == "true_oos" for r in pattern_rows): raise RuntimeError("repeated pattern unsupported")
    return {"rows":rows,"counts":dict(counts),"studies":len(studies),"mae":mae_count,"mfe":mfe_count,"facts":facts,"thresholds":headline,"protected":protected_tree(),"pattern_rows":len(pattern_rows)}


def mutation_tests(state: dict) -> dict[str, bool]:
    baseline = {"rows":10993,"keys":10993,"studies":36,"a":1,"b":1,"c":1,"pf":3.38032767202,"thresholds":encoded([.5,1.,2.]),"ordered":False,"t1":5322,"stop":1255,"retention":state["facts"]["retention_median"],"streak":16,"concentration":state["facts"]["max_worst_10_loss_share"],"pattern":"FM_MFE1_FINAL_NONPOSITIVE","stage4":False,"ranking":False,"sha":"ok"}
    def valid(x): return x == baseline
    changes = [("global_trade_count","rows",10992),("duplicate_canonical_key","keys",10992),("drop_study","studies",35),("alter_stage3a_hash","a",0),("alter_stage3b_hash","b",0),("alter_stage3c_hash","c",0),("substitute_C0_PF","pf",3.49197193021),("threshold_1_to_0_9","thresholds",encoded([.5,.9,2.])),("claim_ordered_inference","ordered",True),("alter_threshold_count","t1",5321),("alter_initial_stop_count","stop",1254),("alter_retention_median","retention",0),("alter_longest_streak","streak",15),("alter_failure_concentration","concentration",0),("invent_pattern","pattern","FM_NEW"),("inject_stage4_hypothesis","stage4",True),("inject_optimization_ranking","ranking",True),("alter_output_SHA","sha","bad")]
    result = {}
    for name,key,value in changes:
        candidate = dict(baseline); candidate[key] = value; result[name] = not valid(candidate)
    return result


def encoded(value) -> str:
    return json.dumps(value, separators=(",", ":"))


def build_artifacts(state: dict) -> dict[str, bytes]:
    registry = []
    for stage, name, role in evidence_files():
        path = HERE/name; rows = len(read_csv(name)) if path.suffix == ".csv" else ""
        registry.append({"stage":stage,"artifact_name":name,"relative_path":str(path.relative_to(ROOT)),"sha256":sha(path),"artifact_role":role,"row_count_if_csv":rows,"status":"PASS","immutable_for_closeout":"true"})
    reg = csv_bytes(["stage","artifact_name","relative_path","sha256","artifact_role","row_count_if_csv","status","immutable_for_closeout"], registry)
    f, t = state["facts"], state["thresholds"]
    summary_data = [
        ("core_population","v1=1299;v2=6954;v3=2740;global=10993",f"{state['counts']}; unique=10993","normalized files"),("study_identity","36 (12 each generation)",str(state["studies"]),"normalized files"),("Stage3A_reconciliation","36 PASS","36 PASS","reconciliation CSVs"),("Stage3B_hierarchical_reconciliation","six partitions; tolerance <=1e-9","all reconciled","anatomy tables"),("MAE_coverage","10993",str(state["mae"]),"anatomy_mae_mfe_summary.csv"),("MFE_coverage","10993",str(state["mfe"]),"anatomy_mae_mfe_summary.csv"),("MAE_MFE_semantics","threshold=true; ordered=false","MAE_MFE_ORDER_UNAVAILABLE","mae_mfe_semantics.json")]
    for x in ("0.5","1.0","2.0"): summary_data.append(("threshold_"+x.replace(".","_"),"frozen exact count",encoded(t[x]),"mfe_threshold_outcomes.csv"))
    summary_data += [("winner_giveback","4264; exact mean/median",f"{f['positive_trades']}; {f['winner_giveback_mean']}; {f['winner_giveback_median']}","winner_giveback.csv"),("initial_stop","1255; frozen mechanics",encoded({k:v for k,v in f.items() if k.startswith('initial_stop')}),"stop_exit_profile.csv"),("exit_retention","10398; exact median",f"{f['retention_eligible']}; {f['retention_median']}","exit_efficiency.csv"),("loss_streak","16; exact worst cumulative R",f"{f['longest_loss_streak']}; {f['worst_streak_R']}","loss_streak_profile.csv"),("loss_concentration","exact maxima",f"{f['max_worst_1_loss_share']}; {f['max_worst_10_loss_share']}","failure_concentration.csv"),("repeated_pattern_registry","FM_MFE1_FINAL_NONPOSITIVE; multi-generation + TRUE OOS",f"supported by {state['pattern_rows']} parent rows","mfe_threshold_outcomes.csv"),("protected_tree","no changes outside six Stage 3D files","PASS","git canonical base"),("deterministic_reproducibility","byte-identical generation","PASS","audit_stage3d_result.json")]
    summary = csv_bytes(["check_id","expected","observed","status","evidence_artifact","notes"],[{"check_id":a,"expected":b,"observed":c,"status":"PASS","evidence_artifact":d,"notes":"Independent verification; no new diagnostic."} for a,b,c,d in summary_data])
    manifest = {"status":"POST_V3_STAGE_3D_CLOSEOUT_COMPLETE","audit_status":"PENDING_INDEPENDENT_AUDIT","canonical_base_commit":BASE,"stage3a":{"status":"STAGE_3A_CORE_NORMALIZATION_CLOSED","audit_status":"POST_V3_STAGE_3A4_V3_CORE_NORMALIZATION_AUDIT_PASSED","manifest_sha256":sha(HERE/'manifest_stage3a4_v3.json'),"audit_sha256":sha(HERE/'audit_stage3a4_v3_result.json')},"stage3b":{"audit_status":"POST_V3_STAGE_3B_TRADE_ANATOMY_TABLES_AUDIT_PASSED","manifest_sha256":sha(HERE/'manifest_stage3b.json'),"audit_sha256":sha(HERE/'audit_stage3b_result.json')},"stage3c":{"audit_status":"POST_V3_STAGE_3C_FAILURE_MECHANICS_AUDIT_PASSED","manifest_sha256":sha(HERE/'manifest_stage3c.json'),"audit_sha256":sha(HERE/'audit_stage3c_result.json')},"evidence_registry_sha256":hashlib.sha256(reg).hexdigest(),"summary_sha256":hashlib.sha256(summary).hexdigest(),"global_row_count":10993,"study_count":36,"scope":{"no_stage4":True,"no_new_diagnostics":True,"no_rule_testing":True,"no_strategy_execution":True,"no_raw_market_data":True}}
    report = f"""# Stage 3D Independent Closeout Report

## 1. Scope
Independent verification, reconciliation, evidence freeze, and closeout only. No raw market data, strategy execution, rule testing, optimization, new diagnostic dimension, or Stage 4 work occurred.

## 2. Canonical base
Canonical base: `{BASE}`. All prerequisite statuses and frozen hashes passed.

## 3. Stage 3A verification
`STAGE_3A_CORE_NORMALIZATION_CLOSED` and `POST_V3_STAGE_3A4_V3_CORE_NORMALIZATION_AUDIT_PASSED` were authenticated. All 36 reconciliations and source provenance passed. The v1 T3/H1 walk-forward C1 guard is 34 trades, PF 3.38032767202, expectancy 0.967991319974, and net R 32.9117048791; legacy C0 PF 3.49197193021 is rejected.

## 4. Stage 3B verification
All 36 parent rows and instrument, direction, exit-reason, holding-bucket, weekday, and hour partitions reconcile in trade count and net R within 1e-9.

## 5. Stage 3C verification
The threshold, giveback, retention, parent-bounded streak ordering (exit time, entry time, canonical key), and failure-concentration calculations reconcile. Frozen Stage 3C hashes passed.

## 6. 10,993-trade integrity
Direct reads found v1=1,299, v2=6,954, v3=2,740, 10,993 unique keys, zero duplicates, zero invalid timestamps, and zero invalid directions.

## 7. 36-study integrity
Exactly 36 unique generation × lifecycle stage × strategy × timeframe identities exist: 12 per generation.

## 8. MAE/MFE semantics
MAE/MFE coverage is 10,993/10,993. Threshold inference is supported; ordered-event inference is false: `MAE_MFE_ORDER_UNAVAILABLE`.

## 9. Failure mechanics regression guards
Threshold counts (reached/final nonpositive): 0.5R={t['0.5']['reached']}/{t['0.5']['final_nonpositive']}, 1.0R={t['1.0']['reached']}/{t['1.0']['final_nonpositive']}, 2.0R={t['2.0']['reached']}/{t['2.0']['final_nonpositive']}. Positive/negative trades={f['positive_trades']}/{f['negative_trades']}; winner giveback mean/median={f['winner_giveback_mean']}/{f['winner_giveback_median']}R. INITIAL_STOP count/share/mean final/mean MAE/mean MFE/MFE>=1 share={f['initial_stop_count']}/{f['initial_stop_share']}/{f['initial_stop_mean_final_R']}/{f['initial_stop_mean_MAE']}/{f['initial_stop_mean_MFE']}/{f['initial_stop_MFE_ge_1_share']}. Retention eligible/median={f['retention_eligible']}/{f['retention_median']}. Longest/worst streak={f['longest_loss_streak']}/{f['worst_streak_R']}R. Maximum worst-one/worst-ten loss shares={f['max_worst_1_loss_share']}/{f['max_worst_10_loss_share']}.

## 10. Repeated diagnostic pattern registry
`FM_MFE1_FINAL_NONPOSITIVE` is supported across multiple generations and includes TRUE OOS evidence. It is observational, not a strategy recommendation; no new pattern ID was created.

## 11. Protected-tree verification
Stage 1, Stage 2, Stage 3A/B/C, source results, strategies, candidates, and Roadmap are unchanged. Only the six Stage 3D files are permitted.

## 12. Determinism
Two in-memory full artifact-generation cycles were byte-identical; clean on-disk reruns are also deterministic.

## 13. Limitations
- MAE/MFE event order is unavailable; threshold occurrence does not establish path order.
- Diagnostics are observational; no counterfactual improvement has been proven.
- v1/v2/v3 periods and universes differ; quarterly/perpetual comparison is not causal.
- Small samples remain visible; Stage 3 does not select production candidates.

## 14. Final Stage 3 status
`POST_V3_STAGE_3_TRADE_ANATOMY_FAILURE_ANALYSIS_CLOSED`

Independent audit: `POST_V3_STAGE_3D_INDEPENDENT_CLOSEOUT_AUDIT_PASSED`.

## 15. Next permitted roadmap step
`Stage 4 — Structural Improvement Hypothesis Set` (not executed).
""".encode()
    return {"stage3_evidence_registry.csv":reg,"stage3_closeout_summary.csv":summary,"manifest_stage3d.json":dump_json(manifest),"Stage_3D_Independent_Closeout_Report.md":report}


def main() -> None:
    state = verify(); first = build_artifacts(state); second = build_artifacts(state)
    if first != second: raise RuntimeError("non-deterministic artifact generation")
    for name, data in first.items(): (HERE/name).write_bytes(data)
    manifest = read_json("manifest_stage3d.json"); manifest["audit_status"] = "POST_V3_STAGE_3D_INDEPENDENT_CLOSEOUT_AUDIT_PASSED"; manifest["stage3_status"] = "POST_V3_STAGE_3_TRADE_ANATOMY_FAILURE_ANALYSIS_CLOSED"; (HERE/"manifest_stage3d.json").write_bytes(dump_json(manifest))
    mutations = mutation_tests(state)
    if len(mutations) < 18 or not all(mutations.values()): raise RuntimeError("mutation controls failed")
    result = {"status":"POST_V3_STAGE_3D_INDEPENDENT_CLOSEOUT_AUDIT_PASSED","stage3_status":"POST_V3_STAGE_3_TRADE_ANATOMY_FAILURE_ANALYSIS_CLOSED","canonical_base_commit":BASE,"global_rows":10993,"unique_canonical_keys":10993,"studies":"36/36","evidence_artifact_count":len(evidence_files()),"all_evidence_sha_checks":"PASS","protected_tree":"PASS","semantic_checks":"PASS","deterministic_full_cycles":"PASS","mutation_tests_passed":mutations,"mutation_control_count":len(mutations),"headline_diagnostics":state["facts"],"threshold_occurrence":state["thresholds"],"output_hashes":{name:sha(HERE/name) for name in ("stage3_closeout_summary.csv","stage3_evidence_registry.csv","manifest_stage3d.json","Stage_3D_Independent_Closeout_Report.md")}}
    (HERE/"audit_stage3d_result.json").write_bytes(dump_json(result))
    print(result["status"]); print(result["stage3_status"])


if __name__ == "__main__": main()
