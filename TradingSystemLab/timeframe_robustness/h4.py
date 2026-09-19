"""Standalone H4 robustness, directly adapted from H1 Phase 3.3.

There is deliberately no search interface: the two declarations below are the
only configurations this stage can execute, and the registry is persisted
before development market data is opened.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from ..core.unified_metrics import concentration, finite, stats
from ..multitimeframe.phase71 import APPROVED_DATA_ROOT, STRATEGY_SHA256, verify_frozen_strategies
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..timeframe_validation import h4_baseline as baseline

PHASE, STATUS, TIMEFRAME = "H4_ROBUSTNESS", "PHASE_H4_ROBUSTNESS_COMPLETE", "H4"
METHODOLOGICAL_SOURCE = "H1_PHASE_3_3"
OUTPUT = Path("TradingSystemLab/results/timeframe_robustness/H4")
OPTIMIZATION = Path("TradingSystemLab/results/timeframe_optimization/H4")
BASELINE_COMMIT = "9133c0f9ad8eddff82ea5b3af0e9532594dec20a"
OPTIMIZATION_COMMIT = "06805ef673607b3302715bf03903c534a3694b85"
SEED, ITERATIONS = 3_302_025, 10_000
DEVELOPMENT_PERIOD = ["2023-01-01", "2024-12-31"]

FROZEN = {
    "T2": {"candidate_id": "T2_H4_candidate_v1", "source_h1_candidate_id": "T2_candidate_v1",
        "configuration_id": "T2-H4-0008-2b0494cdd24b",
        "parameter_hash": "2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00",
        "parameters": {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200, "adx_threshold": 20,
            "impulse_distance_atr": .5, "confirmation_window": 3, "max_initial_stop_atr": 2.5, "trailing_atr": 3},
        "reason": "Predeclared ROBUST_PLATEAU member with materially better instrument/year balance and lower concentration than the other T2 plateau candidate. Not selected by maximum PF or expectancy."},
    "T3": {"candidate_id": "T3_H4_candidate_v1", "source_h1_candidate_id": "T3_candidate_v1",
        "configuration_id": "T3-H4-0003-9b1e60957d91",
        "parameter_hash": "9b1e60957d918a086d58a9a721faa60c5dbd66d73721b08c733be460c930215f",
        "parameters": {"ema_period": 100, "adx_threshold": 20, "breakout_period": 20,
            "atr_average_period": 20, "stop_atr": 2.0, "trail_atr": 3.0},
        "reason": "Predeclared ROBUST_PLATEAU member with positive expectancy in both instruments and both development years. It was not selected by maximum PF, maximum expectancy or minimum drawdown."},
}

PROTECTED = tuple(Path(p) for p in (
    "TradingSystemLab/results/optimization", "TradingSystemLab/results/robustness_validation",
    "TradingSystemLab/results/timeframe_validation", "TradingSystemLab/results/timeframe_optimization",
    "TradingSystemLab/results/timeframe_analysis", "TradingSystemLab/results/timeframe_diagnostics",
    "TradingSystemLab/results/multitimeframe_research", "TradingSystemLab/results/walk_forward",
    "TradingSystemLab/results/true_oos_validation", "TradingSystemLab/results/T2_implementation_check",
    "TradingSystemLab/results/T3_robust"))
STRATEGIES = tuple(Path(p) for p in ("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py",
                                     "TradingSystemLab/strategies/trend/T3_MTF_Trend.py"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_snapshot() -> dict[str, Any]:
    result = {str(p): hash_tree(p) for p in PROTECTED}
    result.update({str(p): _sha(p) for p in STRATEGIES})
    return result


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: Any) -> None:
    pd.DataFrame(rows).map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _summary(values: pd.Series) -> dict[str, Any]:
    m = stats(values.astype(float))
    return {"trades": m["trades"], "PF": m["PF_R"], "expectancy": m["expectancy"], "net_R": m["net_R"],
            "max_DD": m["max_DD_R"], "recovery_factor": m["recovery_factor"], "win_rate": m["winrate"],
            "max_winning_streak": m["max_winning_streak"], "max_losing_streak": m["max_losing_streak"]}


def _validate_prerequisites() -> tuple[dict, list[dict]]:
    base = json.loads(baseline.OUTPUT.joinpath("manifest.json").read_text())
    opt_path = OPTIMIZATION / "manifest.json"; opt = json.loads(opt_path.read_text())
    if (base.get("status") != baseline.STATUS or base.get("timeframe") != TIMEFRAME or
            base.get("development_period") != DEVELOPMENT_PERIOD or not base.get("true_oos_blocked")):
        raise RuntimeError("H4_BASELINE_PROVENANCE_MISMATCH")
    required = (opt.get("status") == "PHASE_H4_OPTIMIZATION_COMPLETE" and opt.get("timeframe") == TIMEFRAME and
        opt.get("methodological_source") == "H1_PHASE_3_2" and opt.get("development_period") == DEVELOPMENT_PERIOD and
        opt.get("cost_scenarios") == ["C1"] and opt.get("tested_configuration_count") == {"T2": 19, "T3": 22} and
        opt.get("overall_plateau_classification") == {"T2": "ROBUST_PLATEAU", "T3": "ROBUST_PLATEAU"} and
        opt.get("true_oos_blocked") is True and opt.get("selection") is False)
    if not required: raise RuntimeError("H4_OPTIMIZATION_CONTRACT_MISMATCH")
    for commit, tree, error in ((BASELINE_COMMIT, baseline.OUTPUT, "H4_BASELINE_COMMIT_PARITY_MISMATCH"),
                                (OPTIMIZATION_COMMIT, OPTIMIZATION, "H4_OPTIMIZATION_COMMIT_PARITY_MISMATCH")):
        if subprocess.run(["git", "diff", "--quiet", commit, "--", str(tree)], check=False).returncode:
            raise RuntimeError(error)
    verify_frozen_strategies()
    registry = []
    for key, frozen in FROZEN.items():
        params = pd.read_csv(OPTIMIZATION/key/"parameters.csv")
        plateau = pd.read_csv(OPTIMIZATION/key/"plateau_report.csv")
        p = params.loc[params.configuration_id.eq(frozen["configuration_id"])]
        q = plateau.loc[plateau.configuration_id.eq(frozen["configuration_id"])]
        if len(p) != 1 or len(q) != 1 or q.iloc[0].classification != "ROBUST_PLATEAU":
            raise RuntimeError(f"{key}_FROZEN_CANDIDATE_PROVENANCE_MISMATCH")
        observed = {name: p.iloc[0][name].item() for name in frozen["parameters"]}
        if observed != frozen["parameters"] or p.iloc[0].parameter_hash != frozen["parameter_hash"] or stable_hash(observed) != frozen["parameter_hash"]:
            raise RuntimeError(f"{key}_FROZEN_PARAMETERS_MISMATCH")
        registry.append({"candidate_id": frozen["candidate_id"], "strategy": key, "timeframe": TIMEFRAME,
            "source_h1_candidate_id": frozen["source_h1_candidate_id"],
            "source_h4_optimization_configuration_id": frozen["configuration_id"], "parameter_hash": frozen["parameter_hash"],
            "parameters": frozen["parameters"], "strategy_hash": STRATEGY_SHA256[key],
            "optimization_merge_commit": OPTIMIZATION_COMMIT, "optimization_manifest_sha256": _sha(opt_path),
            "selection_locked_before_validation": True, "selection_reason": frozen["reason"]})
    return {"baseline": base, "optimization": opt}, registry


def _load_verified_development(data_root: Path, provenance: dict[str, dict]) -> tuple[dict[str, pd.DataFrame], list[dict]]:
    """Load development data and bind this run to both frozen source lists."""
    loaded = {alias: baseline.load_h1_development(Path(data_root), alias)
              for _, alias in baseline.INSTRUMENTS}
    verified = []
    for instrument, alias in baseline.INSTRUMENTS:
        frame, paths = loaded[alias]
        if frame is None:
            raise RuntimeError("H4_ROBUSTNESS_SOURCE_HASH_MISMATCH")
        verified.extend({"instrument": instrument, "alias": alias, "name": path.name,
                         "sha256": _sha(path)} for path in paths)
    expected_optimization = provenance["optimization"].get("source_files")
    expected_baseline = provenance["baseline"].get("source_files")
    if (verified != expected_optimization or verified != expected_baseline or
            expected_optimization != expected_baseline):
        raise RuntimeError("H4_ROBUSTNESS_SOURCE_HASH_MISMATCH")
    return {alias: item[0] for alias, item in loaded.items()}, verified


def _bootstrap(values: pd.Series) -> dict[str, Any]:
    a = values.to_numpy(float); rng = np.random.default_rng(SEED); means = np.empty(ITERATIONS)
    for start in range(0, ITERATIONS, 1000):
        stop = min(start + 1000, ITERATIONS)
        means[start:stop] = rng.choice(a, (stop-start, len(a)), replace=True).mean(axis=1)
    q = np.quantile(means, [.025, .05, .5, .95, .975])
    return {"seed": SEED, "iterations": ITERATIONS, "sample_trades": len(a), "mean": means.mean(),
        "p2_5": q[0], "p5": q[1], "p50": q[2], "p95": q[3], "p97_5": q[4],
        "probability_mean_R_gt_0": (means > 0).mean(), "status": "DIAGNOSTIC_ONLY_IID_TRADE_BOOTSTRAP"}


def _dependence(trades: pd.DataFrame) -> list[dict]:
    dates = pd.to_datetime(trades.exit_time, utc=True); naive = dates.dt.tz_localize(None)
    labels = {"quarter": naive.dt.to_period("Q").astype(str), "year": dates.dt.year.astype(str),
              "half_year_fold": dates.dt.year.astype(str) + "-H" + ((dates.dt.month.sub(1)//6)+1).astype(str)}
    rows = []
    for kind, periods in labels.items():
        for period in sorted(periods.unique()):
            rows.append({"analysis": f"leave_one_{kind}_out", "omitted_period": period,
                         **_summary(trades.loc[periods.ne(period), "net_R"])})
    return rows


def _mae_mfe(trades: pd.DataFrame) -> list[dict]:
    rows=[]
    for scope, mask in (("ALL", pd.Series(True,index=trades.index)), ("WINNERS", trades.net_R.gt(0)), ("LOSERS", trades.net_R.lt(0))):
        for metric in ("MAE_R", "MFE_R"):
            x=trades.loc[mask,metric].astype(float)
            rows.append({"scope":scope,"metric":metric,"trades":len(x),"mean":x.mean(),"std":x.std(ddof=0),
                         "min":x.min(),"p25":x.quantile(.25),"p50":x.quantile(.5),"p75":x.quantile(.75),"max":x.max()})
    return rows


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    before = protected_snapshot(); provenance, registry = _validate_prerequisites()
    data, verified_sources = _load_verified_development(Path(data_root), provenance)
    output=Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    # Auditable ordering guarantee: freeze the registry on disk before candidate execution.
    _json(output/"candidate_registry.json", registry)
    classifications={}; flags_by_strategy={}
    for item in registry:
        key=item["strategy"]; target=output/key; target.mkdir()
        candidate=pd.concat([baseline._execute(key,item["parameters"],alias,data[alias]) for _,alias in baseline.INSTRUMENTS],ignore_index=True)
        candidate=candidate.sort_values(["exit_time","instrument","trade_id"],kind="mergesort").reset_index(drop=True)
        base_params=baseline.EXPECTED[key]["parameters"]
        parent=pd.concat([baseline._execute(key,base_params,alias,data[alias]) for _,alias in baseline.INSTRUMENTS],ignore_index=True)
        parent=parent.sort_values(["exit_time","instrument","trade_id"],kind="mergesort").reset_index(drop=True)
        comparison=[{"version": name,"cost_scenario":"C1",**_summary(frame.net_R)} for name,frame in (("baseline",parent),("candidate",candidate))]
        _csv(target/"baseline_vs_candidate.csv",comparison)
        dates=pd.to_datetime(candidate.exit_time,utc=True); candidate["year"]=dates.dt.year
        def groups(column, values): return [{column:value,**_summary(candidate.loc[candidate[column].eq(value),"net_R"])} for value in values]
        instruments=groups("symbol",["Si","CNY"]); years=groups("year",[2023,2024]); directions=groups("direction",["LONG","SHORT"])
        _csv(target/"instrument_report.csv",instruments); _csv(target/"year_report.csv",years); _csv(target/"direction_report.csv",directions)
        conc=concentration(candidate.net_R); _csv(target/"concentration_report.csv",[conc])
        boot=_bootstrap(candidate.net_R); _csv(target/"bootstrap_report.csv",[boot])
        dependence=_dependence(candidate); _csv(target/"dependence_report.csv",dependence); _csv(target/"mae_mfe_report.csv",_mae_mfe(candidate))
        positive=lambda rows: all(r["expectancy"] is not None and r["expectancy"]>0 for r in rows)
        severe=(conc["top_3_positive_R_share"] is None or conc["top_3_positive_R_share"]>.5 or conc["expectancy_C1_without_top3"]<=0)
        expectancy=comparison[1]["expectancy"]
        ready=expectancy>0 and not severe and positive(instruments) and positive(years) and boot["probability_mean_R_gt_0"]>.5
        classification="ROBUST_READY" if ready else ("BORDERLINE" if expectancy>0 else "REJECTED")
        flags=[]
        if not positive(instruments): flags.append("INSTRUMENT_DEPENDENT")
        if not positive(years): flags.append("YEAR_DEPENDENT")
        if not positive(directions): flags.append("DIRECTION_DEPENDENT")
        if severe: flags.append("CONCENTRATION_DEPENDENT")
        classifications[key]=classification; flags_by_strategy[key]=flags
        change="No parameter change occurred at H4 Optimization." if key=="T2" else "Exact parameter change: `ema_period: 75 → 100`; all other parameters unchanged."
        (target/"final_report.md").write_text(f"# {key} H4 Robustness\n\n**{classification}**. Flags: {', '.join(flags) or 'NONE'}.\n\n{change}\n\nC1 only; bootstrap diagnostic only. No search, walk-forward, or TRUE OOS access.\n",encoding="utf-8")
    after=protected_snapshot()
    if before != after: raise RuntimeError("PROTECTED_RESEARCH_ARTIFACT_MUTATION")
    manifest={"phase":PHASE,"status":STATUS,"timeframe":TIMEFRAME,"methodological_source":METHODOLOGICAL_SOURCE,
        "development_period":DEVELOPMENT_PERIOD,"true_oos_cutoff":"2025-01-01","true_oos_blocked":True,
        "cost_model":"H1_C1","cost_scenarios":["C1"],"ticks_per_side":1,"round_trip_ticks":2,
        "candidate_selection_precedes_validation":True,"optimization_performed":False,"parameter_search_expanded":False,
        "candidate_ranking":False,"candidate_fallback":False,"walk_forward_executed":False,
        "bootstrap":{"seed":SEED,"iterations":ITERATIONS,"diagnostic_only":True},"classifications":classifications,
        "diagnostic_flags":flags_by_strategy,"baseline_merge_commit":BASELINE_COMMIT,"optimization_merge_commit":OPTIMIZATION_COMMIT,
        "baseline_manifest_sha256":_sha(baseline.OUTPUT/"manifest.json"),"optimization_manifest_sha256":_sha(OPTIMIZATION/"manifest.json"),
        "candidate_hashes":{x["strategy"]:x["parameter_hash"] for x in registry},
        "strategy_hashes":STRATEGY_SHA256,"source_hashes":verified_sources,
        "expected_source_files":provenance["optimization"]["source_files"],
        "verified_source_files":verified_sources,
        "protected_artifact_hashes":after,"deterministic_artifacts":True}
    _json(output/"manifest.json",manifest)
    lines=["# H4 Robustness Validation","","H1 Phase 3.3 methodology adapted only for H4 and C1.",""]
    lines += [f"- **{k}: {classifications[k]}**; flags: {', '.join(flags_by_strategy[k]) or 'NONE'}" for k in ("T2","T3")]
    lines += ["","No parameter search, candidate ranking, fallback, walk-forward, or TRUE OOS access.","",STATUS,""]
    (output/"h4_robustness_report.md").write_text("\n".join(lines),encoding="utf-8")
    return manifest
