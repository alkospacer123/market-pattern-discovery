"""Deterministic expanding-window validation for the frozen Phase 3.3 candidates.

There is deliberately no selection or parameter-space API in this module.  A
fold is executed from a fresh strategy instance on its own interval, which is
the simplest auditable guarantee that positions and mutable state cannot cross
fold boundaries.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import pandas as pd

from ..core.data_loader import DataLoader
from ..core.unified_metrics import finite, stats
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, SCENARIOS, SPACES, execute
from ..optimization.validation import reject_true_oos

DEVELOPMENT_START = pd.Timestamp("2023-01-01", tz="UTC")
TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="UTC")

# Predeclared calendar-quarter tests give four observations while retaining a
# full development year for the first training window.  Every later training
# interval contains all earlier test intervals; none reaches TRUE OOS.
SCHEDULE = (
    ("WF01", "2023-01-01", "2023-12-31 23:59:59", "2024-01-01", "2024-03-31 23:59:59"),
    ("WF02", "2023-01-01", "2024-03-31 23:59:59", "2024-04-01", "2024-06-30 23:59:59"),
    ("WF03", "2023-01-01", "2024-06-30 23:59:59", "2024-07-01", "2024-09-30 23:59:59"),
    ("WF04", "2023-01-01", "2024-09-30 23:59:59", "2024-10-01", "2024-12-31 23:59:59"),
)
KEYS = ("T2", "T3")
EXPECTED_IDS = {"T2": "T2_candidate_v1", "T3": "T3_candidate_v1"}


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    frame = pd.DataFrame(rows, columns=columns).map(finite)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def verify_provenance(registry_root: Path, optimization_root: Path) -> list[dict]:
    """Hard-fail unless all three frozen provenance links remain intact."""
    registry = json.loads((registry_root / "candidate_registry.json").read_text())
    validation = json.loads((registry_root / "validation_manifest.json").read_text())
    if validation.get("status") != "PHASE_3_3_ROBUSTNESS_VALIDATION_COMPLETE":
        raise RuntimeError("PHASE33_VALIDATION_REGISTRY_INVALID")
    by_key = {row["strategy"]: row for row in registry}
    if set(by_key) != set(KEYS):
        raise RuntimeError("FROZEN_CANDIDATE_SET_MISMATCH")
    for key in KEYS:
        row = by_key[key]
        if row["candidate_id"] != EXPECTED_IDS[key] or not row.get("selection_locked_before_validation"):
            raise RuntimeError("FROZEN_CANDIDATE_ID_MISMATCH")
        if stable_hash(asdict(PARAMETERS[key])) != row["baseline_parameters_hash"]:
            raise RuntimeError("FROZEN_BASELINE_HASH_MISMATCH")
        parameters = pd.read_csv(optimization_root / key / "parameters.csv")
        source = parameters.loc[parameters.configuration_id.eq(row["phase32_configuration_id"])]
        if len(source) != 1:
            raise RuntimeError("PHASE32_CONFIGURATION_MISSING")
        actual = {name: source.iloc[0][name].item() for name in SPACES[key]}
        if stable_hash(actual) != stable_hash(row["parameters"]):
            raise RuntimeError("FROZEN_PARAMETER_INTEGRITY_FAILURE")
    return [by_key[k] for k in KEYS]


def load_h1(data_root: Path) -> tuple[dict[tuple[str, str], pd.DataFrame], dict]:
    data = {}; coverage = {}
    for symbol in ("Si", "CNY"):
        # Filename selection itself excludes locked years: 2025+ files are never read.
        paths = [p for year in (2023, 2024) for p in sorted((data_root / "2026" / symbol).glob(f"{symbol}_H1_{year}_Q*.csv"))]
        if not paths:
            raise FileNotFoundError(f"no pre-2025 H1 data for {symbol}")
        frame = DataLoader().close_index(DataLoader().load_csv(paths), "1h")
        reject_true_oos(frame.index)
        # Defence in depth: filenames prevent opening TRUE OOS and the content
        # gate above rejects it.  Keep only the approved development interval.
        frame = frame.loc[(frame.index >= DEVELOPMENT_START.tz_convert(frame.index.tz)) &
                          (frame.index < TRUE_OOS_START.tz_convert(frame.index.tz))]
        data[(symbol, "H1")] = frame
        coverage[symbol] = {"first_close": frame.index.min().isoformat(), "last_close": frame.index.max().isoformat(), "bars": len(frame)}
    return data, coverage


def _slice(data: Mapping, start: str, end: str) -> dict:
    return {(s, "H1"): data[(s, "H1")].loc[start:end].copy() for s in ("Si", "CNY")}


def _net(frame: pd.DataFrame, ticks: float = 1.0) -> pd.Series:
    return frame.gross_R.astype(float) - 2 * ticks / frame.initial_risk_ticks.astype(float)


def _summary(values: pd.Series) -> dict:
    s = stats(values)
    return {"trades": s["trades"], "PF": s["PF_R"], "expectancy": s["expectancy"], "net_R": s["net_R"],
            "max_drawdown": s["max_DD_R"], "recovery_factor": s["recovery_factor"], "win_rate": s["winrate"],
            "winning_streak": s["max_winning_streak"], "losing_streak": s["max_losing_streak"]}


def _run_interval(key: str, config: Mapping, data: Mapping, start: str, end: str) -> pd.DataFrame:
    # A new execute call constructs new strategy/portfolio instances and begins FLAT.
    interval = _slice(data, start, end)
    if any(interval[(s, "H1")].empty for s in ("Si", "CNY")):
        return pd.DataFrame(columns=["trade_id","strategy_id","symbol","direction","entry_time","exit_time","gross_R","initial_risk_ticks","MAE_R","MFE_R"])
    frame = execute(key, config, interval)
    if len(frame):
        entry, exit_ = pd.to_datetime(frame.entry_time, utc=True), pd.to_datetime(frame.exit_time, utc=True)
        lo, hi = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
        frame = frame.loc[entry.ge(lo) & exit_.le(hi)].copy()
        frame = frame.sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
    return frame


def _reports(frame: pd.DataFrame, target: Path) -> None:
    net = _net(frame) if len(frame) else pd.Series(dtype=float)
    for filename, column, groups in (("instrument_report.csv", "symbol", ("Si", "CNY")), ("direction_report.csv", "direction", ("LONG", "SHORT"))):
        _csv(target / filename, [{column:g, **_summary(net[frame[column].eq(g)])} for g in groups])
    years = pd.to_datetime(frame.exit_time, utc=True).dt.year if len(frame) else pd.Series(dtype=int)
    _csv(target / "year_report.csv", [{"year":y, **_summary(net[years.eq(y)])} for y in (2023, 2024)])
    positive = net[net > 0].sort_values(ascending=False); total = positive.sum()
    fold_net = frame.assign(net_R=net).groupby("fold", sort=True).net_R.sum() if len(frame) else pd.Series(dtype=float)
    best_fold_share = float(fold_net.max()/net.sum()) if len(fold_net) and net.sum() > 0 else None
    _csv(target / "concentration.csv", [{**{f"top_{n}_trade_share": float(positive.head(n).sum()/total) if total else None for n in (1,3,10)}, "best_fold_contribution":best_fold_share}])
    loo=[]
    for fold in (x[0] for x in SCHEDULE): loo.append({"omitted_fold":fold, **_summary(net[frame.fold.ne(fold)])})
    _csv(target / "leave_one_fold_out.csv", loo)
    mae=[]
    for group, mask in (("ALL", pd.Series(True,index=frame.index)), ("WINNERS",net.gt(0)), ("LOSERS",net.lt(0))):
        for metric in ("MAE_R","MFE_R"):
            x=pd.to_numeric(frame.loc[mask,metric],errors="coerce").dropna() if metric in frame else pd.Series(dtype=float)
            mae.append({"group":group,"metric":metric,"trades":len(x),"mean":x.mean() if len(x) else None,"median":x.median() if len(x) else None,"p75":x.quantile(.75) if len(x) else None,"p90":x.quantile(.9) if len(x) else None})
    _csv(target / "mae_mfe.csv", mae)


def run(data_root: Path, output: Path = Path("TradingSystemLab/results/walk_forward_validation"), registry_root: Path = Path("TradingSystemLab/results/robustness_validation"), optimization_root: Path = Path("TradingSystemLab/results/optimization")) -> dict:
    candidates = verify_provenance(registry_root, optimization_root)
    data, coverage = load_h1(Path(data_root)); output=Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True); (output/"summary").mkdir()
    # Jan 1 is not necessarily a trading day.  Coverage is sufficient when it
    # begins in the first calendar week of 2023 and reaches the final trading
    # days of 2024.  No 2021/2022 history is part of the Phase 4 contract.
    insufficient = any(
        pd.Timestamp(v["first_close"]) >= pd.Timestamp("2023-01-08", tz="UTC")
        or pd.Timestamp(v["last_close"]) < pd.Timestamp("2024-12-30", tz="UTC")
        for v in coverage.values()
    )
    coverage_report = {"status":"INSUFFICIENT_MINIMUM_COVERAGE" if insufficient else "SUFFICIENT",
                       "minimum":["2023-01-01","2025-01-01"], "end_exclusive":True,
                       "actual":coverage,"simulated":False,"true_oos_blocked":True}
    _json(output/"DATA_COVERAGE_REPORT.json", coverage_report)
    if insufficient:
        raise RuntimeError("DATA_COVERAGE_INSUFFICIENT: requires 2023-2024 development coverage")
    verdicts={}; comparison=[]
    for candidate in candidates:
        key=candidate["strategy"]; target=output/key; target.mkdir(); folds=[]; pieces=[]; decay=[]
        for fold, tr0, tr1, te0, te1 in SCHEDULE:
            complete=all(data[(s,"H1")].index.min() <= pd.Timestamp(tr0,tz=data[(s,"H1")].index.tz) and data[(s,"H1")].index.max() >= pd.Timestamp(te1,tz=data[(s,"H1")].index.tz) for s in ("Si","CNY"))
            reason="" if complete else "requested train/test calendar is not fully covered"
            train=_run_interval(key,candidate["parameters"],data,tr0,tr1); test=_run_interval(key,candidate["parameters"],data,te0,te1)
            test["fold"]=fold; test["fold_start_state"]="FLAT"; pieces.append(test)
            ts=_summary(_net(test)); folds.append({"fold":fold,"train_start":tr0,"train_end":tr1,"test_start":te0,"test_end":te1,"status":"complete" if complete else "incomplete","included_in_pass":complete,"reason":reason,**ts})
            a,b=_summary(_net(train)),ts
            decay.append({"fold":fold,"train_expectancy":a["expectancy"],"test_expectancy":b["expectancy"],"expectancy_decay":(b["expectancy"]-a["expectancy"]) if a["expectancy"] is not None and b["expectancy"] is not None else None,"train_PF":a["PF"],"test_PF":b["PF"],"PF_change":(b["PF"]-a["PF"]) if a["PF"] is not None and b["PF"] is not None else None,"train_win_rate":a["win_rate"],"test_win_rate":b["win_rate"],"win_rate_change":(b["win_rate"]-a["win_rate"]) if a["win_rate"] is not None and b["win_rate"] is not None else None})
        trades=pd.concat(pieces,ignore_index=True) if pieces else pd.DataFrame(); _csv(target/"folds.csv",folds); _csv(target/"trades.csv",trades.to_dict("records")); _csv(target/"train_test_decay.csv",decay); _reports(trades,target)
        metrics={"candidate_id":candidate["candidate_id"],"aggregate":{f"C{x:g}":_summary(_net(trades,x)) for x in (0,1,2)}}
        valid=[r for r in folds if r["included_in_pass"]]; c1=metrics["aggregate"]["C1"]
        inst=pd.read_csv(target/"instrument_report.csv"); conc=pd.read_csv(target/"concentration.csv").iloc[0]
        positive_share=sum((r["expectancy"] or 0)>0 for r in valid)/len(valid) if valid else 0
        pass_=c1["trades"]>=50 and (c1["expectancy"] or 0)>0 and positive_share>=.6 and (pd.isna(conc.best_fold_contribution) or conc.best_fold_contribution<=.7) and all(inst.expectancy.fillna(0)>=0) and bool(valid)
        majority_negative=bool(valid) and positive_share<.5
        verdict="WALK_FORWARD_PASS" if pass_ else ("WALK_FORWARD_FAIL" if (c1["expectancy"] or 0)<0 or majority_negative else "WALK_FORWARD_BORDERLINE")
        verdicts[key]=verdict; metrics.update({"positive_complete_fold_share":positive_share,"complete_folds":len(valid),"verdict":verdict}); _json(target/"metrics.json",metrics)
        (target/"final_report.md").write_text(f"# {candidate['candidate_id']} Walk Forward\n\n**{verdict}**\n\nFrozen parameters; no ranking or optimization. Complete folds: {len(valid)}/4. Forward trades: {c1['trades']}. Each fold started FLAT. TRUE OOS remained blocked.\n",encoding="utf-8")
        comparison.append({"candidate_id":candidate["candidate_id"],"verdict":verdict,**c1})
    _csv(output/"summary"/"comparison.csv",comparison)
    phase_status = ("PHASE_4_WALK_FORWARD_COMPLETE" if all(v == "WALK_FORWARD_PASS" for v in verdicts.values())
                    else "PHASE_4_BORDERLINE")
    manifest={"phase":"4","status":phase_status,"development_coverage":["2023-01-01","2024-12-31"],"candidate_ids":[c["candidate_id"] for c in candidates],"frozen_parameter_hashes":{c["candidate_id"]:stable_hash(c["parameters"]) for c in candidates},"parameters_frozen":True,"data_coverage":coverage,"fold_schedule":[{"fold":x[0],"train":[x[1],x[2]],"test":[x[3],x[4]]} for x in SCHEDULE],"true_oos":{"cutoff":"2025-01-01","status":"BLOCKED","read":False},"true_oos_blocked":True,"optimization":False,"ranking":False,"deterministic":True,"verdicts":verdicts}
    _json(output/"summary"/"manifest.json",manifest)
    phase5=[EXPECTED_IDS[k] for k,v in verdicts.items() if v=="WALK_FORWARD_PASS"]
    (output/"summary"/"final_walk_forward_report.md").write_text("# Phase 4 Walk Forward Validation\n\n"+"\n".join(f"- **{EXPECTED_IDS[k]}: {v.replace('WALK_FORWARD_','')}**" for k,v in verdicts.items())+f"\n\n- Development coverage: 2023-2024\n- TRUE OOS: blocked >=2025\n- Optimization: false\n- Ranking: false\n- Parameters frozen: true\n\nPhase 5 Portfolio Construction: {', '.join(phase5) or 'NONE'}.\n\n{phase_status}\n",encoding="utf-8")
    return manifest


def artifact_sha256(root: Path) -> dict[str,str]:
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}
