"""Causal, frozen-parameter expanding-window validation for T3.

This module deliberately discovers and opens only the named 2023/2024 H1
development files.  TRUE OOS is rejected again at every public boundary.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .core.backtester import Backtester
from .core.data_loader import DataLoader
from .core.portfolio import FixedRiskPortfolio
from .strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters

OOS_START = pd.Timestamp("2025-01-01", tz="Europe/Moscow")
SYMBOLS = ("Si", "CNY")
TICK_SIZES = {"Si": 0.001, "CNY": 0.001}
COSTS = {"C0": 0.0, "C1": 1.0, "C2": 2.0}
INITIAL_TRAIN_MONTHS, TEST_MONTHS, STEP_MONTHS = 12, 3, 3
TRADE_COLUMNS = ["trade_id", "fold_id", "symbol", "direction", "entry_time",
                 "entry_price", "initial_stop", "exit_time", "exit_price",
                 "exit_reason", "bars_held", "gross_R", "cost_R", "net_R",
                 "MAE_R", "MFE_R"]


def _iso(value: pd.Timestamp) -> str:
    return value.isoformat()


def load_frozen(path: Path) -> tuple[T3Parameters, dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    fields = set(T3Parameters.__dataclass_fields__)
    values = {key: value for key, value in raw.items() if key in fields}
    if set(values) != fields:
        raise ValueError("frozen baseline does not contain every T3 parameter")
    parameters = T3Parameters(**values)
    # Parity is an invariant, not an alternative source of defaults.
    if asdict(parameters) != asdict(T3Parameters()):
        raise ValueError("frozen baseline no longer matches T3_MTF_Trend_v1.0")
    return parameters, raw


def load_development_data(data_root: Path) -> dict[str, tuple[pd.DataFrame, pd.DataFrame]]:
    data = {}
    for symbol in SYMBOLS:
        # Explicit filenames prevent even opening a 2025+ market-data file.
        paths = [path for year in (2023, 2024) for path in sorted(
            (data_root / "2026" / symbol).glob(f"{symbol}_H1_{year}_Q*.csv"))]
        if not paths:
            raise FileNotFoundError(f"no pre-OOS H1 data for {symbol}")
        h1 = DataLoader().close_index(DataLoader().load_csv(paths))
        assert_pre_oos(h1.index, "loader")
        data[symbol] = (h1, DataLoader.h4_from_h1(h1))
    return data


def assert_pre_oos(timestamps: Iterable, source: str) -> None:
    index = pd.DatetimeIndex(timestamps)
    if len(index) and (index >= OOS_START).any():
        raise ValueError(f"{source}: calendar year 2025+ TRUE OOS is locked")


def data_coverage(data: dict) -> dict:
    result = {}
    starts, ends = [], []
    for symbol in SYMBOLS:
        h1 = data[symbol][0]
        assert_pre_oos(h1.index, "coverage")
        starts.append(h1.index.min()); ends.append(h1.index.max())
        result[symbol] = {"first_timestamp": _iso(h1.index.min()),
                          "last_timestamp_pre_oos": _iso(h1.index.max()),
                          "H1_bars": int(len(h1))}
    common_start, common_end = max(starts), min(ends)
    result.update({"common_start": _iso(common_start), "common_end": _iso(common_end),
                   "common_months": int((common_end.year-common_start.year)*12 +
                                        common_end.month-common_start.month)})
    return result


def generate_folds(common_start: pd.Timestamp, common_end: pd.Timestamp) -> list[dict]:
    assert_pre_oos([common_start, common_end], "scheduler")
    threshold = common_start + pd.DateOffset(months=INITIAL_TRAIN_MONTHS)
    # Calendar windows begin at local midnight, never at common_start's
    # intraday clock component.
    first_test = pd.offsets.MonthBegin().rollforward(threshold.normalize())
    folds, test_start = [], first_test
    while True:
        test_end = test_start + pd.DateOffset(months=TEST_MONTHS)
        if test_end > common_end or test_end > OOS_START:
            break
        fold_id = f"WF{len(folds)+1:02d}"
        folds.append({"fold_id": fold_id, "train_start": common_start,
                      "train_end": test_start, "test_start": test_start,
                      "test_end": test_end,
                      "train_months": int((test_start.year-common_start.year)*12 +
                                          test_start.month-common_start.month),
                      "test_months": TEST_MONTHS, "status": "COMPLETE"})
        test_start += pd.DateOffset(months=STEP_MONTHS)
    for previous, current in zip(folds, folds[1:]):
        if previous["test_end"] > current["test_start"]:
            raise AssertionError("walk-forward test intervals overlap")
    return folds


def _stats(frame: pd.DataFrame, column: str = "net_R") -> dict:
    values = frame[column].astype(float) if len(frame) else pd.Series(dtype=float)
    gains, losses = values[values > 0].sum(), -values[values < 0].sum()
    pf = float(gains/losses) if losses else (math.inf if gains else None)
    cumulative = values.cumsum()
    drawdown = cumulative - cumulative.cummax().clip(lower=0)
    return {"trades": int(len(values)), "PF": pf,
            "expectancy": float(values.mean()) if len(values) else None,
            "net_R": float(values.sum()),
            "max_DD_R": float(drawdown.min()) if len(values) else 0.0,
            "winrate": float((values > 0).mean()) if len(values) else None}


def apply_cost(frame: pd.DataFrame, ticks: float) -> pd.DataFrame:
    result = frame.copy()
    result["cost_R"] = 2 * ticks * result["tick_size"] / result["initial_risk"]
    result["net_R"] = result["gross_R"] - result["cost_R"]
    return result


def run_fold(fold: dict, parameters: T3Parameters, data: dict) -> dict[str, pd.DataFrame]:
    pieces = []
    for symbol in SYMBOLS:
        h1, h4 = data[symbol]
        result = Backtester(FixedRiskPortfolio(), tick_size=TICK_SIZES[symbol]).run(
            T3MTFTrend(parameters), symbol, h1, h4,
            entry_start=fold["test_start"], entry_end=fold["test_end"])
        trades = result.trades.copy()
        if len(trades):
            trades["trade_id"] = fold["fold_id"] + "-" + trades["trade_id"]
            trades["fold_id"] = fold["fold_id"]
        pieces.append(trades)
    base = pd.concat(pieces, ignore_index=True).sort_values(
        ["entry_time", "trade_id"], kind="mergesort").reset_index(drop=True)
    if len(base):
        entries = pd.to_datetime(base.entry_time)
        if not ((entries >= fold["test_start"]) & (entries < fold["test_end"])).all():
            raise AssertionError("fold contains an entry outside its test interval")
        assert_pre_oos(entries, "backtester entries")
        assert_pre_oos(pd.to_datetime(base.exit_time), "backtester exits")
    return {name: apply_cost(base, ticks) for name, ticks in COSTS.items()}


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    out = frame.copy()
    for column in ("entry_time", "exit_time"):
        if column in out:
            out[column] = pd.to_datetime(out[column]).map(_iso)
    assert_artifact_pre_oos(out, path.name)
    out.to_csv(path, index=False, lineterminator="\n", float_format="%.12g")


def assert_artifact_pre_oos(frame: pd.DataFrame, source: str) -> None:
    for column in ("entry_time", "exit_time", "test_start", "train_start"):
        if column in frame and len(frame):
            assert_pre_oos(pd.to_datetime(frame[column], utc=True), f"report {source}")


def _streak(values: pd.Series, winning: bool) -> int:
    best = current = 0
    for value in values:
        current = current + 1 if ((value > 0) == winning) else 0
        best = max(best, current)
    return best


def _percentiles(values: pd.Series) -> dict:
    return {"mean": float(values.mean()) if len(values) else None,
            "median": float(values.median()) if len(values) else None,
            "p25": float(values.quantile(.25)) if len(values) else None,
            "p75": float(values.quantile(.75)) if len(values) else None,
            "p90": float(values.quantile(.90)) if len(values) else None}


def _svg(path: Path, title: str, labels: list[str], values: list[float], reference: float) -> None:
    finite = [v for v in values if v is not None and math.isfinite(v)] + [reference]
    lo, hi = min(finite), max(finite); span = hi-lo or 1.0
    xs = np.linspace(70, 870, max(1, len(values)))
    y = lambda v: 350-(v-lo)/span*280
    points = " ".join(f"{x:.1f},{y(v):.1f}" for x, v in zip(xs, values) if v is not None and math.isfinite(v))
    repeated = len(set(labels)) < len(labels)
    label_points = [(x, label) for i, (x, label) in enumerate(zip(xs, labels))
                    if not repeated or i == 0 or label != labels[i-1]]
    text = "".join(f'<text x="{x:.1f}" y="385" text-anchor="middle">{label}</text>' for x,label in label_points)
    boundaries = "".join(f'<line x1="{x:.1f}" y1="50" x2="{x:.1f}" y2="355" stroke="#bbb" stroke-dasharray="4 3"/>'
                         for x, _ in label_points) if repeated else ""
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="920" height="410"><rect width="100%" height="100%" fill="white"/>'
        f'<text x="20" y="25">{title}</text><line x1="55" y1="{y(reference):.1f}" x2="885" y2="{y(reference):.1f}" stroke="#888"/>'
        f'{boundaries}<polyline points="{points}" fill="none" stroke="#2563eb" stroke-width="2"/>{text}</svg>\n', encoding="utf-8")


def run(data_root: Path, output: Path = Path("TradingSystemLab/results/T3_walk_forward")) -> dict:
    root = Path.cwd(); output = Path(output); (output / "folds").mkdir(parents=True, exist_ok=True)
    parameters, frozen = load_frozen(root / "TradingSystemLab/results/T3_parameter_robustness/frozen_baseline.json")
    data = load_development_data(Path(data_root)); coverage = data_coverage(data)
    (output/"data_coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True)+"\n")
    common_start, common_end = pd.Timestamp(coverage["common_start"]), pd.Timestamp(coverage["common_end"])
    folds = generate_folds(common_start, common_end)
    parameter_hash = hashlib.sha256(json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    manifest_folds = [{**{k: (_iso(v) if isinstance(v, pd.Timestamp) else v) for k,v in fold.items()},
                       "parameters_hash": parameter_hash, "strategy_id": T3MTFTrend.name,
                       "cost_scenarios": COSTS} for fold in folds]
    (output/"folds.json").write_text(json.dumps(manifest_folds, indent=2, sort_keys=True)+"\n")
    all_costs = {name: [] for name in COSTS}; metric_rows=[]; train_rows=[]
    for fold in folds:
        frames = run_fold(fold, parameters, data)
        identities = [tuple(frame.trade_id) for frame in frames.values()]
        if len(set(identities)) != 1: raise AssertionError("cost scenarios changed trade identity")
        for name, frame in frames.items():
            all_costs[name].append(frame)
            _write_csv(frame.reindex(columns=TRADE_COLUMNS), output/"folds"/f"{fold['fold_id']}_trades_{name}.csv")
        row={"fold_id":fold["fold_id"], **{k: _iso(fold[k]) for k in
             ("train_start","train_end","test_start","test_end")}}
        row["trades"] = len(frames["C1"])
        for name in COSTS:
            stats=_stats(frames[name]); row.update({f"PF_{name}":stats["PF"],f"expectancy_{name}":stats["expectancy"],f"net_R_{name}":stats["net_R"]})
        c1=frames["C1"]; s1=_stats(c1); row.update({"max_DD_R_C1":s1["max_DD_R"],"winrate_C1":s1["winrate"],
            "LONG_trades":int((c1.direction=="LONG").sum()),"SHORT_trades":int((c1.direction=="SHORT").sum()),
            "Si_trades":int((c1.symbol=="Si").sum()),"CNY_trades":int((c1.symbol=="CNY").sum()),"positive_C1":bool(s1["net_R"]>0)})
        metric_rows.append(row)
        train_parts=[]
        for symbol in SYMBOLS:
            h1=data[symbol][0].loc[data[symbol][0].index < fold["test_start"]]; h4=DataLoader.h4_from_h1(h1)
            train_parts.append(Backtester(FixedRiskPortfolio(),tick_size=TICK_SIZES[symbol]).run(T3MTFTrend(parameters),symbol,h1,h4,entry_start=fold["train_start"],entry_end=fold["test_start"]).trades)
        train=apply_cost(pd.concat(train_parts,ignore_index=True),1.0); ts=_stats(train)
        train_rows.append({"fold_id":fold["fold_id"],"train_expectancy_C1":ts["expectancy"],"test_expectancy_C1":s1["expectancy"],
                           "expectancy_decay":None if ts["expectancy"] is None or s1["expectancy"] is None else s1["expectancy"]-ts["expectancy"],
                           "train_PF_C1":ts["PF"],"test_PF_C1":s1["PF"]})
    fold_metrics=pd.DataFrame(metric_rows); _write_csv(fold_metrics,output/"fold_metrics.csv")
    stitched={name:(pd.concat(parts,ignore_index=True).sort_values(["entry_time","trade_id"],kind="mergesort").reset_index(drop=True) if parts else pd.DataFrame()) for name,parts in all_costs.items()}
    if len(stitched["C1"]) and stitched["C1"].trade_id.duplicated().any(): raise AssertionError("duplicate forward trade")
    _write_csv(stitched["C1"].reindex(columns=TRADE_COLUMNS),output/"stitched_forward_trades_C1.csv")
    agg={"total_trades":len(stitched["C1"]),"positive_folds":int(fold_metrics.positive_C1.sum()) if len(fold_metrics) else 0,
         "negative_folds":int((~fold_metrics.positive_C1).sum()) if len(fold_metrics) else 0}
    for name in COSTS:
        stats=_stats(stitched[name]); agg.update({f"PF_{name}":stats["PF"],f"expectancy_{name}":stats["expectancy"],f"net_R_{name}":stats["net_R"]})
    c1=stitched["C1"]; s1=_stats(c1); cumulative=c1.net_R.cumsum() if len(c1) else pd.Series(dtype=float)
    agg.update({"average_R_C1":s1["expectancy"],"median_R_C1":float(c1.net_R.median()) if len(c1) else None,
                "win_rate_C1":s1["winrate"],"max_drawdown_R_C1":s1["max_DD_R"],
                "max_losing_streak":_streak(c1.net_R,False),"max_winning_streak":_streak(c1.net_R,True),
                "recovery_factor":float(c1.net_R.sum()/abs(s1["max_DD_R"])) if s1["max_DD_R"] else None})
    (output/"aggregate_metrics.json").write_text(json.dumps(agg,indent=2,sort_keys=True,allow_nan=False)+"\n")
    positive_total=float(c1.loc[c1.net_R>0,"net_R"].sum()) if len(c1) else 0.0; total=float(c1.net_R.sum()) if len(c1) else 0.0
    concentration=[]
    for fold in folds:
        part=c1[c1.fold_id==fold["fold_id"]]; pos=float(part.loc[part.net_R>0,"net_R"].sum()); net=float(part.net_R.sum())
        concentration.append({"fold_id":fold["fold_id"],"net_R_C1":net,"positive_R_C1":pos,
            "share_of_total_positive_R":pos/positive_total if positive_total else None,"share_of_total_net_R":net/total if total else None})
    concentration_frame=pd.DataFrame(concentration); _write_csv(concentration_frame,output/"fold_concentration.csv")
    shares=sorted(concentration_frame.share_of_total_positive_R.dropna(),reverse=True) if len(concentration_frame) else []
    top1=shares[0] if shares else None; top2=sum(shares[:2]) if shares else None
    instrument=[]
    for symbol in SYMBOLS:
        stats=_stats(c1[c1.symbol==symbol]); instrument.append({"symbol":symbol,**{k:stats[k] for k in ("trades","PF","expectancy","net_R","max_DD_R","winrate")}})
    instrument_frame=pd.DataFrame(instrument); instrument_frame.columns=["symbol","trades","PF_C1","expectancy_C1","net_R_C1","max_DD_R_C1","winrate"]
    _write_csv(instrument_frame,output/"instrument_report.csv")
    direction=[]
    for name in ("LONG","SHORT"):
        stats=_stats(c1[c1.direction==name]); direction.append({"direction":name,"trades":stats["trades"],"PF_C1":stats["PF"],"expectancy_C1":stats["expectancy"],"net_R_C1":stats["net_R"]})
    direction_frame=pd.DataFrame(direction); _write_csv(direction_frame,output/"direction_report.csv")
    years=[]
    if len(c1):
        for year in sorted(pd.to_datetime(c1.entry_time).dt.year.unique()):
            stats=_stats(c1[pd.to_datetime(c1.entry_time).dt.year==year]); years.append({"year":int(year),"trades":stats["trades"],"PF_C1":stats["PF"],"expectancy_C1":stats["expectancy"],"net_R_C1":stats["net_R"],"max_DD_R_C1":stats["max_DD_R"]})
    year_frame=pd.DataFrame(years,columns=["year","trades","PF_C1","expectancy_C1","net_R_C1","max_DD_R_C1"]); _write_csv(year_frame,output/"year_report.csv")
    mae=[]
    for label,part in (("all",c1),("winners",c1[c1.net_R>0]),("losers",c1[c1.net_R<=0])):
        a,b=_percentiles(part.MAE_R),_percentiles(part.MFE_R); mae.append({"group":label,"mean_MAE_R":a["mean"],"median_MAE_R":a["median"],"p75_MAE_R":a["p75"],"p90_MAE_R":a["p90"],"mean_MFE_R":b["mean"],"median_MFE_R":b["median"],"p75_MFE_R":b["p75"],"p90_MFE_R":b["p90"]})
    mae_frame=pd.DataFrame(mae); _write_csv(mae_frame,output/"mae_mfe_report.csv")
    efficiency=c1.loc[(c1.net_R>0)&(c1.MFE_R>0),"net_R"]/c1.loc[(c1.net_R>0)&(c1.MFE_R>0),"MFE_R"]
    eff=_percentiles(efficiency); _write_csv(pd.DataFrame([{"mean":eff["mean"],"median":eff["median"],"p25":eff["p25"],"p75":eff["p75"]}]),output/"exit_efficiency.csv")
    decay=pd.DataFrame(train_rows); _write_csv(decay,output/"train_test_decay.csv")
    (output/"baseline_reference.json").write_text(json.dumps({"trades":109,"PF_C1":2.050317,"expectancy_C1":0.463443,"net_R_C1":50.515282},indent=2,sort_keys=True)+"\n")
    enough=len(folds)>=3
    instrument_pass=all(row["trades"]<20 or row["expectancy"]>0 for row in instrument)
    positive_share=agg["positive_folds"]/len(folds) if folds else 0
    pass_all=(enough and agg["total_trades"]>=50 and (agg["expectancy_C1"] or 0)>0 and (agg["PF_C1"] or 0)>1.2 and agg["net_R_C1"]>0 and positive_share>=.6 and (top1 is None or top1<.7) and instrument_pass)
    if not enough: verdict="INSUFFICIENT_HISTORY"
    elif pass_all: verdict="WALK_FORWARD_PASS"
    elif (agg["expectancy_C1"] or 0)>0 and (agg["PF_C1"] or 0)>1 and agg["net_R_C1"]>0: verdict="WALK_FORWARD_BORDERLINE"
    else: verdict="WALK_FORWARD_FAIL"
    manifest={"strategy_id":T3MTFTrend.name,"strategy_parameters":frozen,"symbols":list(SYMBOLS),"tick_sizes":TICK_SIZES,
        "cost_primary":"C1: 1 configured tick per side","common_start":coverage["common_start"],"common_end":coverage["common_end"],
        "initial_train_months":INITIAL_TRAIN_MONTHS,"test_months":TEST_MONTHS,"step_months":STEP_MONTHS,
        "fold_count":len(folds),"forward_trade_count":len(c1),"true_oos_blocked":True,"verdict":verdict}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    _svg(output/"fold_expectancy_C1.svg","Fold C1 expectancy",list(fold_metrics.fold_id),list(fold_metrics.expectancy_C1),0)
    _svg(output/"fold_pf_C1.svg","Fold C1 profit factor",list(fold_metrics.fold_id),list(fold_metrics.PF_C1),1)
    _svg(output/"forward_equity_C1.svg","Stitched forward C1 cumulative R",list(c1.fold_id) if len(c1) else [],list(cumulative),0)
    fold_lines="\n".join(f"- {r.fold_id}: C1 PF {r.PF_C1:.6f}, expectancy {r.expectancy_C1:.6f} R, net {r.net_R_C1:.6f} R." for r in fold_metrics.itertuples())
    report=f"""# T3 Causal Walk Forward Validation

