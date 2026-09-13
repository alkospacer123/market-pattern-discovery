"""Deterministic, descriptive diagnostics for frozen T3 forward trades.

This module never creates signals.  It treats the Sprint 6 walk-forward C1
ledger as immutable evidence and joins only closed, pre-2025 indicator states.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from .run_t3_walk_forward import OOS_START, SYMBOLS, _stats, _streak, load_development_data, load_frozen
from .strategies.trend.T3_MTF_Trend import T3MTFTrend

SEED = 20260913
ITERATIONS = 10_000
SOURCE = Path("TradingSystemLab/results/T3_walk_forward")
DEFAULT_OUTPUT = Path("TradingSystemLab/results/T3_walk_forward_diagnostics")


def _csv(frame: pd.DataFrame, path: Path) -> None:
    out = frame.copy()
    for col in ("entry_time", "feature_time", "signal_time"):
        if col in out:
            out[col] = pd.to_datetime(out[col]).map(lambda x: x.isoformat())
    out.to_csv(path, index=False, lineterminator="\n", float_format="%.12g")


def _metric(frame: pd.DataFrame) -> dict:
    s = _stats(frame)
    v = frame.net_R
    wins, losses = v[v > 0], v[v <= 0]
    return {"trades": len(v), "wins": len(wins), "losses": len(losses),
            "PF": s["PF"], "expectancy_R": s["expectancy"], "net_R": s["net_R"],
            "max_DD_R": s["max_DD_R"], "winrate": s["winrate"],
            "median_R": v.median() if len(v) else None,
            "average_win_R": wins.mean() if len(wins) else None,
            "average_loss_R": losses.mean() if len(losses) else None}


def _exit_reason(row: pd.Series) -> str:
    if row.gross_R < -1.000000001:
        return "GAP_STOP"
    if abs(row.exit_price - row.initial_stop) <= 1e-8 * max(1, abs(row.initial_stop)):
        return "INITIAL_STOP"
    return "ATR_TRAILING_STOP"


def _features(trades: pd.DataFrame, data: dict, parameters) -> pd.DataFrame:
    rows = []
    for symbol in SYMBOLS:
        low, high = T3MTFTrend(parameters).calculate_indicators(*data[symbol])
        part = trades[trades.symbol == symbol]
        for trade in part.itertuples():
            timestamp = pd.Timestamp(trade.entry_time)
            if timestamp >= OOS_START or timestamp not in low.index:
                raise AssertionError("entry is not a pre-OOS closed H1 candle")
            hpos = high.index.searchsorted(timestamp, side="right") - 1
            if hpos < 0 or high.index[hpos] > timestamp:
                raise AssertionError("no causally available closed H4 state")
            lo, hi = low.loc[timestamp], high.iloc[hpos]
            slope = float(hi.EMA100Slope)
            distance = float(lo.Close-lo.PriorHigh if trade.direction == "LONG" else lo.PriorLow-lo.Close)
            initial_risk = abs(float(trade.entry_price)-float(trade.initial_stop))
            rows.append({"trade_id":trade.trade_id,"fold_id":trade.fold_id,"symbol":symbol,
                "direction":trade.direction,"entry_time":timestamp,"signal_time":timestamp,
                "feature_time":high.index[hpos],"H4_close":hi.Close,"EMA100":hi.EMA100,
                "EMA100_slope":slope,"normalized_EMA_slope":slope/hi.ATR,"ADX14":hi.ADX,
                "ATR14":hi.ATR,"ATR_mean20":hi.ATRMean20,"ATR_ratio":hi.ATR/hi.ATRMean20,
                "Donchian_upper":lo.PriorHigh,"Donchian_lower":lo.PriorLow,
                "breakout_distance_points":distance,"breakout_distance_ATR":distance/lo.ATR,
                "initial_risk_R":1,"initial_risk_points":initial_risk,"entry_price":trade.entry_price})
    result = pd.DataFrame(rows).sort_values(["entry_time","trade_id"], kind="mergesort").reset_index(drop=True)
    if list(result.trade_id) != list(trades.trade_id):
        raise AssertionError("feature join changed trade identities")
    if not (result.feature_time <= result.signal_time).all():
        raise AssertionError("future H4 feature")
    return result


def bootstrap(values: np.ndarray, folds: list[np.ndarray], seed: int = SEED,
              iterations: int = ITERATIONS) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    iid = rng.choice(values, (iterations, len(values)), replace=True).mean(axis=1)
    chosen = rng.integers(0, len(folds), (iterations, len(folds)))
    block = np.array([np.concatenate([folds[j] for j in row]).mean() for row in chosen])
    records=[]
    for method, sample, warning in (("TRADE_IID_BOOTSTRAP_DIAGNOSTIC_ONLY",iid,"TEMPORAL_DEPENDENCY_IGNORED"),
                                    ("FOLD_BLOCK_BOOTSTRAP_DIAGNOSTIC_ONLY",block,"VERY_LOW_BLOCK_COUNT")):
        records.append({"method":method,"seed":seed,"iterations":iterations,"sample_count":len(values),
            "p2_5":np.percentile(sample,2.5),"p5":np.percentile(sample,5),"median":np.median(sample),
            "p95":np.percentile(sample,95),"p97_5":np.percentile(sample,97.5),
            "probability_mean_R_gt_0":np.mean(sample>0),"warning":warning})
    return pd.DataFrame(records)


def _simple_svg(path: Path, title: str, labels: list[str], values: list[float]) -> None:
    finite=[v for v in values if pd.notna(v)]; bound=max([abs(v) for v in finite]+[1]); width=760
    bars=[]
    for i,(label,value) in enumerate(zip(labels,values)):
        y=55+i*35; x0=390; x=x0+(value/bound)*320
        bars.append(f'<text x="10" y="{y+14}">{label}</text><line x1="{x0}" y1="{y+8}" x2="{x:.1f}" y2="{y+8}" stroke="#2563eb" stroke-width="12"/><text x="700" y="{y+14}">{value:.4f}</text>')
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'+f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{80+35*len(values)}"><rect width="100%" height="100%" fill="white"/><text x="10" y="25" font-weight="bold">{title}</text><line x1="390" y1="40" x2="390" y2="{65+35*len(values)}" stroke="#555"/>'+''.join(bars)+'</svg>\n')


def discover_pre2023(data_root: Path) -> dict:
    found={s:[] for s in SYMBOLS}
    for symbol in SYMBOLS:
        for path in sorted(data_root.rglob(f"{symbol}_*.csv")):
            # Metadata-only: filenames are inspected; market contents are never opened.
            if any(str(year) in path.name for year in range(1900, 2023)):
                found[symbol].append(str(path))
    return {"discovery":"FILENAME_METADATA_ONLY","searched_root":str(data_root),
            "timestamp_requirement":"pre-2023; candidates not loaded or used", "files":found,
            "pre2023_candidates_found":any(found.values())}


def run(data_root: Path, output: Path = DEFAULT_OUTPUT, source: Path = SOURCE) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    trades=pd.read_csv(source/"stitched_forward_trades_C1.csv")
    trades.entry_time=pd.to_datetime(trades.entry_time); trades.exit_time=pd.to_datetime(trades.exit_time)
    if len(trades)!=39 or trades.trade_id.duplicated().any() or (trades.entry_time.dt.year>=2025).any():
        raise AssertionError("frozen 39-trade pre-OOS ledger invariant failed")
    trades["diagnostic_exit_reason"]=trades.apply(_exit_reason,axis=1)
    parameters,_=load_frozen(Path("TradingSystemLab/results/T3_parameter_robustness/frozen_baseline.json"))
    features=_features(trades,load_development_data(data_root),parameters); _csv(features,output/"entry_regime_features.csv")

    folds=[]
    for fid,part in trades.groupby("fold_id",sort=True):
        m=_metric(part); folds.append({"fold_id":fid,**m,"gross_R":part.gross_R.sum(),"cost_R":part.cost_R.sum(),
            "PF_C1":m["PF"],"expectancy_C1":m["expectancy_R"],"best_trade_R":part.net_R.max(),"worst_trade_R":part.net_R.min(),
            "max_losing_streak":_streak(part.net_R,False),"LONG_trades":(part.direction=="LONG").sum(),
            "SHORT_trades":(part.direction=="SHORT").sum(),"Si_trades":(part.symbol=="Si").sum(),"CNY_trades":(part.symbol=="CNY").sum(),
            "median_holding_bars":part.bars_held.median(),"mean_holding_bars":part.bars_held.mean(),
            "initial_stop_exits":(part.diagnostic_exit_reason=="INITIAL_STOP").sum(),"trailing_exits":(part.diagnostic_exit_reason=="ATR_TRAILING_STOP").sum(),"gap_exits":(part.diagnostic_exit_reason=="GAP_STOP").sum()})
    fold_df=pd.DataFrame(folds); _csv(fold_df,output/"fold_decomposition.csv")
    rows=[]
    for fid in sorted(trades.fold_id.unique()):
      for symbol in SYMBOLS:
       for direction in ("LONG","SHORT"):
        part=trades[(trades.fold_id==fid)&(trades.symbol==symbol)&(trades.direction==direction)]; m=_metric(part)
        rows.append({"fold_id":fid,"symbol":symbol,"direction":direction,**m,"average_win":m["average_win_R"],"average_loss":m["average_loss_R"],"sample_warning":"LOW_SAMPLE" if len(part)<10 else ""})
    fsd=pd.DataFrame(rows); _csv(fsd,output/"fold_symbol_direction.csv")

    loo=[]
    for label,part in [("ALL_FOLDS",trades)]+[(f"WITHOUT_{f}",trades[trades.fold_id!=f]) for f in sorted(trades.fold_id.unique())]:
        m=_metric(part); loo.append({"subset":label,"trades":m["trades"],"PF_C1":m["PF"],"expectancy_C1":m["expectancy_R"],"net_R_C1":m["net_R"],"max_DD_R":m["max_DD_R"],"winrate":m["winrate"]})
    _csv(pd.DataFrame(loo),output/"leave_one_fold_out.csv")

    sorted_wins=trades.loc[trades.net_R>0].sort_values("net_R",ascending=False); positive=sorted_wins.net_R.sum()
    conc=[]
    for n in (1,3,5,10): conc.append({"top_n":n,"share_positive_R":sorted_wins.head(n).net_R.sum()/positive})
    _csv(pd.DataFrame(conc),output/"profit_concentration.csv")
    tc={f"top_{n}_share_positive_R":sorted_wins.head(n).net_R.sum()/positive for n in (1,3,5,10)}
    for n,label in ((1,"best_trade"),(3,"top_3"),(5,"top_5")):
        omit=trades.drop(sorted_wins.head(n).index); m=_metric(omit); tc.update({f"net_R_without_{label}":m["net_R"],f"PF_without_{label}":m["PF"],f"expectancy_without_{label}":m["expectancy_R"]})
    _csv(pd.DataFrame([tc]),output/"trade_concentration.csv")

    ld=[]
    for direction in ("LONG","SHORT"):
        part=trades[trades.direction==direction]; m=_metric(part); wins=part[part.net_R>0]
        ld.append({"direction":direction,**m,"mean_MAE_R":part.MAE_R.mean(),"median_MAE_R":part.MAE_R.median(),"mean_MFE_R":part.MFE_R.mean(),"median_MFE_R":part.MFE_R.median(),"median_holding_bars":part.bars_held.median(),"initial_stop_exit_share":(part.diagnostic_exit_reason=="INITIAL_STOP").mean(),"trailing_exit_share":(part.diagnostic_exit_reason=="ATR_TRAILING_STOP").mean(),"profit_concentration_top3":wins.nlargest(3,"net_R").net_R.sum()/wins.net_R.sum()})
    _csv(pd.DataFrame(ld),output/"long_short_analysis.csv")

    ia=[]
    for symbol in SYMBOLS:
      for fid in ("ALL",*sorted(trades.fold_id.unique())):
        part=trades[(trades.symbol==symbol)&((trades.fold_id==fid) if fid!="ALL" else True)]; m=_metric(part)
        ia.append({"symbol":symbol,"fold_id":fid,**m,"LONG_expectancy":part.loc[part.direction=="LONG","net_R"].mean(),"SHORT_expectancy":part.loc[part.direction=="SHORT","net_R"].mean(),"median_MAE":part.MAE_R.median(),"median_MFE":part.MFE_R.median()})
    _csv(pd.DataFrame(ia),output/"instrument_analysis.csv")
    for filename,column,groups in (("direction_dependency.csv","direction",("LONG","SHORT")),("instrument_dependency.csv","symbol",SYMBOLS)):
        rr=[]
        for label,part in [("ALL",trades)]+[(f"{x.upper()}_ONLY",trades[trades[column]==x]) for x in groups]:
            m=_metric(part); rr.append({"subset":label,"trades":m["trades"],"PF":m["PF"],"expectancy":m["expectancy_R"],"net_R":m["net_R"],"max_DD":m["max_DD_R"]})
        _csv(pd.DataFrame(rr),output/filename)

    ht=[]; mm=[]
    for fid,base in [(f,trades[trades.fold_id==f]) for f in sorted(trades.fold_id.unique())]+[("ALL",trades)]:
      for group,part in (("all",base),("winners",base[base.net_R>0]),("losers",base[base.net_R<=0])):
        ht.append({"fold_id":fid,"group":group,"mean_bars":part.bars_held.mean(),"median_bars":part.bars_held.median(),"p75":part.bars_held.quantile(.75),"p90":part.bars_held.quantile(.9),"max":part.bars_held.max()})
        if fid!="ALL": mm.append({"fold_id":fid,"group":group,**{f"{stat}_{kind}_R":getattr(part[kind+"_R"],stat)() for kind in ("MAE","MFE") for stat in ("mean","median")},**{f"p{int(q*100)}_{kind}_R":part[kind+"_R"].quantile(q) for kind in ("MAE","MFE") for q in (.75,.9)}})
    _csv(pd.DataFrame(ht),output/"holding_time.csv"); _csv(pd.DataFrame(mm),output/"mae_mfe_by_fold.csv")
    md=[]
    for direction,part in trades.groupby("direction",sort=True):
        md.append({"direction":direction,"trades":len(part),"mean_MAE_R":part.MAE_R.mean(),"median_MAE_R":part.MAE_R.median(),"p75_MAE_R":part.MAE_R.quantile(.75),"p90_MAE_R":part.MAE_R.quantile(.9),"mean_MFE_R":part.MFE_R.mean(),"median_MFE_R":part.MFE_R.median(),"p75_MFE_R":part.MFE_R.quantile(.75),"p90_MFE_R":part.MFE_R.quantile(.9)})
    _csv(pd.DataFrame(md),output/"mae_mfe_by_direction.csv")
    er=[]
    for fid,base in [(f,trades[trades.fold_id==f]) for f in sorted(trades.fold_id.unique())]+[("ALL",trades)]:
      for reason,part in base.groupby("diagnostic_exit_reason",sort=True): er.append({"fold_id":fid,"exit_reason":reason,"trades":len(part),"average_R":part.net_R.mean(),"expectancy":part.net_R.mean(),"net_R":part.net_R.sum(),"average_MFE":part.MFE_R.mean(),"average_MAE":part.MAE_R.mean()})
    _csv(pd.DataFrame(er),output/"exit_reason.csv")
    _csv(trades[["trade_id","fold_id","symbol","direction","entry_time","net_R","MAE_R","MFE_R","bars_held","diagnostic_exit_reason"]],output/"trade_distribution.csv")

    joined=features.merge(trades[["trade_id","net_R"]],on="trade_id",validate="one_to_one"); regime=[]
    for fid,base in joined.groupby("fold_id",sort=True):
      for group,part in (("all",base),("winners",base[base.net_R>0]),("losers",base[base.net_R<=0])):
        row={"fold_id":fid,"group":group,"trades":len(part)}
        for col in ("ADX14","normalized_EMA_slope","ATR_ratio","breakout_distance_ATR"): row.update({f"median_{col}":part[col].median(),f"mean_{col}":part[col].mean()})
        regime.append(row)
    _csv(pd.DataFrame(regime),output/"fold_regime_summary.csv")
    uncertainty=bootstrap(trades.net_R.to_numpy(),[p.net_R.to_numpy() for _,p in trades.groupby("fold_id",sort=True)]); _csv(uncertainty,output/"uncertainty_report.csv")

    pre=discover_pre2023(data_root); (output/"available_pre2023_data.json").write_text(json.dumps(pre,indent=2,sort_keys=True)+"\n")
    sample={"forward_folds":3,"forward_trades":39,"trades_per_fold_mean":13.0,"trades_per_fold_median":13.0,"months_tested":9,"forward_calendar_years":1,"estimated_trades_per_year":39.0,"trades_required_for_PASS":50,"additional_trades_needed_for_PASS":11,"folds_required_minimum":8,"folds_available":3}
    (output/"sample_size_report.json").write_text(json.dumps(sample,indent=2,sort_keys=True)+"\n")
    classification="MIXED_EVIDENCE"
    source_hash=hashlib.sha256((source/"manifest.json").read_bytes()).hexdigest()
    manifest={"strategy_id":T3MTFTrend.name,"source_walk_forward_manifest":str(source/"manifest.json"),"source_manifest_sha256":source_hash,"folds":["WF01","WF02","WF03"],"forward_trades":39,"cost_scenario":"C1","bootstrap_seed":SEED,"bootstrap_iterations":ITERATIONS,"true_oos_blocked":True,"diagnostic_classification":classification}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    dvals=[trades[(trades.fold_id==f)&(trades.direction==d)].net_R.mean() for f in ("WF01","WF02","WF03") for d in ("LONG","SHORT")]
    ivals=[trades[(trades.fold_id==f)&(trades.symbol==s)].net_R.mean() for f in ("WF01","WF02","WF03") for s in SYMBOLS]
    _simple_svg(output/"fold_net_R.svg","Fold net R",list(fold_df.fold_id),list(fold_df.net_R)); _simple_svg(output/"fold_expectancy.svg","Fold expectancy",list(fold_df.fold_id),list(fold_df.expectancy_R))
    _simple_svg(output/"long_short_by_fold.svg","Direction expectancy by fold",[f"{f} {d}" for f in ("WF01","WF02","WF03") for d in ("LONG","SHORT")],dvals)
    _simple_svg(output/"instrument_by_fold.svg","Instrument expectancy by fold",[f"{f} {s}" for f in ("WF01","WF02","WF03") for s in SYMBOLS],ivals)
    feature_values=[]; feature_labels=[]
    for fid in ("WF01","WF02","WF03"):
      for col in ("ADX14","normalized_EMA_slope","ATR_ratio","breakout_distance_ATR"):
        feature_labels.append(f"{fid} {col}"); feature_values.append(features.loc[features.fold_id==fid,col].median())
    _simple_svg(output/"entry_feature_distributions.svg","Entry feature medians (descriptive; unlike scales)",feature_labels,feature_values)
    plan="""# T3 Intel Extended Pre-OOS Validation Plan\n\nAcquire read-only, quality-checked Si and CNY H1 history before 2023. Keep frozen T3, C1 costs, causal closed-H4 alignment, and the predeclared walk-forward design. Do not optimize parameters or inspect TRUE OOS 2025+. Target, where history permits: at least 100 forward trades, 8 complete folds, and 3 calendar forward years. Repeat fold, instrument/direction, concentration, MAE/MFE, exit, regime-distribution, leave-one-out, and uncertainty diagnostics. These are target evidence levels, not permission to relax validity rules.\n"""
    (output/"intel_validation_plan.md").write_text(plan)
    iid=uncertainty.iloc[0]; without2=pd.DataFrame(loo).set_index("subset").loc["WITHOUT_WF02"]
    report=f"""# T3 Walk-Forward Borderline Diagnostics\n\n## Scope and invariants\nFrozen T3 and the existing 39 C1 TEST trades were analyzed unchanged. No signal, parameter, schedule, filter, or exit was modified. TRUE OOS 2025+ stayed closed. Common development coverage is 2023-01-03 through 2024-12-31; a 12-month initial train leaves only 2024 forward evidence (3 folds, 39 trades).\n\n## Classification\n**{classification}** — sample limitation is fundamental, while material fold/direction dependence remains unresolved. Two of three folds and both instruments are positive in aggregate, but removing WF02 leaves {without2.net_R_C1:.6f} R ({without2.expectancy_C1:.6f} R/trade). This is descriptive and is not a basis for selecting folds or SHORT-only trading.\n\nWF01 contains few winners and weakness in both instruments; LONG is weak in WF01 but positive in WF03, while SHORT is strong in WF02 and weak in WF01/WF03. Thus the current sample shows temporal/directional dependence, but not a stable defect demonstrated across adequately sized independent subgroups. All fold×symbol×direction cells are explicitly LOW_SAMPLE.\n\nEntry regime summaries describe distributions only and must not be read as threshold proposals. Exit reasons are reconstructed diagnostically: an execution at the initial stop is `INITIAL_STOP`, worse is `GAP_STOP`, otherwise `ATR_TRAILING_STOP`.\n\nThe iid interval is [{iid.p2_5:.6f}, {iid.p97_5:.6f}] R with P(mean>0)={iid.probability_mean_R_gt_0:.6f}; it is **TRADE_IID_BOOTSTRAP_DIAGNOSTIC_ONLY**, ignores temporal dependence, and is not a significance test. Fold-block output has `VERY_LOW_BLOCK_COUNT`. No p-value is reported for 2 positive / 1 negative folds.\n\n## Main reason and roadmap\nWALK_FORWARD_BORDERLINE is primarily constrained by only 39 trades, 3 folds, and one forward calendar year, with meaningful but inconclusive dependence on WF02/direction. **NEXT: T3 Intel Extended Pre-OOS Validation**, solely to resolve ambiguity without optimization; TRUE OOS remains locked.\n"""
    (output/"final_report.md").write_text(report); (output/"summary.md").write_text("# Summary\n\nDiagnostic classification: **MIXED_EVIDENCE**. See `final_report.md`; no strategy change is proposed.\n")
    return manifest


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--data-root",type=Path,required=True); parser.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); args=parser.parse_args()
    print(json.dumps(run(args.data_root,args.output),indent=2))
