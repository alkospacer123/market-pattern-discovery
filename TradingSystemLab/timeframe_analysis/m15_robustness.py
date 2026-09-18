"""Deterministic, read-only robustness replay of frozen M15 candidates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from ..core.unified_metrics import concentration, finite, stats
from ..multitimeframe.phase71 import (APPROVED_DATA_ROOT, COST_TICKS_PER_SIDE,
    STRATEGY_SHA256, reject_true_oos, verify_frozen_strategies)
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..timeframe_validation import m15_baseline

PHASE = "M15_ROBUSTNESS"
STATUS = "PHASE_M15_ROBUSTNESS_COMPLETE"
OUTPUT = Path("TradingSystemLab/results/timeframe_analysis/M15_ROBUSTNESS")
BASELINE = Path("TradingSystemLab/results/timeframe_validation/M15")
OPTIMIZATION = Path("TradingSystemLab/results/timeframe_optimization/M15")
DEVELOPMENT_PERIOD = ["2023-01-01", "2024-12-31"]
TRUE_OOS_CUTOFF = "2025-01-01"
EXPECTED = {
    "T2": ("T2_M15_candidate_v1", "T2-M15-0014-26fb9b19bd4f", "26fb9b19bd4fca7805d88d08817831d516d5de51b118bfd428d8626e593da317"),
    "T3": ("T3_M15_candidate_v1", "T3-M15-0011-76dd2f3526c3", "76dd2f3526c38a3c7abfd3117d2a9ea4a78d0954c868bd01260736011726ba69"),
}
FLAGS = {"optimization": False, "ranking": False, "candidate_selection": False,
         "parameter_change": False, "strategy_change": False, "filter_search": False,
         "walk_forward": False, "true_oos_access": False, "portfolio": False}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: Any) -> None:
    data = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    data.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _metric(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float)
    summary, conc = stats(values), concentration(values)
    holding = ((pd.to_datetime(frame.exit_time, utc=True) - pd.to_datetime(frame.entry_time, utc=True))
               .dt.total_seconds() / 60) if len(frame) else pd.Series(dtype=float)
    return {name: finite(value) for name, value in {
        "trades": summary["trades"], "PF": summary["PF_R"],
        "expectancy_R": summary["expectancy"], "net_R": summary["net_R"],
        "max_drawdown_R": summary["max_DD_R"], "recovery_factor": summary["recovery_factor"],
        "win_rate": summary["winrate"], "average_holding_minutes": holding.mean() if len(holding) else None,
        "losing_streak": summary["max_losing_streak"],
        "average_MAE_R": frame.MAE_R.astype(float).mean() if len(frame) else None,
        "average_MFE_R": frame.MFE_R.astype(float).mean() if len(frame) else None,
        "top_1_positive_R_concentration": conc["top_1_positive_R_share"],
        "top_5_positive_R_concentration": conc["top_5_positive_R_share"],
        "net_R_without_top5": conc["net_R_without_top5"],
        "PF_without_top5": conc["PF_R_C1_without_top5"],
    }.items()}


def _load_provenance(baseline: Path, optimization: Path) -> tuple[dict, dict, dict]:
    bm = json.loads((baseline / "manifest.json").read_text(encoding="utf-8"))
    om = json.loads((optimization / "manifest.json").read_text(encoding="utf-8"))
    if (bm.get("status") != "PHASE_M15_BASELINE_COMPLETE" or bm.get("phase") != "M15_BASELINE" or
            bm.get("development_period") != DEVELOPMENT_PERIOD):
        raise RuntimeError("M15_BASELINE_PROVENANCE_INVALID")
    if (om.get("status") != "PHASE_M15_OPTIMIZATION_COMPLETE" or om.get("phase") != "M15_OPTIMIZATION" or
            om.get("development_period") != DEVELOPMENT_PERIOD):
        raise RuntimeError("M15_OPTIMIZATION_PROVENANCE_INVALID")
    if bm.get("frozen_strategy_hashes") != STRATEGY_SHA256:
        raise RuntimeError("M15_BASELINE_STRATEGY_HASH_MISMATCH")
    optimized_hashes = {k: v["sha256"] for k, v in om.get("frozen_strategy_hashes", {}).items()}
    if optimized_hashes != STRATEGY_SHA256:
        raise RuntimeError("M15_OPTIMIZATION_STRATEGY_HASH_MISMATCH")
    registries = {}
    for key, expected in EXPECTED.items():
        registry = json.loads((optimization / key / "candidate_registry.json").read_text(encoding="utf-8"))
        if (registry.get("candidate_id"), registry.get("configuration_id"), registry.get("parameter_hash")) != expected:
            raise RuntimeError(f"{key}_FROZEN_CANDIDATE_IDENTITY_MISMATCH")
        if stable_hash(registry.get("parameters")) != expected[2]:
            raise RuntimeError(f"{key}_FROZEN_PARAMETER_HASH_MISMATCH")
        if registry.get("strategy_hash") != STRATEGY_SHA256[key]:
            raise RuntimeError(f"{key}_FROZEN_STRATEGY_HASH_MISMATCH")
        if registry.get("baseline_candidate_id") != f"{key}_candidate_v1" or registry.get("baseline_parameter_hash") != bm["parameter_hashes"][key]:
            raise RuntimeError(f"{key}_BASELINE_PROVENANCE_MISMATCH")
        registries[key] = registry
    return bm, om, registries


def _sources(loaded: dict) -> list[dict]:
    return [{"instrument": instrument, "alias": alias,
             "files": [{"name": path.name, "sha256": _sha(path)} for path in loaded[alias][1]]}
            for instrument, alias in m15_baseline.INSTRUMENTS]


def _expected_sources(manifest: dict) -> list[dict]:
    # Baseline records identical files once per strategy; compare its canonical unique snapshot.
    result = []
    for instrument, alias in m15_baseline.INSTRUMENTS:
        matches = [row for row in manifest["source_data_hashes"] if row["instrument"] == instrument]
        snapshots = {(tuple((f["name"], f["sha256"]) for f in row["files"])) for row in matches}
        if len(snapshots) != 1:
            raise RuntimeError("M15_BASELINE_SOURCE_SNAPSHOT_AMBIGUOUS")
        result.append({"instrument": instrument, "alias": alias,
                       "files": [{"name": n, "sha256": h} for n, h in next(iter(snapshots))]})
    return result


def _drawdown(frame: pd.DataFrame) -> list[dict]:
    if frame.empty:
        return []
    ordered = frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    equity = ordered.net_R.astype(float).cumsum(); peaks = equity.cummax().clip(lower=0); dd = equity - peaks
    trough = int(dd.idxmin()); prior = peaks.iloc[:trough + 1]; start = int(prior[prior.eq(prior.iloc[trough])].index[0])
    recoveries = dd.index[(dd.index > trough) & dd.ge(0)]
    recovery = int(recoveries[0]) if len(recoveries) else None
    end = recovery if recovery is not None else len(ordered) - 1
    return [{"max_drawdown_R": finite(float(dd.iloc[trough])),
             "drawdown_start": pd.Timestamp(ordered.iloc[start].exit_time).isoformat(),
             "trough": pd.Timestamp(ordered.iloc[trough].exit_time).isoformat(),
             "recovery": pd.Timestamp(ordered.iloc[recovery].exit_time).isoformat() if recovery is not None else "UNRECOVERED",
             "duration_minutes": (pd.Timestamp(ordered.iloc[end].exit_time) - pd.Timestamp(ordered.iloc[start].exit_time)).total_seconds() / 60}]


def _reports(target: Path, key: str, trades: pd.DataFrame, baseline: Path) -> dict:
    target.mkdir(parents=True)
    overall = _metric(trades); _csv(target / "trades.csv", trades); _json(target / "metrics.json", overall)
    yearly = [{"year": year, **_metric(trades.loc[trades.year.eq(year)])} for year in (2023, 2024)]
    instruments = [{"instrument": name, **_metric(trades.loc[trades.instrument.eq(name)])} for name, _ in m15_baseline.INSTRUMENTS]
    directions = [{"direction": name, **_metric(trades.loc[trades.direction.eq(name)])} for name in ("LONG", "SHORT")]
    monthly = []
    periods = pd.to_datetime(trades.exit_time, utc=True).dt.tz_localize(None).dt.to_period("M") if len(trades) else pd.Series(dtype="period[M]")
    for month in pd.period_range("2023-01", "2024-12", freq="M"):
        monthly.append({"month": str(month), **_metric(trades.loc[periods.eq(month)])})
    positive = float(trades.net_R.clip(lower=0).sum()) if len(trades) else 0.0
    concentration_rows = [{"dimension": "trade", "period": "TOP_1", "share_of_positive_R": overall["top_1_positive_R_concentration"]},
                          {"dimension": "trade", "period": "TOP_5", "share_of_positive_R": overall["top_5_positive_R_concentration"],
                           "net_R_without_top5": overall["net_R_without_top5"], "PF_without_top5": overall["PF_without_top5"]}]
    for row in yearly:
        contribution = float(trades.loc[trades.year.eq(row["year"]), "net_R"].clip(lower=0).sum())
        concentration_rows.append({"dimension": "year", "period": row["year"], "positive_R_contribution": contribution,
                                   "share_of_positive_R": contribution / positive if positive else None})
    base_years = pd.read_csv(baseline / key / "yearly_report.csv").set_index("year")
    comparison = []
    for row in yearly:
        year = row["year"]
        for version, values in (("baseline", base_years.loc[year].to_dict()), ("optimized", row)):
            comparison.append({"year": year, "version": version, **{name: values[name] for name in
                ("trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")}})
    _csv(target / "yearly_report.csv", yearly); _csv(target / "instrument_report.csv", instruments)
    _csv(target / "direction_report.csv", directions); _csv(target / "monthly_report.csv", monthly)
    _csv(target / "concentration_report.csv", concentration_rows); _csv(target / "drawdown_report.csv", _drawdown(trades))
    _csv(target / "mae_mfe_report.csv", [{"scope": "ALL", "average_MAE_R": overall["average_MAE_R"], "average_MFE_R": overall["average_MFE_R"]}])
    _csv(target / "baseline_year_comparison.csv", comparison)
    (target / "final_report.md").write_text(f"# {EXPECTED[key][0]} robustness\n\nDescriptive development-only replay; the frozen candidate was not changed or selected.\n", encoding="utf-8")
    return overall


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT,
        baseline: Path = BASELINE, optimization: Path = OPTIMIZATION) -> dict[str, Any]:
    """Replay both registries through the exact baseline execution function."""
    verify_frozen_strategies(); baseline, optimization, output = map(Path, (baseline, optimization, output))
    bm, om, registries = _load_provenance(baseline, optimization)
    protected = (baseline, optimization, *[p for p in m15_baseline.PROTECTED_ARTIFACTS if p.name != "timeframe_analysis"],
                 *[p for p in Path("TradingSystemLab/results/timeframe_analysis").iterdir() if p != output])
    before = {str(p): hash_tree(p) for p in protected}
    loaded = {alias: m15_baseline.load_m15_development(Path(data_root), alias) for _, alias in m15_baseline.INSTRUMENTS}
    sources = _sources(loaded)
    if sources != _expected_sources(bm) or sources != om.get("source_data_hashes"):
        raise RuntimeError("M15_SOURCE_SNAPSHOT_MISMATCH")
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = []
    for key in ("T2", "T3"):
        frozen = dict(registries[key]["parameters"]); pieces = []
        for _, alias in m15_baseline.INSTRUMENTS:
            frame = loaded[alias][0]
            if frame is not None: pieces.append(m15_baseline._execute(key, frozen, alias, frame))
        trades = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=m15_baseline.TRADE_COLUMNS)
        if len(trades): trades = trades.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
        reject_true_oos(pd.to_datetime(trades.entry_time, utc=True)); reject_true_oos(pd.to_datetime(trades.exit_time, utc=True))
        trades["year"] = pd.to_datetime(trades.exit_time, utc=True).dt.year
        metric = _reports(output / key, key, trades, baseline)
        if frozen != registries[key]["parameters"] or stable_hash(frozen) != registries[key]["parameter_hash"]:
            raise RuntimeError(f"{key}_FROZEN_PARAMETERS_MUTATED")
        summaries.append({"strategy": key, "candidate_id": registries[key]["candidate_id"], **metric})
    _csv(output / "comparison.csv", summaries)
    after = {str(p): hash_tree(p) for p in protected}
    if before != after: raise RuntimeError("PROTECTED_ARTIFACT_MUTATION")
    manifest = {"phase": PHASE, "status": STATUS, "timeframe": "M15",
        "candidate_identities": {k: registries[k]["candidate_id"] for k in registries},
        "candidate_registry_hashes": {k: _sha(optimization / k / "candidate_registry.json") for k in registries},
        "candidate_parameter_hashes": {k: registries[k]["parameter_hash"] for k in registries},
        "frozen_strategy_hashes": STRATEGY_SHA256, "baseline_artifact_hash": hash_tree(baseline),
        "optimization_artifact_hash": hash_tree(optimization), "source_data_hashes": sources,
        "development_period": DEVELOPMENT_PERIOD, "true_oos_cutoff": TRUE_OOS_CUTOFF,
        "cost_model": {"name": "H1_C1", "cost_ticks_per_side": COST_TICKS_PER_SIDE,
                       "round_trip_ticks": 2 * COST_TICKS_PER_SIDE, "slippage_ticks_per_side": 0.0},
        "deterministic": True, "protected_artifact_hashes": after, **FLAGS}
    _json(output / "manifest.json", manifest)
    lines = ["# M15 Frozen Candidate Robustness Validation", "", f"Status: `{STATUS}`", "",
             "Independent descriptive replays of T2 and T3 on the full 2023–2024 development period. No optimization, ranking, selection, filter search, portfolio construction, or TRUE OOS access occurred.", "",
             "| Strategy | Trades | PF | Expectancy R | Net R | Max DD R |", "|---|---:|---:|---:|---:|---:|"]
    for row in summaries: lines.append("| " + " | ".join(str(row[x]) for x in ("strategy", "trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")) + " |")
    (output / "robustness_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest
