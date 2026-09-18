"""Development-only M15 baseline using the frozen H1 methodology.

Only explicitly named 2023/2024 M15 inputs can be discovered.  This module
intentionally exposes no optimization, ranking, selection, walk-forward, or
TRUE-OOS API.
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
TIMEFRAME = "M15"
PHASE = "M15_BASELINE"
STATUS = "PHASE_M15_BASELINE_COMPLETE"
OUTPUT = Path("TradingSystemLab/results/timeframe_validation/M15")
PROTECTED_ARTIFACTS = (
    Path("TradingSystemLab/results/T2_implementation_check"),
    Path("TradingSystemLab/results/T3_robust"),
    Path("TradingSystemLab/results/multitimeframe_research"),
    Path("TradingSystemLab/results/timeframe_validation/M1"),
    Path("TradingSystemLab/results/timeframe_validation/M5"),
    Path("TradingSystemLab/results/timeframe_analysis"),
    Path("TradingSystemLab/results/timeframe_diagnostics"),
    Path("TradingSystemLab/results/timeframe_optimization/M5"),
    Path("TradingSystemLab/results/walk_forward/M5"),
    Path("TradingSystemLab/results/true_oos_validation/M5"),
    Path("TradingSystemLab/results/true_oos_validation/M5_EXPERIMENTAL_EMA50_NORMAL"),
)
TRADE_COLUMNS = ["trade_id", "strategy_id", "symbol", "direction", "entry_time",
                 "exit_time", "gross_R", "initial_risk_ticks", "MAE_R", "MFE_R",
                 "instrument", "strategy", "timeframe", "net_R"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_m15_files(data_root: Path, alias: str) -> list[Path]:
    """Discover only approved M15 development files without a 2025 glob."""
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    folder = root / "2026" / alias
    return sorted((path for year in (2023, 2024)
                   for path in folder.glob(f"{alias}_M15_{year}_Q*.csv")),
                  key=lambda path: path.name)


def validate_m15_candles(frame: pd.DataFrame) -> None:
    """Fail closed on source ordering, uniqueness, grid, timezone, or OOS defects."""
    if not frame.index.is_monotonic_increasing:
        raise ValueError("M15_CHRONOLOGICAL_ORDER_VIOLATION")
    if frame.index.has_duplicates:
        raise ValueError("M15_DUPLICATE_CANDLES")
    index = pd.DatetimeIndex(frame.index)
    if index.tz is None:
        raise ValueError("M15_TIMEFRAME_VIOLATION")
    aligned = ((index.minute % 15 == 0) & (index.second == 0) &
               (index.microsecond == 0) & (index.nanosecond == 0))
    if not aligned.all():
        raise ValueError("M15_TIMEFRAME_VIOLATION")
    for _, day in frame.groupby(index.normalize(), sort=True):
        differences = day.index.to_series().diff().dropna()
        if len(differences) and not (differences % pd.Timedelta("15min") == pd.Timedelta(0)).all():
            raise ValueError("M15_TIMEFRAME_VIOLATION")
    reject_true_oos(index)


def load_m15_development(data_root: Path, alias: str) -> tuple[pd.DataFrame | None, list[Path]]:
    paths = discover_m15_files(data_root, alias)
    if not paths:
        return None, []
    loader = DataLoader(forbid_true_oos=True)
    # Validate raw pieces and their file-order concatenation before the loader
    # can sort or deduplicate anything.
    pieces = [loader._read(path) for path in paths]
    for piece in pieces:
        validate_m15_candles(piece)
    opened = pd.concat(pieces)
    validate_m15_candles(opened)
    frame = loader.close_index(opened, "15min")
    frame = frame.loc[(frame.index >= DEVELOPMENT_START) & (frame.index < TRUE_OOS_START)]
    if frame.empty:
        return None, paths
    validate_m15_candles(frame)
    return frame, paths


def causal_h1_context(m15: pd.DataFrame) -> pd.DataFrame:
    """Aggregate exactly four consecutive closed M15 bars, resetting daily."""
    rows: list[tuple[pd.Timestamp, dict[str, float]]] = []
    for _, day in m15.groupby(m15.index.normalize(), sort=True):
        for offset in range(0, len(day), 4):
            block = day.iloc[offset:offset + 4]
            if len(block) != 4 or not (block.index.to_series().diff().iloc[1:] == pd.Timedelta("15min")).all():
                continue
            row = {"Open": block.Open.iloc[0], "High": block.High.max(),
                   "Low": block.Low.min(), "Close": block.Close.iloc[-1]}
            if "Volume" in block:
                row["Volume"] = block.Volume.sum()
            rows.append((block.index[-1], row))
    columns = [column for column in ("Open", "High", "Low", "Close", "Volume") if column in m15]
    result = pd.DataFrame([row for _, row in rows], index=[stamp for stamp, _ in rows], columns=columns)
    result.index = pd.DatetimeIndex(result.index, name="CloseTime")
    return result


def _execute(key: str, parameters: dict, alias: str, m15: pd.DataFrame) -> pd.DataFrame:
    params = replace(PARAMETERS[key], **parameters)
    spec = get_instrument_spec(alias)
    if key == "T2":
        frame = T2TrendPullback(params).run(m15, alias, tick_size=spec.price_precision)
    else:
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=0,
                         tick_size=spec.price_precision).run(
                             T3MTFTrend(params), alias, m15, causal_h1_context(m15)).trades
        frame = _normalize_backtester(raw, key)
    if frame.empty:
        return pd.DataFrame(columns=TRADE_COLUMNS)
    frame = frame.copy()
    reject_true_oos(frame.entry_time)
    reject_true_oos(frame.exit_time)
    frame["instrument"] = "USDRUBF" if alias == "Si" else "CNYRUBF"
    frame["strategy"], frame["timeframe"] = key, TIMEFRAME
    frame["net_R"] = (frame.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE /
                      frame.initial_risk_ticks.astype(float))
    frame["trade_id"] = [f"{key}-M15-{alias}-{number:06d}" for number in range(1, len(frame) + 1)]
    return frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def _summary(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float)
    metric = stats(values)
    holding = ((pd.to_datetime(frame.exit_time, utc=True) - pd.to_datetime(frame.entry_time, utc=True))
               .dt.total_seconds() / 60) if len(frame) else pd.Series(dtype=float)
    return {"trades": metric["trades"], "PF": metric["PF_R"],
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


def _reports(target: Path, trades: pd.DataFrame, availability: str, key: str) -> dict[str, Any]:
    target.mkdir(parents=True, exist_ok=True)
    metric = _summary(trades)
    _csv(target / "trades.csv", trades)
    _json(target / "metrics.json", {"status": availability, **metric})
    group = lambda column, value: _summary(trades.loc[trades[column].eq(value)])
    _csv(target / "yearly_report.csv", [{"year": year, **group("year", year)} for year in (2023, 2024)])
    _csv(target / "instrument_report.csv", [{"instrument": name, **group("instrument", name)} for name, _ in INSTRUMENTS])
    _csv(target / "direction_report.csv", [{"direction": direction, **group("direction", direction)} for direction in ("LONG", "SHORT")])
    _csv(target / "concentration_report.csv", [concentration(trades.net_R) if len(trades) else concentration(pd.Series(dtype=float))])
    _csv(target / "mae_mfe_report.csv", [{"instrument": name,
        "average_MAE_R": group("instrument", name)["average_MAE_R"],
        "average_MFE_R": group("instrument", name)["average_MFE_R"]} for name, _ in INSTRUMENTS])
    (target / "final_report.md").write_text(
        f"# M15 Baseline — {key}_candidate_v1\n\nStatus: {availability}\n\n"
        "Frozen H1-methodology candidate evaluated on M15 development data only. "
        "No optimization, ranking, selection, parameter changes, or walk-forward was performed.\n",
        encoding="utf-8")
    return metric


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    verify_frozen_strategies()
    candidates = frozen_candidates()
    protected_before = {str(path): hash_tree(path) for path in PROTECTED_ARTIFACTS}
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    loaded = {alias: load_m15_development(Path(data_root), alias) for _, alias in INSTRUMENTS}
    source_coverage = []
    for instrument, alias in INSTRUMENTS:
        frame, paths = loaded[alias]
        source_coverage.append({"instrument": instrument, "alias": alias,
            "candles": 0 if frame is None else len(frame),
            "first_close": None if frame is None else frame.index.min().isoformat(),
            "last_close": None if frame is None else frame.index.max().isoformat(),
            "files": [path.name for path in paths]})
    comparison, sources = [], []
    for key in ("T2", "T3"):
        candidate = candidates[key]
        parameter_hash = stable_hash(candidate["parameters"])
        pieces, statuses = [], []
        for instrument, alias in INSTRUMENTS:
            frame, paths = loaded[alias]
            availability = "DATA_UNAVAILABLE" if frame is None else "AVAILABLE"
            statuses.append(availability)
            if frame is not None:
                pieces.append(_execute(key, candidate["parameters"], alias, frame))
            sources.append({"strategy": key, "instrument": instrument, "alias": alias,
                            "timeframe": TIMEFRAME, "status": availability,
                            "files": [{"name": path.name, "sha256": _sha(path)} for path in paths]})
        trades = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=TRADE_COLUMNS)
        if len(trades):
            trades = trades.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
        trades["year"] = pd.to_datetime(trades.exit_time, utc=True).dt.year if len(trades) else pd.Series(dtype=int)
        availability = "AVAILABLE" if all(item == "AVAILABLE" for item in statuses) else "DATA_UNAVAILABLE"
        metric = _reports(output / key, trades, availability, key)
        comparison.append({"strategy": key, "candidate_id": candidate["candidate_id"],
                           "timeframe": TIMEFRAME, "status": availability, **metric})
        if stable_hash(candidate["parameters"]) != parameter_hash:
            raise RuntimeError(f"{key}_FROZEN_PARAMETERS_MUTATED")
    _csv(output / "comparison.csv", comparison)
    protected_after = {str(path): hash_tree(path) for path in PROTECTED_ARTIFACTS}
    if protected_before != protected_after:
        raise RuntimeError("PROTECTED_RESEARCH_ARTIFACT_MUTATION")
    manifest = {"phase": PHASE, "status": STATUS, "timeframe": TIMEFRAME,
        "development_period": ["2023-01-01", "2024-12-31"], "true_oos_cutoff": "2025-01-01",
        "instruments": [{"instrument": name, "alias": alias} for name, alias in INSTRUMENTS],
        "strategies": [candidates[key]["candidate_id"] for key in ("T2", "T3")],
        "frozen_strategy_hashes": STRATEGY_SHA256,
        "parameter_hashes": {key: stable_hash(candidates[key]["parameters"]) for key in ("T2", "T3")},
        "source_data_hashes": sources, "source_coverage": source_coverage,
        "cost_model": {"name": "H1_C1", "cost_ticks_per_side": COST_TICKS_PER_SIDE,
                       "round_trip_ticks": 2 * COST_TICKS_PER_SIDE, "slippage_ticks_per_side": 0.0},
        "deterministic_execution": True, "optimization": False, "ranking": False,
        "selection": False, "walk_forward": False, "true_oos_blocked": True,
        "parameter_change": False, "strategy_change": False,
        "protected_artifact_hashes": protected_after}
    _json(output / "manifest.json", manifest)
    lines = ["# M15 Baseline Research", "",
        "Frozen `T2_candidate_v1` and `T3_candidate_v1` were evaluated on M15 using the unchanged H1 methodology and full 2023–2024 development period.", "",
        "TRUE OOS is blocked. No optimization, ranking, selection, parameter changes, or strategy changes were performed.", "",
        "| Strategy | Trades | PF | Expectancy R | Net R | Max DD R |",
        "|---|---:|---:|---:|---:|---:|"]
    fmt = lambda value: "" if value is None else (f"{value:.6g}" if isinstance(value, float) else str(value))
    for row in comparison:
        lines.append("| " + " | ".join(fmt(row[column]) for column in
            ("strategy", "trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")) + " |")
    lines += ["", "T3 H1 context uses exactly four consecutive completed M15 candles, resets daily, and is timestamped at the fourth close.", "",
              "optimization=false; ranking=false; selection=false; walk_forward=false; true_oos_blocked=true; parameter_change=false; strategy_change=false.", "", STATUS, ""]
    (output / "m15_baseline_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": STATUS, "strategies": len(comparison)}
