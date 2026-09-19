"""Standalone D1 baseline for the frozen H1 T2/T3 candidates.

This workflow is deliberately descriptive.  It reads only explicitly named
2023/2024 H1 files, constructs causal D1/4D inputs, and exposes no optimization,
ranking, selection, walk-forward, or TRUE-OOS interface.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from ..core.backtester import Backtester
from ..core.data_loader import DataLoader
from ..core.instrument_specs import get_instrument_spec
from ..core.portfolio import FixedRiskPortfolio
from ..core.unified_metrics import concentration, finite, stats
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, _normalize_backtester
from ..strategies.trend.T2_Trend_Pullback import T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend

INSTRUMENTS = (("USDRUBF", "Si"), ("CNYRUBF", "CNY"))
APPROVED_DATA_ROOT = Path("/workspace/market-pattern-data")
DEVELOPMENT_START = pd.Timestamp("2023-01-01", tz="Europe/Moscow")
TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="Europe/Moscow")
COST_TICKS_PER_SIDE = 1.0
STRATEGY_SHA256 = {"T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
                   "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}
STRATEGY_FILES = {"T2": "T2_Trend_Pullback.py", "T3": "T3_MTF_Trend.py"}
TIMEFRAME = "D1"
PHASE = "D1_BASELINE"
STATUS = "PHASE_D1_BASELINE_COMPLETE"
OUTPUT = Path("TradingSystemLab/results/timeframe_validation/D1")
REGISTRY = Path("TradingSystemLab/results/robustness_validation/candidate_registry.json")
EXPECTED = {
    "T2": {"candidate_id": "T2_candidate_v1", "phase32_configuration_id": "T2-0007-608dc87d09f1",
           "parameter_hash": "2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00",
           "parameters": {"adx_threshold": 20, "confirmation_window": 3, "ema_fast": 20,
             "ema_slow": 200, "ema_trend": 50, "impulse_distance_atr": .5,
             "max_initial_stop_atr": 2.5, "trailing_atr": 3}},
    "T3": {"candidate_id": "T3_candidate_v1", "phase32_configuration_id": "T3-0014-0050d828c1a8",
           "parameter_hash": "938b6b3b78f680010115a204b9a49e7eef962db119f4ea121e388c00741920ba",
           "parameters": {"adx_threshold": 20, "atr_average_period": 20, "breakout_period": 20,
             "ema_period": 75, "stop_atr": 2.0, "trail_atr": 3.0}},
}
PROTECTED_ARTIFACTS = tuple(Path(p) for p in (
    "TradingSystemLab/results/T2_implementation_check", "TradingSystemLab/results/T3_robust",
    "TradingSystemLab/results/robustness_validation", "TradingSystemLab/results/multitimeframe_research",
    "TradingSystemLab/results/candidate_registry_v2", "TradingSystemLab/results/timeframe_validation/M1",
    "TradingSystemLab/results/timeframe_validation/M5", "TradingSystemLab/results/timeframe_validation/M15",
    "TradingSystemLab/results/timeframe_validation/M30", "TradingSystemLab/results/timeframe_analysis",
    "TradingSystemLab/results/timeframe_validation/H4",
    "TradingSystemLab/results/timeframe_diagnostics", "TradingSystemLab/results/timeframe_optimization",
    "TradingSystemLab/results/walk_forward", "TradingSystemLab/results/true_oos_validation",
    "TradingSystemLab/strategies/trend/T2_Trend_Pullback.py",
    "TradingSystemLab/strategies/trend/T3_MTF_Trend.py"))
TRADE_COLUMNS = ["trade_id", "strategy_id", "symbol", "direction", "entry_time", "exit_time",
                 "gross_R", "initial_risk_ticks", "MAE_R", "MFE_R", "instrument", "strategy",
                 "timeframe", "net_R"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_tree(path: Path) -> str:
    """Hash a protected file/tree without following or modifying it."""
    digest = hashlib.sha256()
    if not path.exists():
        return "MISSING"
    paths = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    for item in paths:
        digest.update(str(item.relative_to(path) if path.is_dir() else item.name).encode())
        digest.update(item.read_bytes())
    return digest.hexdigest()


def verify_frozen_strategies(project_root: Path = Path(".")) -> None:
    for key, expected in STRATEGY_SHA256.items():
        path = project_root / "TradingSystemLab/strategies/trend" / STRATEGY_FILES[key]
        if _sha(path) != expected:
            raise RuntimeError(f"{key}_FROZEN_STRATEGY_HASH_MISMATCH")


def reject_true_oos(index: pd.Index) -> None:
    stamps = pd.DatetimeIndex(pd.to_datetime(index, utc=True))
    if (stamps >= TRUE_OOS_START.tz_convert("UTC")).any():
        raise ValueError("TRUE_OOS_BARRIER_VIOLATION: timestamp >= 2025-01-01")


def frozen_candidates(registry: Path = REGISTRY) -> dict[str, dict]:
    rows = json.loads(registry.read_text(encoding="utf-8"))
    result = {row["strategy"]: row for row in rows if row.get("candidate_id") in
              ("T2_candidate_v1", "T3_candidate_v1")}
    if set(result) != set(EXPECTED):
        raise RuntimeError("FROZEN_CANDIDATE_REGISTRY_INVALID")
    for key, expected in EXPECTED.items():
        row = result[key]
        if (row["candidate_id"] != expected["candidate_id"] or
                row["phase32_configuration_id"] != expected["phase32_configuration_id"] or
                row["parameters"] != expected["parameters"] or
                stable_hash(row["parameters"]) != expected["parameter_hash"]):
            raise RuntimeError(f"{key}_FROZEN_CANDIDATE_MISMATCH")
    return result


def discover_h1_files(data_root: Path, alias: str) -> list[Path]:
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    folder = root / "2026" / alias
    return sorted((p for year in (2023, 2024)
                   for p in folder.glob(f"{alias}_H1_{year}_Q*.csv")), key=lambda p: p.name)


def validate_development(frame: pd.DataFrame) -> None:
    index = pd.DatetimeIndex(frame.index)
    if index.tz is None or not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError("H1_TIMESTAMP_VIOLATION")
    reject_true_oos(index)


def load_h1_development(data_root: Path, alias: str) -> tuple[pd.DataFrame | None, list[Path]]:
    paths = discover_h1_files(data_root, alias)
    if not paths:
        return None, []
    loader = DataLoader(forbid_true_oos=True)
    # Validate the raw, open-labelled stream before any sorting, de-duplication,
    # filtering, or aggregation can conceal a source defect.
    raw = pd.concat([loader._read(path) for path in paths])  # noqa: SLF001
    validate_development(raw)
    frame = loader.close_index(raw, "1h")
    frame = frame.loc[(frame.index >= DEVELOPMENT_START) & (frame.index < TRUE_OOS_START)]
    validate_development(frame)
    return (frame if not frame.empty else None), paths


def causal_d1(h1: pd.DataFrame) -> pd.DataFrame:
    """Completed Moscow-day candles, labelled only at their final H1 close."""
    rows = []
    for _, day in h1.groupby(h1.index.normalize(), sort=True):
        row = {"Open": day.Open.iloc[0], "High": day.High.max(), "Low": day.Low.min(),
               "Close": day.Close.iloc[-1]}
        if "Volume" in day:
            row["Volume"] = day.Volume.sum()
        rows.append((day.index[-1], row))
    result = (pd.DataFrame([r for _, r in rows], index=[t for t, _ in rows])
              if rows else pd.DataFrame(columns=h1.columns))
    result.index.name = "CloseTime"
    return result


def causal_4d(d1: pd.DataFrame) -> pd.DataFrame:
    """Non-overlapping, complete four-D1-bar blocks, labelled at bar four's close."""
    rows = []
    for offset in range(0, len(d1), 4):
        block = d1.iloc[offset:offset + 4]
        if len(block) != 4:
            continue
        row = {"Open": block.Open.iloc[0], "High": block.High.max(), "Low": block.Low.min(),
               "Close": block.Close.iloc[-1]}
        if "Volume" in block:
            row["Volume"] = block.Volume.sum()
        rows.append((block.index[-1], row))
    result = (pd.DataFrame([r for _, r in rows], index=[t for t, _ in rows])
              if rows else pd.DataFrame(columns=d1.columns))
    result.index.name = "CloseTime"
    return result


