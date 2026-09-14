"""Phase 3.2 conservative bounded designs and deterministic reporting.

The design is deliberately not the Cartesian grid.  It evaluates the frozen
baseline and every one-factor level.  This conservative OAT design provides
direct local neighbors without parameter mining.
"""
from __future__ import annotations

from dataclasses import asdict, replace
import json
import multiprocessing as mp
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from ..core.backtester import Backtester
from ..core.data_loader import DataLoader
from ..core.portfolio import FixedRiskPortfolio
from ..core.unified_metrics import concentration, finite, stats
from ..strategies.range.R1_Bollinger_False_Breakout import R1BollingerFalseBreakout, R1Parameters
from ..strategies.range.R2_Liquidity_Sweep import R2LiquiditySweep, R2Parameters
from ..strategies.range.R3_Round_Level_Rejection import R3RoundLevelRejection, R3Parameters
from ..strategies.trend.T1_BBW_Donchian import T1BBWDonchian, T1Parameters
from ..strategies.trend.T2_Trend_Pullback import T2Parameters, T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters
from .experiment import stable_hash
from .parameter_space import ParameterSpace
from .runner import DEFAULT_SEARCH_SPACE_LIMIT, SearchSpaceTooLarge
from .validation import reject_true_oos

SCENARIOS = {"C0": 0.0, "C0.5": .5, "C1": 1.0, "C2": 2.0}

SPACES: dict[str, dict[str, tuple[str, list[Any]]]] = {
    "T1": {"donchian_period": ("int", [10,15,20,25,30,40,50]), "bbw_percentile_window": ("int", [70,80,90,100]), "bb_period": ("int", [15,20,25]), "ema_period": ("int", [50,100,150]), "stop_atr": ("float", [1.5,2,2.5,3]), "trail_atr": ("float", [2,3,4])},
    "T2": {"ema_fast": ("int", [15,20,25,30]), "ema_trend": ("int", [40,50,60]), "ema_slow": ("int", [150,200,250]), "adx_threshold": ("float", [15,20,25,30]), "impulse_distance_atr": ("float", [.3,.5,.7]), "confirmation_window": ("int", [2,3,4]), "max_initial_stop_atr": ("float", [2,2.5,3]), "trailing_atr": ("float", [2,3,4])},
    "T3": {"ema_period": ("int", [50,75,100,150,200]), "adx_threshold": ("float", [15,20,25,30]), "breakout_period": ("int", [10,20,30,40,55]), "atr_average_period": ("int", [10,20,30,50]), "stop_atr": ("float", [1.5,2,2.5,3]), "trail_atr": ("float", [2,2.5,3,3.5,4])},
    "R1": {"bollinger_period": ("int", [15,20,25]), "bollinger_std": ("float", [1.5,2,2.5]), "bbw_percentile_threshold": ("float", [30,40,50,60]), "adx_range_max": ("float", [15,20,25]), "max_initial_stop_atr": ("float", [1.5,2,2.5]), "max_holding_bars": ("int", [5,10,15])},
    "R2": {"range_lookback_h1": ("int", [10,20,30]), "adx_range_max": ("float", [20,25,30]), "ema_slope_max_atr": ("float", [.25,.35,.5]), "minimum_sweep_atr": ("float", [.05,.1]), "maximum_sweep_atr": ("float", [.75,1]), "max_initial_stop_atr": ("float", [1,1.5]), "max_holding_bars_m15": ("int", [12,16,20])},
    "R3": {"minimum_penetration_atr": ("float", [.05,.1]), "maximum_penetration_atr": ("float", [.5,.75,1]), "minimum_close_distance_atr": ("float", [.05,.1]), "max_initial_stop_atr": ("float", [1,1.25]), "target_fraction_of_step": ("float", [.25,.5,.75]), "max_holding_bars_m15": ("int", [8,12,16])},
}
PARAMETERS = {"T1": T1Parameters(), "T2": T2Parameters(), "T3": T3Parameters(), "R1": R1Parameters(), "R2": R2Parameters(), "R3": R3Parameters()}
STRATEGY_IDS = {"T1": T1BBWDonchian.name, "T2": T2TrendPullback.name, "T3": T3MTFTrend.name, "R1": R1BollingerFalseBreakout.name, "R2": R2LiquiditySweep.name, "R3": R3RoundLevelRejection.name}


def parameter_space(key: str) -> ParameterSpace:
    return ParameterSpace({n: {"type": t, "values": v} for n, (t, v) in SPACES[key].items()})


