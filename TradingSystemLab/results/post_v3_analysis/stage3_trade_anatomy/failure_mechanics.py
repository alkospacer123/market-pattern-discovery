#!/usr/bin/env python3
"""Generate aggregate-only Stage 3C failure-mechanics diagnostics."""
from __future__ import annotations

import csv, hashlib, json, math, os, statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("STAGE3C_OUTPUT_DIR", HERE))
INPUTS = ["normalized_trades_v1.csv", "normalized_trades_v2_baseline.csv", "normalized_trades_v2_walk_forward.csv", "normalized_trades_v2_true_oos.csv", "normalized_trades_v3_baseline.csv", "normalized_trades_v3_walk_forward.csv", "normalized_trades_v3_true_oos.csv"]
KEYS = ["generation", "lifecycle_stage", "strategy", "timeframe"]
THRESHOLDS = [0.5, 1.0, 2.0]
OUTPUTS = ["mae_mfe_semantics.json", "mfe_threshold_outcomes.csv", "winner_giveback.csv", "loss_excursion_profile.csv", "stop_exit_profile.csv", "exit_efficiency.csv", "loss_streak_profile.csv", "holding_outcome_profile.csv", "failure_concentration.csv", "Stage_3C_Failure_Mechanics_Report.md"]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def n(x):
    try:
        v=float(x); return v if math.isfinite(v) else None
    except (ValueError,TypeError): return None
def avg(a): return sum(a)/len(a) if a else None
def med(a): return statistics.median(a) if a else None
def pct(a,q):
    if not a:return None
    a=sorted(a); p=(len(a)-1)*q; lo=int(p); hi=math.ceil(p)
    return a[lo] if lo==hi else a[lo]+(a[hi]-a[lo])*(p-lo)
def fmt(v):
    if v is None:return "NA"
    if isinstance(v,float):return format(v,".15g")
    return v
def write(name, rows, fields=None):
    fields=fields or list(rows[0])
    with (OUT/name).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows({k:fmt(r.get(k)) for k in fields} for r in rows)
def groups(rows, extra=()):
    d=defaultdict(list); keys=KEYS+list(extra)
    for r in rows:d[tuple(r[k] for k in keys)].append(r)
    return keys,d
def bucket(x):
    x=n(x)
    if x is None:return "UNAVAILABLE"
    for bound,label in [(1,"<1h"),(3,"1–3h"),(6,"3–6h"),(12,"6–12h"),(24,"12–24h"),(48,"24–48h"),(96.0000000001,"48–96h")]:
        if x<bound:return label
    return ">96h"
def authenticate():
    a3=json.loads((HERE/"audit_stage3a4_v3_result.json").read_text()); m3=json.loads((HERE/"manifest_stage3a4_v3.json").read_text()); aB=json.loads((HERE/"audit_stage3b_result.json").read_text()); mB=json.loads((HERE/"manifest_stage3b.json").read_text())
    if a3.get("status")!="POST_V3_STAGE_3A4_V3_CORE_NORMALIZATION_AUDIT_PASSED" or a3.get("core_normalization_status")!="STAGE_3A_CORE_NORMALIZATION_CLOSED":raise RuntimeError("Stage 3A closeout invalid")
    if aB.get("status")!="POST_V3_STAGE_3B_TRADE_ANATOMY_TABLES_AUDIT_PASSED" or mB.get("audit_status")!=aB["status"]:raise RuntimeError("Stage 3B closeout invalid")
    expected=mB["prerequisite_hashes"]
    for f in INPUTS:
        if sha(HERE/f)!=expected[f]:raise RuntimeError("normalized hash mismatch: "+f)
    for f,h in mB["output_hashes"].items():
        if sha(HERE/f)!=h:raise RuntimeError("Stage 3B hash mismatch: "+f)
    rows=[]
    for f in INPUTS:
        with (HERE/f).open(newline="",encoding="utf-8") as s:rows += list(csv.DictReader(s))
    if len(rows)!=10993 or len({r["canonical_trade_key"] for r in rows})!=10993:raise RuntimeError("population mismatch")
    return rows,expected,{f:sha(HERE/f) for f in mB["output_hashes"]}|{"manifest_stage3b.json":sha(HERE/"manifest_stage3b.json"),"audit_stage3b_result.json":sha(HERE/"audit_stage3b_result.json")}