## Frozen Strategy
`{T3MTFTrend.name}` used the frozen Sprint 5 JSON unchanged; no fold selected or adapted parameters.

## Data Coverage
Common causal H1 coverage is {coverage['common_start']} through {coverage['common_end']} ({coverage['common_months']} month offsets).

## Fold Schedule
Expanding train, 12-month minimum, three-calendar-month test and step; {len(folds)} complete folds. Partial windows are discarded.

## Causality Rules
Every fold starts FLAT. Only entries in `[test_start, test_end)` count. A test entry may close after `test_end` and remains solely in its originating fold. H4 rows are complete four-H1-bar blocks labelled at the final close; indicator warm-up is historical and rolling computations are backward-looking.

## Fold Results
{fold_lines}

## Aggregate Forward Results
C1: {len(c1)} trades, PF {agg['PF_C1']:.6f}, expectancy {agg['expectancy_C1']:.6f} R, net {agg['net_R_C1']:.6f} R.

## Cost Robustness
C0/C1/C2 expectancy: {agg['expectancy_C0']:.6f} / {agg['expectancy_C1']:.6f} / {agg['expectancy_C2']:.6f} R. C1 alone determines the verdict.

## Instrument Robustness
See `instrument_report.csv`; the pre-declared conditional 20-trade checks are applied without selection.

