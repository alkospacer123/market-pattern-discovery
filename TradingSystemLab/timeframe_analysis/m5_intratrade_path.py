"""Causal intratrade-path diagnostics for the frozen M5 candidates.

Bars are open-labelled.  A bar is deliberately made observable at ``open+5m``;
therefore a checkpoint never uses the OHLC of a candle which has not closed.
The module is descriptive only and does not replay or alter any trading rule.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping, Sequence

import pandas as pd

from ..core.data_loader import DataLoader
from ..timeframe_diagnostics.m5_full import _metrics, _prepare, _write_csv

VALIDATION = Path("TradingSystemLab/results/timeframe_validation/M5")
SESSION = Path("TradingSystemLab/results/timeframe_analysis/M5_SESSION_CANDIDATE")
DATA = Path("/workspace/market-pattern-data")
OUTPUT = Path("TradingSystemLab/results/timeframe_analysis/M5_INTRATRADE_PATH")
CANDIDATES = {"T2": "T2_M5_candidate_v1", "T3": "T3_M5_candidate_v1"}
SESSION_CANDIDATES = {"T2": "T2_M5_session_candidate_v1", "T3": "T3_M5_session_candidate_v1"}
DEVELOPMENT = {"start": "2023-01-01", "end": "2024-12-31"}
CHECKPOINTS = (5, 15, 30, 60, 120)
DURATION_BUCKETS = (("0-15", 0, 15), ("15-30", 15, 30), ("30-60", 30, 60),
                    ("60-120", 60, 120), ("120+", 120, float("inf")))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hashes(paths: Sequence[Path]) -> dict[str, str]:
    return {str(p): _sha(p) for p in sorted(paths, key=str)}


def _load_bars(value: Any) -> tuple[pd.DataFrame, list[Path]]:
    """Return close-labelled M5 bars and the source paths which were read."""
    if isinstance(value, pd.DataFrame):
        bars = value.copy()
        if not isinstance(bars.index, pd.DatetimeIndex):
            raise ValueError("MARKET_DATA_REQUIRES_DATETIME_INDEX")
        if bars.index.tz is None:
            raise ValueError("MARKET_DATA_REQUIRES_TIMEZONE")
        bars.columns = [str(c).title() for c in bars.columns]
        paths: list[Path] = []
    else:
        paths = [Path(p) for p in (value if isinstance(value, (list, tuple)) else [value])]
        bars = DataLoader(forbid_true_oos=True).load_csv(paths)
    if (bars.index.year >= 2025).any():
        raise ValueError("TRUE_OOS_MARKET_DATA_REJECTED")
    if not {"Open", "High", "Low", "Close"}.issubset(bars):
        raise ValueError("M5_OHLC_COLUMNS_MISSING")
    # Inputs are open-labelled. Every value below is indexed by availability.
    bars.index = bars.index + pd.Timedelta(minutes=5)
    bars.index.name = "CloseTime"
    return bars.sort_index(kind="mergesort"), paths


def _discover(data: Path) -> dict[str, list[Path]]:
    aliases = {"USDRUBF": "Si", "CNYRUBF": "CNY"}
    found = {instrument: sorted(path for year in (2023, 2024)
                                for path in (data / "2026" / alias).glob(f"{alias}_M5_{year}_Q*.csv"))
             for instrument, alias in aliases.items()}
    if any(not paths for paths in found.values()):
        raise FileNotFoundError("M5_MARKET_DATA_REQUIRED: pass --usd-data and --cny-data")
    return found


def _session_name(ts: pd.Timestamp) -> str:
    return "Session_A" if ts.hour < 10 else ("Session_B" if ts.hour < 17 else "Session_C")


def _paths(trades: pd.DataFrame, bars: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade in trades.itertuples(index=False):
        entry, exit_ = trade.entry_time, trade.exit_time
        risk = float(getattr(trade, "initial_risk_points", abs(trade.entry_price - trade.initial_stop)))
        if not risk > 0:
            raise ValueError(f"INVALID_INITIAL_RISK:{trade.trade_id}")
        instrument_bars = bars[trade.instrument]
        direction = 1.0 if trade.direction == "LONG" else -1.0
        for minute in CHECKPOINTS:
            checkpoint = entry + pd.Timedelta(minutes=minute)
            # Strictly after entry; equality at checkpoint is allowed because the
            # candle has then closed.  Never inspect bars following trade exit.
            end = min(checkpoint, exit_)
            seen = instrument_bars.loc[(instrument_bars.index > entry) & (instrument_bars.index <= end)]
            if seen.empty:
                close = float(trade.entry_price)
                adverse = favorable = 0.0
            else:
                close = float(seen.Close.iloc[-1])
                if direction > 0:
                    adverse = max(0.0, float(trade.entry_price) - float(seen.Low.min()))
                    favorable = max(0.0, float(seen.High.max()) - float(trade.entry_price))
                else:
                    adverse = max(0.0, float(seen.High.max()) - float(trade.entry_price))
                    favorable = max(0.0, float(trade.entry_price) - float(seen.Low.min()))
            closed = exit_ <= checkpoint
            unrealized = float(trade.net_R) if closed else direction * (close - float(trade.entry_price)) / risk
            rows.append({"trade_id": trade.trade_id, "instrument": trade.instrument,
                         "direction": trade.direction, "session": trade.session,
                         "session_candidate": 10 <= trade.hour < 17,
                         "final_outcome": "WINNER" if trade.net_R > 0 else "LOSER",
                         "final_R": trade.net_R, "holding_minutes": trade.holding_minutes,
                         "checkpoint_minutes": minute, "checkpoint_time": checkpoint.isoformat(),
                         "last_observed_close_time": seen.index[-1].isoformat() if len(seen) else None,
                         "price_movement": direction * (close - float(trade.entry_price)),
                         "unrealized_R": unrealized, "MAE_R": adverse / risk,
                         "MFE_R": favorable / risk, "profitable": unrealized > 0,
                         "stopped": closed and "STOP" in str(getattr(trade, "exit_reason", "")).upper(),
                         "still_open": not closed})
    return pd.DataFrame(rows)


def _dimensions(path: pd.DataFrame):
    yield "ALL", "ALL", path
    for column, values in (("instrument", ("USDRUBF", "CNYRUBF")),
                           ("direction", ("LONG", "SHORT")),
                           ("session", ("Session_A", "Session_B", "Session_C"))):
        for value in values:
            yield column, value, path.loc[path[column].eq(value)]
    yield "candidate", "10:00-17:00", path.loc[path.session_candidate]


def _mean(series: pd.Series) -> Any:
    return series.mean() if len(series) else None


def _checkpoint_rows(path: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for dimension, value, part in _dimensions(path):
        for minute in CHECKPOINTS:
            at = part.loc[part.checkpoint_minutes.eq(minute)]
            rows.append({"dimension": dimension, "value": value, "checkpoint_minutes": minute,
                         "trades": len(at), "average_unrealized_R": _mean(at.unrealized_R),
                         "median_unrealized_R": at.unrealized_R.median(),
                         "average_MAE_R": _mean(at.MAE_R), "average_MFE_R": _mean(at.MFE_R),
                         "average_price_movement": _mean(at.price_movement),
                         "percent_profitable": _mean(at.profitable) * 100 if len(at) else None,
                         "percent_stopped": _mean(at.stopped) * 100 if len(at) else None,
                         "percent_still_open": _mean(at.still_open) * 100 if len(at) else None})
    return rows


def _winner_loser(path: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for dimension, value, part in _dimensions(path):
        for outcome in ("WINNER", "LOSER"):
            selected = part.loc[part.final_outcome.eq(outcome)]
            for minute in CHECKPOINTS:
                at = selected.loc[selected.checkpoint_minutes.eq(minute)]
                rows.append({"dimension": dimension, "value": value, "outcome": outcome,
                             "checkpoint_minutes": minute, "trades": len(at),
                             "average_unrealized_R": _mean(at.unrealized_R),
                             "median_unrealized_R": at.unrealized_R.median(),
                             "average_MAE_R": _mean(at.MAE_R), "average_MFE_R": _mean(at.MFE_R)})
    return rows


def _duration_rows(trades: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for dimension, value, _ in _dimensions(pd.DataFrame({**{c: trades[c] for c in trades},
                                                           "session_candidate": trades.hour.between(10, 16)})):
        if dimension == "candidate":
            part = trades.loc[trades.hour.between(10, 16)]
        elif dimension == "ALL": part = trades
        else: part = trades.loc[trades[dimension].eq(value)]
        for label, low, high in DURATION_BUCKETS:
            bucket = part.loc[(part.holding_minutes >= low) & (part.holding_minutes < high)]
            rows.append({"dimension": dimension, "value": value, "duration_bucket": label, **_metrics(bucket)})
    return rows


def _early_rows(path: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for dimension, value, part in _dimensions(path):
        for minute in (15, 30):
            selected = part.loc[part.checkpoint_minutes.eq(minute) & (part.MAE_R > .5)]
            wins, losses = (selected.final_outcome == "WINNER").sum(), (selected.final_outcome == "LOSER").sum()
            rows.append({"dimension": dimension, "value": value, "checkpoint_minutes": minute,
                         "criterion": "MAE_R > 0.5", "trades": len(selected), "winners": wins,
                         "losers": losses, "winner_loser_ratio": wins / losses if losses else None,
                         "average_final_R": _mean(selected.final_R)})
    return rows


def _write_scope(target: Path, trades: pd.DataFrame, path: pd.DataFrame) -> None:
    target.mkdir(parents=True)
    _write_csv(target / "checkpoint_metrics.csv", _checkpoint_rows(path),
               ["dimension", "value", "checkpoint_minutes", "trades", "average_unrealized_R",
                "median_unrealized_R", "average_MAE_R", "average_MFE_R", "average_price_movement",
                "percent_profitable", "percent_stopped", "percent_still_open"])
    _write_csv(target / "duration_bucket_report.csv", _duration_rows(trades),
               ["dimension", "value", "duration_bucket", "trades", "PF", "expectancy_R", "net_R", "win_rate"])
    _write_csv(target / "early_failure_report.csv", _early_rows(path),
               ["dimension", "value", "checkpoint_minutes", "criterion", "trades", "winners", "losers",
                "winner_loser_ratio", "average_final_R"])
    _write_csv(target / "winner_loser_path.csv", _winner_loser(path),
               ["dimension", "value", "outcome", "checkpoint_minutes", "trades", "average_unrealized_R",
                "median_unrealized_R", "average_MAE_R", "average_MFE_R"])


def run(validation: Path = VALIDATION, data: Path = DATA, output: Path = OUTPUT,
        market_data: Mapping[str, Any] | None = None) -> dict[str, Any]:
    validation, output = Path(validation), Path(output)
    ledgers = {s: validation / s / "trades.csv" for s in CANDIDATES}
    source_paths = list(ledgers.values())
    sources = market_data or _discover(Path(data))
    bars = {}
    for instrument in ("USDRUBF", "CNYRUBF"):
        bars[instrument], read = _load_bars(sources[instrument])
        source_paths.extend(read)
    before = _hashes(source_paths)
    trades = {s: _prepare(p) for s, p in ledgers.items()}
    paths = {s: _paths(frame, bars) for s, frame in trades.items()}
    combined_trades = pd.concat([f.assign(candidate=s) for s, f in trades.items()], ignore_index=True)
    combined_path = pd.concat([f.assign(candidate=s) for s, f in paths.items()], ignore_index=True)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    for strategy in CANDIDATES: _write_scope(output / strategy, trades[strategy], paths[strategy])
    _write_scope(output / "COMBINED", combined_trades, combined_path)
    comparison = []
    for scope, path in [*paths.items(), ("COMBINED", combined_path)]:
        for row in _checkpoint_rows(path):
            if row["dimension"] == "ALL": comparison.append({"scope": scope, **row})
    _write_csv(output / "comparison.csv", comparison,
               ["scope", "dimension", "value", "checkpoint_minutes", "trades", "average_unrealized_R",
                "median_unrealized_R", "average_MAE_R", "average_MFE_R", "average_price_movement",
                "percent_profitable", "percent_stopped", "percent_still_open"])
    manifest = {"phase": "M5_INTRATRADE_PATH", "status": "PHASE_M5_INTRATRADE_PATH_COMPLETE",
                "diagnostic_only": True, "optimization": False, "parameter_changes": False,
                "strategy_changes": False, "candidate_selection": False, "true_oos_access": False,
                "true_oos_cutoff": "2025-01-01", "deterministic": True,
                "candidate_identities": CANDIDATES, "session_candidate_identities": SESSION_CANDIDATES,
                "development_period": DEVELOPMENT, "source_hashes": before,
                "bar_availability": "open_time + 5 minutes", "checkpoints_minutes": list(CHECKPOINTS)}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (output / "intratrade_report.md").write_text(_report(paths), encoding="utf-8")
    if before != _hashes(source_paths): raise RuntimeError("SOURCE_ARTIFACTS_MODIFIED")
    return manifest


def _report(paths: Mapping[str, pd.DataFrame]) -> str:
    lines = ["# M5 intratrade path diagnostic", "", "Status: `PHASE_M5_INTRATRADE_PATH_COMPLETE`", "",
             "Diagnostic only. No strategy, parameter, entry, exit, stop, trailing rule, or candidate selection was changed.", "",
             "## Entry quality", ""]
    for name, path in [*paths.items(), ("COMBINED", pd.concat(paths.values(), ignore_index=True))]:
        p15 = path.loc[path.checkpoint_minutes.eq(15)]
        p30 = path.loc[path.checkpoint_minutes.eq(30)]
        winners, losers = p15[p15.final_outcome.eq("WINNER")], p15[p15.final_outcome.eq("LOSER")]
        winners30 = p30[p30.final_outcome.eq("WINNER")]
        pct = lambda condition, frame: 100 * condition.sum() / len(frame) if len(frame) else float("nan")
        recovered = winners.merge(path.loc[path.checkpoint_minutes.eq(30), ["trade_id", "unrealized_R"]], on="trade_id", suffixes=("_15", "_30"))
        degrading = losers.merge(p30[["trade_id", "unrealized_R"]], on="trade_id", suffixes=("_15", "_30"))
        lines += [f"### {name}",
                  f"- Winners positive after 15m: {pct(winners.unrealized_R > 0, winners):.2f}%.",
                  f"- Winners positive after 30m: {pct(winners30.unrealized_R > 0, winners30):.2f}%.",
                  f"- Losers immediately negative at 15m: {pct(losers.unrealized_R < 0, losers):.2f}%.",
                  f"- Losers non-negative at 15m but negative at 30m (slow degradation): {pct((degrading.unrealized_R_15 >= 0) & (degrading.unrealized_R_30 < 0), degrading):.2f}%.",
                  f"- Winners negative at 15m but recovered by 30m: {pct((recovered.unrealized_R_15 < 0) & (recovered.unrealized_R_30 > 0), recovered):.2f}%.", ""]
    lines += ["All checkpoint OHLC is restricted to candles whose M5 close timestamp is after entry and no later than the checkpoint or actual exit. Session-candidate rows are the frozen 10:00–17:00 entry-time subset, not a newly selected candidate.", ""]
    return "\n".join(lines)
