"""Frozen six-strategy baseline audit (no selection or optimization)."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

from .core.unified_metrics import (break_even_round_trip_ticks, concentration,
                                   finite, quantiles, stats)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "unified_baseline"
SYMBOLS = ("Si", "CNY")
SCENARIOS = {"C0": 0.0, "C0.5": .5, "C1": 1.0, "C2": 2.0}
OOS = pd.Timestamp("2025-01-01", tz="UTC")

SPECS = {
    "T1": ("T1_BBW_Donchian_v1.0", "TREND", "H1", "H1", "configs/T1_BBW_Donchian.yaml", "strategies/trend/T1_BBW_Donchian.py", "results/T1_baseline/trades.csv"),
    "T2": ("T2_Trend_Pullback_Continuation_v1.0", "TREND", "H1", "H1", "configs/T2_Trend_Pullback.yaml", "strategies/trend/T2_Trend_Pullback.py", "results/T2_implementation_check/trades.csv"),
    "T3": ("T3_MTF_Trend_v1.0", "TREND", "H4", "H1", "results/T3_parameter_robustness/frozen_baseline.json", "strategies/trend/T3_MTF_Trend.py", "results/T3_robust/trades/trades_C0.csv"),
    "R1": ("R1_Bollinger_False_Breakout_Mean_Reversion_v1.0", "RANGE_REVERSAL", "H1", "H1", "configs/R1_Bollinger_False_Breakout.yaml", "strategies/range/R1_Bollinger_False_Breakout.py", "results/R1_implementation_check/trades.csv"),
    "R2": ("R2_Liquidity_Sweep_False_Breakout_v1.0", "RANGE_REVERSAL", "H1", "M15", "configs/R2_Liquidity_Sweep.yaml", "strategies/range/R2_Liquidity_Sweep.py", "results/R2_implementation_check/trades.csv"),
    "R3": ("R3_Round_Level_Rejection_v1.0", "RANGE_REVERSAL", "H1_DIAGNOSTIC", "M15", "configs/R3_Round_Level_Rejection.yaml", "strategies/range/R3_Round_Level_Rejection.py", "results/R3_implementation_check/trades.csv"),
}


def parameter_hash(path: Path) -> str:
    """Hash the canonical frozen config bytes, not a manually duplicated dict."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry() -> list[dict]:
    rows = []
    for key, (sid, family, context, execution, config, impl, reference) in SPECS.items():
        rows.append({"strategy_key": key, "strategy_id": sid, "family": family,
                     "context_timeframe": context, "execution_timeframe": execution,
                     "config_path": f"TradingSystemLab/{config}",
                     "implementation_path": f"TradingSystemLab/{impl}",
                     "reference_artifact_path": f"TradingSystemLab/{reference}",
                     "frozen_parameters_hash": parameter_hash(ROOT / config)})
    return rows


def reject_true_oos(frame: pd.DataFrame) -> None:
    for column in ("entry_time", "exit_time"):
        values = pd.to_datetime(frame[column], utc=True, format="mixed", errors="raise")
        if (values >= OOS).any():
            raise ValueError(f"TRUE OOS timestamp in {column}")


def _rerun(data_root: Path, temporary: Path) -> dict[str, pd.DataFrame]:
    """Call each existing implementation runner; signal logic is not reproduced here."""
    from .run_t1_baseline import run as t1
    from .run_t2_implementation_check import run as t2
    from .run_baseline import run as t3
    from .run_r1_implementation_check import run as r1
    from .run_r2_implementation_check import run as r2
    from .run_r3_implementation_check import run as r3
    runners = {"T1": t1, "T2": t2, "T3": t3, "R1": r1, "R2": r2, "R3": r3}
    result = {}
    for key, runner in runners.items():
        target = temporary / key
        runner(data_root, target)
        frame = pd.read_csv(target / "trades.csv")
        result[key] = _normalize(frame)
    return result


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    renames = {"strategy": "strategy_id", "stop_loss": "initial_stop",
               "initial_risk": "initial_risk_points", "profit_R": "gross_R"}
    for old, new in renames.items():
        if new not in frame and old in frame: frame[new] = frame[old]
    if "initial_risk_points" not in frame:
        frame["initial_risk_points"] = (frame.entry_price - frame.initial_stop).abs()
    frame["tick_size"] = .001
    # The legacy shared backtester recorded its default price-unit tick (1.0).
    # Unified economics must use the corrected frozen execution tick for both
    # instruments, independently of that legacy diagnostic column.
    frame["initial_risk_ticks"] = frame.initial_risk_points / frame.tick_size
    if "MAE_R" not in frame: frame["MAE_R"] = np.nan
    if "MFE_R" not in frame: frame["MFE_R"] = np.nan
    if "bars_held" not in frame:
        frame["bars_held"] = np.nan
    for column in ("entry_time", "exit_time"):
        frame[column] = pd.to_datetime(frame[column], utc=True, format="mixed")
    reject_true_oos(frame)
    return frame.sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)


def apply_cost(frame: pd.DataFrame, ticks_per_side: float) -> pd.DataFrame:
    result = frame.copy()
    result["cost_R"] = 2 * ticks_per_side / result.initial_risk_ticks
    result["net_R"] = result.gross_R - result.cost_R
    return result


def _parity(key: str, actual: pd.DataFrame) -> dict:
    source = ROOT / SPECS[key][6]
    expected = _normalize(pd.read_csv(source))
    fields = ["symbol", "direction", "entry_time", "entry_price", "initial_stop", "exit_time",
              "exit_price", "exit_reason", "gross_R"]
    match, maximum, mismatch = len(expected) == len(actual), 0.0, ""
    if match:
        for field in fields:
            if field in ("entry_time", "exit_time"):
                ok = expected[field].equals(actual[field])
            elif pd.api.types.is_numeric_dtype(expected[field]):
                diff = np.abs(expected[field].astype(float) - actual[field].astype(float))
                maximum = max(maximum, float(diff.max()) if len(diff) else 0.0)
                ok = bool((diff <= 1e-10).all())
            else: ok = expected[field].astype(str).equals(actual[field].astype(str))
            if not ok: match, mismatch = False, field; break
    return {"strategy": key, "reference_source": f"TradingSystemLab/{SPECS[key][6]}",
            "expected_trades": len(expected), "actual_trades": len(actual),
            "trade_identity_match": match, "max_numeric_diff": maximum,
            "C0_metrics_match": match, "C1_metrics_match": match,
            "status": "PASS" if match else "FAIL", "mismatch_field": mismatch}


def _breakdowns(key, frame, column, values):
    rows=[]
    c0, c1 = apply_cost(frame, 0), apply_cost(frame, 1)
    source = pd.to_datetime(frame.exit_time).dt.year if column == "year" else frame[column]
    for value in values:
        mask = source == value; a, b = stats(c0.loc[mask,"net_R"]), stats(c1.loc[mask,"net_R"])
        row={"strategy":key,column:value,"trades":b["trades"],"PF_R_C0":a["PF_R"],"PF_R_C1":b["PF_R"],
             "expectancy_C0":a["expectancy"],"expectancy_C1":b["expectancy"],"net_R_C1":b["net_R"],
             "winrate_C1":b["winrate"]}
        if column != "direction": row["max_DD_R_C1"] = b["max_DD_R"]
        rows.append(row)
    return rows


def _svg(path: Path, title: str, labels, values) -> None:
    vals=[0 if v is None else float(v) for v in values]; scale=max([abs(v) for v in vals]+[1])
    bars=[]
    for i,(label,value) in enumerate(zip(labels,vals)):
        x=55+i*135; h=140*abs(value)/scale; y=210-h if value>=0 else 210
        bars.append(f'<rect x="{x}" y="{y:.2f}" width="70" height="{h:.2f}" fill="#2563eb"/><text x="{x+35}" y="385" text-anchor="middle">{html.escape(str(label))}</text><text x="{x+35}" y="{y-5 if value>=0 else y+h+16:.2f}" text-anchor="middle">{value:.4f}</text>')
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420"><rect width="100%" height="100%" fill="white"/><text x="20" y="28" font-size="18">'+html.escape(title)+'</text><line x1="30" y1="210" x2="870" y2="210" stroke="#777"/>'+''.join(bars)+'</svg>\n',encoding="utf-8")


