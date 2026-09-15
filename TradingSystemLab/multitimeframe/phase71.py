"""Deterministic, development-only multi-timeframe adapter and research runner.

This module is deliberately descriptive: it exposes no parameter, optimization,
ranking, walk-forward, or selection interface.  Source files remain read-only.
"""
from __future__ import annotations

from dataclasses import asdict, replace
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
from ..core.unified_metrics import finite, stats
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, _normalize_backtester
from ..strategies.trend.T2_Trend_Pullback import T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend

APPROVED_DATA_ROOT = Path("/workspace/market-pattern-data")
DEVELOPMENT_START = pd.Timestamp("2023-01-01", tz="Europe/Moscow")
TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="Europe/Moscow")
TIMEFRAMES = ("M30", "H1", "H4", "D1")
FUTURE_TIMEFRAMES = ("M15", "M5", "M1")
INSTRUMENTS = (("USDRUBF", "Si"), ("CNYRUBF", "CNY"),
               ("EURRUBF", "EUR"), ("HKDRUBF", "HKD"))
STRATEGY_SHA256 = {
    "T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
    "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c",
}
STRATEGY_FILES = {"T2": "T2_Trend_Pullback.py", "T3": "T3_MTF_Trend.py"}
COST_TICKS_PER_SIDE = 1.0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_strategies(project_root: Path = Path(".")) -> None:
    """Reject modified frozen signal code before opening any market data."""
    for key, expected in STRATEGY_SHA256.items():
        path = project_root / "TradingSystemLab/strategies/trend" / STRATEGY_FILES[key]
        if _sha(path) != expected:
            raise RuntimeError(f"{key}_FROZEN_STRATEGY_HASH_MISMATCH")


def frozen_candidates(registry: Path = Path("TradingSystemLab/results/robustness_validation/candidate_registry.json")) -> dict[str, dict]:
    rows = json.loads(registry.read_text(encoding="utf-8"))
    result = {row["strategy"]: row for row in rows if row["strategy"] in ("T2", "T3")}
    if sorted(result) != ["T2", "T3"]:
        raise RuntimeError("FROZEN_CANDIDATE_REGISTRY_INVALID")
    return result


def reject_true_oos(index: pd.Index) -> None:
    stamps = pd.DatetimeIndex(pd.to_datetime(index, utc=True))
    if (stamps >= TRUE_OOS_START.tz_convert("UTC")).any():
        raise ValueError("TRUE_OOS_BARRIER_VIOLATION: timestamp >= 2025-01-01")


def discover_files(data_root: Path, alias: str, source_tf: str) -> list[Path]:
    """Discover only explicitly year-labelled 2023/2024 files under the approved root."""
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    folder = root / "2026" / alias
    files = [p for year in (2023, 2024)
             for p in sorted(folder.glob(f"{alias}_{source_tf}_{year}_Q*.csv"))]
    return sorted(files, key=lambda p: p.name)


def _aggregate(frame: pd.DataFrame, size: int, *, cross_days: bool = False) -> pd.DataFrame:
    """Build complete causal blocks labelled at their final constituent close.

    Intraday blocks reset at each Moscow trading-day boundary.  ``cross_days``
    is reserved for the explicitly named T3 D1_TO_4D context series.
    """
    groups = [(None, frame)] if cross_days else frame.groupby(frame.index.normalize(), sort=True)
    rows: list[tuple[pd.Timestamp, dict[str, float]]] = []
    for _, group in groups:
        for offset in range(0, len(group), size):
            block = group.iloc[offset:offset + size]
            if len(block) != size:
                continue
            row = {"Open": block.Open.iloc[0], "High": block.High.max(),
                   "Low": block.Low.min(), "Close": block.Close.iloc[-1]}
            if "Volume" in block:
                row["Volume"] = block.Volume.sum()
            rows.append((block.index[-1], row))
    if not rows:
        return pd.DataFrame(columns=frame.columns, index=pd.DatetimeIndex([], name="CloseTime"))
    out = pd.DataFrame([r for _, r in rows], index=[t for t, _ in rows])
    out.index.name = "CloseTime"
    return out


