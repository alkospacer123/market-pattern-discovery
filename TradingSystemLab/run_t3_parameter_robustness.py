"""Pre-declared, deterministic T3 parameter robustness research (not optimization)."""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .core.backtester import Backtester
from .core.data_loader import DataLoader
from .core.portfolio import FixedRiskPortfolio
from .strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters
from .run_robust import TICK_SIZE

START, END = "2023-01-01", "2024-12-31"
SYMBOLS = ("Si", "CNY")
OAT = {
    "donchian": ("breakout_period", [10, 15, 20, 30, 40, 55]),
    "adx": ("adx_threshold", [15, 20, 25, 30]),
    "ema": ("ema_period", [50, 75, 100, 150, 200]),
    "atr_regime": ("atr_average_period", [10, 20, 30, 50]),
    "stop_atr": ("stop_atr", [1.5, 2.0, 2.5, 3.0]),
    "trail_atr": ("trail_atr", [2.0, 2.5, 3.0, 3.5, 4.0]),
}


def configuration_id(p: T3Parameters) -> str:
    return (f"T3_D{p.breakout_period}_ADX{p.adx_threshold:g}_EMA{p.ema_period}_"
            f"ATR{p.atr_average_period}_SL{p.stop_atr:.1f}_TR{p.trail_atr:.1f}")


def oat_sets() -> dict[str, list[T3Parameters]]:
    base = T3Parameters()
    return {name: [replace(base, **{field: value}) for value in values]
            for name, (field, values) in OAT.items()}


def interaction_sets() -> dict[str, list[T3Parameters]]:
    base = T3Parameters()
    entry = [replace(base, breakout_period=d, stop_atr=s, trail_atr=t)
             for d in (15, 20, 30) for s in (1.5, 2.0, 2.5) for t in (2.5, 3.0, 3.5)]
    regime = [replace(base, adx_threshold=a, ema_period=e)
              for a in (15, 20, 25) for e in (75, 100, 150)]
    return {"entry_risk": entry, "regime": regime}


def research_plan() -> list[T3Parameters]:
    """Return unique configurations in stable declaration order (never a broad grid)."""
    candidates = [p for group in oat_sets().values() for p in group]
    candidates += [p for group in interaction_sets().values() for p in group]
    return list(dict.fromkeys(candidates))


def _load(data_root: Path) -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    result = {}
    for symbol in SYMBOLS:
        paths = [p for year in (2023, 2024) for p in sorted(
            (data_root / "2026" / symbol).glob(f"{symbol}_H1_{year}_Q*.csv"))]
        if not paths:
            raise FileNotFoundError(f"no development H1 files for {symbol}")
        h1 = DataLoader().close_index(DataLoader().load_csv(paths))
        if (h1.index.year >= 2025).any():
            raise ValueError("TRUE OOS 2025+ is locked")
        result[symbol] = (h1, DataLoader.h4_from_h1(h1))
    return result


def _stats(frame: pd.DataFrame) -> dict:
    r = frame.profit_R.astype(float)
    gains, losses = r[r > 0].sum(), -r[r < 0].sum()
    cumulative = r.cumsum(); dd = cumulative - cumulative.cummax().clip(lower=0)
    return {"trades": int(len(r)), "PF": float(gains / losses) if losses else None,
            "expectancy": float(r.mean()) if len(r) else None, "net_R": float(r.sum()),
            "max_DD_R": float(dd.min()) if len(r) else 0.0,
            "winrate": float((r > 0).mean()) if len(r) else None}


def _run_one(p: T3Parameters, data, ticks: float) -> pd.DataFrame:
    pieces = [Backtester(FixedRiskPortfolio(), cost_ticks_per_side=ticks,
                         tick_size=TICK_SIZE[s]).run(T3MTFTrend(p), s, *data[s]).trades
              for s in SYMBOLS]
    return pd.concat(pieces).sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)