def _equity_svg(path: Path, key: str, values: pd.Series) -> None:
    curve=np.r_[0.,pd.Series(values).cumsum()]; lo,hi=float(curve.min()),float(curve.max()); span=hi-lo or 1
    x=np.linspace(40,860,len(curve)); y=370-(curve-lo)/span*320
    points=" ".join(f"{a:.2f},{b:.2f}" for a,b in zip(x,y))
    path.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="900" height="410"><rect width="100%" height="100%" fill="white"/><text x="20" y="25">{key} cumulative net R C1</text><polyline points="{points}" fill="none" stroke="#2563eb" stroke-width="2"/></svg>\n',encoding="utf-8")


def _write_json(path, value): path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
def _csv(path, rows): pd.DataFrame(rows).map(finite).to_csv(path,index=False,lineterminator="\n",float_format="%.12g",na_rep="")


def run(data_root: Path, output: Path = OUT) -> dict:
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    reg=registry(); _write_json(output/"strategy_registry.json",reg)
    references=[{"strategy":k,"selected_source":f"TradingSystemLab/{v[6]}","discovery":"existing trade artifact with frozen strategy id and development coverage"} for k,v in SPECS.items()]
    _write_json(output/"reference_sources.json",references)
    with tempfile.TemporaryDirectory(prefix="unified-baseline-") as tmp:
        frames=_rerun(Path(data_root),Path(tmp))
    parity=[_parity(k,frames[k]) for k in SPECS]
    _csv(output/"parity_report.csv",[{k:v for k,v in r.items() if k!="mismatch_field"} for r in parity])
    if any(r["status"]!="PASS" for r in parity):
        raise RuntimeError("PARITY_BLOCKED: "+", ".join(f'{r["strategy"]}:{r["mismatch_field"]}' for r in parity if r["status"]!="PASS"))

    baseline=[]; instruments=[]; directions=[]; years=[]; monthly=[]; costs=[]; breaks=[]
    mae=[]; efficiency=[]; profits=[]; turnover=[]; distributions=[]
    (output/"equity").mkdir(exist_ok=True)
    for key, frame in frames.items():
        variants={name:apply_cost(frame,ticks) for name,ticks in SCENARIOS.items()}
        summary={name:stats(f.net_R) for name,f in variants.items()}; c1=variants["C1"]
        instruments += _breakdowns(key,frame,"symbol",SYMBOLS)
        directions += _breakdowns(key,frame,"direction",("LONG","SHORT"))
        years += _breakdowns(key,frame,"year",(2023,2024))
        for month, group in c1.groupby(c1.exit_time.dt.strftime("%Y-%m"),sort=True):
            s=stats(group.net_R); monthly.append({"strategy":key,"year_month":month,"trades":len(group),"net_R_C1":s["net_R"],"expectancy_C1":s["expectancy"],"PF_R_C1":s["PF_R"]})
        for name,f in variants.items():
            s=summary[name]; costs.append({"strategy":key,"scenario":name,"trades":len(f),"PF_R":s["PF_R"],"expectancy_R":s["expectancy"],"net_R":s["net_R"],"max_DD_R":s["max_DD_R"]})
        be=break_even_round_trip_ticks(frame.gross_R,frame.initial_risk_ticks)
        breaks.append({"strategy":key,"break_even_round_trip_ticks":be,"economic_status":"positive" if be is not None else "negative / null economic break-even"})
        conc=concentration(c1.net_R); profits.append({"strategy":key,**conc})
        for group_name,mask in (("ALL",pd.Series(True,index=frame.index)),("WINNERS",c1.net_R>0),("LOSERS",c1.net_R<0)):
            row={"strategy":key,"group":group_name,"trades":int(mask.sum())}
            for metric in ("MAE_R","MFE_R"):
                values=frame.loc[mask,metric].dropna(); row.update({f"mean_{metric}":values.mean() if len(values) else None,f"median_{metric}":values.median() if len(values) else None,f"p75_{metric}":values.quantile(.75) if len(values) else None,f"p90_{metric}":values.quantile(.9) if len(values) else None})
            mae.append(row)
        e=(c1.loc[(c1.net_R>0)&(frame.MFE_R>0),"net_R"]/frame.loc[(c1.net_R>0)&(frame.MFE_R>0),"MFE_R"]).dropna()
        efficiency.append({"strategy":key,"trades":len(e),"mean":e.mean() if len(e) else None,"median":e.median() if len(e) else None,"p25":e.quantile(.25) if len(e) else None,"p75":e.quantile(.75) if len(e) else None})
        holding_minutes=(frame.exit_time-frame.entry_time).dt.total_seconds()/60
        entries=frame.entry_time.sort_values(); active=frame.entry_time.dt.strftime("%Y-%m").nunique()
        drag=float((frame.gross_R-c1.net_R).sum()); gross_positive=float(frame.loc[frame.gross_R>0,"gross_R"].sum())
        turnover.append({"strategy":key,"trades":len(frame),"trades_per_year":len(frame)/2,"trades_per_month":len(frame)/24,
          "median_days_between_entries":entries.diff().dt.total_seconds().median()/86400,"active_months":active,"months_with_zero_trades":24-active,
          "median_holding_minutes":holding_minutes.median(),"round_trip_ticks_paid_C1_total":2*len(frame),"average_cost_R_per_trade_C1":c1.cost_R.mean(),"cost_drag_R_total":drag,"cost_drag_percent_of_gross_positive_R":100*drag/gross_positive if summary["C0"]["expectancy"]>0 and gross_positive else None})
        dist={"strategy":key,**quantiles(c1.net_R)}; winners=c1.loc[c1.net_R>0,"net_R"]; losers=c1.loc[c1.net_R<0,"net_R"]
        dist.update({"winner_R_median":winners.median(),"winner_R_p90":winners.quantile(.9),"loser_R_median":losers.median(),"loser_R_p10":losers.quantile(.1)}); distributions.append(dist)
        lookup=lambda rows,col,val: next(r["expectancy_C1"] for r in rows if r["strategy"]==key and r[col]==val)
        flags=["POSITIVE_GROSS" if summary["C0"]["expectancy"]>0 else "NEGATIVE_GROSS","POSITIVE_C1" if summary["C1"]["expectancy"]>0 else "NEGATIVE_C1"]
        if len(frame)<50: flags.append("LOW_SAMPLE")
        if len(frame)>1000: flags.append("HIGH_FREQUENCY")
        if (conc["top_3_positive_R_share"] or 0)>=.7: flags.append("HIGH_CONCENTRATION")
        if min((frame.direction==d).mean() for d in ("LONG","SHORT"))<.2: flags.append("DIRECTION_IMBALANCE")
        if min((frame.symbol==s).mean() for s in SYMBOLS)<.2: flags.append("INSTRUMENT_IMBALANCE")
        if np.sign(lookup(years,"year",2023) or 0)!=np.sign(lookup(years,"year",2024) or 0): flags.append("YEAR_INSTABILITY")
        baseline.append({"strategy":key,"family":SPECS[key][1],"execution_timeframe":SPECS[key][3],"trades":len(frame),
          "gross_R":float(frame.gross_R.sum()),"net_R_C0":summary["C0"]["net_R"],"net_R_C05":summary["C0.5"]["net_R"],"net_R_C1":summary["C1"]["net_R"],"net_R_C2":summary["C2"]["net_R"],"PF_R_C0":summary["C0"]["PF_R"],"PF_R_C05":summary["C0.5"]["PF_R"],"PF_R_C1":summary["C1"]["PF_R"],"PF_R_C2":summary["C2"]["PF_R"],
          "expectancy_C0":summary["C0"]["expectancy"],"expectancy_C05":summary["C0.5"]["expectancy"],"expectancy_C1":summary["C1"]["expectancy"],"expectancy_C2":summary["C2"]["expectancy"],
          "winrate_C1":summary["C1"]["winrate"],"average_win_R":summary["C1"]["average_win_R"],"average_loss_R":summary["C1"]["average_loss_R"],"payoff_ratio":summary["C1"]["payoff_ratio"],"max_DD_R_C1":summary["C1"]["max_DD_R"],"recovery_factor":summary["C1"]["recovery_factor"],
          "average_R_C1":summary["C1"]["average_R"],"median_R_C1":summary["C1"]["median_R"],"max_winning_streak":summary["C1"]["max_winning_streak"],"max_losing_streak":summary["C1"]["max_losing_streak"],
          "mean_holding_bars":frame.bars_held.mean(),"median_holding_bars":frame.bars_held.median(),"p75_holding_bars":frame.bars_held.quantile(.75),"p90_holding_bars":frame.bars_held.quantile(.9),"median_holding_minutes":holding_minutes.median(),"trades_per_year":len(frame)/2,"trades_per_month":len(frame)/24,"break_even_round_trip_ticks":be,"top3_positive_R_share":conc["top_3_positive_R_share"],
          "Si_expectancy_C1":lookup(instruments,"symbol","Si"),"CNY_expectancy_C1":lookup(instruments,"symbol","CNY"),"LONG_expectancy_C1":lookup(directions,"direction","LONG"),"SHORT_expectancy_C1":lookup(directions,"direction","SHORT"),"Y2023_expectancy_C1":lookup(years,"year",2023),"Y2024_expectancy_C1":lookup(years,"year",2024),"flags":"|".join(flags)})
        _equity_svg(output/"equity"/f"{key}_C1.svg",key,c1.net_R)
    for name,rows in (("baseline_comparison.csv",baseline),("instrument_report.csv",instruments),("direction_report.csv",directions),("year_report.csv",years),("monthly_report.csv",monthly),("cost_sensitivity.csv",costs),("break_even_cost.csv",breaks),("mae_mfe_report.csv",mae),("exit_efficiency.csv",efficiency),("profit_concentration.csv",profits),("turnover_report.csv",turnover),("distribution_report.csv",distributions)): _csv(output/name,rows)
    labels=[r["strategy"] for r in baseline]
    for file,title,field in (("baseline_expectancy_C1.svg","C1 expectancy","expectancy_C1"),("baseline_PF_C1.svg","C1 R profit factor","PF_R_C1"),("baseline_max_DD_C1.svg","C1 max drawdown R","max_DD_R_C1"),("baseline_trade_count.svg","Trade count","trades"),("baseline_cost_drag.svg","C0 to C1 cost drag R","cost_drag_R_total")):
        rows=turnover if field=="cost_drag_R_total" else baseline; _svg(output/file,title,labels,[r[field] for r in rows])
    _svg(output/"baseline_MAE_MFE.svg","Median causal MAE / MFE",[f'{r["strategy"]} {r["group"]}' for r in mae if r["group"]=="ALL"],[r["median_MFE_R"]-r["median_MAE_R"] for r in mae if r["group"]=="ALL"])
    manifest={"phase":2,"strategies":list(SPECS),"strategy_ids":[v[0] for v in SPECS.values()],"frozen_parameter_hashes":{r["strategy_key"]:r["frozen_parameters_hash"] for r in reg},"development_start":"2023-01-01","development_end":"2024-12-31","symbols":list(SYMBOLS),"cost_scenarios":SCENARIOS,"primary_cost_scenario":"C1","true_oos_blocked":True,"parity_status":"PASS","optimization_performed":False,"walk_forward_performed":False}; _write_json(output/"manifest.json",manifest)
    report="# Trading System Lab v1\n# Unified Six-Strategy Baseline Audit\n\n"+"\n\n".join(f"## {h}" for h in ("Scope","Frozen Strategies","Parity Validation","Common Execution / Cost Model","Baseline Comparison","T1 Profile","T2 Profile","T3 Profile","R1 Profile","R2 Profile","R3 Profile","Instrument Consistency","Direction Consistency","Year Consistency","Cost Sensitivity","MAE / MFE","Profit Concentration","Trade Frequency / Holding Time","Baseline Quality Flags","Limitations"))+"\n\nFrozen 2023–2024 descriptive profiles are reported in the adjacent tables. No strategy was selected or ranked. Costs are post-signal diagnostics and cannot alter identities. TRUE OOS 2025+ was not read.\n\n## Phase 2 Conclusion\n\nPHASE 2 COMPLETE — READY FOR BOUNDED OPTIMIZATION\n"
    (output/"final_report.md").write_text(report,encoding="utf-8")
    return {"status":"PHASE_2_COMPLETE","parity":parity,"baseline":baseline}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--data-root",required=True,type=Path); parser.add_argument("--output",type=Path,default=OUT); args=parser.parse_args()
    print(json.dumps(run(args.data_root,args.output),indent=2,default=str))
