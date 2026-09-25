"""One-shot Phase 5 TRUE OOS evaluation of the four frozen v3 perpetual identities."""
from __future__ import annotations

import argparse, csv, hashlib, json, re, shutil
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ..perpetual_v3_baseline import DATA_ROOT, FROZEN_TICK_SIZE, INSTRUMENTS, four_bar_context
from ..core.backtester import Backtester
from ..core.portfolio import FixedRiskPortfolio
from ..core.unified_metrics import concentration, finite, stats
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import _normalize_backtester
from ..strategies.trend.T2_Trend_Pullback import T2Parameters, T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters

OUTPUT_ROOT = Path("TradingSystemLab/results/perpetual_v3/true_oos")
REGISTRY_PATH = Path("TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze/candidate_registry.json")
WALK_FORWARD_ROOT = Path("TradingSystemLab/results/perpetual_v3/walk_forward")
TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="Europe/Moscow")
STUDIES = (("T2", "M30"), ("T2", "H1"), ("T3", "M30"), ("T3", "H1"))
BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED = 10_000, 5102025
FREEZE_COMMIT = "f123f1468c6b5f1f0719154aba73d4635e6de0ea"
ROBUSTNESS_COMMIT = "d684bfb7f321c2183eab36159c77fa687bd6092b"
WALK_FORWARD_COMMIT = "d5aa616186c2750d5f0b0b9c60eddbf5d096c98f"
STRATEGY_HASHES = {"T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
                   "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}
EXPECTED_IDENTITIES = {
    ("T2", "M30"): ("T2_M30_candidate_v3", "T2-M30-608dc87d09f1", "608dc87d09f10aa0e03026ebb525f6b8ec865060c7890cee08fa0c7ed14cf86b"),
    ("T2", "H1"): ("T2_H1_candidate_v3", "T2-H1-608dc87d09f1", "608dc87d09f10aa0e03026ebb525f6b8ec865060c7890cee08fa0c7ed14cf86b"),
    ("T3", "M30"): ("T3_M30_candidate_v3", "T3-M30-d6feb972db57", "d6feb972db575bf6e66ac901be95fe079dccc82d9e2c3e880d17faeae8d1adf9"),
    ("T3", "H1"): ("T3_H1_candidate_v3", "T3-H1-4e73cdb77246", "4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a"),
}

def load_frozen_registry(path: Path) -> tuple[list[dict[str, Any]], str]:
    raw = path.read_bytes(); payload = json.loads(raw); candidates = payload["candidates"]
    if not payload.get("immutable") or len(candidates) != 4: raise RuntimeError("FROZEN_REGISTRY_INVALID")
    for item in candidates:
        key = (item["strategy"], item["timeframe"])
        if (item["candidate_id"], item["phase2_configuration_id"], item["parameter_hash"]) != EXPECTED_IDENTITIES.get(key):
            raise RuntimeError(f"FROZEN_CANDIDATE_ID_OR_HASH_INVALID:{key}")
        if stable_hash(item["parameters"]) != item["parameter_hash"]: raise RuntimeError(f"FROZEN_PARAMETER_HASH_INVALID:{key}")
    return candidates, hashlib.sha256(raw).hexdigest()

def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")

def _csv(path: Path, rows: Any) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")

def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def _frame_sha(frame: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(frame, index=True).values.tobytes()).hexdigest()

def load_true_oos(data_root: Path, symbol: str, timeframe: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Sequentially locate the boundary, admitting and hashing only closed OOS bars."""
    root = Path(data_root).resolve()
    if root != DATA_ROOT.resolve(): raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    source = root/symbol/f"{symbol}_{timeframe}.csv"
    rows: list[dict[str,str]] = []
    with source.open(encoding="utf-8-sig", newline="") as stream:
        sample=stream.read(4096); stream.seek(0); header=sample.splitlines()[0]
        delimiter=max((",",";","\t"), key=header.count); reader=csv.DictReader(stream, delimiter=delimiter)
        if not reader.fieldnames: raise ValueError("CSV_HEADER_MISSING")
        names={re.sub(r"[<>]","",x).strip().title():x for x in reader.fieldnames}
        time_name=next((names[x] for x in ("Datetime","Timestamp","Date") if x in names),None)
        if not time_name: raise ValueError("DATETIME_COLUMN_MISSING")
        delta=pd.Timedelta("30min" if timeframe=="M30" else "1h")
        for raw in reader:
            opened=pd.Timestamp(raw[time_name]); opened=opened.tz_localize("Europe/Moscow") if opened.tz is None else opened.tz_convert("Europe/Moscow")
            if opened+delta >= TRUE_OOS_START: rows.append(raw)
    if not rows: raise ValueError(f"NO_TRUE_OOS_ROWS:{symbol}/{timeframe}")
    raw=pd.DataFrame(rows).rename(columns=lambda x:re.sub(r"[<>]","",str(x)).strip().title())
    stamps=pd.DatetimeIndex(pd.to_datetime(raw[next(x for x in ("Datetime","Timestamp","Date") if x in raw)],errors="raise"))
    stamps=stamps.tz_localize("Europe/Moscow") if stamps.tz is None else stamps.tz_convert("Europe/Moscow")
    cols=["Open","High","Low","Close"]+(["Volume"] if "Volume" in raw else [])
    frame=raw[cols].apply(pd.to_numeric,errors="raise"); frame.index=stamps+delta; frame.index.name="CloseTime"
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing: raise ValueError("DUPLICATE_OR_UNSORTED_TIMESTAMPS")
    if (frame.index<TRUE_OOS_START).any(): raise RuntimeError("TRUE_OOS_BARRIER_VIOLATION")
    if (frame.High<frame[["Open","Close","Low"]].max(axis=1)).any() or (frame.Low>frame[["Open","Close","High"]].min(axis=1)).any(): raise ValueError("INVALID_OHLC")
    coverage={"source_path":str(source),"first_admitted_oos_close":frame.index[0].isoformat(),
              "last_admitted_oos_close":frame.index[-1].isoformat(),"admitted_oos_rows":len(frame),
              "admitted_frame_sha256":_frame_sha(frame),"development_rows_admitted":0}
    return frame, coverage

class OOST2(T2TrendPullback):
    @staticmethod
    def _validate(frame: pd.DataFrame) -> None:
        if frame.empty or frame.index.tz is None or not frame.index.is_monotonic_increasing: raise ValueError("INVALID_OOS_FRAME")
        if (frame.index<TRUE_OOS_START).any(): raise RuntimeError("TRUE_OOS_BARRIER_VIOLATION")
        if not {"Open","High","Low","Close"}.issubset(frame): raise ValueError("OHLC_REQUIRED")

def execute(strategy: str, timeframe: str, parameters: Mapping[str,Any], frames: Mapping[str,pd.DataFrame]) -> pd.DataFrame:
    pieces=[]
    for symbol in INSTRUMENTS:
        execution=frames[symbol]
        if strategy=="T2":
            piece=OOST2(replace(T2Parameters(),**parameters)).run(execution,symbol,tick_size=FROZEN_TICK_SIZE)
            if "cost_R" not in piece and "cost_R_C1" in piece: piece["cost_R"]=piece.cost_R_C1
            if "net_R_C1" not in piece: piece["net_R_C1"]=piece.gross_R-piece.cost_R
        else:
            context=four_bar_context(execution)
            raw=Backtester(FixedRiskPortfolio(),cost_ticks_per_side=1,tick_size=FROZEN_TICK_SIZE,
                           allow_true_oos=True).run(
                T3MTFTrend(replace(T3Parameters(),**parameters)),symbol,execution,context).trades
            piece=_normalize_backtester(raw,"T3"); piece["net_R_C1"]=piece.gross_R-piece.cost_R
        if len(piece):
            piece=piece.copy(); piece["strategy_id"]=strategy
            piece["trade_id"]=[f"{strategy}-{timeframe}-{symbol}-{n:06d}" for n in range(1,len(piece)+1)]
        pieces.append(piece)
    trades=pd.concat(pieces,ignore_index=True)
    return trades.sort_values(["exit_time","symbol","trade_id"],kind="mergesort").reset_index(drop=True)

def summary(values: pd.Series) -> dict[str,Any]:
    s=stats(values.astype(float)); return {"total_trades":s["trades"],"PF":s["PF_R"],"expectancy":s["expectancy"],
        "net_R":s["net_R"],"max_drawdown":s["max_DD_R"],"win_rate":s["winrate"],
        "average_win":s["average_win_R"],"average_loss":s["average_loss_R"],"recovery_factor":s["recovery_factor"]}

def bootstrap(values: pd.Series) -> dict[str,Any]:
    x=np.asarray(values,dtype=float); means=np.random.default_rng(BOOTSTRAP_SEED).choice(x,size=(BOOTSTRAP_ITERATIONS,len(x)),replace=True).mean(1)
    q=np.quantile(means,[.025,.05,.5,.95,.975]); return {"iterations":BOOTSTRAP_ITERATIONS,"seed":BOOTSTRAP_SEED,"trades":len(x),
        "mean_R_2.5%":q[0],"mean_R_5%":q[1],"mean_R_50%":q[2],"mean_R_95%":q[3],"mean_R_97.5%":q[4],"probability_mean_R_gt_0":float((means>0).mean())}

def classify(overall: Mapping[str,Any], probability: float, observed: int, positive: int,
             instrument_gate: bool, direction_gate: bool, net_without_top5: float) -> str:
    passed=(overall["total_trades"]>=50 and overall["expectancy"]>0 and probability>=.95 and observed>0
            and positive/observed>=.60 and instrument_gate and direction_gate and net_without_top5>0)
    failed=overall["expectancy"]<=0 or probability<=.50
    return "PASS" if passed else ("FAIL" if failed else "BORDERLINE")

def _group(trades: pd.DataFrame,column: str,groups: list[Any]) -> list[dict[str,Any]]:
    return [{column:g,**summary(trades.loc[trades[column].eq(g),"net_R_C1"])} for g in groups]

def reports(item: Mapping[str,Any], trades: pd.DataFrame, target: Path) -> tuple[dict[str,Any],str]:
    trades=trades.copy(); trades["R_result"]=trades.net_R_C1; trades["holding_time"]=(pd.to_datetime(trades.exit_time,utc=True)-pd.to_datetime(trades.entry_time,utc=True)).astype(str)
    wanted=["trade_id","strategy_id","entry_time","exit_time","direction","symbol","entry_price","exit_price","R_result","net_R_C1","gross_R","cost_R","MAE_R","MFE_R","exit_reason","holding_time"]
    _csv(target/"trades.csv",trades[wanted])
    exits=pd.to_datetime(trades.exit_time,utc=True); years=sorted(exits.dt.year.unique()); quarters=exits.dt.to_period("Q").astype(str); months=exits.dt.to_period("M").astype(str)
    yearly=_group(trades.assign(year=exits.dt.year),"year",years); quarterly=_group(trades.assign(quarter=quarters),"quarter",sorted(quarters.unique())); monthly=_group(trades.assign(month=months),"month",sorted(months.unique()))
    instruments=_group(trades,"symbol",list(INSTRUMENTS)); directions=_group(trades,"direction",["LONG","SHORT"])
    for name,rows in (("yearly_report.csv",yearly),("quarterly_report.csv",quarterly),("monthly_report.csv",monthly),("instrument_report.csv",instruments),("direction_report.csv",directions)): _csv(target/name,rows)
    conc=concentration(trades.net_R_C1); _csv(target/"concentration_report.csv",[conc])
    dist=[]
    for group,mask in (("ALL",pd.Series(True,index=trades.index)),("WINNERS",trades.net_R_C1.gt(0)),("LOSERS",trades.net_R_C1.lt(0))):
        for metric in ("MAE_R","MFE_R"):
            x=pd.to_numeric(trades.loc[mask,metric],errors="coerce").dropna(); dist.append({"group":group,"metric":metric,"trades":len(x),"mean":x.mean(),"median":x.median(),"p05":x.quantile(.05),"p95":x.quantile(.95)})
    for reason,part in trades.groupby("exit_reason",sort=True):
        x=part.net_R_C1; dist.append({"group":f"EXIT:{reason}","metric":"R_result","trades":len(x),"mean":x.mean(),"median":x.median(),"p05":x.quantile(.05),"p95":x.quantile(.95)})
    h=(pd.to_datetime(trades.exit_time,utc=True)-pd.to_datetime(trades.entry_time,utc=True)).dt.total_seconds()/3600
    dist.append({"group":"ALL","metric":"holding_hours","trades":len(h),"mean":h.mean(),"median":h.median(),"p05":h.quantile(.05),"p95":h.quantile(.95)}); _csv(target/"mae_mfe_report.csv",dist)
    boot=bootstrap(trades.net_R_C1); _csv(target/"bootstrap_report.csv",[boot]); observed=sum(x["total_trades"]>0 for x in quarterly); positive=sum(x["total_trades"]>0 and x["expectancy"]>0 for x in quarterly)
    ig=all(x["expectancy"]>=0 for x in instruments if x["total_trades"]); dg=all(x["expectancy"]>=0 for x in directions if x["total_trades"]); overall=summary(trades.net_R_C1)
    verdict=classify(overall,boot["probability_mean_R_gt_0"],observed,positive,ig,dg,conc["net_R_without_top5"])
    metrics={"candidate_id":item["candidate_id"],"strategy":item["strategy"],"timeframe":item["timeframe"],"phase2_configuration_id":item["phase2_configuration_id"],"frozen_parameter_hash":item["parameter_hash"],"start_state":"FLAT","cost_ticks_per_side":1,"normalized_research_tick":FROZEN_TICK_SIZE,"aggregate":overall,"classification":verdict,"observed_quarters":observed,"positive_observed_quarters":positive,"positive_quarter_share":positive/observed,"bootstrap_probability_mean_R_gt_0":boot["probability_mean_R_gt_0"],"net_R_without_top5":conc["net_R_without_top5"],"instrument_gate":ig,"direction_gate":dg}; _json(target/"metrics.json",metrics)
    (target/"final_report.md").write_text(f"# {item['candidate_id']} — TRUE OOS\n\n**Classification: {verdict}**\n\nCold, FLAT, frozen one-shot evaluation. C1 only; no optimization, ranking, filtering, or replacement.\n",encoding="utf-8")
    return metrics,verdict

def artifact_sha256(root: Path) -> dict[str,str]:
    return {p.relative_to(root).as_posix():_sha(p) for p in sorted(root.rglob("*")) if p.is_file() and p.relative_to(root).as_posix()!="summary/manifest.json"}

def run(data_root: Path=DATA_ROOT,output: Path=OUTPUT_ROOT) -> dict[str,Any]:
    candidates,registry_sha=load_frozen_registry(REGISTRY_PATH)
    if [(x["strategy"],x["timeframe"]) for x in candidates]!=list(STUDIES): raise RuntimeError("CANDIDATE_ORDER_INVALID")
    for s in ("T2","T3"):
        path=Path(f"TradingSystemLab/strategies/trend/{'T2_Trend_Pullback' if s=='T2' else 'T3_MTF_Trend'}.py")
        if _sha(path)!=STRATEGY_HASHES[s]: raise RuntimeError("STRATEGY_SOURCE_HASH_MISMATCH")
    wf=json.loads((WALK_FORWARD_ROOT/"summary/manifest.json").read_text()); expected={"T2/M30":"WALK_FORWARD_BORDERLINE","T2/H1":"WALK_FORWARD_BORDERLINE","T3/M30":"WALK_FORWARD_BORDERLINE","T3/H1":"WALK_FORWARD_PASS"}
    if wf["verdicts"]!=expected: raise RuntimeError("ALL_PHASE4_IDENTITIES_MUST_CONTINUE")
    cache={}; coverage={}
    for tf in ("M30","H1"):
        coverage[tf]={}
        for symbol in INSTRUMENTS: cache[(symbol,tf)],coverage[tf][symbol]=load_true_oos(data_root,symbol,tf)
    output=Path(output); shutil.rmtree(output,ignore_errors=True); (output/"summary").mkdir(parents=True)
    classifications={}; comparison=[]; wf_rows=pd.read_csv(WALK_FORWARD_ROOT/"summary/comparison.csv").set_index("candidate_id")
    for item in candidates:
        s,tf=item["strategy"],item["timeframe"]; frozen=deepcopy(item["parameters"]); target=output/s/tf; target.mkdir(parents=True)
        trades=execute(s,tf,frozen,{x:cache[(x,tf)] for x in INSTRUMENTS})
        if stable_hash(frozen)!=item["parameter_hash"]: raise RuntimeError("FROZEN_PARAMETERS_MODIFIED")
        metrics,verdict=reports(item,trades,target); classifications[f"{s}/{tf}"]=verdict
        phase2=pd.read_csv(Path("TradingSystemLab/results/perpetual_v3/optimization")/s/tf/"results.csv").set_index("configuration_id").loc[item["phase2_configuration_id"]]
        first=min(pd.Timestamp(coverage[tf][x]["first_admitted_oos_close"]) for x in INSTRUMENTS); last=max(pd.Timestamp(coverage[tf][x]["last_admitted_oos_close"]) for x in INSTRUMENTS); days=(last-first).total_seconds()/86400+1
        manifest={"generation":"v3_perpetual","phase":"PHASE_5_TRUE_OOS","methodological_source":"original H1 Phase 5","strategy":s,"timeframe":tf,"candidate_id":item["candidate_id"],"phase2_configuration_id":item["phase2_configuration_id"],"frozen_parameter_hash":item["parameter_hash"],"full_execution_parameters":dict(replace(T2Parameters(),**frozen).__dict__) if s=="T2" else dict(replace(T3Parameters(),**frozen).__dict__),"frozen_strategy_source_hash":STRATEGY_HASHES[s],"freeze_reference_commit":FREEZE_COMMIT,"robustness_reference_commit":ROBUSTNESS_COMMIT,"walk_forward_reference_commit":WALK_FORWARD_COMMIT,"true_oos_start":"2025-01-01","actual_first_admitted_oos_close":first.isoformat(),"actual_last_admitted_oos_close":last.isoformat(),"admitted_oos_rows":sum(coverage[tf][x]["admitted_oos_rows"] for x in INSTRUMENTS),"coverage":coverage[tf],"oos_dataframe_sha256":hashlib.sha256("".join(coverage[tf][x]["admitted_frame_sha256"] for x in INSTRUMENTS).encode()).hexdigest(),"development_rows_admitted":0,"start_state":"FLAT","cold_start":True,"C1_only":True,"normalized_research_tick":FROZEN_TICK_SIZE,"parameters_frozen":True,"optimization":False,"ranking":False,"candidate_replacement":False,"development_state_reused":False,"phase7_mtf_research":False,"execution_context":"none" if s=="T2" else f"four completed non-overlapping {tf} bars; local-day reset","classification":verdict}; _json(target/"manifest.json",manifest)
        w=wf_rows.loc[item["candidate_id"]]; a=metrics["aggregate"]; comparison.append({"candidate_id":item["candidate_id"],"strategy":s,"timeframe":tf,"phase3_robustness_classification":w.robustness_classification,"phase4_walk_forward_verdict":w.walk_forward_verdict,"phase2_PF":phase2.PF_C1,"phase4_PF":w.PF,"true_oos_PF":a["PF"],"PF_decay_phase2_to_oos":a["PF"]-phase2.PF_C1,"phase2_expectancy":phase2.expectancy_C1,"phase4_expectancy":w.expectancy,"true_oos_expectancy":a["expectancy"],"expectancy_decay_phase2_to_oos":a["expectancy"]-phase2.expectancy_C1,"phase2_max_drawdown":phase2.max_DD_C1,"phase4_max_drawdown":w.max_drawdown,"true_oos_max_drawdown":a["max_drawdown"],"drawdown_expansion_vs_phase4":abs(a["max_drawdown"])-abs(w.max_drawdown),"phase2_trade_frequency":phase2.trades/5,"phase4_forward_trades":w.trades,"true_oos_annualized_trade_frequency":a["total_trades"]/days*365.2425,"oos_observation_days":days,"true_oos_classification":verdict})
    _csv(output/"summary/comparison.csv",comparison)
    lines=["# TradingSystemLab v3 Perpetual — Phase 5 TRUE OOS","","Canonical order; evidence only (no ranking or portfolio selection).",""]+[f"- {r['strategy']}/{r['timeframe']} — Phase 3: {r['phase3_robustness_classification']}; Phase 4: {r['phase4_walk_forward_verdict']}; Phase 5: **{r['true_oos_classification']}**; trades {next(x['aggregate']['total_trades'] for x in [json.loads((output/r['strategy']/r['timeframe']/ 'metrics.json').read_text())])}; PF {r['true_oos_PF']}; expectancy {r['true_oos_expectancy']}; Net R {next(x['aggregate']['net_R'] for x in [json.loads((output/r['strategy']/r['timeframe']/ 'metrics.json').read_text())])}; max DD {r['true_oos_max_drawdown']}" for r in comparison]
    lines += ["","TRUE OOS was opened only in Phase 5. All candidates were frozen before OOS; none was replaced.","No optimization or ranking occurred. Every study started cold and FLAT; Development state was not reused.","","PHASE_5_TRUE_OOS_VALIDATION_COMPLETE"]
    (output/"summary/Final_TRUE_OOS_Report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    root={"generation":"v3_perpetual","phase":"PHASE_5_TRUE_OOS","status":"PENDING_AUDIT","methodological_source":"original H1 Phase 5","candidate_count":4,"candidate_ids":[x["candidate_id"] for x in candidates],"candidate_registry_sha256":registry_sha,"strategies":["T2","T3"],"timeframes":["M30","H1"],"instruments":list(INSTRUMENTS),"true_oos_start":"2025-01-01","coverage":coverage,"development_rows_admitted":0,"cold_start":True,"start_state":"FLAT","C1_only":True,"normalized_research_tick":FROZEN_TICK_SIZE,"parameters_frozen":True,"optimization":False,"ranking":False,"candidate_replacement":False,"bootstrap":{"iterations":BOOTSTRAP_ITERATIONS,"seed":BOOTSTRAP_SEED,"diagnostic_only":True},"classifications":classifications,"strategy_code_hashes":STRATEGY_HASHES,"deterministic":True,"second_complete_execution_compared":False,"walk_forward_reference_commit":WALK_FORWARD_COMMIT}; _json(output/"summary/manifest.json",root); root["artifact_sha256"]=artifact_sha256(output); _json(output/"summary/manifest.json",root); return root

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--data-root",type=Path,default=DATA_ROOT); p.add_argument("--output",type=Path,default=OUTPUT_ROOT); a=p.parse_args(); print(json.dumps(run(a.data_root,a.output),sort_keys=True))
if __name__=="__main__": main()
