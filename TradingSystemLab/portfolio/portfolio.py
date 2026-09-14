"""Phase 6: combine, but never tune, validated frozen TRUE-OOS strategies."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd

from .artifacts import artifact_hashes, sha256, write_csv, write_json
from .metrics import concentration, performance, period_report, risk

EXPECTED_IDS = {"T2": "T2_candidate_v1", "T3": "T3_candidate_v1"}
FROZEN_PARAMETER_HASHES = {
    "T2_candidate_v1": "2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00",
    "T3_candidate_v1": "938b6b3b78f680010115a204b9a49e7eef962db119f4ea121e388c00741920ba",
}
TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="UTC")
BOOTSTRAP_SEED, BOOTSTRAP_ITERATIONS = 62025, 10_000


def load_inputs(root: Path) -> tuple[dict[str, pd.DataFrame], dict]:
    """Read only Phase-5 persisted artifacts and verify their complete chain."""
    root = Path(root); manifest_path = root / "summary/manifest.json"
    if not manifest_path.is_file(): raise FileNotFoundError("PHASE5_MANIFEST_MISSING")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "PHASE_5_TRUE_OOS_VALIDATION_COMPLETE": raise RuntimeError("NOT_TRUE_OOS_ARTIFACTS")
    if manifest.get("candidate_ids") != list(EXPECTED_IDS.values()): raise RuntimeError("CANDIDATE_ID_MISMATCH")
    if not manifest.get("parameters_frozen") or manifest.get("optimization") or manifest.get("walk_forward"):
        raise RuntimeError("FROZEN_PARAMETER_PROVENANCE_INVALID")
    barrier = manifest.get("true_oos_barrier", {})
    if not barrier.get("enabled") or barrier.get("start") != "2025-01-01" or barrier.get("development_rows_read") != 0:
        raise RuntimeError("TRUE_OOS_BARRIER_INVALID")
    frames = {}
    for key, cid in EXPECTED_IDS.items():
        for name in (f"{key}/trades.csv", f"{key}/metrics.json"):
            path = root / name
            if not path.is_file(): raise FileNotFoundError(f"SOURCE_ARTIFACT_MISSING:{name}")
            if sha256(path) != manifest.get("artifact_sha256", {}).get(name): raise RuntimeError(f"SOURCE_SHA256_MISMATCH:{name}")
        meta = json.loads((root / key / "metrics.json").read_text())
        if meta.get("candidate_id") != cid: raise RuntimeError("CANDIDATE_ID_MISMATCH")
        if meta.get("classification") != "PASS" or manifest.get("classifications", {}).get(key) != "PASS":
            raise RuntimeError("TRUE_OOS_VALIDATION_NOT_PASS")
        frame = pd.read_csv(root / key / "trades.csv")
        required = {"trade_id", "entry_time", "exit_time", "direction", "symbol", "R_result", "holding_time"}
        if not required.issubset(frame): raise RuntimeError("TRADE_SCHEMA_INVALID")
        frame["entry_time"] = pd.to_datetime(frame.entry_time, utc=True); frame["exit_time"] = pd.to_datetime(frame.exit_time, utc=True)
        if frame.trade_id.isna().any() or frame.trade_id.duplicated().any(): raise RuntimeError("TRADE_IDENTITY_INVALID")
        if (frame.entry_time < TRUE_OOS_START).any() or (frame.exit_time < frame.entry_time).any(): raise RuntimeError("NON_TRUE_OOS_TRADE_DETECTED")
        frame["strategy"] = key; frame["candidate_id"] = cid
        frames[key] = frame.sort_values(["exit_time", "entry_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
    return frames, manifest


def _daily(frame: pd.DataFrame, value: str = "R_result") -> pd.Series:
    return frame.groupby(frame.exit_time.dt.floor("D"), sort=True)[value].sum()


def _weights(frames: dict[str, pd.DataFrame]) -> dict[str, dict[str, float]]:
    vols = {key: float(_daily(frame).std(ddof=0)) for key, frame in frames.items()}
    inv = {key: 1 / value for key, value in vols.items()}
    total = sum(inv.values())
    return {"A": {"T2": 1.0, "T3": 0.0}, "B": {"T2": 0.0, "T3": 1.0},
            "C": {"T2": .5, "T3": .5}, "D": {key: inv[key] / total for key in ("T2", "T3")}}


def _overlap(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    pairs = []
    for x in a.itertuples():
        for y in b.itertuples():
            if x.entry_time < y.exit_time and y.entry_time < x.exit_time: pairs.append((x, y))
    same = sum(x.direction == y.direction for x, y in pairs)
    return {"cross_strategy_overlap_pairs": len(pairs), "same_direction_overlap_pairs": same,
            "opposite_direction_overlap_pairs": len(pairs) - same,
            "T2_trades_overlapping_T3": len({x.trade_id for x, _ in pairs}),
            "T3_trades_overlapping_T2": len({y.trade_id for _, y in pairs})}


def run(source: Path = Path("TradingSystemLab/results/true_oos_validation"),
        output: Path = Path("TradingSystemLab/results/portfolio_construction")) -> dict:
    frames, phase5 = load_inputs(Path(source)); weights = _weights(frames)
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    metrics_rows=[]; equity_rows=[]; monthly=[]; quarterly=[]; yearly=[]; contributions=[]; conc_rows=[]; dd_rows=[]; bootstrap=[]
    portfolio_trades = {}
    for pid in ("A", "B", "C", "D"):
        pieces=[]
        for key in ("T2", "T3"):
            if not weights[pid][key]: continue
            part=frames[key].copy(); part["portfolio_id"]=pid; part["weight"]=weights[pid][key]
            part["weighted_R"]=part.R_result.astype(float)*part.weight; part["holding_hours"]=(part.exit_time-part.entry_time).dt.total_seconds()/3600
            pieces.append(part)
        trades=pd.concat(pieces).sort_values(["exit_time","strategy","symbol","trade_id"],kind="mergesort").reset_index(drop=True)
        portfolio_trades[pid]=trades
        daily=_daily(trades,"weighted_R"); perf=performance(trades.weighted_R,trades.holding_hours); rr=risk(daily)
        metrics_rows.append({"portfolio_id":pid,"T2_weight":weights[pid]["T2"],"T3_weight":weights[pid]["T3"],**perf,**rr,
                             "worst_month_R":float(trades.groupby(trades.exit_time.dt.tz_localize(None).dt.to_period('M')).weighted_R.sum().min()),
                             "worst_quarter_R":float(trades.groupby(trades.exit_time.dt.tz_localize(None).dt.to_period('Q')).weighted_R.sum().min())})
        eq=trades.weighted_R.cumsum()
        equity_rows.extend({"portfolio_id":pid,"exit_time":t.isoformat(),"strategy":s,"trade_id":i,"trade_R":r,"cumulative_R":e}
                           for t,s,i,r,e in zip(trades.exit_time,trades.strategy,trades.trade_id,trades.weighted_R,eq))
        monthly.append(period_report(trades,"M","month")); quarterly.append(period_report(trades,"Q","quarter")); yearly.append(period_report(trades,"Y","year"))
        for key in ("T2","T3"):
            value=float(trades.loc[trades.strategy.eq(key),"weighted_R"].sum()); net=float(trades.weighted_R.sum())
            contributions.append({"portfolio_id":pid,"strategy":key,"weight":weights[pid][key],"net_R_contribution":value,"profit_contribution":value/net if net else None})
        c=concentration(trades.weighted_R); conc_rows.append({"portfolio_id":pid,**c})
        curve=eq; peaks=curve.cummax().clip(lower=0); draws=curve-peaks
        dd_rows.extend({"portfolio_id":pid,"exit_time":t.isoformat(),"equity_R":e,"drawdown_R":d} for t,e,d in zip(trades.exit_time,curve,draws))
        rng=np.random.default_rng(BOOTSTRAP_SEED); x=trades.weighted_R.to_numpy(); means=rng.choice(x,(BOOTSTRAP_ITERATIONS,len(x)),replace=True).mean(axis=1)
        bootstrap.append({"portfolio_id":pid,"seed":BOOTSTRAP_SEED,"iterations":BOOTSTRAP_ITERATIONS,"probability_mean_R_gt_0":float((means>0).mean()),"mean_R_p05":float(np.quantile(means,.05)),"mean_R_p50":float(np.quantile(means,.5)),"mean_R_p95":float(np.quantile(means,.95))})
    daily_frame=pd.concat({k:_daily(v) for k,v in frames.items()},axis=1,sort=True).fillna(0).sort_index()
    equity_frame=daily_frame.cumsum()
    corr=[{"metric":"daily_returns","T2_T3_correlation":float(daily_frame.T2.corr(daily_frame.T3))},
          {"metric":"equity_curves","T2_T3_correlation":float(equity_frame.T2.corr(equity_frame.T3))}]
    overlap=_overlap(frames["T2"],frames["T3"])
    zero_overlap = {name: 0 for name in overlap}
    overlap_rows=[{"scope":"T2_vs_T3",**overlap}, {"scope":"A",**zero_overlap}, {"scope":"B",**zero_overlap},
                  {"scope":"C",**overlap}, {"scope":"D",**overlap}]
    # Instrument and direction stability are retained alongside period rows.
    for pid,trades in portfolio_trades.items():
        for dimension in ("symbol","direction"):
            for group,part in trades.groupby(dimension,sort=True):
                yearly.append(pd.DataFrame([{"portfolio_id":pid,"year":f"{dimension}:{group}",**performance(part.weighted_R,part.holding_hours)}]))
    metrics_df=pd.DataFrame(metrics_rows); contribution_df=pd.DataFrame(contributions); conc_df=pd.DataFrame(conc_rows)
    combined=metrics_df.loc[metrics_df.portfolio_id.isin(["C","D"])]
    ready=True
    for row in combined.itertuples():
        contrib=contribution_df[contribution_df.portfolio_id.eq(row.portfolio_id)].profit_contribution.max()
        without5=conc_df.loc[conc_df.portfolio_id.eq(row.portfolio_id),"net_R_without_top_5_trades"].iloc[0]
        ready &= row.expectancy>0 and row.net_R>0 and abs(row.max_drawdown)<=1.5*max(abs(json.loads((Path(source)/k/'metrics.json').read_text())['aggregate']['max_drawdown']) for k in ('T2','T3')) and contrib<=.9 and without5>0
    verdict="PORTFOLIO_READY" if ready else "PORTFOLIO_NEEDS_RESEARCH"
    outputs={"portfolio_metrics.csv":metrics_df,"equity_curve.csv":pd.DataFrame(equity_rows),"monthly_report.csv":pd.concat(monthly,ignore_index=True),
             "quarterly_report.csv":pd.concat(quarterly,ignore_index=True),"yearly_report.csv":pd.concat(yearly,ignore_index=True),
             "strategy_contribution.csv":contribution_df,"correlation_report.csv":pd.DataFrame(corr),"overlap_report.csv":pd.DataFrame(overlap_rows),
             "concentration_report.csv":conc_df,"drawdown_report.csv":pd.DataFrame(dd_rows),"bootstrap_report.csv":pd.DataFrame(bootstrap)}
    for name,frame in outputs.items(): write_csv(output/name,frame)
    (output/"portfolio_summary.md").write_text(f"# Phase 6 Portfolio Construction\n\n**Verdict: {verdict}**\n\nPredefined portfolios only: A (T2), B (T3), C (50/50), and D (inverse TRUE-OOS daily volatility). No ranking, optimization, filtering, or trade removal was performed.\n\nPHASE_6_PORTFOLIO_CONSTRUCTION_COMPLETE\n",encoding="utf-8")
    manifest={"phase":"6","status":"PHASE_6_PORTFOLIO_CONSTRUCTION_COMPLETE","verdict":verdict,"candidate_ids":list(EXPECTED_IDS.values()),
              "frozen_parameter_hashes":FROZEN_PARAMETER_HASHES,"source_manifest_sha256":sha256(Path(source)/"summary/manifest.json"),
              "source_trade_sha256":{k:phase5["artifact_sha256"][f"{k}/trades.csv"] for k in ("T2","T3")},
              "true_oos_barrier":{"enabled":True,"start":"2025-01-01","development_rows_read":0},"optimization":False,"walk_forward":False,"ranking":False,
              "weights":weights,"bootstrap":{"seed":BOOTSTRAP_SEED,"iterations":BOOTSTRAP_ITERATIONS},"deterministic":True}
    manifest["artifact_sha256"]=artifact_hashes(output); write_json(output/"manifest.json",manifest)
    return manifest
