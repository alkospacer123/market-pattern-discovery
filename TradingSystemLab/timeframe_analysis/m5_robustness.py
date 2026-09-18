"""Read-only robustness analysis of the two frozen M5 candidate ledgers.

The variants in this module are pre-declared diagnostic slices, not trading
rules.  In particular, no row or result in either source ledger is changed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import pandas as pd

from .m5_entry_quality import DATA, _discover, _entry_rows, _load_bars
from .m5_overextension_session_candidate import (
    CANDIDATES, DEVELOPMENT_PERIOD, DISTANCES, OPTIMIZATION, VALIDATION,
    _canonical_hash, _metrics, _session_mask, _source_hashes,
)
from ..timeframe_diagnostics.m5_full import _prepare, _write_csv

OUTPUT = Path("TradingSystemLab/results/timeframe_analysis/M5_ROBUSTNESS")
TRUE_OOS_BOUNDARY = "2025-01-01"
STATUS = "PHASE_M5_ROBUSTNESS_COMPLETE"
FILES = ("yearly_report.csv", "instrument_report.csv", "monthly_report.csv",
         "direction_report.csv", "interaction_report.csv", "drawdown_report.csv",
         "concentration_report.csv")
CORE = ["trades", "win_rate", "PF", "expectancy_R", "net_R", "max_drawdown_R",
        "recovery_factor", "losing_streak", "average_holding_time"]
ROBUST = ["trades", "PF", "expectancy_R", "net_R", "max_drawdown_R",
          "recovery_factor", "top_1_positive_R_concentration", "top_5_positive_R_concentration"]


def _variant(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    definitions = {
        "BASELINE": pd.Series(True, index=frame.index),
        "SESSION_CANDIDATE": _session_mask(frame),
        "EMA50_NORMAL": frame.location_ema50.eq("normal"),
        "EMA50_EXTENDED": frame.location_ema50.eq("extended"),
        "SESSION_EMA50_NORMAL": _session_mask(frame) & frame.location_ema50.eq("normal"),
        "SESSION_EMA50_EXTENDED": _session_mask(frame) & frame.location_ema50.eq("extended"),
        "EMA50_NEAR": frame.location_ema50.eq("near"),
    }
    return frame.loc[definitions[name]].sort_values(
        ["exit_time", "entry_time", "instrument", "trade_id"], kind="mergesort")


def _row(variant: str, frame: pd.DataFrame) -> dict[str, Any]:
    return {"variant": variant, **_metrics(frame)}


def _yearly(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for variant in ("BASELINE", "SESSION_CANDIDATE"):
        selected = _variant(frame, variant)
        for year in (2023, 2024):
            rows.append({"year": year, **_row(variant, selected.loc[selected.entry_time.dt.year.eq(year)])})
    return rows


def _instrument(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for variant in ("BASELINE", "SESSION_CANDIDATE", "EMA50_NORMAL", "EMA50_EXTENDED"):
        selected = _variant(frame, variant)
        for instrument in ("USDRUBF", "CNYRUBF"):
            rows.append({"instrument": instrument, **_row(variant, selected.loc[selected.instrument.eq(instrument)])})
    return rows


def _direction(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for variant in ("BASELINE", "SESSION_CANDIDATE", "EMA50_NORMAL"):
        selected = _variant(frame, variant)
        for direction in ("LONG", "SHORT"):
            rows.append({"direction": direction, **_row(variant, selected.loc[selected.direction.eq(direction)])})
    return rows


def _interaction(frame: pd.DataFrame) -> list[dict[str, Any]]:
    names = ("SESSION_CANDIDATE", "EMA50_NEAR", "EMA50_NORMAL", "EMA50_EXTENDED",
             "SESSION_EMA50_NORMAL", "SESSION_EMA50_EXTENDED")
    return [_row(name, _variant(frame, name)) for name in names]


def _monthly(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    months = pd.period_range("2023-01", "2024-12", freq="M")
    for variant in ("BASELINE", "SESSION_CANDIDATE", "EMA50_NORMAL", "EMA50_EXTENDED",
                    "SESSION_EMA50_NORMAL", "SESSION_EMA50_EXTENDED"):
        selected = _variant(frame, variant)
        values = []
        for month in months:
            part = selected.loc[selected.entry_time.dt.tz_localize(None).dt.to_period("M").eq(month)]
            values.append(_metrics(part))
        positive = sum(value["net_R"] > 0 for value in values)
        negative = sum(value["net_R"] < 0 for value in values)
        nets = [value["net_R"] for value in values]
        for month, value in zip(months, values):
            rows.append({"variant": variant, "month": str(month), **{key: value[key] for key in ("trades", "PF", "net_R")},
                         "positive_months": positive, "negative_months": negative,
                         "largest_losing_month_R": min(nets), "largest_winning_month_R": max(nets)})
    return rows


def _drawdowns(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for variant in ("BASELINE", "SESSION_CANDIDATE", "SESSION_EMA50_NORMAL"):
        selected = _variant(frame, variant).reset_index(drop=True)
        equity = selected.net_R.cumsum(); peak = equity.cummax().clip(lower=0); dd = equity - peak
        active = dd.lt(0); period = (active & ~active.shift(fill_value=False)).cumsum()
        for number in sorted(period.loc[active].unique()):
            positions = period.index[(period.eq(number) & active)]
            start, trough = positions[0], dd.loc[positions].idxmin()
            recovery_positions = dd.index[(dd.index > positions[-1]) & dd.ge(0)]
            recovery = int(recovery_positions[0]) if len(recovery_positions) else None
            end = recovery if recovery is not None else positions[-1]
            # Attribute only losses through the trough; the recovering winner is
            # part of duration, but did not contribute to drawdown depth.
            part = selected.loc[start:trough]
            contributions = lambda column: "|".join(
                f"{key}:{value:.12g}" for key, value in sorted(part.groupby(column).net_R.sum().items()))
            rows.append({"variant": variant, "drawdown_period": int(number),
                         "start": selected.loc[start, "exit_time"].isoformat(),
                         "trough": selected.loc[trough, "exit_time"].isoformat(),
                         "recovery": selected.loc[recovery, "exit_time"].isoformat() if recovery is not None else "UNRECOVERED",
                         "duration_minutes": (selected.loc[end, "exit_time"] - selected.loc[start, "exit_time"]).total_seconds() / 60,
                         "depth_R": float(dd.loc[trough]), "instrument_contribution_R": contributions("instrument"),
                         "direction_contribution_R": contributions("direction"), "session_contribution_R": contributions("session")})
    return rows


def _concentration(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for variant in ("BASELINE", "SESSION_CANDIDATE", "SESSION_EMA50_NORMAL"):
        selected = _variant(frame, variant); positive = float(selected.net_R.clip(lower=0).sum())
        basic = _metrics(selected)
        ordered = selected.net_R.sort_values(ascending=False, kind="mergesort").clip(lower=0)
        rows += [{"variant": variant, "dimension": "trade", "period": "ALL",
                  "contribution_R": float(ordered.head(n).sum()), "share_of_positive_R": basic[f"top_{n}_positive_R_concentration"]}
                 for n in (1, 5)]
        rows[-2]["period"] = "TOP_1"; rows[-1]["period"] = "TOP_5"
        for dimension, periods in (("year", (2023, 2024)), ("month", pd.period_range("2023-01", "2024-12", freq="M"))):
            stamps = selected.entry_time.dt.year if dimension == "year" else selected.entry_time.dt.tz_localize(None).dt.to_period("M")
            for period in periods:
                contribution = float(selected.loc[stamps.eq(period), "net_R"].clip(lower=0).sum())
                rows.append({"variant": variant, "dimension": dimension, "period": str(period),
                             "contribution_R": contribution,
                             "share_of_positive_R": contribution / positive if positive else None})
    return rows


def _write_scope(target: Path, frame: pd.DataFrame) -> None:
    target.mkdir(parents=True)
    _write_csv(target / "yearly_report.csv", _yearly(frame), ["year", "variant", *CORE])
    _write_csv(target / "instrument_report.csv", _instrument(frame), ["instrument", "variant", *CORE])
    _write_csv(target / "monthly_report.csv", _monthly(frame), ["variant", "month", "trades", "PF", "net_R", "positive_months", "negative_months", "largest_losing_month_R", "largest_winning_month_R"])
    _write_csv(target / "direction_report.csv", _direction(frame), ["direction", "variant", *CORE])
    _write_csv(target / "interaction_report.csv", _interaction(frame), ["variant", *ROBUST])
    _write_csv(target / "drawdown_report.csv", _drawdowns(frame), ["variant", "drawdown_period", "start", "trough", "recovery", "duration_minutes", "depth_R", "instrument_contribution_R", "direction_contribution_R", "session_contribution_R"])
    _write_csv(target / "concentration_report.csv", _concentration(frame), ["variant", "dimension", "period", "contribution_R", "share_of_positive_R"])


def _report(frames: Mapping[str, pd.DataFrame]) -> str:
    base = _metrics(frames["COMBINED"]); session = _metrics(_variant(frames["COMBINED"], "SESSION_CANDIDATE"))
    normal = _metrics(_variant(frames["COMBINED"], "SESSION_EMA50_NORMAL"))
    return ("# M5 candidate robustness validation\n\n"
            f"Status: `{STATUS}`\n\n"
            "This is deterministic, evidence-only robustness analysis. It neither selects a production candidate nor changes strategy or parameters.\n\n"
            "## Combined overview\n\n"
            f"| Slice | Trades | PF | Expectancy R | Net R | Max DD R |\n|---|---:|---:|---:|---:|---:|\n"
            f"| Baseline | {base['trades']} | {base['PF']} | {base['expectancy_R']} | {base['net_R']} | {base['max_drawdown_R']} |\n"
            f"| 10:00–17:00 | {session['trades']} | {session['PF']} | {session['expectancy_R']} | {session['net_R']} | {session['max_drawdown_R']} |\n"
            f"| 10:00–17:00 + EMA50 normal | {normal['trades']} | {normal['PF']} | {normal['expectancy_R']} | {normal['net_R']} | {normal['max_drawdown_R']} |\n\n"
            "All results use only the 2023–2024 development period. Calendar 2025 TRUE OOS remained blocked.\n")


def run(validation: Path = VALIDATION, optimization: Path = OPTIMIZATION, data: Path = DATA,
        output: Path = OUTPUT, market_data: Mapping[str, Any] | None = None) -> dict[str, Any]:
    validation, optimization, data, output = map(Path, (validation, optimization, data, output))
    registries = {}
    for key, identity in CANDIDATES.items():
        registries[key] = json.loads((optimization / key / "candidate_registry.json").read_text())
        if registries[key].get("candidate_id") != identity:
            raise ValueError(f"CANDIDATE_IDENTITY_MISMATCH:{key}")
    supplied = market_data if market_data is not None else _discover(data)
    bars, market_paths = {}, []
    for instrument in ("USDRUBF", "CNYRUBF"):
        bars[instrument], paths = _load_bars(supplied[instrument]); market_paths += paths
    before = _source_hashes(validation, optimization, market_paths)
    prepared = {key: _prepare(validation / key / "trades.csv") for key in CANDIDATES}
    if any((frame.entry_time.dt.year >= 2025).any() or (frame.exit_time.dt.year >= 2025).any() for frame in prepared.values()):
        raise ValueError("TRUE_OOS_TRADE_REJECTED")
    frames = {key: _entry_rows(frame, bars) for key, frame in prepared.items()}
    frames["COMBINED"] = pd.concat([frames[key].assign(strategy=key) for key in CANDIDATES], ignore_index=True)
    frames["COMBINED"] = frames["COMBINED"].sort_values(["exit_time", "strategy", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    for scope, frame in frames.items(): _write_scope(output / scope, frame)
    definitions = {"session": "Monday-Friday 10:00 inclusive to 17:00 exclusive", "ema50_distance": list(DISTANCES)}
    candidate_hashes = {key: _canonical_hash({"candidate_id": identity, "registry": registries[key]}) for key, identity in CANDIDATES.items()}
    manifest = {"phase": "M5_ROBUSTNESS", "status": STATUS, "candidate_identities": CANDIDATES,
                "candidate_hashes": candidate_hashes, "source_hashes": before,
                "development_period": DEVELOPMENT_PERIOD, "true_oos_boundary": TRUE_OOS_BOUNDARY,
                "deterministic_execution": True,
                "deterministic_execution_hash": _canonical_hash({"sources": before, "candidates": candidate_hashes, "definitions": definitions}),
                "diagnostic_only": True, "optimization": False, "strategy_change": False,
                "parameter_change": False, "true_oos_access": False, "candidate_definitions": definitions}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (output / "robustness_report.md").write_text(_report(frames))
    if before != _source_hashes(validation, optimization, market_paths): raise RuntimeError("SOURCE_ARTIFACTS_MODIFIED")
    return manifest