class TimeframeAdapter:
    """Map frozen strategy inputs onto another resolution without changing strategy code."""

    def __init__(self, timeframe: str) -> None:
        if timeframe not in TIMEFRAMES + FUTURE_TIMEFRAMES:
            raise ValueError(f"unsupported timeframe: {timeframe}")
        self.timeframe = timeframe

    @property
    def source_timeframe(self) -> str:
        return "M30" if self.timeframe == "M30" else "H1"

    def execution(self, source_closed: pd.DataFrame) -> pd.DataFrame:
        if self.timeframe in ("M30", "H1"):
            return source_closed.copy()
        if self.timeframe == "H4":
            return _aggregate(source_closed, 4)
        if self.timeframe == "D1":
            rows = []
            for _, day in source_closed.groupby(source_closed.index.normalize(), sort=True):
                row = {"Open": day.Open.iloc[0], "High": day.High.max(),
                       "Low": day.Low.min(), "Close": day.Close.iloc[-1]}
                if "Volume" in day: row["Volume"] = day.Volume.sum()
                rows.append((day.index[-1], row))
            out = pd.DataFrame([r for _, r in rows], index=[t for t, _ in rows]) if rows else pd.DataFrame(columns=source_closed.columns)
            out.index.name = "CloseTime"
            return out
        # Future-compatible direct resolutions are admitted when matching files exist.
        return source_closed.copy()

    def strategy_inputs(self, source_closed: pd.DataFrame, strategy: str) -> tuple[pd.DataFrame, pd.DataFrame | None]:
        execution = self.execution(source_closed)
        reject_true_oos(execution.index)
        if strategy == "T2": return execution, None
        # T3 uses four completed execution candles at M30/H1. At H4 the next
        # causal session resolution is D1; D1_TO_4D is explicitly cross-day.
        if self.timeframe == "H4":
            context = TimeframeAdapter("D1").execution(source_closed)
        else:
            context = _aggregate(execution, 4, cross_days=self.timeframe == "D1")
        return execution, context


def load_development(data_root: Path, alias: str, adapter: TimeframeAdapter) -> tuple[pd.DataFrame | None, list[str]]:
    paths = discover_files(data_root, alias, adapter.source_timeframe)
    if not paths: return None, []
    duration = "30min" if adapter.source_timeframe == "M30" else "1h"
    frame = DataLoader(forbid_true_oos=True).close_index(DataLoader(forbid_true_oos=True).load_csv(paths), duration)
    frame = frame.loc[(frame.index >= DEVELOPMENT_START) & (frame.index < TRUE_OOS_START)]
    reject_true_oos(frame.index)
    return frame, [p.name for p in paths]


def _execute(key: str, parameters: dict, alias: str, timeframe: str, source: pd.DataFrame) -> pd.DataFrame:
    adapter = TimeframeAdapter(timeframe); low, high = adapter.strategy_inputs(source, key)
    params = replace(PARAMETERS[key], **parameters)
    spec = get_instrument_spec(alias)
    if key == "T2":
        frame = T2TrendPullback(params).run(low, alias, tick_size=spec.price_precision)
    else:
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=0,
                         tick_size=spec.price_precision).run(T3MTFTrend(params), alias, low, high).trades
        frame = _normalize_backtester(raw, key)
    if len(frame):
        reject_true_oos(frame.entry_time); reject_true_oos(frame.exit_time)
        frame["trade_id"] = [f"{key}-{alias}-{timeframe}-{i:06d}" for i in range(1, len(frame) + 1)]
        frame = frame.sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
    return frame


def _summary(frame: pd.DataFrame) -> dict[str, Any]:
    values = (frame.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE /
              frame.initial_risk_ticks.astype(float)) if len(frame) else pd.Series(dtype=float)
    s = stats(values)
    holding = ((pd.to_datetime(frame.exit_time, utc=True) - pd.to_datetime(frame.entry_time, utc=True))
               .dt.total_seconds() / 3600) if len(frame) else pd.Series(dtype=float)
    return {"trades": s["trades"], "PF": s["PF_R"], "expectancy": s["expectancy"],
            "net_R": s["net_R"], "max_drawdown": s["max_DD_R"],
            "recovery_factor": s["recovery_factor"], "win_rate": s["winrate"],
            "average_holding_hours": finite(holding.mean()),
            "average_MAE_R": finite(frame.MAE_R.astype(float).mean()) if len(frame) else None,
            "average_MFE_R": finite(frame.MFE_R.astype(float).mean()) if len(frame) else None}