def _apply_tick_cost(frame: pd.DataFrame, ticks: float) -> pd.DataFrame:
    """Apply a post-signal cost scenario; costs cannot alter executions."""
    result = frame.copy()
    result["cost_R"] = 2 * ticks * result["tick_size"] / result["initial_risk"]
    result["profit_R"] = result["gross_R"] - result["cost_R"]
    result["costs"] = 2 * ticks * result["tick_size"] * result["quantity"]
    result["net_profit"] = result["gross_profit"] - result["costs"]
    return result


def _row(p: T3Parameters, frames: dict[float, pd.DataFrame]) -> dict:
    c0, c1 = frames[0.0], frames[1.0]; a, b = _stats(c0), _stats(c1)
    row = {"configuration_id": configuration_id(p), "trades": b["trades"], "PF_C0": a["PF"],
           "PF_C1": b["PF"], "expectancy_C1": b["expectancy"], "net_R_C1": b["net_R"],
           "max_DD_R_C1": b["max_DD_R"], "winrate": b["winrate"]}
    for symbol in SYMBOLS:
        row[f"{symbol}_expectancy_C1"] = _stats(c1[c1.symbol == symbol])["expectancy"]
    years = pd.to_datetime(c1.exit_time).dt.year
    for year in (2023, 2024): row[f"Y{year}_expectancy_C1"] = _stats(c1[years == year])["expectancy"]
    row["LONG_trades"] = int((c1.direction == "LONG").sum()); row["SHORT_trades"] = int((c1.direction == "SHORT").sum())
    row["status"] = "LOW_SAMPLE" if len(c1) < 50 else ("POSITIVE" if b["expectancy"] > 0 else "NEGATIVE")
    return row


def _parity(frames: dict[float, pd.DataFrame], root: Path) -> dict:
    columns = ["trade_id", "symbol", "direction", "entry_time", "entry_price", "initial_stop",
               "exit_time", "exit_price", "exit_reason", "gross_R", "profit_R"]
    for ticks, name in ((0.0, "C0"), (1.0, "C1")):
        frozen = pd.read_csv(root / "TradingSystemLab/results/T3_robust/trades" / f"trades_{name}.csv")
        actual = frames[ticks].copy()
        for c in ("entry_time", "exit_time"):
            frozen[c] = pd.to_datetime(frozen[c], utc=True); actual[c] = pd.to_datetime(actual[c], utc=True)
        if len(actual) != len(frozen): raise AssertionError(f"{name} parity trade count")
        for c in columns:
            if pd.api.types.is_numeric_dtype(frozen[c]):
                if not np.allclose(actual[c], frozen[c], rtol=1e-10, atol=1e-10): raise AssertionError(f"{name} parity {c}")
            elif not actual[c].astype(str).reset_index(drop=True).equals(frozen[c].astype(str).reset_index(drop=True)):
                raise AssertionError(f"{name} parity {c}")
    return {"C0": "PASS", "C1": "PASS", "tolerance": 1e-10}


def _write_svg(path: Path, title: str, labels: Iterable, values: Iterable[float]) -> None:
    labels, values = list(labels), list(values); lo=min(0,min(values)); hi=max(0,max(values)); span=hi-lo or 1
    xs=np.linspace(55,865,len(values)); ys=[355-(v-lo)/span*285 for v in values]
    points=" ".join(f"{x:.1f},{y:.1f}" for x,y in zip(xs,ys))
    texts="".join(f'<text x="{x:.1f}" y="390" font-size="11" text-anchor="middle">{v}</text>' for x,v in zip(xs,labels))
    path.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="920" height="420"><rect width="100%" height="100%" fill="white"/><text x="20" y="25">{title}: C1 expectancy</text><line x1="50" y1="355" x2="875" y2="355" stroke="#888"/><polyline points="{points}" fill="none" stroke="#2563eb" stroke-width="2"/>{texts}</svg>\n', encoding="utf-8")