def bounded_design(key: str) -> list[dict[str, Any]]:
    """Return baseline plus every one-factor perturbation, sorted."""
    baseline = {name: getattr(PARAMETERS[key], name) for name in SPACES[key]}
    candidates = {stable_hash(baseline): baseline}
    deviations = {n: [v for v in spec[1] if v != baseline[n]] for n, spec in SPACES[key].items()}
    names = sorted(deviations)
    for name in names:
        for value in deviations[name]:
            row = {**baseline, name: value}; candidates[stable_hash(row)] = row
    rows = sorted(candidates.values(), key=lambda r: json.dumps(r, sort_keys=True, separators=(",", ":")))
    if len(rows) > DEFAULT_SEARCH_SPACE_LIMIT:
        raise SearchSpaceTooLarge(f"SEARCH_SPACE_TOO_LARGE: {len(rows)} > {DEFAULT_SEARCH_SPACE_LIMIT}")
    return rows


def experiment_definition(key: str) -> dict[str, Any]:
    space, design = parameter_space(key), bounded_design(key)
    body = {"phase": "3.2", "strategy_key": key, "strategy_id": STRATEGY_IDS[key],
            "frozen_baseline": asdict(PARAMETERS[key]), "parameter_space": space.as_dict(),
            "design": "BASELINE_PLUS_ONE_FACTOR_AT_A_TIME", "tested_configurations": len(design),
            "cartesian_space_size": space.size, "search_space_limit": DEFAULT_SEARCH_SPACE_LIMIT,
            "cost_scenarios_ticks_per_side": SCENARIOS, "development_period": ["2023-01-01", "2024-12-31"],
            "symbols": ["Si", "CNY"], "true_oos_blocked": True, "seed": 0}
    body["experiment_id"] = "phase32-" + stable_hash(body)[:20]
    return body


def _load(root: Path, symbol: str, timeframe: str) -> pd.DataFrame:
    paths = [p for year in (2023, 2024) for p in sorted((root / "2026" / symbol).glob(f"{symbol}_{timeframe}_{year}_Q*.csv"))]
    if not paths: raise FileNotFoundError(f"no development {timeframe} data for {symbol}")
    return DataLoader().close_index(DataLoader().load_csv(paths), "1h" if timeframe == "H1" else "15min")


def load_development_data(root: Path) -> dict[tuple[str, str], pd.DataFrame]:
    result = {(s, tf): _load(root, s, tf) for s in ("Si", "CNY") for tf in ("H1", "M15")}
    for frame in result.values(): reject_true_oos(frame.index)
    return result


def _normalize_backtester(frame: pd.DataFrame, key: str) -> pd.DataFrame:
    if frame.empty: return pd.DataFrame(columns=["trade_id","strategy_id","symbol","direction","entry_time","exit_time","gross_R","initial_risk_ticks"])
    out = frame.copy(); out["strategy_id"] = STRATEGY_IDS[key]
    if "trade_id" not in out:
        out["trade_id"] = [f"{symbol}-{i+1:06d}" for symbol, i in zip(out.symbol, out.groupby("symbol",sort=False).cumcount())]
    if "initial_risk" in out:
        out["initial_risk_points"] = out.initial_risk.abs()
    else:
        # Legacy T3 rows retain normalized R and points but not their entry stop.
        # Their ratio exactly reconstructs frozen initial risk without future data.
        out["initial_risk_points"] = (out.profit_points / out.profit_R).abs()
    out["initial_risk_ticks"] = out.initial_risk_points / .001
    out["gross_R"] = out.profit_R
    return out