def _group(frame: pd.DataFrame, column: str, values: list[Any]) -> list[dict]:
    return [{column: value, **_summary(frame.loc[frame[column].eq(value)])} for value in values]


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: Any) -> None:
    pd.DataFrame(rows).map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def run(data_root: Path = APPROVED_DATA_ROOT,
        output: Path = Path("TradingSystemLab/results/multitimeframe_research")) -> dict:
    verify_frozen_strategies(); candidates = frozen_candidates(); output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    comparison, availability, source_manifest = [], [], []
    cache: dict[tuple[str, str], tuple[pd.DataFrame | None, list[str]]] = {}
    for key in ("T2", "T3"):
        candidate = candidates[key]
        before = stable_hash(candidate["parameters"])
        for timeframe in TIMEFRAMES:
            target = output / key / timeframe; target.mkdir(parents=True)
            for canonical, alias in INSTRUMENTS:
                cache_key = (alias, TimeframeAdapter(timeframe).source_timeframe)
                if cache_key not in cache: cache[cache_key] = load_development(Path(data_root), alias, TimeframeAdapter(timeframe))
                source, files = cache[cache_key]
                status = "AVAILABLE" if source is not None and len(source) else "DATA_UNAVAILABLE"
                availability.append({"strategy": key, "instrument": canonical, "timeframe": timeframe, "status": status})
                source_manifest.append({"instrument": canonical, "source_timeframe": cache_key[1], "files": files,
                                        "status": status})
                if status != "AVAILABLE":
                    comparison.append({"strategy": key, "instrument": canonical, "timeframe": timeframe,
                                       "status": status, **_summary(pd.DataFrame())})
                    continue
                frame = _execute(key, candidate["parameters"], alias, timeframe, source)
                metric = _summary(frame); comparison.append({"strategy": key, "instrument": canonical,
                    "timeframe": timeframe, "status": status, **metric})
                if len(frame):
                    frame = frame.copy(); frame["year"] = pd.to_datetime(frame.exit_time, utc=True).dt.year
                else: frame = frame.assign(year=pd.Series(dtype=int), direction=pd.Series(dtype=str))
                prefix = canonical
                _csv(target / f"{prefix}_trades.csv", frame)
                _csv(target / f"{prefix}_yearly.csv", _group(frame, "year", [2023, 2024]))
                _csv(target / f"{prefix}_instrument.csv", [{"instrument": canonical, **metric}])
                _csv(target / f"{prefix}_direction.csv", _group(frame, "direction", ["LONG", "SHORT"]))
        if stable_hash(candidate["parameters"]) != before:
            raise RuntimeError(f"{key}_FROZEN_PARAMETERS_MUTATED")
    comparison.sort(key=lambda r: (r["strategy"], TIMEFRAMES.index(r["timeframe"]), r["instrument"]))
    _csv(output / "comparison.csv", comparison)
    manifest = {"phase": "7.1", "status": "PHASE_7_1_MULTITIMEFRAME_RESEARCH_COMPLETE",
        "development_period": ["2023-01-01", "2024-12-31"], "true_oos_blocked": True,
        "timeframes": list(TIMEFRAMES), "future_compatible_timeframes": list(FUTURE_TIMEFRAMES),
        "strategies": ["T2", "T3"], "candidate_ids": [candidates[k]["candidate_id"] for k in ("T2", "T3")],
        "frozen_parameter_hashes": {k: stable_hash(candidates[k]["parameters"]) for k in ("T2", "T3")},
        "frozen_strategy_hashes": STRATEGY_SHA256, "cost_ticks_per_side": COST_TICKS_PER_SIDE,
        "optimization_performed": False, "ranking_performed": False, "selection_performed": False,
        "walk_forward_performed": False, "source_data_copied": False,
        "instrument_availability": availability,
        "source_discovery": [json.loads(x) for x in sorted({json.dumps(x, sort_keys=True) for x in source_manifest})]}
    _json(output / "manifest.json", manifest)
    lines = ["# Phase 7.1 Multi-Timeframe Trend Research", "",
        "Descriptive research only. No optimization, ranking, winner selection, or walk-forward was performed. C1 execution costs are included. TRUE OOS 2025+ was not read.", "",
        "| Strategy | Instrument | TF | Status | Trades | PF | Expectancy | Net R | DD |", "|---|---|---|---|---:|---:|---:|---:|---:|"]
    def fmt(value: Any) -> str: return "" if value is None else (f"{value:.6g}" if isinstance(value, float) else str(value))
    for row in comparison:
        lines.append("| " + " | ".join(fmt(row[x]) for x in ("strategy", "instrument", "timeframe", "status", "trades", "PF", "expectancy", "net_R", "max_drawdown")) + " |")
    lines += ["", "## Status", "", "PHASE_7_1_MULTITIMEFRAME_RESEARCH_COMPLETE", ""]
    (output / "multitimeframe_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": manifest["status"], "combinations": len(comparison)}
