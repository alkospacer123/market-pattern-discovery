"""Development-only M5 baseline using the frozen H1 research methodology.

The loader can discover only explicitly named 2023/2024 M5 files.  There is
deliberately no optimization, ranking, selection, walk-forward, or TRUE-OOS
entry point in this module.
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
TIMEFRAME = "M5"
PHASE = "M5_BASELINE"
STATUS = "PHASE_M5_BASELINE_COMPLETE"
OUTPUT = Path("TradingSystemLab/results/timeframe_validation/M5")
H1_ARTIFACTS = (Path("TradingSystemLab/results/T2_implementation_check"),
                Path("TradingSystemLab/results/T3_robust"),
                Path("TradingSystemLab/results/multitimeframe_research"))
TRADE_COLUMNS = ["trade_id", "strategy_id", "symbol", "direction", "entry_time",
                 "exit_time", "gross_R", "initial_risk_ticks", "MAE_R", "MFE_R",
                 "instrument", "strategy", "timeframe", "net_R"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_m5_files(data_root: Path, alias: str) -> list[Path]:
    """List only M5 development inputs; never enumerate a 2025 pattern."""
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    folder = root / "2026" / alias
    return sorted((path for year in (2023, 2024)
                   for path in folder.glob(f"{alias}_M5_{year}_Q*.csv")),
                  key=lambda path: path.name)


def validate_m5_candles(frame: pd.DataFrame) -> None:
    """Validate order, uniqueness, five-minute alignment, and the OOS barrier."""
    if not frame.index.is_monotonic_increasing:
        raise ValueError("M5_CHRONOLOGICAL_ORDER_VIOLATION")
    if frame.index.has_duplicates:
        raise ValueError("M5_DUPLICATE_CANDLES")
    index = pd.DatetimeIndex(frame.index)
    if index.tz is None:
        raise ValueError("M5_TIMEFRAME_VIOLATION")
    aligned = ((index.minute % 5 == 0) & (index.second == 0) &
               (index.microsecond == 0) & (index.nanosecond == 0))
    if not aligned.all():
        raise ValueError("M5_TIMEFRAME_VIOLATION")
    # Gaps are allowed, but an observed timestamp may never fall between the
    # five-minute grid points of its trading day.
    for _, day in frame.groupby(index.normalize(), sort=True):
        differences = day.index.to_series().diff().dropna()
        if len(differences) and not (differences % pd.Timedelta("5min") == pd.Timedelta(0)).all():
            raise ValueError("M5_TIMEFRAME_VIOLATION")
    reject_true_oos(index)


def load_m5_development(data_root: Path, alias: str) -> tuple[pd.DataFrame | None, list[Path]]:
    paths = discover_m5_files(data_root, alias)
    if not paths:
        return None, []
    loader = DataLoader(forbid_true_oos=True)
    # Validate before DataLoader's deterministic sort/de-duplication so source
    # defects cannot be hidden by normalization.
    pieces = [loader._read(path) for path in paths]
    for piece in pieces:
        validate_m5_candles(piece)
    opened = pd.concat(pieces)
    validate_m5_candles(opened)
    frame = loader.close_index(opened, "5min")
    frame = frame.loc[(frame.index >= DEVELOPMENT_START) & (frame.index < TRUE_OOS_START)]
    if frame.empty:
        return None, paths
    validate_m5_candles(frame)
    return frame, paths


def causal_four_bar_context(m5: pd.DataFrame) -> pd.DataFrame:
    """Build the unchanged T3 four-bar context, reset at each trading day."""
    rows: list[tuple[pd.Timestamp, dict[str, float]]] = []
    for _, day in m5.groupby(m5.index.normalize(), sort=True):
        for offset in range(0, len(day), 4):
            block = day.iloc[offset:offset + 4]
            if len(block) != 4 or not (block.index.to_series().diff().iloc[1:] == pd.Timedelta("5min")).all():
                continue
            row = {"Open": block.Open.iloc[0], "High": block.High.max(),
                   "Low": block.Low.min(), "Close": block.Close.iloc[-1]}
            if "Volume" in block:
                row["Volume"] = block.Volume.sum()
            # A completed context block is observable at its last M5 close.
            rows.append((block.index[-1], row))
    columns = [column for column in ("Open", "High", "Low", "Close", "Volume") if column in m5]
    result = pd.DataFrame([row for _, row in rows], index=[stamp for stamp, _ in rows], columns=columns)
    result.index = pd.DatetimeIndex(result.index, name="CloseTime")
    return result


def _execute(key: str, parameters: dict, alias: str, m5: pd.DataFrame) -> pd.DataFrame:
    params = replace(PARAMETERS[key], **parameters)
    spec = get_instrument_spec(alias)
    if key == "T2":
        frame = T2TrendPullback(params).run(m5, alias, tick_size=spec.price_precision)
    else:
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=0,
                         tick_size=spec.price_precision).run(
                             T3MTFTrend(params), alias, m5, causal_four_bar_context(m5)).trades
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
    frame["trade_id"] = [f"{key}-M5-{alias}-{number:06d}" for number in range(1, len(frame) + 1)]
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


def _reports(target: Path, trades: pd.DataFrame, status: str, key: str) -> dict[str, Any]:
    target.mkdir(parents=True, exist_ok=True)
    metric = _summary(trades)
    _csv(target / "trades.csv", trades)
    _json(target / "metrics.json", {"status": status, **metric})
    group = lambda column, value: _summary(trades.loc[trades[column].eq(value)])
    _csv(target / "yearly_report.csv", [{"year": year, **group("year", year)} for year in (2023, 2024)])
    _csv(target / "instrument_report.csv", [{"instrument": name, **group("instrument", name)}
                                               for name, _ in INSTRUMENTS])
    _csv(target / "direction_report.csv", [{"direction": direction, **group("direction", direction)}
                                              for direction in ("LONG", "SHORT")])
    conc = concentration(trades.net_R) if len(trades) else concentration(pd.Series(dtype=float))
    _csv(target / "concentration_report.csv", [conc])
    _csv(target / "mae_mfe_report.csv", [{"instrument": name,
        "average_MAE_R": group("instrument", name)["average_MAE_R"],
        "average_MFE_R": group("instrument", name)["average_MFE_R"]} for name, _ in INSTRUMENTS])
    (target / "final_report.md").write_text(
        f"# M5 Baseline — {key}_candidate_v1\n\nStatus: {status}\n\n"
        "Frozen H1-methodology candidate evaluated on M5 development data only. "
        "No optimization, ranking, selection, or walk-forward was performed.\n",
        encoding="utf-8")
    return metric


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    verify_frozen_strategies()
    candidates = frozen_candidates()
    h1_before = {str(path): hash_tree(path) for path in H1_ARTIFACTS}
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    loaded = {alias: load_m5_development(Path(data_root), alias) for _, alias in INSTRUMENTS}
    comparison, sources = [], []
    for key in ("T2", "T3"):
        candidate = candidates[key]
        parameter_hash = stable_hash(candidate["parameters"])
        pieces, statuses = [], []
        for instrument, alias in INSTRUMENTS:
            frame, paths = loaded[alias]
            statuses.append("DATA_UNAVAILABLE" if frame is None else "AVAILABLE")
            if frame is not None:
                pieces.append(_execute(key, candidate["parameters"], alias, frame))
            sources.append({"strategy": key, "instrument": instrument, "timeframe": TIMEFRAME,
                            "status": statuses[-1],
                            "files": [{"name": path.name, "sha256": _sha(path)} for path in paths]})
        trades = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=TRADE_COLUMNS)
        if len(trades):
            trades = trades.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
        trades["year"] = pd.to_datetime(trades.exit_time, utc=True).dt.year if len(trades) else pd.Series(dtype=int)
        status = "AVAILABLE" if all(item == "AVAILABLE" for item in statuses) else "DATA_UNAVAILABLE"
        metric = _reports(output / key, trades, status, key)
        comparison.append({"strategy": key, "candidate_id": candidate["candidate_id"],
                           "timeframe": TIMEFRAME, "status": status, **metric})
        if stable_hash(candidate["parameters"]) != parameter_hash:
            raise RuntimeError(f"{key}_FROZEN_PARAMETERS_MUTATED")
    _csv(output / "comparison.csv", comparison)
    h1_after = {str(path): hash_tree(path) for path in H1_ARTIFACTS}
    if h1_before != h1_after:
        raise RuntimeError("H1_ARTIFACT_MUTATION")
    manifest = {"phase": PHASE, "status": STATUS, "timeframe": TIMEFRAME,
        "development_period": ["2023-01-01", "2024-12-31"],
        "true_oos_cutoff": "2025-01-01", "instruments": [name for name, _ in INSTRUMENTS],
        "strategies": [candidates[key]["candidate_id"] for key in ("T2", "T3")],
        "frozen_strategy_hashes": STRATEGY_SHA256,
        "parameter_hashes": {key: stable_hash(candidates[key]["parameters"]) for key in ("T2", "T3")},
        "source_data_hashes": sources,
        "cost_model": {"cost_ticks_per_side": COST_TICKS_PER_SIDE,
                       "round_trip_ticks": 2 * COST_TICKS_PER_SIDE, "slippage_ticks_per_side": 0.0},
        "deterministic_execution": True, "optimization": False, "ranking": False,
        "walk_forward": False, "true_oos_blocked": True,
        "h1_artifact_hashes": h1_after}
    _json(output / "manifest.json", manifest)
    lines = ["# M5 Baseline Research", "", "Frozen `T2_candidate_v1` and `T3_candidate_v1` were evaluated with the unchanged H1 methodology on M5 development data only.", "",
        "| Strategy | Status | Trades | PF | Expectancy R | Net R | Max DD R |",
        "|---|---|---:|---:|---:|---:|---:|"]
    fmt = lambda value: "" if value is None else (f"{value:.6g}" if isinstance(value, float) else str(value))
    for row in comparison:
        lines.append("| " + " | ".join(fmt(row[column]) for column in
            ("strategy", "status", "trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")) + " |")
    lines += ["", "M5 inputs only. Four-bar T3 context resets daily and uses complete, consecutive closed candles.", "",
              "optimization=false; ranking=false; walk_forward=false; true_oos_blocked=true.", "", STATUS, ""]
    (output / "m5_baseline_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": STATUS, "strategies": len(comparison)}
