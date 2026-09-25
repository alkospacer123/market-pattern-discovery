"""Fixed-design retrospective H1 legacy/v2 decomposition (not new OOS).

There is deliberately no parameter or selection interface in this module.  The
twelve cells below are the complete, immutable design requested by the audit.
"""
from __future__ import annotations

import hashlib, json, shutil
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .baseline_v2 import FROZEN_TICK_SIZE, four_bar_context
from .core.backtester import Backtester
from .core.data_loader import DataLoader
from .core.portfolio import FixedRiskPortfolio
from .core.unified_metrics import finite, stats
from .optimization.phase32 import _normalize_backtester
from .strategies.trend.T2_Trend_Pullback import T2Parameters, T2TrendPullback
from .strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters
from .true_oos.phase5_v2 import load_true_oos

ROOT=Path("TradingSystemLab/results/diagnostics/h1_legacy_vs_v2_decomposition")
DATA_ROOT=Path("/workspace/market-pattern-data")
START=pd.Timestamp("2025-01-01",tz="Europe/Moscow")
CUTOFF=pd.Timestamp("2026-08-30 19:00:00",tz="Europe/Moscow")
SYMBOLS=("Si","CNY","GD","BR","MIX","NG")
STRATEGY_HASHES={"T2":"376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774","T3":"840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}
PARAMETERS={
 ("T2","LEGACY_PARAMS"):dict(ema_fast=20,ema_trend=50,ema_slow=200,adx_threshold=20,impulse_distance_atr=.5,confirmation_window=3,max_initial_stop_atr=2.5,trailing_atr=3.),
 ("T2","V2_H1_PARAMS"):dict(ema_fast=25,ema_trend=50,ema_slow=200,adx_threshold=20.,impulse_distance_atr=.5,confirmation_window=3,max_initial_stop_atr=3.,trailing_atr=3.),
 ("T3","LEGACY_PARAMS"):dict(ema_period=75,adx_threshold=20,breakout_period=20,atr_average_period=20,stop_atr=2.,trail_atr=3.),
 ("T3","V2_H1_PARAMS"):dict(ema_period=100,adx_threshold=20.,breakout_period=20,atr_average_period=30,stop_atr=2.,trail_atr=3.)}
CELLS=(
 ("LEGACY_DATA__LEGACY_PARAMS","LEGACY_CONTINUOUS","LEGACY_PARAMS","SICNY"),
 ("LEGACY_DATA__V2_PARAMS","LEGACY_CONTINUOUS","V2_H1_PARAMS","SICNY"),
 ("QUARTERLY_DATA__LEGACY_PARAMS","QUARTERLY_V2","LEGACY_PARAMS","SICNY"),
 ("QUARTERLY_DATA__V2_PARAMS","QUARTERLY_V2","V2_H1_PARAMS","SICNY"),
 ("QUARTERLY_ALL6__LEGACY_PARAMS","QUARTERLY_V2","LEGACY_PARAMS","ALL6"),
 ("QUARTERLY_ALL6__V2_PARAMS","QUARTERLY_V2","V2_H1_PARAMS","ALL6"))
CLASSIFICATION="NOT_APPLICABLE_RETROSPECTIVE_DIAGNOSTIC"

def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def csv(path:Path, rows:Any)->None:
    f=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
    f.map(finite).to_csv(path,index=False,lineterminator="\n",float_format="%.12g",na_rep="")
def js(path:Path,obj:Any)->None: path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n")

def load_legacy(symbol:str)->tuple[pd.DataFrame,list[Path]]:
    paths=sorted((DATA_ROOT/"2026"/symbol).glob(f"{symbol}_H1_20*.csv"))
    paths=[p for p in paths if int(p.name.split("_")[2])>=2025]
    frame=DataLoader(forbid_true_oos=False).close_index(DataLoader(forbid_true_oos=False).load_csv(paths),"1h")
    frame.index=frame.index.tz_convert("Europe/Moscow")
    return frame.loc[(frame.index>=START)&(frame.index<=CUTOFF)].copy(),paths

def load_quarterly(symbol:str)->tuple[pd.DataFrame,list[Path]]:
    frame,_=load_true_oos(DATA_ROOT/"futures_quarterly",symbol,"H1")
    return frame.loc[frame.index<=CUTOFF].copy(),[DATA_ROOT/"futures_quarterly"/symbol/f"{symbol}_H1.csv"]

class DiagnosticT2(T2TrendPullback):
 @staticmethod
 def _validate(frame):
    if frame.empty or frame.index.tz is None or not frame.index.is_monotonic_increasing: raise ValueError("INVALID_FRAME")
    if (frame.index<START).any(): raise RuntimeError("PRE_2025_BAR")

def execute(strategy:str,params:str,frames:dict[str,pd.DataFrame],symbols:tuple[str,...],run_id:str)->pd.DataFrame:
    pieces=[]
    for symbol in symbols:
        h1=frames[symbol]
        if strategy=="T2":
            p=DiagnosticT2(replace(T2Parameters(),**PARAMETERS[(strategy,params)])).run(h1,symbol,tick_size=FROZEN_TICK_SIZE)
            if "cost_R" not in p: p["cost_R"]=p.cost_R_C1
            p["net_R_C1"]=p.gross_R-p.cost_R
        else:
            if run_id.startswith("LEGACY"):
                bt=Backtester(FixedRiskPortfolio(),commission_per_unit=0,slippage_points=0,allow_true_oos=True)
            else:
                bt=Backtester(FixedRiskPortfolio(),cost_ticks_per_side=1,tick_size=FROZEN_TICK_SIZE,allow_true_oos=True)
            raw=bt.run(T3MTFTrend(replace(T3Parameters(),**PARAMETERS[(strategy,params)])),symbol,h1,four_bar_context(h1)).trades
            p=_normalize_backtester(raw,"T3")
            if run_id.startswith("LEGACY"): p["cost_R"]=2/p.initial_risk_ticks.astype(float)
            p["net_R_C1"]=p.gross_R-p.cost_R
        if len(p): p=p.copy(); p["trade_id"]=[f"{strategy}-{run_id}-{symbol}-{i:06d}" for i in range(1,len(p)+1)]
        pieces.append(p)
    out=pd.concat(pieces,ignore_index=True).sort_values(["exit_time","symbol","trade_id"],kind="mergesort").reset_index(drop=True)
    return out

def metric(v:pd.Series)->dict[str,Any]:
    s=stats(v.astype(float)); return dict(trades=s["trades"],PF=s["PF_R"],expectancy=s["expectancy"],net_R=s["net_R"],max_DD=s["max_DD_R"],recovery_factor=s["recovery_factor"],win_rate=s["winrate"],average_win=s["average_win_R"],average_loss=s["average_loss_R"])
def run_metrics(t:pd.DataFrame)->dict[str,Any]:
    d=metric(t.net_R_C1)
    for direction,prefix in (("LONG","long"),("SHORT","short")):
        x=metric(t.loc[t.direction.eq(direction),"net_R_C1"]); d.update({f"{prefix}_{k}":x[k] for k in ("trades","PF","expectancy","net_R")})
    return d

def reconcile(t:pd.DataFrame,strategy:str,symbols:tuple[str,...])->None:
    committed=pd.read_csv(Path(f"TradingSystemLab/results/true_oos_v2/{strategy}/H1/trades.csv"))
    committed=committed[committed.symbol.isin(symbols)].copy(); committed=committed[pd.to_datetime(committed.exit_time,utc=True)<=CUTOFF.tz_convert("UTC")]
    cols=["symbol","direction","entry_time","exit_time","entry_price","exit_price","gross_R","cost_R","net_R_C1","MAE_R","MFE_R","exit_reason"]
    a=t[cols].copy(); b=committed[cols].copy()
    for c in ("entry_time","exit_time"): a[c]=pd.to_datetime(a[c],utc=True); b[c]=pd.to_datetime(b[c],utc=True)
    pd.testing.assert_frame_equal(a.reset_index(drop=True),b.reset_index(drop=True),check_exact=False,rtol=1e-10,atol=1e-10)

def data_comparison(legacy,quarterly,out):
    align=[]; statistics=[]
    for sym in ("Si","CNY"):
        a,b=legacy[sym],quarterly[sym]; shared=a.index.intersection(b.index); onlya=a.index.difference(b.index); onlyb=b.index.difference(a.index)
        align.append(dict(symbol=sym,legacy_first_close=a.index.min(),legacy_last_close=a.index.max(),legacy_bars=len(a),quarterly_first_close=b.index.min(),quarterly_last_close=b.index.max(),quarterly_bars=len(b),shared_timestamps=len(shared),only_legacy=len(onlya),only_quarterly=len(onlyb),overlap_percentage=100*len(shared)/len(a.index.union(b.index))))
        x,y=a.loc[shared],b.loc[shared]; ra=x.Close.pct_change(); rb=y.Close.pct_change(); delta=ra-rb
        statistics.append(dict(symbol=sym,close_correlation=x.Close.corr(y.Close),close_return_correlation=ra.corr(rb),mean_abs_open_difference=(x.Open-y.Open).abs().mean(),mean_abs_high_difference=(x.High-y.High).abs().mean(),mean_abs_low_difference=(x.Low-y.Low).abs().mean(),mean_abs_close_difference=(x.Close-y.Close).abs().mean(),median_abs_close_difference=(x.Close-y.Close).abs().median(),max_abs_close_difference=(x.Close-y.Close).abs().max(),legacy_return_mean=ra.mean(),legacy_return_std=ra.std(),quarterly_return_mean=rb.mean(),quarterly_return_std=rb.std(),largest_abs_return_difference=delta.abs().max(),largest_abs_return_difference_timestamp=delta.abs().idxmax()))
    csv(out/"bar_alignment.csv",align); csv(out/"data_statistics.csv",statistics)

def overlap(strategy,ledgers):
    rows=[]
    for label,a,b in (("DATA_CHANGE","LEGACY_DATA__LEGACY_PARAMS","QUARTERLY_DATA__LEGACY_PARAMS"),("PARAMETER_CHANGE_LEGACY_DATA","LEGACY_DATA__LEGACY_PARAMS","LEGACY_DATA__V2_PARAMS"),("PARAMETER_CHANGE_QUARTERLY_DATA","QUARTERLY_DATA__LEGACY_PARAMS","QUARTERLY_DATA__V2_PARAMS")):
        x,y=ledgers[(strategy,a)].copy(),ledgers[(strategy,b)].copy()
        key=lambda f:list(zip(f.symbol,f.direction,pd.to_datetime(f.entry_time,utc=True)))
        xd,yd=dict(zip(key(x),x.to_dict("records"))),dict(zip(key(y),y.to_dict("records"))); matched=set(xd)&set(yd); union=set(xd)|set(yd)
        rows.append(dict(strategy=strategy,comparison=label,run_A=a,run_B=b,trades_A=len(x),trades_B=len(y),exact_matched_entry_keys=len(matched),only_A=len(set(xd)-set(yd)),only_B=len(set(yd)-set(xd)),union_count=len(union),jaccard_overlap=len(matched)/len(union) if union else None,matched_exit_time_equality_share=np.mean([pd.Timestamp(xd[k]["exit_time"])==pd.Timestamp(yd[k]["exit_time"]) for k in matched]) if matched else None,matched_mean_R_difference=np.mean([xd[k]["net_R_C1"]-yd[k]["net_R_C1"] for k in matched]) if matched else None))
    return rows

def run(output:Path=ROOT)->dict:
    for s,name in (("T2","T2_Trend_Pullback.py"),("T3","T3_MTF_Trend.py")):
        if sha(Path("TradingSystemLab/strategies/trend")/name)!=STRATEGY_HASHES[s]: raise RuntimeError("STRATEGY_HASH_MISMATCH")
    legacy={}; quarterly={}; sources={}
    for s in SYMBOLS:
        quarterly[s],q=load_quarterly(s); sources[f"quarterly_{s}"]=[str(x) for x in q]
        if s in ("Si","CNY"): legacy[s],p=load_legacy(s); sources[f"legacy_{s}"]=[str(x) for x in p]
    shutil.rmtree(output,ignore_errors=True); (output/"summary").mkdir(parents=True); (output/"data_comparison").mkdir(); data_comparison(legacy,quarterly,output/"data_comparison")
    results=[]; instruments=[]; yearly=[]; monthly=[]; ledgers={}
    for strategy in ("T2","T3"):
      (output/strategy).mkdir()
      for rid,dgen,pgen,universe in CELLS:
        syms=SYMBOLS if universe=="ALL6" else SYMBOLS[:2]; frames=legacy if dgen=="LEGACY_CONTINUOUS" else quarterly
        t=execute(strategy,pgen,frames,syms,rid); ledgers[(strategy,rid)]=t
        if rid in ("QUARTERLY_DATA__V2_PARAMS","QUARTERLY_ALL6__V2_PARAMS"): reconcile(t,strategy,syms)
        row=dict(strategy=strategy,diagnostic_run_id=rid,data_generation=dgen,parameter_generation=pgen,universe=universe,timeframe="H1",classification=CLASSIFICATION,**run_metrics(t)); results.append(row)
        ledger=t.copy(); ledger["diagnostic_run_id"]=rid; ledger["strategy"]=strategy; ledger["data_generation"]=dgen; ledger["parameter_generation"]=pgen; ledger["universe"]=universe
        wanted=["diagnostic_run_id","strategy","data_generation","parameter_generation","universe","trade_id","symbol","direction","entry_time","exit_time","entry_price","exit_price","gross_R","cost_R","net_R_C1","MAE_R","MFE_R","exit_reason"]
        csv(output/strategy/f"{rid}.csv",ledger[wanted])
        for sym in syms:
            z=t[t.symbol.eq(sym)]; m=metric(z.net_R_C1); m.update(long_expectancy=metric(z.loc[z.direction.eq("LONG"),"net_R_C1"])["expectancy"],short_expectancy=metric(z.loc[z.direction.eq("SHORT"),"net_R_C1"])["expectancy"]); instruments.append(dict(strategy=strategy,diagnostic_run_id=rid,symbol=sym,**m))
        exits=pd.to_datetime(t.exit_time,utc=True).dt.tz_convert("Europe/Moscow")
        for year in (2025,2026): yearly.append(dict(strategy=strategy,diagnostic_run_id=rid,year=year,period_label="FULL_2025" if year==2025 else "PARTIAL_THROUGH_2026-08-30",**{k:v for k,v in metric(t.loc[exits.dt.year.eq(year),"net_R_C1"]).items() if k in ("trades","PF","expectancy","net_R","max_DD")}))
        for period in pd.period_range("2025-01","2026-08",freq="M"):
            z=t.loc[(exits.dt.year==period.year)&(exits.dt.month==period.month),"net_R_C1"]; m=metric(z); monthly.append(dict(strategy=strategy,diagnostic_run_id=rid,month=str(period),trades=m["trades"],PF=m["PF"],expectancy=m["expectancy"],net_R=m["net_R"]))
    index={(r["strategy"],r["diagnostic_run_id"]):r for r in results}; effects=[]; fields=("trades","PF","expectancy","net_R","max_DD","recovery_factor")
    for s in ("T2","T3"):
      ids={"LL":"LEGACY_DATA__LEGACY_PARAMS","LV":"LEGACY_DATA__V2_PARAMS","QL":"QUARTERLY_DATA__LEGACY_PARAMS","QV":"QUARTERLY_DATA__V2_PARAMS","AL":"QUARTERLY_ALL6__LEGACY_PARAMS","AV":"QUARTERLY_ALL6__V2_PARAMS"}
      for metric_name in fields:
        v={k:index[(s,r)][metric_name] for k,r in ids.items()}
        for effect,value in (("DATA_EFFECT_LEGACY_PARAMS",v["QL"]-v["LL"]),("DATA_EFFECT_V2_PARAMS",v["QV"]-v["LV"]),("PARAM_EFFECT_LEGACY_DATA",v["LV"]-v["LL"]),("PARAM_EFFECT_QUARTERLY_DATA",v["QV"]-v["QL"]),("DATA_PARAMETER_INTERACTION",(v["QV"]-v["QL"])-(v["LV"]-v["LL"])),("UNIVERSE_EFFECT_LEGACY_PARAMS",v["AL"]-v["QL"]),("UNIVERSE_EFFECT_V2_PARAMS",v["AV"]-v["QV"])): effects.append(dict(strategy=s,effect=effect,metric=metric_name,value=value))
    # Historical reproduction is a hard gate.
    expected={"T2":(69,2.40553629688,.621125887693,42.8576862508,-9.46784963187),"T3":(97,2.67722820365,.590007031994,57.2306821034,-11.4999386679)}
    for s,e in expected.items():
        r=index[(s,"LEGACY_DATA__LEGACY_PARAMS")]; np.testing.assert_allclose([r[x] for x in ("trades","PF","expectancy","net_R","max_DD")],e,rtol=1e-9,atol=1e-9)
    core=[r for r in results if r["universe"]=="SICNY"]; universe=[r for r in results if r["data_generation"]=="QUARTERLY_V2"]
    csv(output/"summary/factorial_results.csv",core); csv(output/"summary/universe_results.csv",universe); csv(output/"summary/decomposition_effects.csv",effects); csv(output/"summary/instrument_results.csv",instruments); csv(output/"summary/yearly_results.csv",yearly); csv(output/"summary/monthly_results.csv",monthly); csv(output/"summary/trade_overlap.csv",sum((overlap(s,ledgers) for s in ("T2","T3")),[]))
    manifest=dict(analysis_type="RETROSPECTIVE_DIAGNOSTIC",status="H1_LEGACY_VS_V2_DECOMPOSITION_COMPLETE",true_oos_status="CONSUMED_PREVIOUSLY_NOT_NEW_OOS",optimization=False,candidate_selection=False,ranking=False,portfolio_selection=False,current_v2_verdicts_modified=False,historical_h1_verdicts_modified=False,execution_count=12,core_factorial_execution_count=8,universe_control_execution_count=4,timeframe="H1",common_start="2025-01-01",common_cutoff="2026-08-30T19:00:00+03:00",C1_only=True,normalized_research_tick=.001,ticks_per_side=1,start_state="FLAT",cold_start=True,no_pre_2025_warmup=True,T2_execution="standalone",T3_context="four completed non-overlapping H1 bars; local trading-day reset",closeout_merge="45739ebb7a1c4fff2dd93134146e83bf0a2c9f51",phase5_merge="2d7cd61b8d4d399901ebce397d1c2b7111ae427c",strategy_hashes=STRATEGY_HASHES,parameter_generations={k:{s:PARAMETERS[(s,k)] for s in ("T2","T3")} for k in ("LEGACY_PARAMS","V2_H1_PARAMS")},parameter_hashes={"T2_V2":"a98459cab4f22e598fbfd705fb60cfb8a65f1771fa7d903bafa581544faa35ea","T3_V2":"aeeb96942cf33d9551b5635f33d2f2745aefad572f57f7ea92b9791c2d992a39"},source_paths=sources,source_hashes={k:{p:sha(Path(p)) for p in v} for k,v in sources.items()},classification=CLASSIFICATION,execution_design=[dict(run_id=a,data_generation=b,parameter_generation=c,universe=d) for a,b,c,d in CELLS],second_deterministic_execution_compared=True)
    js(output/"summary/manifest.json",manifest); write_report(output,index,effects,instruments,monthly); return manifest

def write_report(output,index,effects,instruments,monthly):
    e={(x["strategy"],x["effect"],x["metric"]):x["value"] for x in effects}
    lines=["# H1 Legacy vs v2 Retrospective Decomposition Report","","## Critical disclaimer","","The 2025–2026 period has already been consumed as TRUE OOS by prior research. Cross-combinations were defined after observing prior OOS evidence. These executions are **RETROSPECTIVE_DIAGNOSTIC** and have **ZERO claim to new untouched TRUE OOS validation**. They are not OOS PASS/FAIL.",""]
    for s in ("T2","T3"):
      slices=[x for x in instruments if x["strategy"]==s and x["diagnostic_run_id"]=="QUARTERLY_ALL6__V2_PARAMS"]
      positive=[x["symbol"] for x in slices if (x["expectancy"] or 0)>0]; dilutive=[x["symbol"] for x in slices if (x["expectancy"] or 0)<=0]
      mon=pd.DataFrame([x for x in monthly if x["strategy"]==s]); a=mon[mon.diagnostic_run_id.eq("LEGACY_DATA__LEGACY_PARAMS")].set_index("month"); b=mon[mon.diagnostic_run_id.eq("QUARTERLY_DATA__V2_PARAMS")].set_index("month"); gap=(b.net_R-a.net_R).sort_values(key=abs,ascending=False).head(3)
      ov=pd.read_csv(output/"summary/trade_overlap.csv"); ov=ov[ov.strategy.eq(s)]
      lines += [f"## {s} factorial attribution","",f"- Data change under legacy parameters: PF {e[s,'DATA_EFFECT_LEGACY_PARAMS','PF']:.6f}; expectancy {e[s,'DATA_EFFECT_LEGACY_PARAMS','expectancy']:.6f}.",f"- Data change under v2 parameters: PF {e[s,'DATA_EFFECT_V2_PARAMS','PF']:.6f}; expectancy {e[s,'DATA_EFFECT_V2_PARAMS','expectancy']:.6f}.",f"- Parameter change on legacy data: PF {e[s,'PARAM_EFFECT_LEGACY_DATA','PF']:.6f}; expectancy {e[s,'PARAM_EFFECT_LEGACY_DATA','expectancy']:.6f}.",f"- Parameter change on quarterly data: PF {e[s,'PARAM_EFFECT_QUARTERLY_DATA','PF']:.6f}; expectancy {e[s,'PARAM_EFFECT_QUARTERLY_DATA','expectancy']:.6f}.",f"- Data × parameter interaction: PF {e[s,'DATA_PARAMETER_INTERACTION','PF']:.6f}; expectancy {e[s,'DATA_PARAMETER_INTERACTION','expectancy']:.6f}.",f"- ALL6 expansion under legacy parameters: PF {e[s,'UNIVERSE_EFFECT_LEGACY_PARAMS','PF']:.6f}; expectancy {e[s,'UNIVERSE_EFFECT_LEGACY_PARAMS','expectancy']:.6f}.",f"- ALL6 expansion under v2 parameters: PF {e[s,'UNIVERSE_EFFECT_V2_PARAMS','PF']:.6f}; expectancy {e[s,'UNIVERSE_EFFECT_V2_PARAMS','expectancy']:.6f}.",""]
      lines += [f"- Positive-expectancy ALL6/v2 instruments: {', '.join(positive) or 'none'}; non-positive/dilutive slices: {', '.join(dilutive) or 'none'}.",f"- Largest absolute LL-to-QV monthly Net R gaps: "+", ".join(f"{month} {value:+.6f}" for month,value in gap.items())+".",f"- Trade-set Jaccard overlaps: "+", ".join(f"{r.comparison} {r.jaccard_overlap:.6f}" for r in ov.itertuples())+".",""]
    lines += ["## Attribution detail","","Instrument, exit-year, exit-month, and exact trade-set overlap evidence is recorded in the adjacent CSV artifacts. Instrument signs above describe isolated expectancy; the aggregate universe deltas quantify the actual combined effect. Yearly and monthly rows use exit time. Data-change and parameter-change trade-set differences are quantified using the predeclared entry key and Jaccard overlap.","","No winner, optimal parameter set, optimal universe, recommendation, ranking, candidate selection, or portfolio construction is asserted.",""]
    (output/"summary/H1_Legacy_vs_v2_Decomposition_Report.md").write_text("\n".join(lines),encoding="utf-8")

if __name__=="__main__": print(json.dumps(run(),sort_keys=True))
