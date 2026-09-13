"""Frozen T3 extended pre-OOS validation.

The runner is intentionally fail-closed: files containing a 2025+ row are
inventoried as contaminated but never passed to feature or strategy code.
There is no parameter-search surface in this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

from .core.data_loader import DataLoader
from .run_t3_walk_forward import (COSTS, INITIAL_TRAIN_MONTHS, OOS_START,
    STEP_MONTHS, SYMBOLS, TEST_MONTHS, TICK_SIZES, TRADE_COLUMNS, _iso, _stats,
    _streak, _svg, apply_cost, assert_pre_oos, generate_folds, load_frozen,
    run_fold)
from .strategies.trend.T3_MTF_Trend import T3MTFTrend

OUTPUT = Path("TradingSystemLab/results/T3_extended_validation")
PARITY_SOURCE = Path("TradingSystemLab/results/T3_walk_forward")
SEED, ITERATIONS = 20260913, 10_000
EXPECTED = {"trades": 39, "PF": 2.092928448988337,
            "expectancy": .4994669848709337, "net_R": 19.479212409966415}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _csv(frame: pd.DataFrame, path: Path) -> None:
    out = frame.copy()
    for column in ("entry_time", "exit_time", "train_start", "train_end", "test_start", "test_end"):
        if column in out:
            out[column] = pd.to_datetime(out[column]).map(_iso)
    out.to_csv(path, index=False, lineterminator="\n", float_format="%.12g")


def _json(value: object, path: Path) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _candidate(path: Path) -> tuple[str | None, str | None]:
    name = path.name.upper()
    symbol = next((s for s in SYMBOLS if name.startswith(s.upper() + "_")), None)
    timeframe = "H1" if "_H1_" in name else None
    return symbol, timeframe


def inventory(data_root: Path) -> tuple[pd.DataFrame, dict[str, list[Path]]]:
    """Inspect candidate CSVs for quality; return only wholly pre-OOS H1 files."""
    rows, valid = [], {s: [] for s in SYMBOLS}
    for path in sorted(data_root.rglob("*.csv"), key=lambda p: p.as_posix().lower()):
        symbol, timeframe = _candidate(path)
        if symbol is None:
            continue
        row = {"symbol": symbol, "file/path": str(path.relative_to(data_root)).replace("\\", "/"),
               "first_timestamp": "", "last_timestamp": "", "bars": 0,
               "timeframe": timeframe or "UNSUPPORTED", "timezone": "",
               "duplicate_count": 0, "malformed_rows": 0, "status": "UNSUPPORTED"}
        if timeframe != "H1":
            rows.append(row); continue
        try:
            parsed = DataLoader(forbid_true_oos=False)._read(path)
            times = parsed.index
            malformed = pd.Series(False, index=range(len(parsed)))
            row.update({"bars": len(parsed), "timezone": "Europe/Moscow",
                        "duplicate_count": int(times.duplicated().sum()), "malformed_rows": 0})
            if (times >= OOS_START).any():
                # Do not serialize OOS-derived bounds into an artifact.
                row["status"] = "OOS_CONTAMINATED"
            else:
                row.update({"first_timestamp": _iso(times.min()), "last_timestamp": _iso(times.max())})
                row["status"] = "VALID" if not bool(malformed.any()) and not times.duplicated().any() and times.is_monotonic_increasing else "INVALID"
                if row["status"] == "VALID": valid[symbol].append(path)
        except Exception:
            row["status"] = "INVALID"; row["malformed_rows"] = -1
        rows.append(row)
    frame = pd.DataFrame(rows, columns=["symbol", "file/path", "first_timestamp", "last_timestamp", "bars", "timeframe", "timezone", "duplicate_count", "malformed_rows", "status"])
    return frame, valid


def load_files(paths: list[Path]) -> pd.DataFrame:
    frame = DataLoader().close_index(DataLoader().load_csv(paths))
    assert_pre_oos(frame.index, "extended loader")
    return frame


def parity_gate(data_root: Path, output: Path) -> dict:
    """Re-execute all three Sprint 6 folds and compare every identity field."""
    parameters, _ = load_frozen(Path("TradingSystemLab/results/T3_parameter_robustness/frozen_baseline.json"))
    data = {}
    for symbol in SYMBOLS:
        paths = [p for year in (2023, 2024) for p in sorted((data_root / "2026" / symbol).glob(f"{symbol}_H1_{year}_Q*.csv"))]
        h1 = load_files(paths); data[symbol] = (h1, DataLoader.h4_from_h1(h1))
    start = max(x[0].index.min() for x in data.values()); end = min(x[0].index.max() for x in data.values())
    actual = pd.concat([run_fold(f, parameters, data)["C1"] for f in generate_folds(start, end)], ignore_index=True).sort_values(["entry_time", "trade_id"], kind="mergesort").reset_index(drop=True)
    expected = pd.read_csv(PARITY_SOURCE / "stitched_forward_trades_C1.csv")
    identity = ["trade_id", "symbol", "direction", "entry_time", "entry_price", "initial_stop", "exit_time", "exit_price", "exit_reason", "gross_R", "cost_R", "net_R"]
    comparable = actual[identity].copy()
    for c in ("entry_time", "exit_time"): comparable[c] = pd.to_datetime(comparable[c]).map(_iso)
    expected = expected[identity].copy()
    for c in ("entry_time", "exit_time"): expected[c] = pd.to_datetime(expected[c]).map(_iso)
    numeric = [c for c in identity if c not in ("trade_id", "symbol", "direction", "entry_time", "exit_time", "exit_reason")]
    maxdiff = max([float(np.max(np.abs(comparable[c].astype(float)-expected[c].astype(float)))) for c in numeric] + [0.0]) if len(actual) == len(expected) else math.inf
    stats = _stats(actual)
    ok = len(actual) == EXPECTED["trades"] and comparable.drop(columns=numeric).equals(expected.drop(columns=numeric)) and maxdiff <= 1e-10 and all(abs(stats[k]-EXPECTED[k]) <= 1e-10 for k in ("PF", "expectancy", "net_R"))
    report = {"status": "PASS" if ok else "FAIL", "expected_trades": 39, "actual_trades": len(actual), "expected_PF_C1": EXPECTED["PF"], "actual_PF_C1": stats["PF"], "expected_expectancy_C1": EXPECTED["expectancy"], "actual_expectancy_C1": stats["expectancy"], "expected_net_R_C1": EXPECTED["net_R"], "actual_net_R_C1": stats["net_R"], "max_numeric_difference": maxdiff}
    _json(report, output / "parity_report.json")
    if not ok: raise RuntimeError("Sprint 6 parity gate failed; extended validation stopped")
    return report


def bootstrap(values: np.ndarray, blocks: list[np.ndarray]) -> pd.DataFrame:
    if not len(values) or not blocks: return pd.DataFrame(columns=["method", "seed", "iterations", "p2.5", "p5", "median", "p95", "p97.5", "probability(mean_R > 0)", "warning"])
    rng = np.random.default_rng(SEED)
    iid = rng.choice(values, (ITERATIONS, len(values)), replace=True).mean(1)
    picks = rng.integers(0, len(blocks), (ITERATIONS, len(blocks)))
    block = np.array([np.concatenate([blocks[i] for i in row]).mean() for row in picks])
    result=[]
    for method, sample, warning in (("TRADE_IID_BOOTSTRAP_DIAGNOSTIC_ONLY", iid, "iid assumption ignores temporal dependence."), ("FOLD_BLOCK_BOOTSTRAP", block, "")):
        result.append({"method":method,"seed":SEED,"iterations":ITERATIONS,"p2.5":np.percentile(sample,2.5),"p5":np.percentile(sample,5),"median":np.median(sample),"p95":np.percentile(sample,95),"p97.5":np.percentile(sample,97.5),"probability(mean_R > 0)":np.mean(sample>0),"warning":warning})
    return pd.DataFrame(result)


def _metric_rows(trades: pd.DataFrame, column: str, values) -> pd.DataFrame:
    rows=[]
    for value in values:
        s=_stats(trades[trades[column] == value]); rows.append({column:value,"trades":s["trades"],"PF_C1":s["PF"],"expectancy_C1":s["expectancy"],"net_R_C1":s["net_R"],"max_DD_R_C1":s["max_DD_R"],"winrate_C1":s["winrate"]})
    return pd.DataFrame(rows)


def _required(output: Path) -> None:
    (output / "required_data.md").write_text("# Required pre-OOS data\n\nAdd read-only **Si H1** and **CNY H1** files with common coverage, preferably `2020-01-01` through `2024-12-31`, and minimally `2021-01-01` through `2024-12-31`. TRUE OOS 2025+ is neither required nor permitted. Do not copy source market data into this repository.\n", encoding="utf-8")


def run(data_root: Path, output: Path = OUTPUT) -> dict:
    output.mkdir(parents=True, exist_ok=True); (output / "folds").mkdir(exist_ok=True)
    parity = parity_gate(data_root, output)
    inv, candidates = inventory(data_root); _csv(inv, output / "data_inventory.csv")
    usable, used = {}, []
    for symbol in SYMBOLS:
        pre = [p for p in candidates[symbol] if pd.Timestamp(inv.loc[inv["file/path"] == str(p.relative_to(data_root)).replace("\\","/"), "first_timestamp"].iloc[0]).year < 2023]
        # Entire valid source set is used only when it has pre-2023 history.
        if pre: usable[symbol] = load_files(candidates[symbol]); used.extend((symbol,p) for p in candidates[symbol])
    manifest_rows=[]
    for symbol,path in used:
        frame=load_files([path]); manifest_rows.append({"symbol":symbol,"file":str(path.relative_to(data_root)).replace("\\","/"),"size_bytes":path.stat().st_size,"sha256":sha256(path),"first_timestamp":_iso(frame.index.min()),"last_timestamp":_iso(frame.index.max()),"bars":len(frame)})
    data_manifest=pd.DataFrame(manifest_rows,columns=["symbol","file","size_bytes","sha256","first_timestamp","last_timestamp","bars"]); _csv(data_manifest,output/"data_manifest.csv")
    starts={s:(_iso(usable[s].index.min()) if s in usable else None) for s in SYMBOLS}; ends={s:(_iso(usable[s].index.max()) if s in usable else None) for s in SYMBOLS}
    common_start=max((usable[s].index.min() for s in SYMBOLS),default=None) if len(usable)==2 else None; common_end=min((usable[s].index.max() for s in SYMBOLS),default=None) if len(usable)==2 else None
    coverage={"Si_start":starts["Si"],"Si_end":ends["Si"],"Si_bars":len(usable.get("Si",[])),"CNY_start":starts["CNY"],"CNY_end":ends["CNY"],"CNY_bars":len(usable.get("CNY",[])),"common_start":_iso(common_start) if common_start is not None else None,"common_end":_iso(common_end) if common_end is not None else None,"common_months":((common_end.year-common_start.year)*12+common_end.month-common_start.month) if common_start is not None else 0,"common_years":sorted(set(range(common_start.year,common_end.year+1))) if common_start is not None else [],"pre_2023_available":bool(common_start is not None and common_start.year<2023),"true_oos_blocked":True}; _json(coverage,output/"common_coverage.json")
    parameters,frozen=load_frozen(Path("TradingSystemLab/results/T3_parameter_robustness/frozen_baseline.json"))
    if not coverage["pre_2023_available"]:
        _required(output)
        empty_specs={"fold_metrics.csv":[],"stitched_forward_trades_C0.csv":TRADE_COLUMNS,"stitched_forward_trades_C1.csv":TRADE_COLUMNS,"stitched_forward_trades_C2.csv":TRADE_COLUMNS,"leave_one_fold_out.csv":[],"fold_concentration.csv":[],"trade_concentration.csv":[],"instrument_report.csv":[],"instrument_by_fold.csv":[],"direction_report.csv":[],"direction_by_fold.csv":[],"year_report.csv":[],"mae_mfe_report.csv":[],"exit_reason_report.csv":[],"rolling_forward_summary.csv":[],"uncertainty_report.csv":[],"comparison_2023_2024_vs_extended.csv":[]}
        for name,cols in empty_specs.items(): _csv(pd.DataFrame(columns=cols),output/name)
        _json([],output/"folds.json"); _json({"folds":0,"trades":0},output/"aggregate_metrics.json")
        for name in ("extended_equity_C1.svg","fold_expectancy_C1.svg","fold_net_R_C1.svg","year_expectancy_C1.svg","instrument_expectancy_C1.svg","direction_expectancy_C1.svg"): _svg(output/name,name,[],[],0)
        result={"strategy_id":T3MTFTrend.name,"frozen_parameters":frozen,"parameter_source":"TradingSystemLab/results/T3_parameter_robustness/frozen_baseline.json","tick_sizes":TICK_SIZES,"cost_primary":"C1: 1 tick per side","data_files":[],"data_hashes":{},"common_start":None,"common_end":None,"initial_train_months":12,"test_months":3,"step_months":3,"fold_count":0,"forward_trade_count":0,"forward_year_count":0,"true_oos_blocked":True,"parity_status":parity["status"],"verdict":"DATA_BLOCKED"}
        _json(result,output/"manifest.json"); (output/"final_report.md").write_text("# T3 Extended Pre-OOS Temporal Validation\n\nSprint 6 parity: **PASS**. No usable common Si/CNY history before 2023 was found. Extended research was not simulated. TRUE OOS remained blocked.\n\n## Final Verdict\n\n**DATA_BLOCKED**\n",encoding="utf-8"); return result
    data={s:(usable[s],DataLoader.h4_from_h1(usable[s])) for s in SYMBOLS}; folds=generate_folds(common_start,common_end); _json([{k:_iso(v) if isinstance(v,pd.Timestamp) else v for k,v in f.items()} for f in folds],output/"folds.json")
    costs={k:[] for k in COSTS}; fm=[]
    for fold in folds:
        frames=run_fold(fold,parameters,data)
        for c,frame in frames.items(): costs[c].append(frame); _csv(frame.reindex(columns=TRADE_COLUMNS),output/"folds"/f"{fold['fold_id']}_trades_{c}.csv")
        row={"fold_id":fold["fold_id"],**{x:_iso(fold[x]) for x in ("train_start","train_end","test_start","test_end")},"trades":len(frames["C1"])}
        for c in COSTS: s=_stats(frames[c]); row.update({f"PF_{c}":s["PF"],f"expectancy_{c}":s["expectancy"],f"net_R_{c}":s["net_R"]})
        s=_stats(frames["C1"]); row.update({"max_DD_R_C1":s["max_DD_R"],"winrate_C1":s["winrate"],"LONG_trades":int((frames["C1"].direction=="LONG").sum()),"SHORT_trades":int((frames["C1"].direction=="SHORT").sum()),"Si_trades":int((frames["C1"].symbol=="Si").sum()),"CNY_trades":int((frames["C1"].symbol=="CNY").sum()),"positive_expectancy_C1":bool((s["expectancy"] or 0)>0),"positive_net_R_C1":bool(s["net_R"]>0)}); fm.append(row)
    fold_metrics=pd.DataFrame(fm); _csv(fold_metrics,output/"fold_metrics.csv")
    stitched={c:pd.concat(v,ignore_index=True).sort_values(["entry_time","trade_id"],kind="mergesort").reset_index(drop=True) for c,v in costs.items()}
    for c,frame in stitched.items(): _csv(frame.reindex(columns=TRADE_COLUMNS),output/f"stitched_forward_trades_{c}.csv")
    c1=stitched["C1"]; aggregate={"folds":len(folds),"trades":len(c1),"forward_years":int(pd.to_datetime(c1.entry_time).dt.year.nunique()),"positive_expectancy_folds":int(fold_metrics.positive_expectancy_C1.sum()),"positive_net_folds":int(fold_metrics.positive_net_R_C1.sum())}
    for c in COSTS: s=_stats(stitched[c]); aggregate.update({f"PF_{c}":s["PF"],f"expectancy_{c}":s["expectancy"],f"net_R_{c}":s["net_R"]})
    s=_stats(c1); aggregate.update({"median_R_C1":float(c1.net_R.median()),"winrate_C1":s["winrate"],"max_DD_R_C1":s["max_DD_R"],"max_winning_streak":_streak(c1.net_R,True),"max_losing_streak":_streak(c1.net_R,False),"recovery_factor":s["net_R"]/abs(s["max_DD_R"]) if s["max_DD_R"] else None}); _json(aggregate,output/"aggregate_metrics.json")
    loo=[]
    for label,part in [("ALL",c1)]+[(f"WITHOUT_{f['fold_id']}",c1[c1.fold_id!=f["fold_id"]]) for f in folds]:
        x=_stats(part); loo.append({"subset":label,"trades":x["trades"],"PF_C1":x["PF"],"expectancy_C1":x["expectancy"],"net_R_C1":x["net_R"],"max_DD_R_C1":x["max_DD_R"],"winrate_C1":x["winrate"]})
    _csv(pd.DataFrame(loo),output/"leave_one_fold_out.csv")
    foldc=[]; pos=c1.loc[c1.net_R>0,"net_R"].sum(); total=c1.net_R.sum()
    for f in folds:
        p=c1[c1.fold_id==f["fold_id"]]; foldc.append({"fold_id":f["fold_id"],"trades":len(p),"net_R_C1":p.net_R.sum(),"positive_R_C1":p.loc[p.net_R>0,"net_R"].sum(),"share_of_total_positive_R":p.loc[p.net_R>0,"net_R"].sum()/pos,"share_of_total_net_R":p.net_R.sum()/total})
    fcf=pd.DataFrame(foldc); shares=sorted(fcf.share_of_total_positive_R,reverse=True); fcf["top_1_fold_positive_R_share"]=[shares[0]]+[None]*(len(fcf)-1); fcf["top_2_fold_positive_R_share"]=[sum(shares[:2])]+[None]*(len(fcf)-1); fcf["top_3_fold_positive_R_share"]=[sum(shares[:3])]+[None]*(len(fcf)-1); _csv(fcf,output/"fold_concentration.csv")
    wins=c1[c1.net_R>0].sort_values(["net_R","trade_id"],ascending=[False,True],kind="mergesort"); tc={f"top_{n}_positive_R_share":wins.head(n).net_R.sum()/pos for n in (1,3,5,10)}
    for n,label in ((1,"best_trade"),(3,"top3"),(5,"top5")):
        x=_stats(c1.drop(wins.head(n).index)); tc.update({f"net_R_without_{label}":x["net_R"],f"PF_without_{label}":x["PF"],f"expectancy_without_{label}":x["expectancy"]})
    _csv(pd.DataFrame([tc]),output/"trade_concentration.csv")
    inst=_metric_rows(c1,"symbol",SYMBOLS); dire=_metric_rows(c1,"direction",("LONG","SHORT")); _csv(inst,output/"instrument_report.csv"); _csv(dire.drop(columns="winrate_C1"),output/"direction_report.csv")
    _csv(pd.concat([_metric_rows(c1[c1.fold_id==f["fold_id"]],"symbol",SYMBOLS).assign(fold_id=f["fold_id"]) for f in folds]),output/"instrument_by_fold.csv"); _csv(pd.concat([_metric_rows(c1[c1.fold_id==f["fold_id"]],"direction",("LONG","SHORT")).assign(fold_id=f["fold_id"]) for f in folds]),output/"direction_by_fold.csv")
    years=_metric_rows(c1.assign(year=pd.to_datetime(c1.entry_time).dt.year),"year",sorted(pd.to_datetime(c1.entry_time).dt.year.unique())); _csv(years,output/"year_report.csv")
    groups=[("ALL",c1),("LONG",c1[c1.direction=="LONG"]),("SHORT",c1[c1.direction=="SHORT"]),("Si",c1[c1.symbol=="Si"]),("CNY",c1[c1.symbol=="CNY"])]+[(f["fold_id"],c1[c1.fold_id==f["fold_id"]]) for f in folds]
    mm=[]
    for name,p in groups: mm.append({"group":name,**{f"{stat}_{kind}_R":getattr(p[f"{kind}_R"],stat)() for kind in ("MAE","MFE") for stat in ("mean","median")},**{f"p{q}_{kind}_R":p[f"{kind}_R"].quantile(q/100) for kind in ("MAE","MFE") for q in (75,90)}})
    _csv(pd.DataFrame(mm),output/"mae_mfe_report.csv")
    er=[]
    for breakdown,key,p in [("overall","ALL",c1)]+[("fold",f["fold_id"],c1[c1.fold_id==f["fold_id"]]) for f in folds]+[("instrument",x,c1[c1.symbol==x]) for x in SYMBOLS]+[("direction",x,c1[c1.direction==x]) for x in ("LONG","SHORT")]:
        for reason,q in p.groupby("exit_reason",sort=True): er.append({"breakdown":breakdown,"group":key,"exit_reason":reason,"trades":len(q),"expectancy_R":q.net_R.mean(),"net_R":q.net_R.sum(),"mean_MAE_R":q.MAE_R.mean(),"mean_MFE_R":q.MFE_R.mean()})
    _csv(pd.DataFrame(er),output/"exit_reason_report.csv")
    rolling=[]
    temp=c1.assign(period=pd.to_datetime(c1.entry_time).dt.to_period("Q").astype(str))
    for period,p in temp.groupby("period",sort=True): x=_stats(p); rolling.append({"period":period,"trades":x["trades"],"expectancy_C1":x["expectancy"],"net_R_C1":x["net_R"],"max_DD_R_C1":x["max_DD_R"]})
    _csv(pd.DataFrame(rolling),output/"rolling_forward_summary.csv"); _csv(bootstrap(c1.net_R.to_numpy(),[p.net_R.to_numpy() for _,p in c1.groupby("fold_id",sort=True)]),output/"uncertainty_report.csv")
    sprint=pd.read_json(PARITY_SOURCE/"aggregate_metrics.json",typ="series"); comparison=[{"sample":"SPRINT6_2023_2024","common_start":"2023-01-03","common_end":"2024-12-31","folds":3,"forward_years":1,"trades":39,"PF_C1":EXPECTED["PF"],"expectancy_C1":EXPECTED["expectancy"],"net_R_C1":EXPECTED["net_R"],"max_DD_R_C1":sprint["max_drawdown_R_C1"],"positive_expectancy_fold_share":2/3,"positive_net_fold_share":2/3,"top1_fold_positive_share":None,"top3_trade_positive_share":None},{"sample":"EXTENDED_PRE_OOS","common_start":_iso(common_start),"common_end":_iso(common_end),"folds":len(folds),"forward_years":aggregate["forward_years"],"trades":len(c1),"PF_C1":aggregate["PF_C1"],"expectancy_C1":aggregate["expectancy_C1"],"net_R_C1":aggregate["net_R_C1"],"max_DD_R_C1":aggregate["max_DD_R_C1"],"positive_expectancy_fold_share":aggregate["positive_expectancy_folds"]/len(folds),"positive_net_fold_share":aggregate["positive_net_folds"]/len(folds),"top1_fold_positive_share":shares[0],"top3_trade_positive_share":tc["top_3_positive_R_share"]}]; _csv(pd.DataFrame(comparison),output/"comparison_2023_2024_vs_extended.csv")
    pass_sample=len(folds)>=8 and len(c1)>=100 and aggregate["forward_years"]>=3; positive=aggregate["PF_C1"]>1 and aggregate["expectancy_C1"]>0 and aggregate["net_R_C1"]>0
    pass_all=pass_sample and aggregate["PF_C1"]>1.2 and aggregate["positive_expectancy_folds"]/len(folds)>=.6 and aggregate["positive_net_folds"]/len(folds)>=.6 and all(r["expectancy_C1"]>0 and r["net_R_C1"]>0 for r in loo[1:]) and shares[0]<.5 and tc["top_3_positive_R_share"]<.7 and all(r.expectancy_C1>0 for r in inst.itertuples() if r.trades>=30)
    verdict="EXTENDED_WF_PASS" if pass_all else ("INSUFFICIENT_EXTENDED_HISTORY" if not pass_sample else ("EXTENDED_WF_BORDERLINE" if positive else "EXTENDED_WF_FAIL"))
    hashes={r["file"]:r["sha256"] for r in manifest_rows}; result={"strategy_id":T3MTFTrend.name,"frozen_parameters":frozen,"parameter_source":"TradingSystemLab/results/T3_parameter_robustness/frozen_baseline.json","tick_sizes":TICK_SIZES,"cost_primary":"C1: 1 tick per side","data_files":list(hashes),"data_hashes":hashes,"common_start":_iso(common_start),"common_end":_iso(common_end),"initial_train_months":12,"test_months":3,"step_months":3,"fold_count":len(folds),"forward_trade_count":len(c1),"forward_year_count":aggregate["forward_years"],"true_oos_blocked":True,"parity_status":"PASS","verdict":verdict}; _json(result,output/"manifest.json")
    _svg(output/"extended_equity_C1.svg","Extended C1 equity",list(c1.trade_id),list(c1.net_R.cumsum()),0); _svg(output/"fold_expectancy_C1.svg","Fold C1 expectancy",list(fold_metrics.fold_id),list(fold_metrics.expectancy_C1),0); _svg(output/"fold_net_R_C1.svg","Fold C1 net R",list(fold_metrics.fold_id),list(fold_metrics.net_R_C1),0); _svg(output/"year_expectancy_C1.svg","Year C1 expectancy",list(years.year.astype(str)),list(years.expectancy_C1),0); _svg(output/"instrument_expectancy_C1.svg","Instrument C1 expectancy",list(inst.symbol),list(inst.expectancy_C1),0); _svg(output/"direction_expectancy_C1.svg","Direction C1 expectancy",list(dire.direction),list(dire.expectancy_C1),0)
    (output/"final_report.md").write_text(f"# T3 Extended Pre-OOS Temporal Validation\n\nFrozen parameters and the predeclared expanding schedule were used without optimization. Sprint 6 parity: **PASS**. {len(folds)} complete folds produced {len(c1)} trades. C1 PF {aggregate['PF_C1']:.6f}, expectancy {aggregate['expectancy_C1']:.6f} R, net {aggregate['net_R_C1']:.6f} R. TRUE OOS stayed blocked; uncertainty results are diagnostic only.\n\n## Final Verdict\n\n**{verdict}**\n",encoding="utf-8"); return result


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--data-root",type=Path,required=True); parser.add_argument("--output",type=Path,default=OUTPUT); args=parser.parse_args(); print(json.dumps(run(args.data_root,args.output),indent=2))
