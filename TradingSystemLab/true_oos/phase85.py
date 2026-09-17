"""Phase 8.5 M1 TRUE-OOS validation.

This module is intentionally a replay-only endpoint: it accepts exactly the two
Phase 8.2 registries proven by Phases 8.3 and 8.4 and exposes no search surface.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import numpy as np
import pandas as pd

from ..core.backtester import Backtester
from ..core.data_loader import DataLoader
from ..core.instrument_specs import get_instrument_spec
from ..core.portfolio import FixedRiskPortfolio
from ..core.unified_metrics import concentration, finite, stats
from ..multitimeframe.phase71 import APPROVED_DATA_ROOT, COST_TICKS_PER_SIDE
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, _normalize_backtester
from ..optimization.phase82 import OUTPUT as PHASE82_ROOT
from ..robustness.phase83 import OUTPUT as PHASE83_ROOT
from ..strategies.trend.T2_Trend_Pullback import T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend
from ..timeframe_validation.phase81 import INSTRUMENTS, TRADE_COLUMNS, causal_four_minute_context
from ..walk_forward.phase84 import OUTPUT as PHASE84_ROOT

OUTPUT = Path("TradingSystemLab/results/timeframe_validation/M1/true_oos")
STATUS = "PHASE_8_5_M1_TRUE_OOS_COMPLETE"
OOS_START = pd.Timestamp("2025-01-01", tz="UTC")
BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 850_003
PROTECTED = (Path("TradingSystemLab/results/true_oos_validation"),
             Path("TradingSystemLab/results/portfolio_construction"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: Any) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def discover_true_oos_files(data_root: Path, alias: str) -> list[Path]:
    """Return only explicitly named 2025-or-later M1 source files."""
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    folder = root / "2026" / alias
    paths = sorted(folder.glob(f"{alias}_M1_*.csv"), key=lambda p: p.name)
    accepted = []
    for path in paths:
        pieces = path.stem.split("_")
        if len(pieces) >= 4 and pieces[2].isdigit() and int(pieces[2]) >= 2025:
            accepted.append(path)
    return accepted


def validate_true_oos_candles(frame: pd.DataFrame) -> None:
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise ValueError("TRUE_OOS_TIMESTAMP_REQUIRED")
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("M1_CANDLE_ORDER_VIOLATION")
    if len(frame) and frame.index.min() < OOS_START:
        raise ValueError("DEVELOPMENT_DATA_IN_TRUE_OOS")


def load_m1_true_oos(data_root: Path, alias: str) -> tuple[pd.DataFrame | None, list[Path]]:
    paths = discover_true_oos_files(data_root, alias)
    if not paths:
        return None, []
    # close_index labels every bar by the instant at which that complete candle
    # becomes observable; strategies therefore cannot consume an open candle.
    frame = DataLoader(forbid_true_oos=False).close_index(DataLoader(forbid_true_oos=False).load_csv(paths), "1min")
    frame = frame.loc[frame.index >= OOS_START].copy()
    validate_true_oos_candles(frame)
    return (frame if len(frame) else None), paths


def _execute(key: str, parameters: dict, alias: str, m1: pd.DataFrame) -> pd.DataFrame:
    """Fresh, FLAT replay using only closed OOS candles and frozen parameters."""
    params = replace(PARAMETERS[key], **parameters)
    spec = get_instrument_spec(alias)
    if key == "T2":
        frame = T2TrendPullback(params).run(m1, alias, tick_size=spec.price_precision)
    else:
        context = causal_four_minute_context(m1)
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=0,
                         tick_size=spec.price_precision).run(T3MTFTrend(params), alias, m1, context).trades
        frame = _normalize_backtester(raw, key)
    if frame.empty:
        return pd.DataFrame(columns=TRADE_COLUMNS + ["instrument", "strategy", "timeframe", "net_R"])
    frame = frame.copy()
    frame["instrument"] = "USDRUBF" if alias == "Si" else "CNYRUBF"
    frame["strategy"], frame["timeframe"] = key, "M1"
    frame["net_R"] = frame.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE / frame.initial_risk_ticks.astype(float)
    frame["trade_id"] = [f"{key}-M1-OOS-{alias}-{n:06d}" for n in range(1, len(frame) + 1)]
    result = frame.sort_values(["exit_time", "trade_id"], kind="mergesort").reset_index(drop=True)
    for column in ("entry_time", "exit_time"):
        times = pd.to_datetime(result[column], utc=True)
        if len(times) and times.min() < OOS_START:
            raise RuntimeError("DEVELOPMENT_TRADE_IN_TRUE_OOS")
    return result


def _metrics(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float)
    result = stats(values)
    holding = ((pd.to_datetime(frame.exit_time, utc=True) - pd.to_datetime(frame.entry_time, utc=True))
               .dt.total_seconds() / 60) if len(frame) else pd.Series(dtype=float)
    return {"total_trades": result["trades"], "PF": finite(result["PF_R"]),
            "expectancy_R": finite(result["expectancy"]), "net_R": result["net_R"],
            "max_drawdown_R": result["max_DD_R"], "recovery_factor": finite(result["recovery_factor"]),
            "win_rate": finite(result["winrate"]), "average_holding_minutes": finite(holding.mean()),
            "losing_streak": result["max_losing_streak"]}


def _groups(trades: pd.DataFrame, column: str, values: list[Any]) -> list[dict]:
    return [{column: value, **_metrics(trades.loc[trades[column].eq(value)])} for value in values]


def _bootstrap(trades: pd.DataFrame) -> tuple[list[dict], dict]:
    values = trades.net_R.to_numpy(float)
    if not len(values):
        rows = [{"percentile": p, "expectancy_R": None, "net_R": None} for p in (2.5, 5, 25, 50, 75, 95, 97.5)]
        return rows, {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED,
                      "probability_mean_R_gt_0": None}
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    # Chunking bounds memory while preserving the exact seeded stream.
    means, nets = [], []
    for start in range(0, BOOTSTRAP_ITERATIONS, 500):
        count = min(500, BOOTSTRAP_ITERATIONS - start)
        samples = rng.choice(values, size=(count, len(values)), replace=True)
        nets.extend(samples.sum(axis=1)); means.extend(samples.mean(axis=1))
    means, nets = np.asarray(means), np.asarray(nets)
    percentiles = (2.5, 5, 25, 50, 75, 95, 97.5)
    rows = [{"percentile": p, "expectancy_R": finite(np.percentile(means, p)),
             "net_R": finite(np.percentile(nets, p))} for p in percentiles]
    return rows, {"iterations": BOOTSTRAP_ITERATIONS, "seed": BOOTSTRAP_SEED,
                  "probability_mean_R_gt_0": finite((means > 0).mean())}


def _classify(metric: dict, bootstrap: dict, quarterly: list[dict], yearly: list[dict],
              instruments: list[dict], directions: list[dict], conc: dict) -> tuple[str, dict]:
    top5_share = conc.get("top_5_positive_R_share")
    checks = {"minimum_30_trades": metric["total_trades"] >= 30,
              "positive_expectancy": (metric["expectancy_R"] or 0) > 0,
              "positive_net_R": metric["net_R"] > 0,
              "drawdown_at_most_20R": metric["max_drawdown_R"] <= 20,
              "bootstrap_probability_at_least_0_90": (bootstrap["probability_mean_R_gt_0"] or 0) >= .90,
              "year_positive": all(x["net_R"] > 0 for x in yearly),
              "majority_quarters_positive": sum(x["net_R"] > 0 for x in quarterly) >= max(1, len(quarterly) // 2 + 1),
              "instruments_positive": all(x["net_R"] > 0 for x in instruments),
              "directions_positive": all(x["net_R"] > 0 for x in directions),
              "top5_share_at_most_50pct": top5_share is not None and top5_share <= .50,
              "positive_without_top5": (conc.get("net_R_without_top5") or 0) > 0}
    checks = {name: bool(value) for name, value in checks.items()}
    passed = sum(checks.values())
    status = "PASS" if passed == len(checks) else ("BORDERLINE" if passed >= 7 else "FAILED")
    return status, checks


def _run_candidate(key: str, registry: dict, loaded: dict[str, tuple], target: Path) -> dict:
    target.mkdir(parents=True)
    parts = []
    for _, alias in INSTRUMENTS:
        candles = loaded[alias][0]
        if candles is not None:
            parts.append(_execute(key, registry["parameters"], alias, candles))
    trades = (pd.concat(parts, ignore_index=True).sort_values(["exit_time", "trade_id"], kind="mergesort")
              .reset_index(drop=True) if parts else pd.DataFrame(columns=TRADE_COLUMNS +
              ["instrument", "strategy", "timeframe", "net_R"]))
    if trades.trade_id.duplicated().any():
        raise RuntimeError("DUPLICATE_TRADE_ID")
    _csv(target / "trades.csv", trades)
    dated = trades.assign(exit=pd.to_datetime(trades.exit_time, utc=True))
    dated["year"] = dated.exit.dt.year
    dated["quarter"] = dated.exit.dt.year.astype(str) + "Q" + dated.exit.dt.quarter.astype(str)
    dated["month"] = dated.exit.dt.strftime("%Y-%m")
    yearly = _groups(dated, "year", sorted(dated.year.unique().tolist()))
    quarterly = _groups(dated, "quarter", sorted(dated.quarter.unique().tolist()))
    monthly = _groups(dated, "month", sorted(dated.month.unique().tolist()))
    instruments = _groups(trades, "instrument", [x[0] for x in INSTRUMENTS])
    directions = _groups(trades, "direction", ["LONG", "SHORT"])
    for name, rows in (("yearly_report.csv", yearly), ("quarterly_report.csv", quarterly),
                       ("monthly_report.csv", monthly), ("instrument_report.csv", instruments),
                       ("direction_report.csv", directions)):
        _csv(target / name, rows)
    conc = concentration(trades.net_R.astype(float))
    _csv(target / "concentration_report.csv", [{**conc,
        "top_five_trade_removal_net_R": conc["net_R_without_top5"],
        "top_five_trade_removal_PF": conc["PF_R_C1_without_top5"]}])
    excursion = [{"statistic": name,
        "MAE_R": finite(trades.MAE_R.astype(float).quantile(q)) if len(trades) else None,
        "MFE_R": finite(trades.MFE_R.astype(float).quantile(q)) if len(trades) else None}
        for name, q in (("minimum", 0), ("p25", .25), ("median", .5), ("p75", .75), ("maximum", 1))]
    _csv(target / "mae_mfe_report.csv", excursion)
    boot_rows, bootstrap = _bootstrap(trades); _csv(target / "bootstrap_report.csv", boot_rows)
    metric = _metrics(trades)
    status, checks = _classify(metric, bootstrap, quarterly, yearly, instruments, directions, conc)
    payload = {"candidate_id": registry["candidate_id"], "parameter_hash": registry["parameter_hash"],
               "classification": status, "classification_checks": checks, "bootstrap": bootstrap, **metric}
    _json(target / "metrics.json", payload)
    (target / "final_report.md").write_text(
        f"# {registry['candidate_id']} TRUE OOS validation\n\nClassification: **{status}**\n\n"
        f"Trades: {metric['total_trades']}; net R: {metric['net_R']}; expectancy R: {metric['expectancy_R']}.\n\n"
        "Frozen replay only; starts FLAT by instrument; no optimization, ranking, or walk-forward.\n",
        encoding="utf-8")
    return {"strategy": key, **payload}


def _verify_inputs(root83: Path, root84: Path, root82: Path) -> tuple[dict, dict, dict[str, dict]]:
    paths = (root83 / "manifest.json", root84 / "manifest.json")
    if not all(p.is_file() for p in paths):
        raise RuntimeError("PHASE_8_3_OR_8_4_PROVENANCE_MISSING")
    m83, m84 = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    if m83.get("phase") != "8.3" or m84.get("phase") != "8.4":
        raise RuntimeError("INVALID_VALIDATION_PROVENANCE")
    if m84.get("phase8_3_candidate_hashes") != m83.get("candidate_hashes") or m84.get("frozen_parameter_hashes") != m83.get("parameter_hashes"):
        raise RuntimeError("PHASE_8_4_FROZEN_PROVENANCE_MISMATCH")
    registries = {}
    for key in ("T2", "T3"):
        path = root82 / key / "candidate_registry.json"
        if not path.is_file() or _sha(path) != m83.get("candidate_hashes", {}).get(key):
            raise RuntimeError(f"{key}_FROZEN_CANDIDATE_HASH_MISMATCH")
        registry = json.loads(path.read_text(encoding="utf-8"))
        if registry.get("candidate_id") != f"{key}_M1_candidate_v1" or stable_hash(registry.get("parameters", {})) != m83["parameter_hashes"][key]:
            raise RuntimeError(f"{key}_FROZEN_PARAMETER_HASH_MISMATCH")
        registries[key] = registry
    return m83, m84, registries


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT,
        phase83_root: Path = PHASE83_ROOT, phase84_root: Path = PHASE84_ROOT,
        phase82_root: Path = PHASE82_ROOT) -> dict[str, Any]:
    output, phase83_root, phase84_root, phase82_root = map(Path, (output, phase83_root, phase84_root, phase82_root))
    m83, m84, registries = _verify_inputs(phase83_root, phase84_root, phase82_root)
    protected = (*PROTECTED, phase82_root, phase83_root, phase84_root)
    before = {str(p): hash_tree(p) for p in protected}
    loaded = {alias: load_m1_true_oos(Path(data_root), alias) for _, alias in INSTRUMENTS}
    sources = [{"instrument": instrument, "alias": alias,
                "files": [{"name": p.name, "sha256": _sha(p)} for p in loaded[alias][1]]}
               for instrument, alias in INSTRUMENTS]
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = [_run_candidate(key, registries[key], loaded, output / key) for key in ("T2", "T3")]
    _csv(output / "comparison.csv", summaries)
    after = {str(p): hash_tree(p) for p in protected}
    if before != after:
        raise RuntimeError("PROTECTED_ARTIFACT_MUTATION")
    all_times = [frame.index for frame, _ in loaded.values() if frame is not None]
    period_end = max(index.max() for index in all_times).isoformat() if all_times else None
    manifest = {"phase": "8.5", "status": STATUS, "timeframe": "M1",
        "candidates": [registries[k]["candidate_id"] for k in ("T2", "T3")],
        "phase8_3_candidate_hashes": m83["candidate_hashes"],
        "phase8_4_validation_hashes": {"manifest.json": _sha(phase84_root / "manifest.json"), "artifact_tree": hash_tree(phase84_root)},
        "frozen_parameter_hashes": m83["parameter_hashes"], "true_oos_source_hashes": sources,
        "oos_period": ["2025-01-01", period_end], "instruments": [x[0] for x in INSTRUMENTS],
        "cost_model": {"cost_ticks_per_side": COST_TICKS_PER_SIDE, "round_trip_ticks": 2 * COST_TICKS_PER_SIDE,
                       "slippage_ticks_per_side": 0.0},
        "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "flat_initialization_per_candidate_instrument": True, "completed_candles_only": True,
        "deterministic": True, "optimization": False, "ranking": False, "walk_forward": False,
        "true_oos_blocked": False, "protected_artifact_hashes": after}
    _json(output / "manifest.json", manifest)
    lines = ["# Phase 8.5 M1 TRUE OOS Validation", "", "Independent validation; this table is not a ranking.", "",
             "| Candidate | Classification | Trades | PF | Expectancy R | Net R | Max DD R | Bootstrap P(mean R > 0) |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for x in summaries:
        lines.append(f"| {x['candidate_id']} | {x['classification']} | {x['total_trades']} | {x['PF']} | {x['expectancy_R']} | {x['net_R']} | {x['max_drawdown_R']} | {x['bootstrap']['probability_mean_R_gt_0']} |")
    lines += ["", "Frozen candidates; independent FLAT instrument replays; completed 2025+ candles only.", "",
              "optimization=false; ranking=false; walk_forward=false; true_oos_blocked=false; deterministic=true.", "", STATUS, ""]
    (output / "m1_true_oos_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": STATUS, "candidates": summaries, "oos_period": manifest["oos_period"]}