def execute(key: str, config: Mapping[str, Any], data: Mapping[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    params = replace(PARAMETERS[key], **config); pieces=[]
    for symbol in ("Si", "CNY"):
        if key in ("T1", "T3"):
            strategy = T1BBWDonchian(params) if key == "T1" else T3MTFTrend(params)
            h1=data[(symbol,"H1")]; h4=h1 if key == "T1" else DataLoader.h4_from_h1(h1)
            raw=Backtester(FixedRiskPortfolio(),commission_per_unit=0,slippage_points=0).run(strategy,symbol,h1,h4).trades
            pieces.append(_normalize_backtester(raw,key))
        elif key == "T2": pieces.append(T2TrendPullback(params).run(data[(symbol,"H1")],symbol,tick_size=.001))
        elif key == "R1": pieces.append(R1BollingerFalseBreakout(params).run(data[(symbol,"H1")],symbol,tick_size=.001))
        elif key == "R2": pieces.append(R2LiquiditySweep(params).run(data[(symbol,"H1")],data[(symbol,"M15")],symbol,tick_size=.001))
        else: pieces.append(R3RoundLevelRejection(params).run(data[(symbol,"M15")],symbol,round_level_step=.10 if symbol=="Si" else .05,tick_size=.001))
    frame=pd.concat(pieces,ignore_index=True)
    if len(frame): frame=frame.sort_values(["exit_time","symbol","trade_id"],kind="mergesort").reset_index(drop=True)
    reject_true_oos(frame.entry_time if len(frame) else []); reject_true_oos(frame.exit_time if len(frame) else [])
    return frame


def _metric_row(config_id: str, frame: pd.DataFrame) -> dict[str, Any]:
    gross=frame.gross_R.astype(float) if len(frame) else pd.Series(dtype=float)
    risk=frame.initial_risk_ticks.astype(float) if len(frame) else pd.Series(dtype=float)
    row={"configuration_id":config_id,"trades":len(frame),"trade_count":len(frame)}
    for scenario,ticks in SCENARIOS.items():
        values=gross-2*ticks/risk; s=stats(values); suffix=scenario.replace(".","")
        row.update({f"PF_{suffix}":s["PF_R"],f"expectancy_{suffix}":s["expectancy"],f"net_R_{suffix}":s["net_R"],f"max_DD_{suffix}":s["max_DD_R"],f"recovery_factor_{suffix}":s["recovery_factor"],f"win_rate_{suffix}":s["winrate"]})
    net=gross-2/risk
    for symbol in ("Si","CNY"):
        s=stats(net[frame.symbol.eq(symbol)]); row.update({f"{symbol}_trades":s["trades"],f"{symbol}_expectancy_C1":s["expectancy"]})
    years=pd.to_datetime(frame.exit_time,utc=True).dt.year if len(frame) else pd.Series(dtype=int)
    for year in (2023,2024):
        s=stats(net[years.eq(year)]); row.update({f"Y{year}_trades":s["trades"],f"Y{year}_expectancy_C1":s["expectancy"]})
    for direction in ("LONG","SHORT"):
        s=stats(net[frame.direction.eq(direction)]); row.update({f"{direction}_trades":s["trades"],f"{direction}_expectancy_C1":s["expectancy"]})
    row.update(concentration(net)); return {k:finite(v) for k,v in row.items()}


_WORKER_DATA: Mapping[tuple[str,str],pd.DataFrame] | None = None


def _worker(task: tuple[str,dict,str]) -> dict[str,Any]:
    key,config,cid=task
    if _WORKER_DATA is None: raise RuntimeError("worker development data is not initialized")
    return _metric_row(cid,execute(key,config,_WORKER_DATA))


def _neighbors(rows: list[dict], i: int, names: list[str], values: Mapping[str,list]) -> list[int]:
    found=[]
    for j,other in enumerate(rows):
        differing=[n for n in names if rows[i][n]!=other[n]]
        if len(differing)==1:
            n=differing[0]; order=values[n]
            if abs(order.index(rows[i][n])-order.index(other[n]))==1: found.append(j)
    return found


def analyze(configs: list[dict], results: list[dict], key: str) -> tuple[list[dict],list[dict],str]:
    names=sorted(SPACES[key]); values={n:SPACES[key][n][1] for n in names}; plateau=[]
    for i,(cfg,res) in enumerate(zip(configs,results)):
        neighbors=_neighbors(configs,i,names,values); valid=[results[j] for j in neighbors]
        positive=res["expectancy_C1"] is not None and res["expectancy_C1"]>0
        positive_neighbors=[r for r in valid if r["expectancy_C1"] is not None and r["expectancy_C1"]>0]
        stable=[r for r in positive_neighbors if abs(r["expectancy_C1"]-res["expectancy_C1"]) <= max(.01,abs(res["expectancy_C1"])*.35)] if positive else []
        classification="ROBUST_PLATEAU" if positive and len(stable)>=2 else ("LOCAL_SPIKE" if positive else "NO_EDGE")
        plateau.append({"configuration_id":res["configuration_id"],"neighbor_count":len(valid),"positive_neighbors":len(positive_neighbors),"stable_neighbors":len(stable),"classification":classification,"expectancy_C1":res["expectancy_C1"],"PF_C1":res["PF_C1"]})
    sensitivity=[]
    for name in names:
        for value in values[name]:
            sample=[r for c,r in zip(configs,results) if c[name]==value]
            ex=[r["expectancy_C1"] for r in sample if r["expectancy_C1"] is not None]
            sensitivity.append({"parameter":name,"value":value,"configurations":len(sample),"positive_C1_share":sum(x>0 for x in ex)/len(ex) if ex else None,"mean_expectancy_C1":np.mean(ex) if ex else None,"std_expectancy_C1":np.std(ex) if ex else None})
    robust=sum(r["classification"]=="ROBUST_PLATEAU" for r in plateau)
    overall="ROBUST_PLATEAU" if robust else ("LOCAL_SPIKE" if any((r["expectancy_C1"] or 0)>0 for r in results) else "NO_EDGE")
    return plateau,sensitivity,overall


def _csv(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).map(finite).to_csv(path,index=False,lineterminator="\n",float_format="%.12g",na_rep="")


def run_strategy(key: str, data: Mapping[tuple[str,str],pd.DataFrame], output: Path) -> dict:
    output.mkdir(parents=True,exist_ok=True); definition=experiment_definition(key); configs=bounded_design(key)
    global _WORKER_DATA
    results=[]; parameter_rows=[]; tasks=[]
    for number,config in enumerate(configs):
        cid=f"{key}-{number:04d}-{stable_hash(config)[:12]}"; parameter_rows.append({"configuration_id":cid,**config})
        tasks.append((key,config,cid))
    # Forked workers inherit the read-only development frames without copying
    # source files into the repository. ``map`` preserves deterministic order.
    _WORKER_DATA=data
    context=mp.get_context("fork")
    with context.Pool(processes=min(8,len(tasks))) as pool:
        results=pool.map(_worker,tasks)
    _WORKER_DATA=None
    plateau,sensitivity,overall=analyze(configs,results,key)
    baseline_config={n:getattr(PARAMETERS[key],n) for n in SPACES[key]}; baseline_id=next(r["configuration_id"] for c,r in zip(configs,results) if c==baseline_config)
    baseline=next(r for r in results if r["configuration_id"]==baseline_id)
    robust_ids={r["configuration_id"] for r in plateau if r["classification"]=="ROBUST_PLATEAU"}
    robust_rows=[r for r in results if r["configuration_id"] in robust_ids]
    recommendation="ROBUST_CANDIDATE" if overall=="ROBUST_PLATEAU" else ("CONTINUE_RESEARCH" if overall=="LOCAL_SPIKE" else "NO_EDGE")
    summary=[{"strategy":key,"tested_configurations":len(configs),"plateau_classification":overall,"robust_configurations":len(robust_rows),"baseline_configuration_id":baseline_id,"baseline_expectancy_C1":baseline["expectancy_C1"],"baseline_PF_C1":baseline["PF_C1"],"baseline_net_R_C1":baseline["net_R_C1"],"recommendation":recommendation}]
    manifest={"phase":"3.2","strategy":key,"experiment_id":definition["experiment_id"],"optimization_type":"BOUNDED_ROBUSTNESS","selection_objective":"PLATEAU_NOT_MAXIMUM_PF","tested_configurations":len(configs),"true_oos_blocked":True,"cost_scenarios":SCENARIOS,"deterministic":True,"source_data_copied":False}
    for name,value in (("manifest.json",manifest),("experiment.json",definition)):
        (output/name).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    _csv(output/"parameters.csv",parameter_rows); _csv(output/"results.csv",results); _csv(output/"metrics_summary.csv",summary); _csv(output/"plateau_report.csv",plateau); _csv(output/"sensitivity_report.csv",sensitivity)
    region="No robust C1-positive region." if not robust_rows else f"{len(robust_rows)} configurations have at least two adjacent, stable, C1-positive neighbors. Review plateau_report.csv; no single PF winner is selected."
    (output/"best_regions.md").write_text(f"# {key} Stable Regions\n\n**Classification:** {overall}\n\n{region}\n",encoding="utf-8")
    (output/"final_report.md").write_text(f"# {key} Phase 3.2 Bounded Optimization\n\n- Tested configurations: {len(configs)}\n- Baseline C1 expectancy: {baseline['expectancy_C1']}\n- Baseline C1 PF: {baseline['PF_C1']}\n- Plateau classification: **{overall}**\n- C1 cost survival: {'YES' if robust_rows else 'NO'}\n- Recommendation: **{recommendation}**\n\nThe finite baseline/OAT design assesses immediate neighborhoods rather than maximizing PF. 2025+ TRUE OOS data was not selected or read.\n",encoding="utf-8")
    return summary[0]


def run_all(data_root: Path, output: Path) -> list[dict]:
    data=load_development_data(Path(data_root)); summaries=[run_strategy(k,data,Path(output)/k) for k in SPACES]
    lines=["# Phase 3.2 Final Optimization Report","","Bounded baseline/OAT research only; no maximum-PF selection. TRUE OOS 2025+ was not read.",""]
    for row in summaries: lines += [f"## {row['strategy']}",f"- Tested: {row['tested_configurations']}",f"- Baseline C1 expectancy / PF / net R: {row['baseline_expectancy_C1']} / {row['baseline_PF_C1']} / {row['baseline_net_R_C1']}",f"- Stable region: {row['plateau_classification']} ({row['robust_configurations']} robust configurations)",f"- Cost robustness: {'survives C1 in a plateau' if row['robust_configurations'] else 'no C1-positive plateau'}",f"- Recommendation: **{row['recommendation']}**",""]
    lines += ["## Status","","PHASE_3_2_BOUNDED_OPTIMIZATION_COMPLETE",""]
    (Path(output)/"final_optimization_report.md").write_text("\n".join(lines),encoding="utf-8")
    return summaries
