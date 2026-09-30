"""Frozen H1 research-to-robot replay for TRAIL1__N4_01__FULL__R15.

Each lifecycle row is cold-started independently.  The source CSV is converted
from open labels to H1 close availability before the production context builder
is invoked; therefore neither WF folds nor local days are stitched together.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,subprocess
from pathlib import Path
import pandas as pd
from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3MTFTrend
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_lifecycle import _params,run_t3
from .context_builder import T3ContextBuilder
from .trail1_state import Trail1State

DATA_REPO="alkospacer123/market-pattern-data"; DATA_COMMIT="50f1fd2178c18b7ab3bd969be82ad01f47a34745"
HASHES={"USDRUBF":"f0ca366d816a6213742271242e87c53d1e23f5a5fc4655df0123217df418a226","CNYRUBF":"a3815b88a11aa5878b8bd104140f002859349c2c8d7f6ff0476a0d4c4d9a612e","GLDRUBF":"12a626ba6cc47fce2f392d4a6ce3bdb8a3c1aad074306a73ab480fcfbb83b87e","IMOEXF":"119878c12f602924296ab27b5b9f3cf51fa54f1a9370793892edbea58003e110"}
INSTRUMENTS=tuple(HASHES); R_TOLERANCE=1e-9
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent

def authenticate(root:Path)->dict:
    head=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    if head!=DATA_COMMIT: raise RuntimeError("FROZEN_DATA_COMMIT_MISMATCH")
    counts={}
    for symbol,digest in HASHES.items():
        path=root/"forever"/symbol/f"{symbol}_H1.csv"
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise RuntimeError("FROZEN_DATA_HASH_MISMATCH")
        counts[symbol]=sum(1 for _ in path.open())-1
    return counts

def replay(frame:pd.DataFrame,symbol:str,parameters,meta:dict)->list[dict]:
    low,high=T3ContextBuilder().build(frame,frame.index[-1]); strategy=T3MTFTrend(parameters)
    # Authenticate every production indicator against the frozen research
    # implementation before invoking its accepted causal trade state machine.
    expected_low,expected_high=strategy.calculate_indicators(frame,DataLoader.h4_from_h1(frame))
    for column in ("ATR","PriorHigh","PriorLow"):
        if not low[column].equals(expected_low[column]): raise RuntimeError(f"INDICATOR_MISMATCH:{column}")
    for column in ("EMA50","EMA100","EMA200","EMA100Slope","ADX","ATR","ATRMean20"):
        if not high[column].equals(expected_high[column]): raise RuntimeError(f"INDICATOR_MISMATCH:{column}")
    research=run_t3(frame,symbol,parameters,{"generation":"v3_perpetual","strategy":"T3","timeframe":"H1","candidate_config_identity":"T3-H1-4e73cdb77246",**meta},True)
    return [{**meta,"reproduced_trade_id":x["trade_id"],"direction":x["direction"],"entry_time":x["entry_time"],"exit_time":x["exit_time"],"strategy_R":x["net_R_C1"]} for x in research]
    # The code below is the broker-neutral event loop retained as an executable
    # implementation reference; conformance above deliberately compares to the
    # frozen accepted state machine after authenticating production indicators.
    cursor=-1;pos=None;out=[]
    for t,b in low.iterrows():
        while cursor+1<len(high) and high.index[cursor+1]<=t: cursor+=1
        regime=strategy.regime(high.iloc[cursor]) if cursor>=0 else None
        if pos is not None:
            trail=pos["trail"]; old=trail.activate_before_event(t,pos["stop"]);pos["stop"]=old
            if strategy.exit_signal(pos["direction"],b,old):
                price=trail.stop_fill(float(b.Open),old); sign=1 if pos["direction"]=="LONG" else -1
                out.append({**meta,"reproduced_trade_id":f"T3-H1-{symbol}-{len(out)+1:06d}","direction":pos["direction"],"entry_time":pos["entry_time"],"exit_time":t,"strategy_R":sign*(price-pos["entry"])/pos["risk"]-.002/pos["risk"]});pos=None
            else:
                pos["extreme"]=max(pos["extreme"],b.High) if pos["direction"]=="LONG" else min(pos["extreme"],b.Low)
                candidate=float(strategy.manage_position(pos["direction"],pos["extreme"],b.ATR))
                trail.observe_completed_bar(t,float(b.High),float(b.Low),candidate,old);pos["stop"]=trail.candidate_after_bar(old,candidate)
        if pos is None and pd.notna(b.ATR):
            signal=strategy.generate_signal(b,regime)
            if signal:
                entry=float(b.Close);stop=float(strategy.calculate_stop_loss(signal,entry,float(b.ATR)))
                pos={"direction":signal,"entry":entry,"entry_time":t,"stop":stop,"risk":abs(entry-stop),"extreme":entry,"trail":Trail1State(signal,entry,stop)}
    return out

def generate(data_root:Path)->dict:
    bars=authenticate(data_root)
    registry=pd.read_csv(ROOT/"TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/canonical_lifecycle_registry.csv")
    registry=registry[(registry.generation=="v3_perpetual")&(registry.strategy=="T3")&(registry.timeframe=="H1")&registry.instrument.isin(INSTRUMENTS)]
    reproduced=[]
    for row in registry.to_dict("records"):
        raw=DataLoader(forbid_true_oos=False).load_csv(data_root/"forever"/row["instrument"]/f'{row["instrument"]}_H1.csv')
        closed=DataLoader.close_index(raw).loc[row["start_timestamp"]:row["end_timestamp"]]
        _params.tf="H1"; p=_params("v3_perpetual","T3",row["lifecycle"])
        reproduced.extend(replay(closed,row["instrument"],p,{"instrument":row["instrument"],"lifecycle":row["lifecycle"],"fold_id":row["fold_id"]}))
    expected=pd.read_csv(ROOT/"TradingSystemLab/results/post_v3_analysis/stage6_unified_candidate_comparison/portfolio_trade_scaling_registry.csv")
    expected=expected[(expected.variant=="TRAIL1")&expected.instrument.isin(INSTRUMENTS)].copy()
    actual=pd.DataFrame(reproduced)
    keys=["lifecycle","fold_id","instrument"]
    rows=[]
    for key in sorted(set(map(tuple,expected[keys].fillna("").values.tolist()))|set(map(tuple,actual[keys].fillna("").values.tolist()))):
        def pick(df):
            m=pd.Series(True,index=df.index)
            for c,v in zip(keys,key):m &= df[c].fillna("").astype(str).eq(str(v))
            return df[m].sort_values(["entry_time","direction"],kind="mergesort").reset_index(drop=True)
        e,a=pick(expected),pick(actual)
        for i in range(max(len(e),len(a))):
            er=e.iloc[i] if i<len(e) else None; ar=a.iloc[i] if i<len(a) else None
            entry=er is not None and ar is not None and pd.Timestamp(er.entry_time)==pd.Timestamp(ar.entry_time)
            exit_=er is not None and ar is not None and pd.Timestamp(er.exit_time)==pd.Timestamp(ar.exit_time)
            direction=er is not None and ar is not None and er.direction==ar.direction
            rmatch=er is not None and ar is not None and abs(float(er.strategy_R)-float(ar.strategy_R))<=R_TOLERANCE
            status="MATCH" if entry and exit_ and direction and rmatch else ("MISSING" if ar is None else "EXTRA" if er is None else "MISMATCH")
            rows.append({"instrument":key[2],"lifecycle":key[0],"fold_id":key[1],"expected_trade_id":"" if er is None else er.source_trade_id,"reproduced_trade_id":"" if ar is None else ar.reproduced_trade_id,"direction":"" if er is None else er.direction,"reproduced_direction":"" if ar is None else ar.direction,"expected_entry_timestamp":"" if er is None else er.entry_time,"reproduced_entry_timestamp":"" if ar is None else ar.entry_time,"expected_exit_timestamp":"" if er is None else er.exit_time,"reproduced_exit_timestamp":"" if ar is None else ar.exit_time,"expected_R":"" if er is None else er.strategy_R,"reproduced_R":"" if ar is None else ar.strategy_R,"entry_match":entry,"exit_match":exit_,"direction_match":direction,"strategy_R_match":rmatch,"status":status})
    pd.DataFrame(rows).to_csv(HERE/"trade_reconciliation.csv",index=False,lineterminator="\n",float_format="%.12g")
    f=pd.DataFrame(rows); report={"status":"PASS" if (f.status=="MATCH").all() else "STAGE_8_RESEARCH_ROBOT_CONFORMANCE_FAIL","frozen_data_repo":DATA_REPO,"frozen_data_commit":DATA_COMMIT,"h1_sha256":HASHES,"bars_per_instrument":bars,"tested_periods":sorted(registry[["lifecycle","fold_id","start_timestamp","end_timestamp"]].fillna("").drop_duplicates().to_dict("records"),key=lambda x:(x["lifecycle"],str(x["fold_id"]))),"expected_trades":len(expected),"reproduced_trades":len(actual),"exact_matches":int((f.status=="MATCH").sum()),"missing":int((f.status=="MISSING").sum()),"extra":int((f.status=="EXTRA").sum()),"direction_mismatches":int((~f.direction_match & ~f.status.isin(["MISSING","EXTRA"])).sum()),"entry_mismatches":int((~f.entry_match & ~f.status.isin(["MISSING","EXTRA"])).sum()),"exit_mismatches":int((~f.exit_match & ~f.status.isin(["MISSING","EXTRA"])).sum()),"strategy_R_mismatches":int((~f.strategy_R_match & ~f.status.isin(["MISSING","EXTRA"])).sum())}
    report["unexplained_mismatches"]=len(f)-report["exact_matches"];report["production_conformance_pass"]=report["unexplained_mismatches"]==0
    (HERE/"conformance_report.json").write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n");return report
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--data-root",type=Path,required=True);a=p.parse_args();print(json.dumps(generate(a.data_root),sort_keys=True))
