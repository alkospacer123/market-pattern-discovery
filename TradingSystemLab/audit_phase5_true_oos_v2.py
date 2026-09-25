"""Independent fail-closed audit of committed v2 Phase 5 evidence."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from TradingSystemLab.core.unified_metrics import concentration
from TradingSystemLab.true_oos.phase5_v2 import (BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED,
    FREEZE_COMMIT, INSTRUMENTS, OUTPUT_ROOT, REGISTRY_PATH, ROBUSTNESS_COMMIT,
    STRATEGY_HASHES, STUDIES, TRUE_OOS_START, WALK_FORWARD_COMMIT, artifact_sha256,
    bootstrap, classify, summary)

REQUIRED={"trades.csv","yearly_report.csv","quarterly_report.csv","instrument_report.csv","direction_report.csv","concentration_report.csv","mae_mfe_report.csv","bootstrap_report.csv","metrics.json","manifest.json","final_report.md"}
def req(x: bool,msg: str)->None:
    if not x: raise RuntimeError(msg)
def close(a,b)->bool: return bool((pd.isna(a) and pd.isna(b)) or np.isclose(float(a),float(b),rtol=1e-8,atol=1e-10))

def audit(root: Path=OUTPUT_ROOT)->dict:
    registry_raw=REGISTRY_PATH.read_bytes(); candidates=json.loads(registry_raw)["candidates"]
    req([(x["strategy"],x["timeframe"]) for x in candidates]==list(STUDIES),"FOUR_FROZEN_IDENTITIES_INVALID")
    protected=((FREEZE_COMMIT,"TradingSystemLab/results/baseline_v2"),(FREEZE_COMMIT,"TradingSystemLab/results/optimization_v2"),(FREEZE_COMMIT,"TradingSystemLab/results/phase3_candidate_freeze"),(ROBUSTNESS_COMMIT,"TradingSystemLab/results/robustness_v2"),(WALK_FORWARD_COMMIT,"TradingSystemLab/results/walk_forward_v2"))
    for commit,path in protected: req(subprocess.run(["git","diff","--quiet",commit,"--",path]).returncode==0,f"PROTECTED_TREE_CHANGED:{path}")
    manifest=json.loads((root/"summary/manifest.json").read_text()); req(manifest["candidate_registry_sha256"]==hashlib.sha256(registry_raw).hexdigest(),"REGISTRY_HASH_INVALID")
    req(manifest["candidate_count"]==4 and manifest["development_rows_admitted"]==0 and manifest["cold_start"] and manifest["start_state"]=="FLAT","OOS_LIFECYCLE_INVALID")
    req(manifest["C1_only"] and manifest["normalized_research_tick"]==.001 and not any(manifest[x] for x in ("optimization","ranking","candidate_replacement")),"RESEARCH_CONTRACT_INVALID")
    req(manifest["walk_forward_reference_commit"]==WALK_FORWARD_COMMIT,"WALK_FORWARD_PROVENANCE_INVALID")
    for s,path in (("T2",Path("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py")),("T3",Path("TradingSystemLab/strategies/trend/T3_MTF_Trend.py"))): req(hashlib.sha256(path.read_bytes()).hexdigest()==STRATEGY_HASHES[s],"STRATEGY_HASH_INVALID")
    classes={}
    for item in candidates:
        s,tf=item["strategy"],item["timeframe"]; target=root/s/tf; req({p.name for p in target.iterdir()}==REQUIRED,"ARTIFACT_SET_INVALID")
        trades=pd.read_csv(target/"trades.csv"); metrics=json.loads((target/"metrics.json").read_text()); study=json.loads((target/"manifest.json").read_text())
        req(not trades.trade_id.duplicated().any(),"DUPLICATE_TRADE_ID"); req(pd.to_datetime(trades.entry_time,utc=True).ge(TRUE_OOS_START.tz_convert("UTC")).all(),"PRE_OOS_ENTRY"); req(pd.to_datetime(trades.exit_time,utc=True).ge(TRUE_OOS_START.tz_convert("UTC")).all(),"PRE_OOS_EXIT")
        req(study["cold_start"] and study["development_rows_admitted"]==0 and study["execution_context"]==("none" if s=="T2" else f"four completed non-overlapping {tf} bars; local-day reset"),"CONTEXT_OR_COLD_START_INVALID")
        overall=summary(trades.net_R_C1); [req(close(metrics["aggregate"][k],v),f"AGGREGATE:{k}") for k,v in overall.items()]
        for filename,column in (("yearly_report.csv","year"),("quarterly_report.csv","quarter"),("instrument_report.csv","symbol"),("direction_report.csv","direction")):
            report=pd.read_csv(target/filename)
            if column=="year": keys=pd.to_datetime(trades.exit_time,utc=True).dt.year
            elif column=="quarter": keys=pd.to_datetime(trades.exit_time,utc=True).dt.to_period("Q").astype(str)
            else: keys=trades[column]
            for _,row in report.iterrows():
                expected=summary(trades.loc[keys.eq(row[column]),"net_R_C1"])
                [req(close(row[k],v),f"{filename}:{row[column]}:{k}") for k,v in expected.items()]
        conc=concentration(trades.net_R_C1); row=pd.read_csv(target/"concentration_report.csv").iloc[0]; [req(close(row[k],v),f"CONCENTRATION:{k}") for k,v in conc.items()]
        boot=bootstrap(trades.net_R_C1); brow=pd.read_csv(target/"bootstrap_report.csv").iloc[0]; [req(close(brow[k],v),f"BOOTSTRAP:{k}") for k,v in boot.items()]
        quarterly=pd.read_csv(target/"quarterly_report.csv"); observed=int((quarterly.total_trades>0).sum()); positive=int(((quarterly.total_trades>0)&(quarterly.expectancy>0)).sum())
        instruments=pd.read_csv(target/"instrument_report.csv"); directions=pd.read_csv(target/"direction_report.csv"); ig=bool((instruments.loc[instruments.total_trades>0,"expectancy"]>=0).all()); dg=bool((directions.loc[directions.total_trades>0,"expectancy"]>=0).all())
        verdict=classify(overall,boot["probability_mean_R_gt_0"],observed,positive,ig,dg,conc["net_R_without_top5"]); req(verdict==metrics["classification"]==study["classification"],"CLASSIFICATION_INVALID"); classes[f"{s}/{tf}"]=verdict
    req(manifest["classifications"]==classes,"ROOT_CLASSIFICATIONS_INVALID"); req(manifest["artifact_sha256"]==artifact_sha256(root),"ARTIFACT_HASH_INVALID")
    manifest["status"]="PHASE_5_TRUE_OOS_VALIDATION_COMPLETE"; (root/"summary/manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True,allow_nan=False)+"\n")
    return {"status":"PHASE_5_TRUE_OOS_AUDIT_PASSED","classifications":classes}
if __name__=="__main__": print(json.dumps(audit(),sort_keys=True))
