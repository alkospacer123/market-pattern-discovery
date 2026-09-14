"""Phase 3.3 validation of the predeclared T2/T3 plateau candidates.

This module does no search. Candidate configuration IDs were frozen from the
Phase 3.2 ROBUST_PLATEAU set before any validation statistic is calculated.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..core.unified_metrics import concentration, finite, stats
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, SCENARIOS, SPACES, execute, load_development_data
from ..optimization.validation import reject_true_oos

CANDIDATE_IDS = {"T2": "T2-0007-608dc87d09f1", "T3": "T3-0014-0050d828c1a8"}
SEED = 330_2025
ITERATIONS = 10_000


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def select_candidate(key: str, optimization_root: Path) -> dict[str, Any]:
    """Resolve a predeclared plateau ID; never rank validation results or PF."""
    root = Path(optimization_root) / key
    plateau = pd.read_csv(root / "plateau_report.csv", dtype={"configuration_id": str})
    parameters = pd.read_csv(root / "parameters.csv", dtype={"configuration_id": str})
    candidate_id = CANDIDATE_IDS[key]
    match = plateau.loc[plateau.configuration_id.eq(candidate_id)]
    if len(match) != 1 or match.iloc[0].classification != "ROBUST_PLATEAU":
        raise ValueError(f"CANDIDATE_NOT_FROM_ROBUST_PLATEAU: {candidate_id}")
    row = parameters.loc[parameters.configuration_id.eq(candidate_id)]
    if len(row) != 1:
        raise ValueError(f"CANDIDATE_PROVENANCE_MISSING: {candidate_id}")
    config = {name: row.iloc[0][name].item() for name in SPACES[key]}
    return {"candidate_id": f"{key}_candidate_v1", "phase32_configuration_id": candidate_id,
            "parameters": config, "selection_locked_before_validation": True}


def _net(frame: pd.DataFrame, ticks: float) -> pd.Series:
    return frame.gross_R.astype(float) - 2 * ticks / frame.initial_risk_ticks.astype(float)


def _summary(values: pd.Series) -> dict:
    s = stats(values)
    return {"trade_count": s["trades"], "PF": s["PF_R"], "expectancy": s["expectancy"],
            "net_R": s["net_R"], "max_DD": s["max_DD_R"], "recovery_factor": s["recovery_factor"],
            "win_rate": s["winrate"], "max_winning_streak": s["max_winning_streak"],
            "max_losing_streak": s["max_losing_streak"]}


def _bootstrap(values: pd.Series) -> dict:
    a = np.asarray(values, dtype=float); rng = np.random.default_rng(SEED)
    means = np.empty(ITERATIONS)
    for start in range(0, ITERATIONS, 1000):
        stop = min(start + 1000, ITERATIONS)
        means[start:stop] = rng.choice(a, size=(stop-start, len(a)), replace=True).mean(axis=1)
    q = np.quantile(means, [.025, .05, .5, .95, .975])
    return {"iterations": ITERATIONS, "seed": SEED, "sample_trades": len(a),
            "bootstrap_mean_R": float(means.mean()), "p2_5": q[0], "p5": q[1], "p50": q[2],
            "p95": q[3], "p97_5": q[4], "probability_mean_R_gt_0": float((means > 0).mean()),
            "interpretation": "DIAGNOSTIC_ONLY_IID_TRADE_BOOTSTRAP"}


def _group_rows(frame: pd.DataFrame, column: str, groups: list[Any]) -> list[dict]:
    values = _net(frame, 1.0)
    return [{column: group, **_summary(values[frame[column].eq(group)])} for group in groups]


def _mae_mfe(frame: pd.DataFrame) -> list[dict]:
    net = _net(frame, 1.0)
    rows=[]
    for group, mask in (("ALL", pd.Series(True,index=frame.index)), ("WINNERS", net.gt(0)), ("LOSERS", net.lt(0))):
        for metric in ("MAE_R", "MFE_R"):
            data = pd.to_numeric(frame.loc[mask, metric], errors="coerce").dropna() if metric in frame else pd.Series(dtype=float)
            rows.append({"group":group,"metric":metric,"trade_count":len(data),"mean":data.mean() if len(data) else None,
                         "median":data.median() if len(data) else None,"p75":data.quantile(.75) if len(data) else None,
                         "p90":data.quantile(.9) if len(data) else None})
    return rows


def _dependence(frame: pd.DataFrame) -> list[dict]:
    dates=pd.to_datetime(frame.exit_time,utc=True); naive=dates.dt.tz_localize(None); net=_net(frame,1.0); periods={
        "quarter": naive.dt.to_period("Q").astype(str), "year": dates.dt.year.astype(str),
        "fold": naive.dt.to_period("6M").astype(str)}
    rows=[]
    for kind, labels in periods.items():
        for label in sorted(labels.unique()):
            s=_summary(net[labels.ne(label)]); rows.append({"analysis":f"leave_one_{kind}_out","omitted_period":label,**s})
    return rows


def run(data_root: Path, output: Path, optimization_root: Path | None = None) -> dict:
    output=Path(output); optimization_root=optimization_root or Path("TradingSystemLab/results/optimization")
    registry=[]
    for key in ("T2","T3"):
        selected=select_candidate(key,optimization_root); baseline=asdict(PARAMETERS[key]); baseline_hash=stable_hash(baseline)
        selected.update({"strategy":key,"baseline_parameters":baseline,
            "baseline_parameters_hash":baseline_hash,
            "reason":"Predeclared ROBUST_PLATEAU member with balanced instruments/years and lower C1 drawdown; not maximum PF."})
        registry.append(selected)
    # Selection and registry construction intentionally precede the sole data read.
    data=load_development_data(Path(data_root))
    classifications={}
    for item in registry:
        key=item["strategy"]; target=output/key; target.mkdir(parents=True,exist_ok=True)
        baseline=execute(key,{n:getattr(PARAMETERS[key],n) for n in SPACES[key]},data)
        candidate=execute(key,item["parameters"],data)
        for frame in (baseline,candidate):
            reject_true_oos(frame.entry_time); reject_true_oos(frame.exit_time)
        comparison=[]
        for version,frame in (("baseline",baseline),("candidate",candidate)):
            for scenario,ticks in SCENARIOS.items(): comparison.append({"version":version,"scenario":scenario,**_summary(_net(frame,ticks))})
        _csv(target/"baseline_vs_candidate.csv",comparison)
        _csv(target/"cost_report.csv",[r for r in comparison if r["version"]=="candidate"])
        c=candidate.copy(); dates=pd.to_datetime(c.exit_time,utc=True); c["year"]=dates.dt.year; c["quarter"]=dates.dt.tz_localize(None).dt.to_period("Q").astype(str)
        instruments=_group_rows(c,"symbol",["Si","CNY"]); years=_group_rows(c,"year",[2023,2024]); directions=_group_rows(c,"direction",["LONG","SHORT"])
        _csv(target/"instrument_report.csv",instruments); _csv(target/"year_report.csv",years); _csv(target/"direction_report.csv",directions)
        conc={"analysis":"profit_concentration",**concentration(_net(c,1.0))}; dependence=_dependence(c)
        _csv(target/"concentration_report.csv",[conc,*dependence]); _csv(target/"mae_mfe_report.csv",_mae_mfe(c))
        boot=_bootstrap(_net(c,1.0)); _csv(target/"bootstrap_report.csv",[boot])
        c1=next(r for r in comparison if r["version"]=="candidate" and r["scenario"]=="C1"); c2=next(r for r in comparison if r["version"]=="candidate" and r["scenario"]=="C2")
        positive_groups=lambda rows: all((r["expectancy"] or 0)>0 for r in rows)
        severe=(conc["top_3_positive_R_share"] or 1)>.5 or (conc["expectancy_C1_without_top3"] or 0)<=0
        ready=(c1["expectancy"] or 0)>0 and (c2["expectancy"] or 0)>0 and not severe and positive_groups(instruments) and positive_groups(years) and boot["probability_mean_R_gt_0"]>.5
        edge=(c1["expectancy"] or 0)>0 and (c2["expectancy"] or 0)>0
        classification="ROBUST_READY" if ready else ("BORDERLINE" if edge else "REJECTED"); classifications[key]=classification
        flags=[]
        if not positive_groups(instruments): flags.append("INSTRUMENT_DEPENDENT")
        if not positive_groups(years): flags.append("YEAR_DEPENDENT")
        if not positive_groups(directions): flags.append("DIRECTION_DEPENDENT")
        (target/"final_report.md").write_text(f"# {key} Phase 3.3 Robustness Validation\n\n**Classification: {classification}**\n\nCandidate `{item['candidate_id']}` was frozen from `{item['phase32_configuration_id']}` before validation. C1 expectancy: {c1['expectancy']:.6f} R; C2 expectancy: {c2['expectancy']:.6f} R. Flags: {', '.join(flags) or 'NONE'}. Bootstrap is diagnostic only. No walk-forward was executed and TRUE OOS remained blocked.\n",encoding="utf-8")
        if stable_hash(asdict(PARAMETERS[key])) != item["baseline_parameters_hash"]: raise RuntimeError("FROZEN_BASELINE_MODIFIED")
    _json(output/"candidate_registry.json",registry)
    manifest={"phase":"3.3","status":"PHASE_3_3_ROBUSTNESS_VALIDATION_COMPLETE","development_period":["2023-01-01","2024-12-31"],"true_oos_cutoff":"2025-01-01","true_oos_blocked":True,"candidate_selection_precedes_validation":True,"optimization_performed":False,"parameter_search_expanded":False,"walk_forward_executed":False,"bootstrap":{"iterations":ITERATIONS,"seed":SEED,"diagnostic_only":True},"expected_inputs":{"symbols":["Si","CNY"],"timeframes":["H1","M15"],"source":"external read-only market data"},"phase4_schedule":{"action":"expanding-window walk-forward","status":"PREPARED_NOT_EXECUTED","candidate_ids":[x["candidate_id"] for x in registry]},"classifications":classifications}
    _json(output/"validation_manifest.json",manifest)
    (output/"final_robustness_report.md").write_text("# Phase 3.3 Final Robustness Report\n\n"+"\n".join(f"- **{k}: {v}**" for k,v in classifications.items())+"\n\nCandidates are frozen for Phase 4. No further optimization or walk-forward occurred. TRUE OOS 2025+ was not read. Bootstrap intervals are diagnostic only.\n\nPHASE_3_3_ROBUSTNESS_VALIDATION_COMPLETE\n",encoding="utf-8")
    return manifest
