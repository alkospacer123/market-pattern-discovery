"""Read-only, deterministic diagnostics for the completed M5 candidates.

Only the frozen development trade ledgers and candidate registries are read.
In particular, this module neither imports strategy code nor opens market data.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Iterable

import pandas as pd

from ..core.unified_metrics import finite, quantiles, stats
from ..multitimeframe.phase73 import hash_tree

VALIDATION = Path("TradingSystemLab/results/timeframe_validation/M5")
OPTIMIZATION = Path("TradingSystemLab/results/timeframe_optimization/M5")
OUTPUT = Path("TradingSystemLab/results/timeframe_diagnostics/M5_FULL")
CANDIDATES = {"T2": "T2_M5_candidate_v1", "T3": "T3_M5_candidate_v1"}
INSTRUMENTS = ("USDRUBF", "CNYRUBF")
SESSIONS = ("Session_A", "Session_B", "Session_C")
METRICS = ["trades", "PF", "expectancy_R", "net_R", "max_drawdown_R",
           "recovery_factor", "win_rate"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_hashes(*roots: Path) -> dict[str, str]:
    return {str(path): _sha(path) for root in roots for path in sorted(root.rglob("*")) if path.is_file()}


def _write_csv(path: Path, rows: Any, columns: list[str]) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.reindex(columns=columns).map(finite).to_csv(
        path, index=False, lineterminator="\n", float_format="%.12g", na_rep="DATA_UNAVAILABLE")


def _session(hour: int) -> str:
    if 0 <= hour < 10:
        return "Session_A"
    if 10 <= hour < 17:
        return "Session_B"
    return "Session_C"


def _prepare(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"trade_id", "instrument", "direction", "entry_time", "exit_time", "net_R"}
    if missing := required - set(frame.columns):
        raise ValueError(f"M5_TRADE_COLUMNS_MISSING:{','.join(sorted(missing))}")
    frame = frame.copy()
    entry = pd.to_datetime(frame.entry_time, utc=True)
    exit_ = pd.to_datetime(frame.exit_time, utc=True)
    # UTC conversion can move a local midnight. Calendar attribution deliberately
    # uses the timestamp's written offset, while the hard cutoff uses instants.
    local = frame.entry_time.map(pd.Timestamp)
    local_exit = frame.exit_time.map(pd.Timestamp)
    cutoff = pd.Timestamp("2025-01-01", tz="UTC")
    start = pd.Timestamp("2023-01-01", tz="UTC")
    if (entry >= cutoff).any() or (exit_ >= cutoff).any() or \
            local.map(lambda x: x.year >= 2025).any() or local_exit.map(lambda x: x.year >= 2025).any():
        raise ValueError("TRUE_OOS_TRADE_REJECTED")
    if (entry < start).any():
        raise ValueError("PRE_DEVELOPMENT_TRADE_REJECTED")
    if (~frame.instrument.isin(INSTRUMENTS)).any():
        raise ValueError("UNEXPECTED_INSTRUMENT")
    if (~frame.direction.isin(("LONG", "SHORT"))).any():
        raise ValueError("UNEXPECTED_DIRECTION")
    frame["entry_time"] = entry
    frame["exit_time"] = exit_
    frame["net_R"] = pd.to_numeric(frame.net_R, errors="raise")
    frame["hour"] = local.map(lambda x: x.hour)
    frame["session"] = frame.hour.map(_session)
    frame["weekday"] = local.map(lambda x: x.day_name())
    frame["month"] = local.map(lambda x: f"{x.month:02d}-{x.month_name()}")
    frame["quarter"] = local.map(lambda x: f"{x.year}-Q{x.quarter}")
    frame["year"] = local.map(lambda x: x.year)
    frame["entry_date"] = local.map(lambda x: x.date().isoformat())
    frame["holding_minutes"] = (exit_ - entry).dt.total_seconds() / 60
    if (frame.holding_minutes < 0).any():
        raise ValueError("NEGATIVE_HOLDING_TIME")
    return frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def _metrics(frame: pd.DataFrame) -> dict[str, Any]:
    result = stats(frame.net_R)
    return {"trades": result["trades"], "PF": result["PF_R"],
            "expectancy_R": result["expectancy"], "net_R": result["net_R"],
            "max_drawdown_R": result["max_DD_R"],
            "recovery_factor": result["recovery_factor"], "win_rate": result["winrate"]}


def _groups(frame: pd.DataFrame, column: str, values: Iterable[Any]) -> list[dict[str, Any]]:
    return [{column: value, **_metrics(frame.loc[frame[column].eq(value)])} for value in values]


def _distribution(frame: pd.DataFrame) -> list[dict[str, Any]]:
    ordered = frame.sort_values(["net_R", "exit_time", "instrument", "trade_id"],
                                ascending=[False, True, True, True], kind="mergesort")
    top1, top5 = ordered.head(1), ordered.head(5)
    rows = [{"section": "SUMMARY", "rank": None, "trade_id": None,
             "net_R": float(frame.net_R.sum()),
             "top_1_dependency": finite(float(top1.net_R.clip(lower=0).sum() /
                 frame.net_R.clip(lower=0).sum()) if frame.net_R.clip(lower=0).sum() else None),
             "net_R_without_top_5": _metrics(frame.drop(top5.index))["net_R"],
             "PF_without_top_5": _metrics(frame.drop(top5.index))["PF"],
             **quantiles(frame.net_R, "R")}]
    best = ordered.head(5)
    worst = ordered.tail(5).sort_values(["net_R", "exit_time", "instrument", "trade_id"], kind="mergesort")
    for label, selected in (("BEST_TRADE", best), ("WORST_TRADE", worst)):
        for rank, (_, trade) in enumerate(selected.iterrows(), 1):
            rows.append({"section": label, "rank": rank, "trade_id": trade.trade_id,
                         "instrument": trade.instrument, "direction": trade.direction,
                         "entry_time": trade.entry_time.isoformat(), "net_R": trade.net_R})
    # Top-5 dependency is intentionally a share of all positive R, not net R.
    rows[0]["top_5_dependency"] = finite(float(top5.net_R.clip(lower=0).sum() /
        frame.net_R.clip(lower=0).sum()) if frame.net_R.clip(lower=0).sum() else None)
    return rows


def _mae_mfe(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if not {"MAE_R", "MFE_R"}.issubset(frame.columns):
        return [{"scope": "ALL", "status": "DATA_UNAVAILABLE"}]
    rows = []
    for scope, part in [("ALL", frame), *((i, frame.loc[frame.instrument.eq(i)]) for i in INSTRUMENTS)]:
        mae, mfe = pd.to_numeric(part.MAE_R), pd.to_numeric(part.MFE_R)
        rows.append({"scope": scope, "status": "AVAILABLE", "average_MAE_R": mae.mean(),
                     "average_MFE_R": mfe.mean(), **quantiles(mae, "MAE_R"), **quantiles(mfe, "MFE_R")})
    return rows


def _holding(frame: pd.DataFrame) -> list[dict[str, Any]]:
    buckets = [("0-15 min", 0, 15), ("15-30 min", 15, 30),
               ("30-60 min", 30, 60), ("60+ min", 60, float("inf"))]
    rows = []
    for label, low, high in buckets:
        part = frame.loc[(frame.holding_minutes >= low) & (frame.holding_minutes < high)]
        rows.append({"category": "BUCKET", "holding_bucket": label,
                     "average_duration_minutes": finite(part.holding_minutes.mean()),
                     "median_duration_minutes": finite(part.holding_minutes.median()), **_metrics(part)})
    for label, part in (("WINNING", frame.loc[frame.net_R > 0]), ("LOSING", frame.loc[frame.net_R < 0]),
                        ("ALL", frame)):
        rows.append({"category": label, "holding_bucket": "ALL",
                     "average_duration_minutes": finite(part.holding_minutes.mean()),
                     "median_duration_minutes": finite(part.holding_minutes.median()), **_metrics(part)})
    return rows


def _drawdowns(frame: pd.DataFrame) -> list[dict[str, Any]]:
    equity = peak = 0.0
    start = None
    episodes: list[tuple[float, int, int]] = []
    trough = 0.0
    for pos, value in enumerate(frame.net_R):
        equity += value
        if equity < peak:
            start = pos if start is None else start
            trough = min(trough, equity - peak)
        elif start is not None:
            episodes.append((trough, start, pos))
            peak, start, trough = equity, None, 0.0
        else:
            peak = max(peak, equity)
    if start is not None:
        episodes.append((trough, start, len(frame) - 1))
    rows = []
    for rank, (depth, first, last) in enumerate(sorted(episodes, key=lambda x: (x[0], x[1]))[:5], 1):
        part = frame.iloc[first:last + 1]
        counts = lambda c: ";".join(f"{k}:{v}" for k, v in sorted(Counter(part[c]).items()))
        rows.append({"rank": rank, "start_date": part.entry_date.iloc[0],
                     "end_date": part.exit_time.iloc[-1].date().isoformat(), "trades": len(part),
                     "net_R": part.net_R.sum(), "max_drawdown_R": depth,
                     "instruments": counts("instrument"), "directions": counts("direction"),
                     "sessions": counts("session")})
    return rows


def _availability(frame: pd.DataFrame, strategy: str) -> list[dict[str, Any]]:
    regime = [("volatility_ATR", ("ATR", "atr")), ("trend_ADX", ("ADX", "adx")),
              ("trend_EMA_context", ("EMA_context", "ema_context"))]
    specific = ([('pullback_characteristics', ('setup_age_bars', 'pullback_time')),
                 ('impulse_distance', ('impulse_distance',)), ('trend_context', ('trend_context',))]
                if strategy == "T2" else
                [('breakout_characteristics', ('breakout_distance',)),
                 ('trend_context', ('trend_context',)), ('volatility_expansion', ('volatility_expansion',))])
    return [{"analysis": name, "status": "AVAILABLE" if any(c in frame.columns for c in columns)
             else "DATA_UNAVAILABLE", "source_fields": ";".join(c for c in columns if c in frame.columns)}
            for name, columns in regime + specific]


def _write_strategy(target: Path, strategy: str, frame: pd.DataFrame) -> dict[str, Any]:
    target.mkdir(parents=True)
    cols = lambda key: [key, *METRICS]
    time_rows = [{"time_dimension": "hour", "time_value": hour,
                  **_metrics(frame.loc[frame.hour.eq(hour)])} for hour in range(24)]
    time_rows += [{"time_dimension": "year", "time_value": year,
                   **_metrics(frame.loc[frame.year.eq(year)])} for year in (2023, 2024)]
    _write_csv(target / "time_report.csv", time_rows, ["time_dimension", "time_value", *METRICS])
    _write_csv(target / "session_report.csv", _groups(frame, "session", SESSIONS), cols("session"))
    _write_csv(target / "weekday_report.csv", _groups(frame, "weekday",
               ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")), cols("weekday"))
    _write_csv(target / "month_report.csv", _groups(frame, "month",
               [f"{n:02d}-{pd.Timestamp(2000, n, 1).month_name()}" for n in range(1, 13)]), cols("month"))
    _write_csv(target / "quarter_report.csv", _groups(frame, "quarter",
               [f"{y}-Q{q}" for y in (2023, 2024) for q in range(1, 5)]), cols("quarter"))
    _write_csv(target / "instrument_report.csv", _groups(frame, "instrument", INSTRUMENTS), cols("instrument"))
    _write_csv(target / "direction_report.csv", _groups(frame, "direction", ("LONG", "SHORT")), cols("direction"))
    pairs = [{"instrument": i, "session": s, **_metrics(frame.loc[frame.instrument.eq(i) & frame.session.eq(s)])}
             for i in INSTRUMENTS for s in SESSIONS]
    _write_csv(target / "instrument_session_report.csv", pairs, ["instrument", "session", *METRICS])
    dist_cols = ["section", "rank", "trade_id", "instrument", "direction", "entry_time", "net_R",
                 "top_1_dependency", "top_5_dependency", "net_R_without_top_5",
                 "PF_without_top_5", *quantiles([], "R").keys()]
    _write_csv(target / "trade_distribution_report.csv", _distribution(frame), dist_cols)
    mm = _mae_mfe(frame)
    _write_csv(target / "mae_mfe_report.csv", mm, sorted({k for row in mm for k in row}, key=lambda x: (x not in ("scope", "status"), x)))
    _write_csv(target / "holding_time_report.csv", _holding(frame),
               ["category", "holding_bucket", "average_duration_minutes", "median_duration_minutes", *METRICS])
    _write_csv(target / "drawdown_report.csv", _drawdowns(frame),
               ["rank", "start_date", "end_date", "trades", "net_R", "max_drawdown_R",
                "instruments", "directions", "sessions"])
    availability = _availability(frame, strategy)
    _write_csv(target / "regime_report.csv", availability, ["analysis", "status", "source_fields"])
    summary = _metrics(frame)
    unavailable = [x["analysis"] for x in availability if x["status"] == "DATA_UNAVAILABLE"]
    text = [f"# {CANDIDATES[strategy]} full M5 diagnostic", "", "Diagnostic only: no rules, parameters, or candidates were changed.", "",
            "## Development result", "", *(f"- {key}: {finite(value)}" for key, value in summary.items()), "",
            "## Data availability", "", f"Unavailable analyses: {', '.join(unavailable) or 'none'}.",
            "Available ledger fields are summarized descriptively; unavailable fields are not reconstructed."]
    (target / "diagnostic_report.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    return summary


def run(validation: Path = VALIDATION, optimization: Path = OPTIMIZATION,
        output: Path = OUTPUT) -> dict[str, Any]:
    validation, optimization, output = map(Path, (validation, optimization, output))
    before = _source_hashes(validation, optimization)
    frames = {s: _prepare(validation / s / "trades.csv") for s in CANDIDATES}
    # Validate identities from the immutable optimization registry.
    for strategy, identity in CANDIDATES.items():
        registry = json.loads((optimization / strategy / "candidate_registry.json").read_text(encoding="utf-8"))
        if registry and registry.get("candidate_id") != identity:
            raise ValueError(f"CANDIDATE_IDENTITY_MISMATCH:{strategy}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    summaries = {s: _write_strategy(output / s, s, frames[s]) for s in CANDIDATES}
    _write_csv(output / "comparison.csv", [{"candidate": CANDIDATES[s], **summaries[s]} for s in CANDIDATES],
               ["candidate", *METRICS])
    manifest = {"phase": "M5_FULL_DIAGNOSTIC", "status": "PHASE_M5_FULL_DIAGNOSTIC_COMPLETE",
                "source_artifact_hashes": before, "candidate_identities": CANDIDATES,
                "development_period": {"start": "2023-01-01", "end": "2024-12-31"},
                "true_oos_cutoff": "2025-01-01", "deterministic": True,
                "optimization_performed": False, "parameter_changes": False,
                "strategy_changes": False, "ranking": False, "candidate_selection": False,
                "true_oos_access": False,
                "session_definitions": {"Session_A": "[00:00,10:00)", "Session_B": "[10:00,17:00)",
                                        "Session_C": "[17:00,24:00)"}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = ["# M5 full diagnostic analysis", "", "Status: `PHASE_M5_FULL_DIAGNOSTIC_COMPLETE`", "",
              "This is read-only research information, not optimization, ranking, candidate selection, or a strategy change.",
              "Only completed 2023–2024 M5 trade ledgers were analyzed; TRUE OOS is rejected before analysis.", "",
              "Missing ATR, ADX, EMA-context, breakout, or volatility-expansion ledger fields are reported as `DATA_UNAVAILABLE`; no indicator was recreated."]
    (output / "m5_full_diagnostic_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if before != _source_hashes(validation, optimization):
        raise RuntimeError("SOURCE_ARTIFACTS_MODIFIED")
    return manifest