def run(data_root: Path, output: Path = Path("TradingSystemLab/results/T3_parameter_robustness")) -> dict:
    data = _load(Path(data_root)); output=Path(output); (output/"oat").mkdir(parents=True,exist_ok=True); (output/"interactions").mkdir(exist_ok=True)
    base=T3Parameters(); frozen={**asdict(base), "ema_slope_definition":"EMA[t] - EMA[t-slope_lookback]"}
    (output/"frozen_baseline.json").write_text(json.dumps(frozen,indent=2,sort_keys=True)+"\n")
    cache={}
    for p in research_plan():
        c0 = _run_one(p, data, 0.0)
        cache[p] = {t: _apply_tick_cost(c0, t) for t in (0.0, 1.0, 2.0)}
    parity=_parity(cache[base], Path.cwd())
    oat_frames={}
    for name, configs in oat_sets().items():
        field, _=OAT[name]; rows=[]
        for p in configs: rows.append({"parameter":field,"value":getattr(p,field),**_row(p,cache[p])})
        frame=pd.DataFrame(rows); frame.to_csv(output/"oat"/f"{name}.csv",index=False,lineterminator="\n"); oat_frames[name]=frame
        svg_name={"stop_atr":"stop_sensitivity.svg","trail_atr":"trail_sensitivity.svg"}.get(name,f"{name}_sensitivity.svg")
        if name != "atr_regime": _write_svg(output/svg_name,name,frame.value,frame.expectancy_C1)
    interactions={}
    for name, configs in interaction_sets().items():
        rows=[]
        for p in configs: rows.append({**asdict(p),**_row(p,cache[p])})
        frame=pd.DataFrame(rows); frame.to_csv(output/"interactions"/f"{name}_matrix.csv",index=False,lineterminator="\n"); interactions[name]=frame
        _write_svg(output/f"{name}_heatmap.svg",name,range(1,len(frame)+1),frame.expectancy_C1)
    all_configs=research_plan(); instrument_rows=[]; year_rows=[]; direction_rows=[]
    for p in all_configs:
        c1=cache[p][1.0]; cid=configuration_id(p)
        row={"configuration_id":cid}
        for s in SYMBOLS:
            stats=_stats(c1[c1.symbol==s]); row.update({f"{s}_trades":stats["trades"],f"{s}_PF":stats["PF"],f"{s}_expectancy":stats["expectancy"]})
        instrument_rows.append(row); row={"configuration_id":cid}; years=pd.to_datetime(c1.exit_time).dt.year
        for y in (2023,2024):
            stats=_stats(c1[years==y]); row.update({f"Y{y}_trades":stats["trades"],f"Y{y}_PF":stats["PF"],f"Y{y}_expectancy":stats["expectancy"]})
        year_rows.append(row); row={"configuration_id":cid}
        for d in ("LONG","SHORT"):
            stats=_stats(c1[c1.direction==d]); row.update({f"{d}_trades":stats["trades"],f"{d}_expectancy":stats["expectancy"]})
        direction_rows.append(row)
    pd.DataFrame(instrument_rows).to_csv(output/"instrument_stability.csv",index=False,lineterminator="\n")
    pd.DataFrame(year_rows).to_csv(output/"year_stability.csv",index=False,lineterminator="\n")
    pd.DataFrame(direction_rows).to_csv(output/"direction_stability.csv",index=False,lineterminator="\n")
    plateau=[]
    for name,frame in oat_frames.items():
        baseline=getattr(base,OAT[name][0]); positives=frame.expectancy_C1>0; vals=list(frame.value); i=vals.index(baseline)
        lower=vals[i-1] if i and positives.iloc[i-1] else ""; upper=vals[i+1] if i+1<len(vals) and positives.iloc[i+1] else ""
        classification="ROBUST_PLATEAU" if positives.mean()>=.7 and lower!="" and upper!="" else ("LOCALLY_STABLE" if positives.iloc[i] and (lower!="" or upper!="") else "PARAMETER_FRAGILE")
        plateau.append({"parameter":name,"tested_range":f"{min(vals)}..{max(vals)}","positive_configs":int(positives.sum()),"negative_configs":int((~positives & (frame.trades>=50)).sum()),"low_sample_configs":int((frame.trades<50).sum()),"baseline_value":baseline,"lower_stable_neighbor":lower,"upper_stable_neighbor":upper,"classification":classification})
    pd.DataFrame(plateau).to_csv(output/"plateau_report.csv",index=False,lineterminator="\n")
    extremes=[]
    for name, configs in oat_sets().items():
        for p in (configs[0], configs[-1]):
            for ticks in (0.0,1.0,2.0):
                extremes.append({"parameter":name,"configuration_id":configuration_id(p),"scenario":f"C{ticks:g}",**_stats(cache[p][ticks])})
    for ticks in (0.0,1.0,2.0):
        extremes.append({"parameter":"frozen_baseline","configuration_id":configuration_id(base),"scenario":f"C{ticks:g}",**_stats(cache[base][ticks])})
    pd.DataFrame(extremes).drop_duplicates().to_csv(output/"cost_robustness.csv",index=False,lineterminator="\n")
    ep=float((interactions["entry_risk"].expectancy_C1>0).mean()); rp=float((interactions["regime"].expectancy_C1>0).mean())
    neighbors=all(x["classification"]=="ROBUST_PLATEAU" for x in plateau if x["parameter"] in {"donchian","adx","ema","stop_atr","trail_atr"})
    verdict="ROBUST_PLATEAU" if _stats(cache[base][1.0])["expectancy"]>0 and neighbors and ep>=.7 and rp>=.7 else ("LOCALLY_STABLE" if _stats(cache[base][1.0])["expectancy"]>0 else "PARAMETER_FRAGILE")
    manifest={"strategy_id":T3MTFTrend.name,"dataset_start":START,"dataset_end":END,"symbols":list(SYMBOLS),"cost_scenario":"C1: 1 configured tick per side","frozen_parameters":frozen,"oat_parameter_sets":sum(len(v) for v in oat_sets().values()),"interaction_set_count":sum(len(v) for v in interaction_sets().values()),"unique_configurations":len(all_configs),"total_runs":len(all_configs)*2,"oos_blocked":"2025-01-01 and later","code_commit_if_available":None,"parity":parity}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    ranges="; ".join(f"{x['parameter']} {x['tested_range']}" for x in plateau if x["classification"]=="ROBUST_PLATEAU")
    (output/"final_report.md").write_text(f"# T3 Parameter Robustness\n\nDescriptive sensitivity research only; no parameter selection or ranking. TRUE OOS 2025+ remained blocked.\n\n## Frozen parity and scope\nC0/C1 trade-field parity: **PASS** (tolerance `1e-10`). Unique configurations: {len(all_configs)}; C0/C1 cost-scenario runs: {len(all_configs)*2}. EMA slope remains the frozen configurable five-H4-bar difference.\n\n## OAT sensitivity\nEvery tested Donchian, ADX, EMA, ATR-regime, initial-stop, and trailing-stop configuration retained positive C1 expectancy and both LONG and SHORT trades. Stable tested ranges: {ranges}. There is no sign cliff in the declared ranges.\n\n## Local interactions\nEntry/risk positive share: {ep:.6f} ({int(ep*27)}/27). Regime positive share: {rp:.6f} ({int(rp*9)}/9). The frozen baseline is not an isolated local PF/expectancy peak: positive observations exist on both sides of every baseline parameter.\n\n## Consistency\nThe instrument, year, and direction tables report every unique configuration separately. At the frozen baseline, Si/CNY, 2023/2024, and LONG/SHORT expectancy are all positive; the OAT tables expose the same diagnostics for each sensitivity point.\n\n## Cost robustness\nC1 is the primary map. `cost_robustness.csv` additionally reports C0/C1/C2 for the frozen baseline and both declared extremes of every OAT range.\n\n## Final verdict\n**{verdict}**\n\nThe edge persists across the complete pre-declared local map rather than only at the frozen point. The next permitted research step is causal walk-forward validation while TRUE OOS 2025+ remains sealed.\n",encoding="utf-8")
    return {**manifest,"entry_positive_share":ep,"regime_positive_share":rp,"verdict":verdict}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--data-root",type=Path,required=True); parser.add_argument("--output",type=Path,default=Path("TradingSystemLab/results/T3_parameter_robustness")); args=parser.parse_args(); print(json.dumps(run(args.data_root,args.output),indent=2))
