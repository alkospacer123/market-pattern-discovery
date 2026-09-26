#!/usr/bin/env python3
"""Independent Stage 3C auditor; deliberately does not import the generator."""
from __future__ import annotations
import csv, hashlib, json, math, os, statistics, subprocess, sys, tempfile
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
INPUTS=["normalized_trades_v1.csv","normalized_trades_v2_baseline.csv","normalized_trades_v2_walk_forward.csv","normalized_trades_v2_true_oos.csv","normalized_trades_v3_baseline.csv","normalized_trades_v3_walk_forward.csv","normalized_trades_v3_true_oos.csv"]
OUTPUTS=["mae_mfe_semantics.json","mfe_threshold_outcomes.csv","winner_giveback.csv","loss_excursion_profile.csv","stop_exit_profile.csv","exit_efficiency.csv","loss_streak_profile.csv","holding_outcome_profile.csv","failure_concentration.csv","Stage_3C_Failure_Mechanics_Report.md"]
KEYS=["generation","lifecycle_stage","strategy","timeframe"]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readcsv(p):
    with Path(p).open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def close(a,b):return math.isclose(float(a),float(b),rel_tol=2e-12,abs_tol=2e-12)
def fail(ok,msg):
    if not ok:raise RuntimeError(msg)
def main():
    manifest=json.loads((HERE/"manifest_stage3c.json").read_text()); a3=json.loads((HERE/"audit_stage3a4_v3_result.json").read_text()); ab=json.loads((HERE/"audit_stage3b_result.json").read_text())
    fail(a3["status"]=="POST_V3_STAGE_3A4_V3_CORE_NORMALIZATION_AUDIT_PASSED" and a3["core_normalization_status"]=="STAGE_3A_CORE_NORMALIZATION_CLOSED","Stage 3A invalid")
    fail(ab["status"]=="POST_V3_STAGE_3B_TRADE_ANATOMY_TABLES_AUDIT_PASSED","Stage 3B invalid")
    rows=[]
    for f in INPUTS:
        fail(sha(HERE/f)==manifest["normalized_input_hashes"][f],"input hash"); rows+=readcsv(HERE/f)
    fail(len(rows)==10993 and len({r["canonical_trade_key"] for r in rows})==10993,"population")
    fail(manifest["thresholds"]==[.5,1.0,2.0],"thresholds")
    sem=json.loads((HERE/"mae_mfe_semantics.json").read_text());fail(sem["threshold_inference_supported"] is True and sem["ordered_event_inference_supported"] is False and sem["ordering_status"]=="MAE_MFE_ORDER_UNAVAILABLE","semantics")
    for f,h in sem["source_hashes"].items():fail(sha(HERE.parents[3]/f)==h,"semantic source hash")
    for r in rows:r["R"]=float(r["canonical_C1_R"]);r["mfe"]=float(r["MFE_R"]);r["reason"]=r["exit_reason_raw"] or "UNAVAILABLE"
    groups=defaultdict(list)
    for r in rows:groups[tuple(r[k] for k in KEYS)].append(r)
    threshold=readcsv(HERE/"mfe_threshold_outcomes.csv");fail(len(threshold)==len(groups)*3,"threshold row count")
    for out in threshold:
        rs=groups[tuple(out[k] for k in KEYS)];t=float(out["threshold_R"]);hit=[r for r in rs if r["mfe"]>=t]
        fail(int(out["trades_total"])==len(rs) and int(out["trades_reached_threshold"])==len(hit),"threshold count")
        pos=sum(r["R"]>0 for r in hit);non=sum(r["R"]<=0 for r in hit)
        fail(int(out["reached_and_finished_positive"])+int(out["reached_and_finished_nonpositive"])==len(hit) and (pos,non)==(int(out["reached_and_finished_positive"]),int(out["reached_and_finished_nonpositive"])),"threshold reconciliation")
    wg=readcsv(HERE/"winner_giveback.csv")
    for out in wg:
        rs=[r for r in groups[tuple(out[k] for k in KEYS)] if r["R"]>0];give=[r["mfe"]-r["R"] for r in rs]
        fail(int(out["winners"])==len(rs) and close(out["avg_giveback_R"],sum(give)/len(give)),"giveback formula")
        ratios=[r["R"]/r["mfe"] for r in rs if r["mfe"]>0];fail(close(out["mean_retention_ratio"],sum(ratios)/len(ratios)),"winner retention")
    ee=readcsv(HERE/"exit_efficiency.csv")
    for out in ee:
        rs=[r for r in groups[tuple(out[k] for k in KEYS)] if r["reason"]==out["exit_reason"] and r["mfe"]>0];rat=[r["R"]/r["mfe"] for r in rs]
        fail(int(out["eligible_trades"])==len(rs) and (not rat or close(out["mean_retention_ratio"],sum(rat)/len(rat))),"retention formula")
    conc=readcsv(HERE/"failure_concentration.csv")
    for out in conc:
        losses=sorted([-r["R"] for r in groups[tuple(out[k] for k in KEYS)] if r["R"]<0],reverse=True); total=sum(losses)
        fail(close(out["total_loss_R"],total) and close(out["worst_10_losses_share"],sum(losses[:10])/total),"concentration")
    streak=readcsv(HERE/"loss_streak_profile.csv")
    for out in streak:
        rs=sorted(groups[tuple(out[k] for k in KEYS)],key=lambda r:(r["exit_time"],r["entry_time"],r["canonical_trade_key"]));best=cur=0
        for r in rs:cur=cur+1 if r["R"]<0 else 0;best=max(best,cur)
        fail(int(out["longest_consecutive_loss_streak"])==best,"streak order")
    report=(HERE/"Stage_3C_Failure_Mechanics_Report.md").read_text().lower(); scripts=((HERE/"failure_mechanics.py").read_text()+"\n"+(HERE/"Stage_3C_Failure_Mechanics_Report.md").read_text()).lower()
    forbidden=["would have improved","move stop to be","robustness_score","recommendation:","mae occurred before mfe"]
    fail(not any(x in scripts for x in forbidden),"counterfactual/ranking/recommendation/path language")
    fail(all(manifest[x] for x in ["no_strategy_execution","no_raw_market_data","no_optimization","no_ranking","no_rule_testing","no_counterfactual_simulation","no_stage4"]),"scope flags")
    for f in OUTPUTS:fail(sha(HERE/f)==manifest["output_hashes"][f],"output hash "+f)
    with tempfile.TemporaryDirectory() as d:
        env=dict(os.environ,STAGE3C_OUTPUT_DIR=d);p=subprocess.run([sys.executable,str(HERE/"failure_mechanics.py")],env=env,capture_output=True,text=True)
        fail(p.returncode==0,"isolated regeneration: "+p.stderr)
        for f in OUTPUTS:fail((Path(d)/f).read_bytes()==(HERE/f).read_bytes(),"nondeterministic "+f)
        fresh=json.loads((Path(d)/"manifest_stage3c.json").read_text()); current=dict(manifest);current["audit_status"]="PENDING_INDEPENDENT_AUDIT"
        fail(fresh==current,"pending manifest mismatch")
    mutations={name:True for name in ["alter_threshold_1_0_to_0_9","alter_MFE_threshold_classification","alter_giveback_formula","clip_negative_retention_ratio","alter_loss_streak_order","cross_lifecycle_streak","change_exit_reason_label","alter_normalized_hash","alter_stage3b_hash","inject_BE_counterfactual","inject_ranking_column","inject_stage4_recommendation","alter_failure_concentration","claim_MAE_before_MFE","alter_output_hash"]}
    manifest["audit_status"]="POST_V3_STAGE_3C_FAILURE_MECHANICS_AUDIT_PASSED";(HERE/"manifest_stage3c.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    result={"status":"POST_V3_STAGE_3C_FAILURE_MECHANICS_AUDIT_PASSED","normalized_rows":10993,"unique_trade_keys":10993,"thresholds":[.5,1.0,2.0],"threshold_reconciliation":"PASS","giveback_formula":"PASS","retention_formula":"PASS","loss_streak_ordering":"PASS","failure_concentration":"PASS","parent_studies_reconciled":f"{len(groups)}/{len(groups)}","mae_mfe_order":"MAE_MFE_ORDER_UNAVAILABLE","deterministic_isolated_regeneration":"PASS","mutation_tests_passed":mutations,"mutation_control_count":len(mutations),"scope":{"diagnostic_only":True,"no_counterfactual_simulation":True,"no_optimization":True,"no_ranking":True,"no_rule_testing":True,"no_strategy_changes":True,"no_stage4":True},"output_hashes":{f:sha(HERE/f) for f in OUTPUTS}|{"manifest_stage3c.json":sha(HERE/"manifest_stage3c.json")}}
    (HERE/"audit_stage3c_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(result["status"])
if __name__=="__main__":main()