## Direction Robustness
See `direction_report.csv`; LONG and SHORT are diagnostics, not selection inputs.

## Year Robustness
See `year_report.csv`, grouped by forward entry year only.

## Fold Concentration
Top-one/top-two positive-R shares are {top1 if top1 is not None else 'N/A'} / {top2 if top2 is not None else 'N/A'}.

## MAE/MFE
See `mae_mfe_report.csv`; exit efficiency is diagnostic and trailing parameters were not changed.

## Train vs Test Decay
See `train_test_decay.csv`. Train results are diagnostic only and never enter parameter selection or the verdict.

## Limitations
This is a development walk-forward, not TRUE OOS. TRUE OOS 2025+ was not read or used. The parameter robustness map was performed previously; parameters in this Sprint were completely frozen. Results must not be described as TRUE OOS.

## Final Verdict
**{verdict}**
"""
    (output/"final_report.md").write_text(report,encoding="utf-8")
    return {**manifest,"aggregate":agg,"positive_fold_share":positive_share,"top_1_fold_positive_R_share":top1,"top_2_fold_positive_R_share":top2}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--data-root",type=Path,required=True); parser.add_argument("--output",type=Path,default=Path("TradingSystemLab/results/T3_walk_forward")); args=parser.parse_args()
    print(json.dumps(run(args.data_root,args.output),indent=2))
