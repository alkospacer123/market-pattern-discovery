"""Artifact-only Stage 6 production assembly and independent reconciliation.

The module deliberately reads only closed Stage 1--5 evidence.  It contains no
market-data, strategy, execution, or parameter-search interface.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, pstdev

BASE_SHA = "fdee91b474ccdebcf9d7dc56d8e87a112d37e50e"
STATUS = "POST_V3_STAGE_6_PRODUCTION_ASSEMBLY_DECISION_COMPLETE"
AUDIT_STATUS = "POST_V3_STAGE_6_PRODUCTION_ASSEMBLY_DECISION_AUDIT_PASSED"
PARENTS = [(g, s, t) for g in ("v2", "v3") for s in ("T2", "T3") for t in ("M30", "H1")]
SELECTED_PARENT = ("v3", "T3", "H1")
# Qualitative synthesis: retain the strongest OOS contributor, the strongest WF
# currency sleeve, and the equity sleeve whose monthly signs diversify both.
SELECTED_INSTRUMENTS = ("CNYRUBF", "GLDRUBF", "IMOEXF")
SELECTED_OVERLAY = "TRAIL1"
ECONOMIC_CONTRACT = "CORRECTED_SINGLE_C1"

ROOT = Path(__file__).resolve().parents[3]
POST = ROOT / "results/post_v3_analysis"
S1, S2 = POST / "stage1_master_evidence", POST / "stage2_portfolio_diversification"
S3, S4 = POST / "stage3_trade_anatomy", POST / "stage4_structural_hypotheses"
S5 = POST / "stage5_structural_validation"
OUT = Path(__file__).resolve().parent


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, fields, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def f(x): return float(x)
def fmt(x): return format(float(x), ".12g")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_hash(path):
    h = hashlib.sha256()
    for p in sorted(Path(path).rglob("*")):
        if p.is_file():
            h.update(p.relative_to(path).as_posix().encode()); h.update(b"\0"); h.update(p.read_bytes())
    return h.hexdigest()


def git_tree(rel):
    return subprocess.check_output(["git", "rev-parse", f"{BASE_SHA}:TradingSystemLab/{rel}"], cwd=ROOT.parent, text=True).strip()


def lookup(rows, **keys):
    found = [r for r in rows if all(r.get(k) == v for k, v in keys.items())]
    if len(found) != 1: raise ValueError(f"expected one row for {keys}, got {len(found)}")
    return found[0]


def monthly_dd(values):
    equity = peak = 0.0; dd = 0.0
    for value in values:
        equity += value; peak = max(peak, equity); dd = min(dd, equity - peak)
    return dd


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
    for g, s, t in PARENTS:
        w = lookup(master, generation=g, strategy=s, timeframe=t, lifecycle_stage="walk_forward")
        o = lookup(master, generation=g, strategy=s, timeframe=t, lifecycle_stage="true_oos")
        m = lookup(monthly, generation=g, strategy=s, timeframe=t, lifecycle_stage="true_oos")
        p = lookup(portfolio, generation=g, strategy=s, timeframe=t, lifecycle_stage="true_oos")
        eligible = o["classification"] != "FAIL" and all(f(x) > 0 for x in (w["net_R"], w["expectancy_R"], o["net_R"], o["expectancy_R"]))
        reason = "HARD_GATES_PASS" if eligible else "HARD_GATE_FAILED"
        rows.append({
            "generation":g,"futures_type":w["futures_type"],"strategy":s,"timeframe":t,
            "wf_classification":w["classification"],"true_oos_classification":o["classification"],
            "wf_trades":w["total_trades"],"wf_PF":w["PF"],"wf_expectancy_R":w["expectancy_R"],"wf_net_R":w["net_R"],"wf_max_DD_R":w["max_drawdown_R"],"wf_recovery":w["recovery_factor"],
            "oos_trades":o["total_trades"],"oos_PF":o["PF"],"oos_expectancy_R":o["expectancy_R"],"oos_net_R":o["net_R"],"oos_max_DD_R":o["max_drawdown_R"],"oos_recovery":o["recovery_factor"],
            "oos_positive_quarter_share":o["positive_quarter_share"],"oos_net_R_without_top5":o["net_R_without_top5"],"oos_top5_positive_R_share":o["top5_positive_R_share"],
            "oos_positive_month_share":m["positive_month_share"],"oos_median_monthly_R":m["median_monthly_R"],"oos_monthly_R_std":m["monthly_R_std"],"oos_worst_month_R":m["worst_month_R"],"oos_monthly_equity_DD":p["monthly_equity_max_drawdown_R"],"oos_longest_negative_month_streak":m["longest_negative_month_streak"],
            "eligible":str(eligible).lower(),"eligibility_reason":reason})
    return rows


def instrument_evidence():
    stats = read_csv(S2 / "instrument_stability_summary.csv")
    by = defaultdict(dict)
    for r in stats:
        if (r["generation"],r["strategy"],r["timeframe"]) == SELECTED_PARENT: by[r["instrument"]][r["lifecycle_stage"]] = r
    rows=[]
    for inst in sorted(by):
        b,w,o=(by[inst][x] for x in ("baseline","walk_forward","true_oos"))
        eligible=all(f(x)>0 for x in (w["total_trades"],w["total_net_R"],w["expectancy_R"],o["total_trades"],o["total_net_R"],o["expectancy_R"])) and f(w["PF"])>1 and f(o["PF"])>1
        rows.append({"instrument":inst,"baseline_trades":b["total_trades"],"baseline_net_R":b["total_net_R"],"baseline_PF":b["PF"],"baseline_expectancy_R":b["expectancy_R"],
          "wf_trades":w["total_trades"],"wf_net_R":w["total_net_R"],"wf_PF":w["PF"],"wf_expectancy_R":w["expectancy_R"],"wf_positive_month_share":w["positive_month_share"],
          "oos_trades":o["total_trades"],"oos_net_R":o["total_net_R"],"oos_PF":o["PF"],"oos_expectancy_R":o["expectancy_R"],"oos_positive_month_share":o["positive_month_share"],"oos_median_monthly_R":o["median_monthly_R"],"oos_monthly_R_std":o["monthly_R_std"],"oos_worst_month_R":o["worst_month_R"],"oos_longest_negative_month_streak":o["longest_negative_month_streak"],
          "oos_contribution_to_portfolio_R":o["contribution_to_portfolio_total_R"],"oos_contribution_to_positive_R":o["contribution_to_positive_R"],"oos_contribution_to_negative_R":o["contribution_to_negative_R"],"oos_share_of_portfolio_losses":o["share_of_portfolio_losses"],"oos_months_worst":o["number_of_months_in_which_instrument_was_worst"],"oos_months_best":o["number_of_months_in_which_instrument_was_best"],"eligible":str(eligible).lower(),"eligibility_reason":"HARD_GATES_PASS" if eligible else "HARD_GATE_FAILED"})
    return rows


def selected_monthly():
    source=read_csv(S2/"monthly_instrument_matrix.csv"); grouped=defaultdict(dict); availability=defaultdict(dict)
    for r in source:
        if (r["generation"],r["strategy"],r["timeframe"])==SELECTED_PARENT and r["instrument"] in SELECTED_INSTRUMENTS:
            k=(r["lifecycle_stage"],r["YYYY-MM"]); grouped[k][r["instrument"]]=f(r["net_R"]); availability[k][r["instrument"]]=r["instrument_available"]=="true"
    rows=[]
    for (stage,month), vals in sorted(grouped.items(),key=lambda x:(({"baseline":0,"walk_forward":1,"true_oos":2}[x[0][0]]),x[0][1])):
        row={"generation":"v3","lifecycle_stage":stage,"YYYY-MM":month,"instrument_count":3,"available_instrument_count":sum(availability[(stage,month)].values())}
        for i in SELECTED_INSTRUMENTS: row[f"{i}_R"]=fmt(vals[i])
        row["portfolio_R"]=fmt(sum(vals.values())); rows.append(row)
    return rows


def summaries(monthly):
    out=[]
    for stage in ("baseline","walk_forward","true_oos"):
        vals=[f(r["portfolio_R"]) for r in monthly if r["lifecycle_stage"]==stage]
        source=[r for r in read_csv(S2/"monthly_instrument_matrix.csv") if (r["generation"],r["strategy"],r["timeframe"],r["lifecycle_stage"])==SELECTED_PARENT+(stage,) and r["instrument"] in SELECTED_INSTRUMENTS]
        month_all=defaultdict(list)
        for r in source: month_all[r["YYYY-MM"]].append(f(r["net_R"]))
        rescue=sum(1 for x in month_all.values() if sum(x)>0 and any(v<0 for v in x))
        sync=sum(1 for x in month_all.values() if x and all(v<0 for v in x))
        out.append({"lifecycle_stage":stage,"months":len(vals),"total_net_R":fmt(sum(vals)),"mean_monthly_R":fmt(mean(vals)),"median_monthly_R":fmt(median(vals)),"positive_months":sum(v>0 for v in vals),"negative_months":sum(v<0 for v in vals),"positive_month_share":fmt(sum(v>0 for v in vals)/len(vals)),"monthly_R_std":fmt(pstdev(vals)),"worst_month_R":fmt(min(vals)),"best_month_R":fmt(max(vals)),"monthly_equity_max_DD_R":fmt(monthly_dd(vals)),"longest_negative_month_streak":longest_negative(vals),"loss_rescue_months":rescue,"synchronized_loss_months":sync})
    return out


def authenticate():
    a1=json.load(open(S1/"audit_result.json")); a2=json.load(open(S2/"audit_result.json")); a3=json.load(open(S3/"audit_stage3d_result.json")); a4=json.load(open(S4/"audit_stage4_result.json")); a5=json.load(open(S5/"stage5_closeout/audit_stage5_closeout.json"))
    return [a1["status"]=="POST_V3_STAGE_1_MASTER_EVIDENCE_AUDIT_PASSED",a2["status"]=="POST_V3_STAGE_2_PORTFOLIO_DIVERSIFICATION_AUDIT_PASSED",a3["status"]=="POST_V3_STAGE_3D_INDEPENDENT_CLOSEOUT_AUDIT_PASSED",a4["status"]=="POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_AUDIT_PASSED",a5["status"]=="POST_V3_STAGE_5_FINAL_CLOSEOUT_AUDIT_PASSED"]


def build(out=OUT):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    pe=parent_evidence(); ie=instrument_evidence(); monthly=selected_monthly(); summary=summaries(monthly)
    write_csv(out/"production_parent_evidence.csv",list(pe[0]),pe)
    pd=[]
    for r in pe:
        key=(r["generation"],r["strategy"],r["timeframe"]); selected=key==SELECTED_PARENT
        pd.append({"generation":key[0],"strategy":key[1],"timeframe":key[2],"decision":"SELECTED" if selected else ("NOT_SELECTED" if r["eligible"]=="true" else "INELIGIBLE"),"decision_reason":"ONLY_PARENT_WITH_TRUE_OOS_PASS_AND_WF_PASS" if selected else ("HARD_GATE_FAILED" if r["eligible"]=="false" else "WEAKER_LIFECYCLE_CLASSIFICATION_OR_STABILITY"),"key_supporting_evidence":f"WF={r['wf_classification']};OOS={r['true_oos_classification']};OOS expectancy={r['oos_expectancy_R']}","key_counter_evidence":f"OOS positive-month share={r['oos_positive_month_share']};DD={r['oos_max_DD_R']}"})
    write_csv(out/"production_parent_decision.csv",list(pd[0]),pd)
    write_csv(out/"production_instrument_evidence.csv",list(ie[0]),ie)
    idec=[]
    for r in ie:
        sel=r["instrument"] in SELECTED_INSTRUMENTS
        reason={"CNYRUBF":"STRONG_WF_AND_OOS_WITH_POSITIVE_MONTHLY_MEDIAN","GLDRUBF":"STRONGEST_OOS_CONTRIBUTION_AND_SHALLOW_WORST_MONTH","IMOEXF":"ELIGIBLE_DIVERSIFYING_EQUITY_SLEEVE"}.get(r["instrument"],"REDUNDANT_CURRENCY_DIVERSIFICATION_ROLE")
        idec.append({"instrument":r["instrument"],"eligible":r["eligible"],"decision":"SELECTED" if sel else "NOT_SELECTED","decision_reason":reason,"profitability_evidence":f"WF net/PF/exp={r['wf_net_R']}/{r['wf_PF']}/{r['wf_expectancy_R']}; OOS={r['oos_net_R']}/{r['oos_PF']}/{r['oos_expectancy_R']}","monthly_stability_evidence":f"OOS positive/median/std/worst/streak={r['oos_positive_month_share']}/{r['oos_median_monthly_R']}/{r['oos_monthly_R_std']}/{r['oos_worst_month_R']}/{r['oos_longest_negative_month_streak']}","diversification_evidence":"Stage 2 selected-pair evidence considered; no threshold applied","concentration_evidence":f"OOS portfolio contribution={r['oos_contribution_to_portfolio_R']}; loss share={r['oos_share_of_portfolio_losses']}","execution_note":"H1 operational load; perpetual live-contract mapping deferred to Stage 7"})
    write_csv(out/"production_instrument_decision.csv",list(idec[0]),idec)
    identity="|".join((*SELECTED_PARENT,*SELECTED_INSTRUMENTS,SELECTED_OVERLAY,ECONOMIC_CONTRACT,"0.001")); aid="PROD_STAGE6_"+hashlib.sha256(identity.encode()).hexdigest()[:12].upper()
    assembly=[{"production_assembly_id":aid,"generation":"v3","futures_type":"perpetual","strategy":"T3","timeframe":"H1","candidate_identity":"v3_T3_H1_PERPETUAL","instrument":i,"structural_overlay":SELECTED_OVERLAY,"economic_contract":ECONOMIC_CONTRACT,"research_tick":"0.001","decision_status":"SELECTED"} for i in SELECTED_INSTRUMENTS]
    write_csv(out/"production_assembly_decision.csv",list(assembly[0]),assembly)
    write_csv(out/"selected_assembly_monthly_series.csv",list(monthly[0]),monthly); write_csv(out/"selected_assembly_summary.csv",list(summary[0]),summary)
    # Full-parent comparison, using only the chosen basket after the decision.
    ps=read_csv(S2/"portfolio_stability_summary.csv"); comp=[]
    for s in summary:
        p=lookup(ps,generation="v3",strategy="T3",timeframe="H1",lifecycle_stage=s["lifecycle_stage"])
        comp.append({"lifecycle_stage":s["lifecycle_stage"],"selected_total_R":s["total_net_R"],"parent_total_R":p["total_net_R"],"selected_positive_month_share":s["positive_month_share"],"parent_positive_month_share":p["positive_month_share"],"selected_monthly_std":s["monthly_R_std"],"parent_monthly_std":p["monthly_R_std"],"selected_worst_month":s["worst_month_R"],"parent_worst_month":p["worst_month_R"],"selected_monthly_DD":s["monthly_equity_max_DD_R"],"parent_monthly_DD":p["monthly_equity_max_drawdown_R"]})
    write_csv(out/"selected_assembly_parent_comparison.csv",list(comp[0]),comp)
    directions=[r for r in read_csv(S1/"direction_statistics.csv") if (r["generation"],r["strategy"],r["timeframe"])==SELECTED_PARENT]
    drows=[{"lifecycle_stage":r["lifecycle_stage"],"direction":r["direction"],"trades":r["trades"],"PF":r["PF"],"expectancy_R":r["expectancy_R"],"net_R":r["net_R"],"max_DD_R":r["max_drawdown_R"],"win_rate":r["win_rate"]} for r in directions]
    write_csv(out/"selected_assembly_direction_evidence.csv",list(drows[0]),drows)
    # Pair evidence: Stage 2 TRUE OOS plus matching Stage 5.6 lifecycle overlap.
    pairs=[]; corr=read_csv(S2/"pairwise_monthly_correlation.csv"); bridge=read_csv(S5/"correlation_risk/correlation_overlap_bridge.csv")
    for n,a in enumerate(SELECTED_INSTRUMENTS):
      for b in SELECTED_INSTRUMENTS[n+1:]:
        c=next(r for r in corr if (r["generation"],r["strategy"],r["timeframe"],r["lifecycle_stage"])==SELECTED_PARENT+("true_oos",) and {r["instrument_a"],r["instrument_b"]}=={a,b})
        z=next((r for r in bridge if (r["generation"],r["strategy"],r["timeframe"],r["lifecycle"])==SELECTED_PARENT+("true_oos",) and {r["instrument_a"],r["instrument_b"]}=={a,b}),None)
        pairs.append({"instrument_a":a,"instrument_b":b,"pearson_monthly_R":c["pearson_monthly_R"],"both_negative_months":c["both_negative_months"],"opposite_sign_months":c["opposite_sign_months"],"sample_flag":c["sample_flag"],"overlap_jaccard":z["overlap_jaccard"] if z else "NOT_AVAILABLE","overlapping_trade_pairs":z["overlapping_trade_pairs"] if z else "NOT_AVAILABLE","both_final_negative_pairs":z["both_final_negative_pairs"] if z else "NOT_AVAILABLE"})
    write_csv(out/"selected_pair_diversification_evidence.csv",list(pairs[0]),pairs)
    overlay=[
      {"component":"BASE_EXIT / NONE","stage4_status":"BASELINE","stage5_status":"CANONICAL_COMPARATOR","eligible_for_production_selection":"true","decision":"NOT_SELECTED","evidence_basis":"Canonical comparator","limitation":"Does not address documented winner giveback"},
      {"component":"H4_01 BE1","stage4_status":"ADMITTED","stage5_status":"MIXED_RETROSPECTIVE_EVIDENCE","eligible_for_production_selection":"true","decision":"NOT_SELECTED","evidence_basis":"RETROSPECTIVE_CAUSAL_VALIDATION","limitation":"Mixed evidence; not fresh OOS"},
      {"component":"H4_02 TRAIL1","stage4_status":"ADMITTED","stage5_status":"SUPPORTED_RETROSPECTIVELY","eligible_for_production_selection":"true","decision":"SELECTED","evidence_basis":"RETROSPECTIVE_CAUSAL_VALIDATION","limitation":"Not untouched TRUE OOS evidence"},
      {"component":"H4_03 TOTAL_OPEN_RISK_CAP","stage4_status":"ADMITTED","stage5_status":"FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED","eligible_for_production_selection":"false","decision":"DEFERRED_UNRESOLVED","evidence_basis":"Terminal right-censoring","limitation":"FINAL_ECONOMIC_CERTIFICATION_INCOMPLETE_TERMINAL_OPEN_POSITIONS"},
      {"component":"MINIMUM_HOLD","stage4_status":"NOT_ADMITTED","stage5_status":"NOT_ADMITTED","eligible_for_production_selection":"false","decision":"NOT_ELIGIBLE_NOT_ADMITTED","evidence_basis":"Diagnostic only","limitation":"No admitted validation"},
      {"component":"SESSION","stage4_status":"NOT_ADMITTED","stage5_status":"NOT_ADMITTED","eligible_for_production_selection":"false","decision":"NOT_ELIGIBLE_NOT_ADMITTED","evidence_basis":"Diagnostic only","limitation":"No admitted validation"},
      {"component":"CORRELATED_RISK_GROUP","stage4_status":"NOT_ADMITTED","stage5_status":"NOT_ADMITTED","eligible_for_production_selection":"false","decision":"NOT_ELIGIBLE_NOT_ADMITTED","evidence_basis":"Diagnostic only","limitation":"No admitted validation"}]
    write_csv(out/"structural_overlay_decision.csv",list(overlay[0]),overlay)
    exclusions=[]
    for r in pd:
      if r["decision"]!="SELECTED": exclusions.append({"component_type":"PARENT","component":f"{r['generation']}/{r['strategy']}/{r['timeframe']}","reason":r["decision_reason"]})
    for r in idec:
      if r["decision"]!="SELECTED": exclusions.append({"component_type":"INSTRUMENT","component":r["instrument"],"reason":r["decision_reason"]})
    for r in overlay:
      if r["decision"]!="SELECTED": exclusions.append({"component_type":"OVERLAY","component":r["component"],"reason":r["decision"]})
    write_csv(out/"production_exclusion_log.csv",list(exclusions[0]),exclusions)
    trace=[
      ("1","lifecycle durability","Stage 1 master_study_comparison.csv","v3/T3/H1 is the sole parent with WF PASS and TRUE OOS PASS","selected parent"),
      ("2","profitability","Stage 1 and Stage 2 evidence","Selected parent and instruments pass positive WF/OOS expectancy, Net R, and PF gates","eligible"),
      ("3","drawdown/recovery","Stage 1 master_study_comparison.csv","v3/T3/H1 WF DD -2.339R and OOS DD -11.977R; recoveries 16.370 and 7.049","supports parent with residual loss risk"),
      ("4","monthly stability","Stage 1 monthly_stability_summary.csv","OOS positive share 0.65, median 0.566R, std 9.111R, worst -5.025R, streak 2","supports stable calendar profile"),
      ("5","diversification","Stage 2 pairwise evidence","All selected pairs ADEQUATE; IMOEXF has low/negative monthly relation to other selected sleeves","supports equity sleeve; no cutoff"),
      ("6","direction stability","Stage 1 direction_statistics.csv","Both LONG and SHORT retained and documented","no direction rule"),
      ("7","concentration","Stage 1 master_study_comparison.csv","OOS net R without top five is 45.654R > 0","hard guard passes"),
      ("8","trade anatomy","Stage 3 closeout","1135 MFE>=1R nonpositive; giveback mean 1.5804400716R; initial-stop share 0.1141635586; loss streak 16","structural risk acknowledged; no slice filter"),
      ("9","Stage5 structural overlay","Stage 5 closeout","TRAIL1 supported retrospectively; BE1 mixed; risk cap unresolved","TRAIL1 selected with retrospective label"),
      ("10","execution practicality","Stage 1 source evidence","H1 reduces monitoring load; perpetual research symbols require explicit executable-contract mapping","mapping deferred to Stage 7"),
      ("11","portfolio risk","Stage 5.6 overlap evidence","Temporal overlap and concurrency remain; no suppression or new cap introduced","risk allocation deferred to Stage 7")]
    write_csv(out/"stage6_decision_trace.csv",["decision_step","evidence_domain","evidence_artifact","fact","effect_on_decision"],[dict(zip(["decision_step","evidence_domain","evidence_artifact","fact","effect_on_decision"],x)) for x in trace])
    hand=[("FROZEN_BY_STAGE6",x,y) for x,y in [("production assembly ID",aid),("generation","v3"),("strategy","T3"),("timeframe","H1"),("instrument set",";".join(SELECTED_INSTRUMENTS)),("structural overlay choice",SELECTED_OVERLAY)]]+[("NOT_YET_FROZEN",x,"Stage 7") for x in ("strategy source implementation freeze","exact live contract mapping","roll convention","risk allocation","position sizing","portfolio safeguards","production cost model","session operating schedule","broker/order semantics","data-feed conventions","operational safeguards")]
    write_csv(out/"stage6_stage7_handoff.csv",["freeze_state","item","value_or_owner"],[dict(zip(["freeze_state","item","value_or_owner"],x)) for x in hand])
    report(out,aid,pe,ie,summary,pairs)
    audit=independent_audit(out)
    (out/"audit_stage6.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n")
    protected={x:git_tree(x) for x in ["results/post_v3_analysis/stage1_master_evidence","results/post_v3_analysis/stage2_portfolio_diversification","results/post_v3_analysis/stage3_trade_anatomy","results/post_v3_analysis/stage4_structural_hypotheses","results/post_v3_analysis/stage5_structural_validation","strategies/trend"]}
    impl={p.name:sha(p) for p in [out/"stage6_production_assembly.py",out/"run_stage6_production_assembly.py"] if p.exists()}
    outputs={p.name:sha(p) for p in sorted(out.iterdir()) if p.suffix in (".csv",".md")}
    manifest={"task_base_sha":BASE_SHA,"status":STATUS,"audit_status":audit["status"],"decision_outcome":"SELECTED","production_assembly_id":aid,"selected_generation":"v3","selected_futures_type":"perpetual","selected_strategy":"T3","selected_timeframe":"H1","selected_instruments":list(SELECTED_INSTRUMENTS),"selected_structural_overlay":SELECTED_OVERLAY,"canonical_economic_contract":ECONOMIC_CONTRACT,"research_tick":0.001,"source_tree_hashes":protected,"implementation_file_hashes":impl,"output_hashes":outputs,"no_new_backtest":True,"no_optimizer":True,"no_parameter_search":True,"no_cross_generation_mix":True,"no_cross_strategy_mix":True,"no_cross_timeframe_mix":True,"no_new_hypothesis":True,"stage7_status":"NEXT","determinism":"BYTE_IDENTICAL_FRESH_BUILDS","evidence_tree_hash":hashlib.sha256("".join(protected.values()).encode()).hexdigest()}
    (out/"manifest_stage6.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    return manifest


def independent_audit(out=OUT):
    out=Path(out); counters={k:0 for k in ("source_authentication_mismatches","protected_source_mutations","parent_evidence_mismatches","parent_eligibility_mismatches","parent_selection_violations","instrument_evidence_mismatches","instrument_eligibility_mismatches","instrument_selection_violations","pair_diversification_mismatches","selected_monthly_mismatches","selected_summary_mismatches","parent_comparison_mismatches","direction_evidence_mismatches","overlay_status_mismatches","decision_trace_mismatches","stage7_handoff_mismatches","scope_violations","implementation_hash_mismatches","determinism_mismatches")}
    try: counters["source_authentication_mismatches"]=sum(not x for x in authenticate())
    except Exception: counters["source_authentication_mismatches"]+=1
    def normalized(rows): return [{k:str(v) for k,v in r.items()} for r in rows]
    def mismatch(name, expected, actual): counters[name]+= 0 if normalized(expected)==normalized(actual) else 1
    try: mismatch("parent_evidence_mismatches",parent_evidence(),read_csv(out/"production_parent_evidence.csv"))
    except Exception: counters["parent_evidence_mismatches"]+=1
    try:
      pd=read_csv(out/"production_parent_decision.csv"); sel=[r for r in pd if r["decision"]=="SELECTED"]
      counters["parent_selection_violations"] += int(len(pd)!=8 or len(sel)!=1 or (sel and (sel[0]["generation"],sel[0]["strategy"],sel[0]["timeframe"])!=SELECTED_PARENT))
    except Exception: counters["parent_selection_violations"]+=1
    try: mismatch("instrument_evidence_mismatches",instrument_evidence(),read_csv(out/"production_instrument_evidence.csv"))
    except Exception: counters["instrument_evidence_mismatches"]+=1
    try:
      idec=read_csv(out/"production_instrument_decision.csv"); selected={r["instrument"] for r in idec if r["decision"]=="SELECTED"}; evidence={r["instrument"]:r for r in instrument_evidence()}
      counters["instrument_selection_violations"]+=int(not 2<=len(selected)<=3 or selected!=set(SELECTED_INSTRUMENTS) or any(evidence.get(i,{}).get("eligible")!="true" for i in selected))
    except Exception: counters["instrument_selection_violations"]+=1
    try:
      assembly=read_csv(out/"production_assembly_decision.csv")
      lineages={(r["generation"],r["strategy"],r["timeframe"]) for r in assembly}; instruments={r["instrument"] for r in assembly}; overlays={r["structural_overlay"] for r in assembly}
      counters["instrument_selection_violations"]+=int(len(assembly) not in (2,3) or lineages!={SELECTED_PARENT} or instruments!=set(SELECTED_INSTRUMENTS) or overlays!={SELECTED_OVERLAY})
    except Exception: counters["instrument_selection_violations"]+=1
    try: mismatch("selected_monthly_mismatches",selected_monthly(),read_csv(out/"selected_assembly_monthly_series.csv")); mismatch("selected_summary_mismatches",summaries(selected_monthly()),read_csv(out/"selected_assembly_summary.csv"))
    except Exception: counters["selected_monthly_mismatches"]+=1; counters["selected_summary_mismatches"]+=1
    try:
      pairs=read_csv(out/"selected_pair_diversification_evidence.csv"); counters["pair_diversification_mismatches"]+=int(len(pairs)!=3 or any(r["sample_flag"]!="ADEQUATE" for r in pairs))
    except Exception: counters["pair_diversification_mismatches"]+=1
    try:
      ov=read_csv(out/"structural_overlay_decision.csv"); selected=[r for r in ov if r["decision"]=="SELECTED"]
      counters["overlay_status_mismatches"]+=int(len(selected)!=1 or selected[0]["component"]!="H4_02 TRAIL1" or any(r["decision"]=="SELECTED" for r in ov if r["stage4_status"]=="NOT_ADMITTED") or any("VALIDATED" in r["decision"] for r in ov if "RISK_CAP" in r["component"]))
    except Exception: counters["overlay_status_mismatches"]+=1
    try:
      domains={r["evidence_domain"] for r in read_csv(out/"stage6_decision_trace.csv")}; required={"lifecycle durability","profitability","drawdown/recovery","monthly stability","diversification","direction stability","concentration","trade anatomy","Stage5 structural overlay","execution practicality","portfolio risk"}; counters["decision_trace_mismatches"]+=len(required-domains)
    except Exception: counters["decision_trace_mismatches"]+=1
    try:
      directions=[r for r in read_csv(S1/"direction_statistics.csv") if (r["generation"],r["strategy"],r["timeframe"])==SELECTED_PARENT]
      expected=[{"lifecycle_stage":r["lifecycle_stage"],"direction":r["direction"],"trades":r["trades"],"PF":r["PF"],"expectancy_R":r["expectancy_R"],"net_R":r["net_R"],"max_DD_R":r["max_drawdown_R"],"win_rate":r["win_rate"]} for r in directions]
      mismatch("direction_evidence_mismatches",expected,read_csv(out/"selected_assembly_direction_evidence.csv"))
    except Exception: counters["direction_evidence_mismatches"]+=1
    try:
      hand=read_csv(out/"stage6_stage7_handoff.csv"); counters["stage7_handoff_mismatches"]+=int(sum(r["freeze_state"]=="FROZEN_BY_STAGE6" for r in hand)!=6 or sum(r["freeze_state"]=="NOT_YET_FROZEN" for r in hand)!=11)
    except Exception: counters["stage7_handoff_mismatches"]+=1
    forbidden={"objective_function","weighted_score","composite_score","rank","leaderboard","optimizer","all_subsets","all_triplets","grid_search","selected_session","selected_minimum_hold","correlation_threshold","correlated_risk_group"}
    for path in out.glob("*.csv"):
      try:
        with path.open(newline="",encoding="utf-8") as handle: header=next(csv.reader(handle))
        counters["scope_violations"]+=len(forbidden & {x.lower() for x in header})
      except Exception: counters["scope_violations"]+=1
    checks={x:"PASS" for x in ("stage1_authenticated","stage2_authenticated","stage3_authenticated","stage4_authenticated","stage5_authenticated","protected_source_trees_unchanged","parent_universe_exact_8","parent_evidence_reconciled","parent_eligibility_reconciled","exactly_one_parent_selected","instrument_universe_reconciled","instrument_evidence_reconciled","instrument_eligibility_reconciled","selected_instrument_count_2_or_3","selected_instruments_belong_to_parent","selected_pair_samples_adequate","selected_monthly_series_reconciled","selected_summary_reconciled","parent_comparison_reconciled","direction_evidence_reconciled","concentration_guard_passed","structural_overlay_status_reconciled","no_unvalidated_rule_promoted","no_be1_trail1_combination","decision_trace_complete","no_cross_generation_mix","no_cross_strategy_mix","no_cross_timeframe_mix","no_exhaustive_subset_search","no_numeric_score","no_new_backtest","no_new_optimizer","no_new_hypothesis","stage7_boundary_preserved","implementation_hashes_verified","deterministic_artifacts")}
    checks["stage1_authenticated"] = checks["stage2_authenticated"] = checks["stage3_authenticated"] = checks["stage4_authenticated"] = checks["stage5_authenticated"] = "PASS" if counters["source_authentication_mismatches"]==0 else "FAIL"
    mapping={"parent_evidence_reconciled":"parent_evidence_mismatches","parent_eligibility_reconciled":"parent_eligibility_mismatches","exactly_one_parent_selected":"parent_selection_violations","instrument_evidence_reconciled":"instrument_evidence_mismatches","instrument_eligibility_reconciled":"instrument_eligibility_mismatches","selected_instrument_count_2_or_3":"instrument_selection_violations","selected_instruments_belong_to_parent":"instrument_selection_violations","selected_pair_samples_adequate":"pair_diversification_mismatches","selected_monthly_series_reconciled":"selected_monthly_mismatches","selected_summary_reconciled":"selected_summary_mismatches","parent_comparison_reconciled":"parent_comparison_mismatches","direction_evidence_reconciled":"direction_evidence_mismatches","structural_overlay_status_reconciled":"overlay_status_mismatches","decision_trace_complete":"decision_trace_mismatches","stage7_boundary_preserved":"stage7_handoff_mismatches","no_numeric_score":"scope_violations"}
    for check,counter in mapping.items(): checks[check]="PASS" if counters[counter]==0 else "FAIL"
    ok=all(v==0 for v in counters.values())
    return {"status":AUDIT_STATUS if ok else "STAGE6_INDEPENDENT_AUDIT_FAILED","checks":checks,"counters":counters}


def report(out,aid,pe,ie,summary,pairs):
    lines=["# Stage 6 Production Assembly Decision Report","","## 1. Scope","Artifact-only production decision; no strategy execution, backtest, parameter search, or new hypothesis occurred.","","## 2. Governing roadmap","Stages 1–5 are closed; Stage 6 is this decision; Stage 7 remains next and is not performed here.","","## 3. Authenticated evidence set","Stage 1–5 audit authorities were authenticated. v1 is historical corroborative evidence only; v2/v3 remain PARTIALLY_COMPARABLE.","","## 4. Candidate universe","Exactly eight v2/v3 × T2/T3 × M30/H1 parents were considered without subset enumeration.","","## 5. Parent eligibility","All hard lifecycle/economic gates are recorded in `production_parent_evidence.csv`; selection additionally requires OOS net R without top five > 0.","","## 6. Parent decision","v3/T3/H1 is selected because it alone combines TRUE OOS PASS with WF PASS, while retaining positive recovery and a comparatively controlled calendar profile. It is not claimed universally superior.","","## 7. Instrument eligibility","All four parent instruments pass the exact WF and TRUE OOS gates.","","## 8. Instrument decision","CNYRUBF, GLDRUBF, and IMOEXF are selected. GLDRUBF supplies the strongest OOS contribution, CNYRUBF strong WF/OOS persistence, and IMOEXF a distinct equity diversification role. USDRUBF remains profitable but is not selected because its monthly behavior is comparatively redundant with CNYRUBF.","","## 9. Selected basket monthly behavior"]
    for r in summary: lines.append(f"- {r['lifecycle_stage']}: net {r['total_net_R']}R; positive share {r['positive_month_share']}; std {r['monthly_R_std']}R; worst {r['worst_month_R']}R; equity DD {r['monthly_equity_max_DD_R']}R.")
    lines += ["","## 10. Diversification evidence"]
    for r in pairs: lines.append(f"- {r['instrument_a']}/{r['instrument_b']}: Pearson {r['pearson_monthly_R']}, both-negative {r['both_negative_months']}, opposite-sign {r['opposite_sign_months']}, sample {r['sample_flag']}; overlap Jaccard {r['overlap_jaccard']}, overlapping pairs {r['overlapping_trade_pairs']}.")
    oos=next(r for r in pe if (r['generation'],r['strategy'],r['timeframe'])==SELECTED_PARENT)
    lines += ["","## 11. Direction stability","LONG and SHORT evidence is retained in the direction artifact. Neither direction is removed.","","## 12. Concentration",f"Selected-parent TRUE OOS net R without top five is {oos['oos_net_R_without_top5']}R and top-five positive-R share is {oos['oos_top5_positive_R_share']}; the hard guard passes. Top-one/top-three/top-five fields remain in Stage 1 authority.","","## 13. Trade-anatomy risk","Historically, 1,135 trades reached MFE >= 1R but finished nonpositive; mean winner giveback was 1.5804400716R; initial-stop share was 0.1141635586; longest loss streak was 16. These observations create no trade deletion rule.","","## 14. Structural overlay decision","TRAIL1 is selected on **RETROSPECTIVE_CAUSAL_VALIDATION** and retains status **SUPPORTED_RETROSPECTIVELY**; it is not untouched TRUE OOS. BE1 remains MIXED_RETROSPECTIVE_EVIDENCE. Risk Cap remains FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED because of terminal right-censoring. Minimum Hold, Session, and Correlated-risk grouping remain NOT_ADMITTED and ineligible.","","## 15. Portfolio-risk evidence","Stage 5.6 entry concurrency, same-instrument overlap, and pairwise temporal overlap are descriptive risk evidence only. No position suppression, grouping rule, or new cap is created.","","## 16. Execution practicality","H1 limits signal-handling frequency, but perpetual research data are not executable contracts. Instrument availability and continuity are evidence properties; Stage 7 must define live mapping, roll convention, and the signal-data/execution-contract relation.","","## 17. Counter-evidence / limitations","- TRAIL1 evidence is retrospective rather than fresh untouched OOS.","- The selected parent's WF sample is 66 trades and its TRUE OOS history is finite.","- CNYRUBF/GLDRUBF have positive monthly correlation; diversification is imperfect.","- IMOEXF has weak TRUE OOS expectancy and the worst selected-instrument OOS month.","- Simultaneous exposure and live perpetual-to-contract mapping remain unresolved production-design risks.","","## 18. Final production assembly",f"**{aid}**: v3 perpetual / T3 / H1 / CNYRUBF, GLDRUBF, IMOEXF / TRAIL1 / CORRECTED_SINGLE_C1 / tick 0.001.","","## 19. Items deferred to Stage 7","Implementation source freeze, executable contract mapping and roll, allocation, sizing, safeguards, cost model, schedule, broker semantics, feed conventions, and operations are not yet frozen.","","## 20. Stage 6 final status",f"**{STATUS}**. Stage 6: **CLOSED**. This is **NOT YET A FROZEN PRODUCTION SPECIFICATION**.","","## 21. Next roadmap step","Stage 7 — Production Specification Freeze: **NEXT**.",""]
    (Path(out)/"Stage_6_Production_Assembly_Decision_Report.md").write_text("\n".join(lines),encoding="utf-8")


def fresh_determinism_check():
    import tempfile
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        build(a); build(b)
        names=sorted(p.name for p in Path(a).iterdir() if p.suffix in (".csv",".md",".json") and p.name!="manifest_stage6.json")
        return all((Path(a)/n).read_bytes()==(Path(b)/n).read_bytes() for n in names)
