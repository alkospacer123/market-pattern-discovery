"""Phase 8.1 frozen-candidate M1 baseline research.

Only explicitly named 2023/2024 M1 files are discoverable.  This module has no
optimization, ranking, selection, walk-forward, or TRUE-OOS interface.
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
from ..multitimeframe.phase71 import (APPROVED_DATA_ROOT, COST_TICKS_PER_SIDE,
    DEVELOPMENT_START, STRATEGY_SHA256, TRUE_OOS_START, frozen_candidates,
    reject_true_oos, verify_frozen_strategies)
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, _normalize_backtester
from ..strategies.trend.T2_Trend_Pullback import T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend

INSTRUMENTS = (("USDRUBF", "Si"), ("CNYRUBF", "CNY"))
PROTECTED = (Path("TradingSystemLab/results/true_oos_validation"),
             Path("TradingSystemLab/results/portfolio_construction"))
TRADE_COLUMNS = ["trade_id", "strategy_id", "symbol", "direction", "entry_time",
                 "exit_time", "gross_R", "initial_risk_ticks", "MAE_R", "MFE_R"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_m1_files(data_root: Path, alias: str) -> list[Path]:
    """Discover M1 development files without traversing or opening OOS files."""
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    folder = root / "2026" / alias
    return sorted((p for year in (2023, 2024)
                   for p in folder.glob(f"{alias}_M1_{year}_Q*.csv")), key=lambda p: p.name)


def validate_candle_order(frame: pd.DataFrame) -> None:
    """Require one deterministic observation per strictly increasing close."""
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("M1_CANDLE_ORDER_VIOLATION")
    reject_true_oos(frame.index)


def load_m1_development(data_root: Path, alias: str) -> tuple[pd.DataFrame | None, list[Path]]:
    paths = discover_m1_files(data_root, alias)
    if not paths:
        return None, []
    loader = DataLoader(forbid_true_oos=True)
    frame = loader.close_index(loader.load_csv(paths), "1min")
    frame = frame.loc[(frame.index >= DEVELOPMENT_START) & (frame.index < TRUE_OOS_START)]
    if frame.empty:
        return None, paths
    validate_candle_order(frame)
    return frame, paths


def causal_four_minute_context(m1: pd.DataFrame) -> pd.DataFrame:
    """Build complete consecutive four-M1 blocks, resetting every trading day."""
    rows: list[tuple[pd.Timestamp, dict[str, float]]] = []
    for _, day in m1.groupby(m1.index.normalize(), sort=True):
        for offset in range(0, len(day), 4):
            block = day.iloc[offset:offset + 4]
            if len(block) != 4 or not (block.index.to_series().diff().iloc[1:] == pd.Timedelta("1min")).all():
                continue
            row = {"Open": block.Open.iloc[0], "High": block.High.max(),
                   "Low": block.Low.min(), "Close": block.Close.iloc[-1]}
            if "Volume" in block:
                row["Volume"] = block.Volume.sum()
            rows.append((block.index[-1] + pd.Timedelta("1min"), row))
    columns = [c for c in ("Open", "High", "Low", "Close", "Volume") if c in m1.columns]
    result = pd.DataFrame([r for _, r in rows], index=[t for t, _ in rows], columns=columns)
    result.index = pd.DatetimeIndex(result.index, name="CloseTime")
    return result


def _execute(key: str, parameters: dict, alias: str, m1: pd.DataFrame) -> pd.DataFrame:
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
    reject_true_oos(frame.entry_time); reject_true_oos(frame.exit_time)
    frame["instrument"] = "USDRUBF" if alias == "Si" else "CNYRUBF"
    frame["strategy"] = key
    frame["timeframe"] = "M1"
    frame["net_R"] = frame.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE / frame.initial_risk_ticks.astype(float)
    frame["trade_id"] = [f"{key}-M1-{alias}-{n:06d}" for n in range(1, len(frame) + 1)]
    return frame.sort_values(["exit_time", "trade_id"], kind="mergesort").reset_index(drop=True)


def _summary(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float)
    metric = stats(values)
    holding = ((pd.to_datetime(frame.exit_time, utc=True) - pd.to_datetime(frame.entry_time, utc=True))
               .dt.total_seconds() / 60) if len(frame) else pd.Series(dtype=float)
    return {"total_trades": metric["trades"], "PF": metric["PF_R"],
            "expectancy_R": metric["expectancy"], "net_R": metric["net_R"],
            "max_drawdown_R": metric["max_DD_R"], "recovery_factor": metric["recovery_factor"],
            "win_rate": metric["winrate"], "average_holding_minutes": finite(holding.mean()),
            "losing_streak": metric["max_losing_streak"],
            "average_MAE_R": finite(frame.MAE_R.astype(float).mean()) if len(frame) else None,
            "average_MFE_R": finite(frame.MFE_R.astype(float).mean()) if len(frame) else None}


def _csv(path: Path, rows: Any) -> None:
    data = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    data.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _write_combination(target: Path, trades: pd.DataFrame, status: str,
                       strategy: str, instrument: str) -> dict[str, Any]:
    target.mkdir(parents=True, exist_ok=True)
    metric = _summary(trades)
    _csv(target / "trades.csv", trades)
    _json(target / "metrics.json", {"status": status, **metric})
    _csv(target / "instrument_report.csv", [{"instrument": instrument, **metric}])
    def group(column: str, values: list[Any]) -> list[dict[str, Any]]:
        return [{column: value, **_summary(trades.loc[trades[column].eq(value)])} for value in values]
    _csv(target / "direction_report.csv", group("direction", ["LONG", "SHORT"]))
    years = pd.to_datetime(trades.exit_time, utc=True).dt.year if len(trades) else pd.Series(dtype=int)
    yearly = trades.assign(year=years)
    _csv(target / "yearly_report.csv", [{"year": year, **_summary(yearly.loc[yearly.year.eq(year)])}
                                         for year in (2023, 2024)])
    _csv(target / "mae_mfe_report.csv", [{"instrument": instrument, **metric}])
    value = concentration(trades.net_R) if len(trades) else concentration(pd.Series(dtype=float))
    _csv(target / "concentration_report.csv", [{**value,
        "top_5_trade_removal_net_R": value["net_R_without_top5"],
        "top_5_trade_removal_PF": value["PF_R_C1_without_top5"]}])
    (target / "final_report.md").write_text(
        f"# Phase 8.1 {strategy}_M1 — {instrument}\n\nStatus: {status}\n\n"
        "Frozen candidate baseline on development data; no optimization, ranking, selection, or walk-forward.\n",
        encoding="utf-8")
    return metric


def run(data_root: Path = APPROVED_DATA_ROOT,
        output: Path = Path("TradingSystemLab/results/timeframe_validation/M1")) -> dict[str, Any]:
    verify_frozen_strategies()
    candidates = frozen_candidates()
    protected_before = {str(path): hash_tree(path) for path in PROTECTED}
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    loaded = {alias: load_m1_development(Path(data_root), alias) for _, alias in INSTRUMENTS}
    comparison, sources = [], []
    for key in ("T2", "T3"):
        candidate = candidates[key]
        parameter_hash = stable_hash(candidate["parameters"])
        for instrument, alias in INSTRUMENTS:
            frame, paths = loaded[alias]
            status = "DATA_UNAVAILABLE" if frame is None else "AVAILABLE"
            trades = _execute(key, candidate["parameters"], alias, frame) if frame is not None else pd.DataFrame(
                columns=TRADE_COLUMNS + ["instrument", "strategy", "timeframe", "net_R"])
            metric = _write_combination(output / key / instrument, trades, status, key, instrument)
            comparison.append({"strategy": key, "candidate_id": candidate["candidate_id"],
                               "instrument": instrument, "timeframe": "M1", "status": status, **metric})
            sources.append({"strategy": key, "instrument": instrument, "timeframe": "M1", "status": status,
                            "files": [{"name": path.name, "sha256": _sha(path)} for path in paths]})
        if stable_hash(candidate["parameters"]) != parameter_hash:
            raise RuntimeError(f"{key}_FROZEN_PARAMETERS_MUTATED")
    _csv(output / "comparison.csv", comparison)
    protected_after = {str(path): hash_tree(path) for path in PROTECTED}
    if protected_before != protected_after:
        raise RuntimeError("PROTECTED_ARTIFACT_MUTATION")
    manifest = {"phase": "8.1", "status": "PHASE_8_1_M1_BASELINE_COMPLETE", "timeframe": "M1",
        "development_period": ["2023-01-01", "2024-12-31"],
        "instruments": [x[0] for x in INSTRUMENTS],
        "strategies": [candidates[x]["candidate_id"] for x in ("T2", "T3")],
        "source_data_hashes": sources, "frozen_strategy_hashes": STRATEGY_SHA256,
        "parameter_hashes": {key: stable_hash(candidates[key]["parameters"]) for key in ("T2", "T3")},
        "cost_model": {"cost_ticks_per_side": COST_TICKS_PER_SIDE,
                       "round_trip_ticks": 2 * COST_TICKS_PER_SIDE, "slippage_ticks_per_side": 0.0},
        "optimization": False, "ranking": False, "walk_forward": False,
        "true_oos_blocked": True, "deterministic": True,
        "protected_artifact_hashes": protected_after}
    _json(output / "manifest.json", manifest)
    lines = ["# Phase 8.1 M1 Baseline Research", "",
        "Frozen T2_candidate_v1 and T3_candidate_v1 were evaluated independently on M1 development data only.", "",
        "| Strategy | Instrument | Status | Trades | PF | Expectancy R | Net R | Max DD R |",
        "|---|---|---|---:|---:|---:|---:|---:|"]
    fmt = lambda value: "" if value is None else (f"{value:.6g}" if isinstance(value, float) else str(value))
    for row in comparison:
        lines.append("| " + " | ".join(fmt(row[k]) for k in
            ("strategy", "instrument", "status", "total_trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")) + " |")
    lines += ["", "M1 files only; missing candles are not fabricated. T3 context uses completed consecutive four-M1 blocks and becomes visible on the following M1 candle.", "",
              "optimization=false; ranking=false; walk_forward=false; true_oos_blocked=true.", "", "PHASE_8_1_M1_BASELINE_COMPLETE", ""]
    (output / "m1_baseline_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": manifest["status"], "combinations": len(comparison)}