def _execute(key: str, parameters: dict, alias: str, h1: pd.DataFrame) -> pd.DataFrame:
    params = replace(PARAMETERS[key], **parameters)
    tick = get_instrument_spec(alias).price_precision
    execution = causal_d1(h1)
    if key == "T2":
        frame = T2TrendPullback(params).run(execution, alias, tick_size=tick)
    else:
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=0, tick_size=tick).run(
            T3MTFTrend(params), alias, execution, causal_4d(execution)).trades
        frame = _normalize_backtester(raw, key)
    if frame.empty:
        return pd.DataFrame(columns=TRADE_COLUMNS)
    frame = frame.copy()
    reject_true_oos(frame.entry_time); reject_true_oos(frame.exit_time)
    frame["instrument"] = "USDRUBF" if alias == "Si" else "CNYRUBF"
    frame["strategy"], frame["timeframe"] = key, TIMEFRAME
    frame["net_R"] = frame.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE / frame.initial_risk_ticks.astype(float)
    frame["trade_id"] = [f"{key}-D1-{alias}-{n:06d}" for n in range(1, len(frame) + 1)]
    return frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def _summary(frame: pd.DataFrame) -> dict[str, Any]:
    metric = stats(frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float))
    holding = ((pd.to_datetime(frame.exit_time, utc=True) - pd.to_datetime(frame.entry_time, utc=True))
               .dt.total_seconds() / 60) if len(frame) else pd.Series(dtype=float)
    return {"trades": metric["trades"], "PF": metric["PF_R"], "expectancy_R": metric["expectancy"],
            "net_R": metric["net_R"], "max_drawdown_R": metric["max_DD_R"],
            "recovery_factor": metric["recovery_factor"], "win_rate": metric["winrate"],
            "average_win_R": metric["average_win_R"], "average_loss_R": metric["average_loss_R"],
            "max_winning_streak": metric["max_winning_streak"],
            "max_losing_streak": metric["max_losing_streak"],
            "average_holding_minutes": finite(holding.mean()),
            "median_holding_minutes": finite(holding.median()),
            "average_MAE_R": finite(frame.MAE_R.astype(float).mean()) if len(frame) else None,
            "average_MFE_R": finite(frame.MFE_R.astype(float).mean()) if len(frame) else None}