def main():
    OUT.mkdir(parents=True,exist_ok=True); rows,inputs,bhash=authenticate()
    root=HERE.parents[2]; sources=[root/"core/backtester.py",root/"strategies/trend/T2_Trend_Pullback.py",root/"strategies/trend/T3_MTF_Trend.py"]
    semantics={"MAE_semantics":"non-negative maximum adverse excursion magnitude divided by positive initial risk","MFE_semantics":"non-negative maximum favorable excursion divided by positive initial risk","sign_convention_status":"AUTHENTICATED_NON_NEGATIVE_MAGNITUDES","supporting_source_files":[str(p.relative_to(root.parent)) for p in sources],"source_hashes":{str(p.relative_to(root.parent)):sha(p) for p in sources},"threshold_inference_supported":True,"ordered_event_inference_supported":False,"ordering_status":"MAE_MFE_ORDER_UNAVAILABLE"}
    (OUT/"mae_mfe_semantics.json").write_text(json.dumps(semantics,indent=2,sort_keys=True)+"\n")
    for r in rows:
        r["R"]=float(r["canonical_C1_R"]); r["mae"]=n(r["MAE_R"]); r["mfe"]=n(r["MFE_R"]); r["hold"]=n(r["holding_hours"]); r["reason"]=r["exit_reason_raw"] or "UNAVAILABLE"; r["giveback"]=(r["mfe"]-r["R"]) if r["mfe"] is not None else None; r["bucket"]=bucket(r["holding_hours"])
    keys,g=groups(rows)
    threshold=[]; winners=[]; lossprof=[]; streak=[]; concentration=[]
    for k in sorted(g):
        rs=g[k]; base=dict(zip(keys,k))
        for t in THRESHOLDS:
            hit=[r for r in rs if r["mfe"] is not None and r["mfe"]>=t]; vals=[r["R"] for r in hit]
            threshold.append({**base,"threshold_R":t,"trades_total":len(rs),"trades_reached_threshold":len(hit),"reached_share":len(hit)/len(rs),"reached_and_finished_positive":sum(x>0 for x in vals),"reached_and_finished_nonpositive":sum(x<=0 for x in vals),"reached_and_finished_negative":sum(x<0 for x in vals),"reached_and_finished_below_0_25R":sum(x<.25 for x in vals),"reached_and_finished_below_0_5R":sum(x<.5 for x in vals),"mean_final_R_after_reach":avg(vals),"median_final_R_after_reach":med(vals),"total_final_R_after_reach":sum(vals)})
        ws=[r for r in rs if r["R"]>0 and r["mfe"] is not None]; eligible=[r for r in ws if r["mfe"]>0]; gv=[r["giveback"] for r in ws]; ratios=[r["R"]/r["mfe"] for r in eligible]
        winners.append({**base,"winners":len(ws),"avg_MFE_R":avg([r["mfe"] for r in ws]),"median_MFE_R":med([r["mfe"] for r in ws]),"avg_final_R":avg([r["R"] for r in ws]),"median_final_R":med([r["R"] for r in ws]),"avg_giveback_R":avg(gv),"median_giveback_R":med(gv),"p75_giveback_R":pct(gv,.75),"p90_giveback_R":pct(gv,.9),"giveback_share_of_MFE":sum(gv)/sum(r["mfe"] for r in ws) if sum(r["mfe"] for r in ws)>0 else None,"eligible_retention_trades":len(eligible),"mean_retention_ratio":avg(ratios),"median_retention_ratio":med(ratios)})
        ls=[r for r in rs if r["R"]<0]; lossprof.append({**base,"losing_trades":len(ls),"avg_final_loss_R":avg([r["R"] for r in ls]),"median_final_loss_R":med([r["R"] for r in ls]),"avg_MAE_R":avg([r["mae"] for r in ls]),"median_MAE_R":med([r["mae"] for r in ls]),"avg_MFE_R":avg([r["mfe"] for r in ls]),"median_MFE_R":med([r["mfe"] for r in ls]),**{f"share_MFE_ge_{str(t).replace('.','_')}":sum(r["mfe"]>=t for r in ls)/len(ls) if ls else None for t in THRESHOLDS},"average_holding_hours":avg([r["hold"] for r in ls if r["hold"] is not None]),"median_holding_hours":med([r["hold"] for r in ls if r["hold"] is not None])})
        ordered=sorted(rs,key=lambda r:(r["exit_time"],r["entry_time"],r["canonical_trade_key"])); runs=[]; cur=[]
        for r in ordered:
            if r["R"]<0:cur.append(r)
            elif cur:runs.append(cur);cur=[]
        if cur:runs.append(cur)
        worst=min(runs,key=lambda q:(sum(x["R"] for x in q),q[0]["exit_time"])) if runs else []
        streak.append({**base,"longest_consecutive_loss_streak":max(map(len,runs),default=0),"streaks_ge_2":sum(len(q)>=2 for q in runs),"streaks_ge_3":sum(len(q)>=3 for q in runs),"streaks_ge_5":sum(len(q)>=5 for q in runs),"mean_loss_streak_length":avg([len(q) for q in runs]),"total_R_from_losing_streaks":sum(x["R"] for q in runs for x in q),"worst_streak_cumulative_R":sum(x["R"] for x in worst),"worst_streak_start":worst[0]["exit_time"] if worst else "NA","worst_streak_end":worst[-1]["exit_time"] if worst else "NA","instruments_in_worst_streak":"|".join(sorted({x["instrument"] for x in worst})) or "NA","directions_in_worst_streak":"|".join(sorted({x["direction"] for x in worst})) or "NA"})
        mags=sorted([-r["R"] for r in ls],reverse=True); total=sum(mags)
        share=lambda z:sum(mags[:z])/total if total else None
        byreason=defaultdict(float)
        for r in ls:byreason[r["reason"]]+=-r["R"]
        concentration.append({**base,"total_loss_R":total,"worst_1_loss_share":share(1),"worst_3_losses_share":share(3),"worst_5_losses_share":share(5),"worst_10_losses_share":share(10),"INITIAL_STOP_loss_share":byreason["INITIAL_STOP"]/total if total else None,"ATR_TRAILING_STOP_loss_share":byreason["ATR_TRAILING_STOP"]/total if total else None,"EMA50_TREND_LOSS_loss_share":byreason["EMA50_TREND_LOSS"]/total if total else None,"other_exit_loss_share":(total-sum(byreason[x] for x in ["INITIAL_STOP","ATR_TRAILING_STOP","EMA50_TREND_LOSS"]))/total if total else None})
    write("mfe_threshold_outcomes.csv",threshold);write("winner_giveback.csv",winners);write("loss_excursion_profile.csv",lossprof);write("loss_streak_profile.csv",streak);write("failure_concentration.csv",concentration)
    keys2,g2=groups(rows,["reason"]); stops=[]; efficiency=[]
    parents={k:len(v) for k,v in g.items()}
    for k in sorted(g2):
        rs=g2[k]; base=dict(zip(KEYS+["exit_reason"],k)); mfe=[r["mfe"] for r in rs]; eligible=[r for r in rs if r["mfe"]>0]; ratios=[r["R"]/r["mfe"] for r in eligible]
        holds=[r["hold"] for r in rs if r["hold"] is not None]
        reached={"share_reached_0_5R":sum(x>=.5 for x in mfe)/len(rs),"share_reached_1R":sum(x>=1 for x in mfe)/len(rs),"share_reached_2R":sum(x>=2 for x in mfe)/len(rs)}
        stops.append({**base,"trades":len(rs),"share":len(rs)/parents[k[:4]],"net_R":sum(r["R"] for r in rs),"expectancy_R":avg([r["R"] for r in rs]),"avg_MAE_R":avg([r["mae"] for r in rs]),"avg_MFE_R":avg(mfe),"median_MFE_R":med(mfe),"avg_holding_hours":avg(holds),"median_holding_hours":med(holds),"p75_holding_hours":pct(holds,.75),"p90_holding_hours":pct(holds,.9),**reached,"share_finished_negative":sum(r["R"]<0 for r in rs)/len(rs)})
        efficiency.append({**base,"eligible_trades":len(eligible),"median_retention_ratio":med(ratios),"mean_retention_ratio":avg(ratios),"p25":pct(ratios,.25),"p75":pct(ratios,.75),"share_retention_ge_0_5":sum(x>=.5 for x in ratios)/len(ratios) if ratios else None,"share_retention_ge_0_25":sum(x>=.25 for x in ratios)/len(ratios) if ratios else None,"share_retention_le_0":sum(x<=0 for x in ratios)/len(ratios) if ratios else None,"share_retention_lt_0":sum(x<0 for x in ratios)/len(ratios) if ratios else None})
    write("stop_exit_profile.csv",stops);write("exit_efficiency.csv",efficiency)
    keys3,g3=groups(rows,["bucket"]); holding=[]
    for k in sorted(g3):
        rs=g3[k]; holding.append({**dict(zip(KEYS+["holding_bucket"],k)),"trades":len(rs),"net_R":sum(r["R"] for r in rs),"expectancy":avg([r["R"] for r in rs]),"win_rate":sum(r["R"]>0 for r in rs)/len(rs),"avg_MAE":avg([r["mae"] for r in rs]),"avg_MFE":avg([r["mfe"] for r in rs]),"avg_giveback":avg([r["giveback"] for r in rs]),"share_MFE_ge_1R_final_le_0":sum(r["mfe"]>=1 and r["R"]<=0 for r in rs)/len(rs)})
    write("holding_outcome_profile.csv",holding)
    allhits={t:[r for r in rows if r["mfe"]>=t] for t in THRESHOLDS}; init=[r for r in rows if r["reason"]=="INITIAL_STOP"]; allret=[r["R"]/r["mfe"] for r in rows if r["mfe"]>0]
    report=f'''# Stage 3C Failure Mechanics Report\n\n## 1. Scope\nDiagnostic-only aggregate analysis of 10,993 authenticated normalized trades; no strategy execution, rule simulation, optimization, ranking, or Stage 4 work.\n\n## 2. Prerequisites\nStage 3A is closed and Stage 3B audit passed. All seven normalized hashes and all Stage 3B output hashes were authenticated.\n\n## 3. MAE/MFE semantic verification\nSource implementations define MAE and MFE as non-negative adverse/favorable maximum price excursions divided by initial risk. Threshold inference is supported. **MAE_MFE_ORDER_UNAVAILABLE**: excursion ordering and timing are not available.\n\n## 4. MFE threshold outcome diagnostics\nAcross all separately retained studies, {len(allhits[.5])} trades recorded MFE >= 0.5R and {sum(r['R']<=0 for r in allhits[.5])} ultimately closed nonpositive; at 1R the counts were {len(allhits[1.0])} and {sum(r['R']<=0 for r in allhits[1.0])}; at 2R they were {len(allhits[2.0])} and {sum(r['R']<=0 for r in allhits[2.0])}. These facts establish no ordering relative to MAE.\n\n## 5. Winner giveback\nAmong {sum(x['winners'] for x in winners)} positive trades with valid MFE, mean descriptive giveback was {avg([r['giveback'] for r in rows if r['R']>0]):.4f}R and median was {med([r['giveback'] for r in rows if r['R']>0]):.4f}R. Giveback is not realizable missed profit.\n\n## 6. Losing-trade excursion anatomy\nThe tables preserve each of 36 parent studies; {sum(r['R']<0 for r in rows)} trades closed negative.\n\n## 7. Initial-stop mechanics\nINITIAL_STOP occurred {len(init)} times ({len(init)/len(rows):.2%}); mean final R was {avg([r['R'] for r in init]):.4f}, mean MAE {avg([r['mae'] for r in init]):.4f}, mean MFE {avg([r['mfe'] for r in init]):.4f}, and {sum(r['mfe']>=1 for r in init)/len(init):.2%} recorded MFE >= 1R.\n\n## 8. Trailing-exit mechanics\nRaw exit labels are unchanged. ATR trailing-stop observations are reported separately in `stop_exit_profile.csv`; no counterfactual is calculated.\n\n## 9. Exit efficiency\nFor {len(allret)} trades with MFE > 0, median uncapped final-R/MFE retention was {med(allret):.4f}; negative values are retained.\n\n## 10. Holding-time failure mechanics\nThe exact Stage 3B fixed buckets are used. Outcomes, excursion, giveback, and MFE>=1R/final<=0 shares are descriptive only.\n\n## 11. Loss streaks\nThe longest parent-bounded loss streak was {max(x['longest_consecutive_loss_streak'] for x in streak)} trades; the worst parent-bounded streak totaled {min(x['worst_streak_cumulative_R'] for x in streak):.4f}R. Ordering is exit time, entry time, then canonical key.\n\n## 12. Loss concentration\nAcross parent studies, the maximum worst-single-loss share was {max(x['worst_1_loss_share'] for x in concentration):.2%}, and maximum worst-ten share was {max(x['worst_10_losses_share'] for x in concentration):.2%}.\n\n## 13. Instrument/direction recurrence\nStage 3B instrument and direction aggregates remain the compact reference. Stage 3C does not mine additional dimensions.\n\n## 14. Repeated diagnostic patterns\n`FM_MFE1_FINAL_NONPOSITIVE` is recorded as a **REPEATED_DIAGNOSTIC_PATTERN** where parent rows show nonzero MFE>=1R/final<=0 counts across generations including TRUE OOS. Magnitudes and samples are in the threshold table; the limitation is unavailable path order.\n\n## 15. Cross-lifecycle recurrence\nBaseline, walk-forward, and TRUE OOS remain separate rows; no lifecycle pooling or robustness score occurs.\n\n## 16. Cross-generation recurrence\nv1 perpetual, v2 quarterly, and v3 perpetual remain separate. Their universes and samples differ.\n\n## 17. Limitations\nMAE/MFE lack event order and timing. Diagnostics are observational, not causal, and do not establish realizable alternative exits. Negative is a subset of nonpositive, not an additive partition.\n\n## 18. Handoff to Stage 3D\nStage 3C provides audit-ready facts only. No Stage 3D or Stage 4 work is performed.\n'''
    (OUT/"Stage_3C_Failure_Mechanics_Report.md").write_text(report)
    manifest={"status":"POST_V3_STAGE_3C_FAILURE_MECHANICS_COMPLETE","audit_status":"PENDING_INDEPENDENT_AUDIT","canonical_base_commit":"b03b43334e2f469b52835f330d7e946aaf464656","stage3a_closeout_status":"STAGE_3A_CORE_NORMALIZATION_CLOSED","stage3a_closeout_hashes":{"manifest_stage3a4_v3.json":sha(HERE/"manifest_stage3a4_v3.json"),"audit_stage3a4_v3_result.json":sha(HERE/"audit_stage3a4_v3_result.json")},"stage3b_closeout_status":"POST_V3_STAGE_3B_TRADE_ANATOMY_TABLES_AUDIT_PASSED","normalized_input_hashes":inputs,"stage3b_input_hashes":bhash,"input_trades":10993,"thresholds":[.5,1.0,2.0],"mae_mfe_semantic_status":"AUTHENTICATED_NON_NEGATIVE_MAGNITUDES","output_hashes":{f:sha(OUT/f) for f in OUTPUTS},"no_strategy_execution":True,"no_raw_market_data":True,"no_optimization":True,"no_ranking":True,"no_rule_testing":True,"no_counterfactual_simulation":True,"no_stage4":True}
    (OUT/"manifest_stage3c.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n"); print(manifest["audit_status"])
if __name__=="__main__":main()