def _csv(path: Path, rows: Any) -> None:
    (rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)).map(finite).to_csv(
        path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _reports(target: Path, trades: pd.DataFrame, key: str) -> dict[str, Any]:
    target.mkdir(parents=True)
    metric = _summary(trades)
    _csv(target / "trades.csv", trades); _json(target / "metrics.json", metric)
    group = lambda column, value: _summary(trades.loc[trades[column].eq(value)])
    _csv(target / "yearly_report.csv", [{"year": y, **group("year", y)} for y in (2023, 2024)])
    _csv(target / "instrument_report.csv", [{"instrument": n, **group("instrument", n)} for n, _ in INSTRUMENTS])
    _csv(target / "direction_report.csv", [{"direction": d, **group("direction", d)} for d in ("LONG", "SHORT")])
    _csv(target / "concentration_report.csv", [concentration(trades.net_R)])
    scopes = [("ALL", trades), ("WINNERS", trades.loc[trades.net_R > 0]),
              ("LOSERS", trades.loc[trades.net_R < 0])]
    _csv(target / "mae_mfe_report.csv", [{"scope": name,
        "average_MAE_R": finite(rows.MAE_R.astype(float).mean()) if len(rows) else None,
        "average_MFE_R": finite(rows.MFE_R.astype(float).mean()) if len(rows) else None}
        for name, rows in scopes])
    (target / "final_report.md").write_text(
        f"# D1 Baseline — {key}_candidate_v1\n\nFrozen H1 candidate; descriptive baseline only. "
        "No optimization, ranking, selection, or strategy/parameter change.\n", encoding="utf-8")
    return metric


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    verify_frozen_strategies(); candidates = frozen_candidates()
    protected_before = {str(p): hash_tree(p) for p in PROTECTED_ARTIFACTS}
    loaded = {alias: load_h1_development(data_root, alias) for _, alias in INSTRUMENTS}
    if any(frame is None for frame, _ in loaded.values()):
        raise RuntimeError("DATA_UNAVAILABLE: required H1 development data is missing")
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    coverage, sources = [], []
    for instrument, alias in INSTRUMENTS:
        frame, paths = loaded[alias]
        files = [{"filename": p.name, "sha256": _sha(p)} for p in paths]
        d1 = causal_d1(frame)
        context = causal_4d(d1)
        coverage.append({"instrument": instrument, "alias": alias, "source_bar_count": len(frame),
                         "d1_bar_count": len(d1), "first_source_close": frame.index.min().isoformat(),
                         "last_source_close": frame.index.max().isoformat(), "first_d1_close": d1.index.min().isoformat(),
                         "last_d1_close": d1.index.max().isoformat(), "t3_4d_context_count": len(context),
                         "first_t3_4d_close": context.index.min().isoformat(),
                         "last_t3_4d_close": context.index.max().isoformat(), "files": files,
                         "years_present": sorted(set(frame.index.year))})
        sources.extend({"instrument": instrument, "alias": alias, **item} for item in files)
    comparison, trades_by_key = [], {}
    for key in ("T2", "T3"):
        pieces = [_execute(key, candidates[key]["parameters"], alias, loaded[alias][0]) for _, alias in INSTRUMENTS]
        trades = pd.concat(pieces, ignore_index=True).sort_values(
            ["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
        trades["year"] = pd.to_datetime(trades.exit_time, utc=True).dt.year
        trades_by_key[key] = trades
        metric = _reports(output / key, trades, key)
        comparison.append({"strategy": key, "candidate_id": candidates[key]["candidate_id"], **metric})
    _csv(output / "comparison.csv", comparison)
    historical = pd.read_csv("TradingSystemLab/results/multitimeframe_research/comparison.csv")
    historical = historical.loc[(historical.timeframe == "D1") & historical.strategy.isin(("T2", "T3")) &
                                historical.instrument.isin(("USDRUBF", "CNYRUBF"))]
    actual_counts = {(key, instrument): int(len(trades_by_key[key].loc[
                        trades_by_key[key].instrument == instrument]))
                     for key in ("T2", "T3") for instrument, _ in INSTRUMENTS}
    parity = [{"strategy": row.strategy, "instrument": row.instrument,
               "historical_trades": int(row.trades),
               "standalone_trades": actual_counts[(row.strategy, row.instrument)],
               "matches": int(row.trades) == actual_counts[(row.strategy, row.instrument)]}
              for row in historical.itertuples(index=False)]
    protected_after = {str(p): hash_tree(p) for p in PROTECTED_ARTIFACTS}
    if protected_before != protected_after: raise RuntimeError("PROTECTED_RESEARCH_ARTIFACT_MUTATION")
    manifest = {"phase": PHASE, "status": STATUS, "timeframe": TIMEFRAME,
        "methodological_source": "H1_BASELINE", "t3_context": "D1_TO_4D",
        "development_period": ["2023-01-01", "2024-12-31"], "true_oos_cutoff": "2025-01-01",
        "candidates": {k: {"candidate_id": candidates[k]["candidate_id"],
            "phase32_configuration_id": candidates[k]["phase32_configuration_id"],
            "parameter_hash": stable_hash(candidates[k]["parameters"]),
            "strategy_hash": STRATEGY_SHA256[k]} for k in ("T2", "T3")},
        "instruments": [{"instrument": n, "alias": a} for n, a in INSTRUMENTS],
        "source_files": sources, "source_coverage": coverage,
        "cost_model": {"name": "H1_C1", "ticks_per_side": 1.0, "round_trip_ticks": 2.0,
                       "additional_slippage_ticks": 0.0}, "deterministic_execution": True,
        "optimization": False, "ranking": False, "selection": False, "robustness": False, "walk_forward": False,
        "true_oos_blocked": True, "parameter_change": False, "strategy_change": False,
        "historical_phase_7_1_parity": parity, "protected_research_unchanged": True,
        "protected_artifact_hashes": protected_after}
    _json(output / "manifest.json", manifest)
    lines = ["# D1 Baseline Research", "", "Frozen H1 candidates on causal D1 execution candles over full 2023–2024 development data.", "",
             "| Strategy | Trades | PF | Expectancy R | Net R | Max DD R |", "|---|---:|---:|---:|---:|---:|"]
    for row in comparison:
        lines.append("| " + " | ".join(str(row[c]) for c in ("strategy", "trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")) + " |")
    lines += ["", "T2 ran directly on D1. T3 used four completed D1 bars per causal 4D context candle.",
              "H1 C1: one tick per side; no additional slippage. No optimization, ranking, or selection.",
              "", "## Historical Phase 7.1 parity", ""]
    lines += [f"- {p['strategy']} {p['instrument']}: standalone {p['standalone_trades']}, historical "
              f"{p['historical_trades']} — {'MATCH' if p['matches'] else 'DIFF'}" for p in parity]
    lines += ["", STATUS, ""]
    (output / "d1_baseline_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": STATUS, "strategies": 2}
