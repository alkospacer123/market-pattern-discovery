"""Phase 7.3: causal higher-timeframe context with lower-timeframe execution.

This is a fixed-candidate research runner, not a selection facility.  In
particular it has no optimizer, parameter input, ranking, or TRUE-OOS path.
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
from ..core.mtf import align_closed_context
from ..core.portfolio import FixedRiskPortfolio
from ..core.unified_metrics import concentration, finite, stats
from ..optimization.experiment import stable_hash
from ..optimization.phase32 import PARAMETERS, _normalize_backtester
from ..strategies.trend.T2_Trend_Pullback import T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend
from .phase71 import (APPROVED_DATA_ROOT, COST_TICKS_PER_SIDE, DEVELOPMENT_START,
                      STRATEGY_FILES, STRATEGY_SHA256, TRUE_OOS_START,
                      frozen_candidates, reject_true_oos, verify_frozen_strategies)

PAIRS = (("H4", "H1"), ("H1", "M30"), ("H1", "M15"))
FUTURE_PAIRS = (("D1", "H1"), ("H4", "M30"), ("M30", "M5"), ("M15", "M1"))
INSTRUMENTS = (("USDRUBF", "Si"), ("CNYRUBF", "CNY"))
DURATIONS = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min",
             "H1": "1h", "H4": "4h", "D1": "1D"}
PROTECTED = (Path("TradingSystemLab/results/true_oos_validation"),
             Path("TradingSystemLab/results/portfolio_construction"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_tree(path: Path) -> dict[str, str]:
    """Return a deterministic content inventory without modifying artifacts."""
    return {str(p.relative_to(path)): _sha(p) for p in sorted(path.rglob("*")) if p.is_file()}


def discover_development_files(data_root: Path, alias: str, timeframe: str) -> list[Path]:
    root = Path(data_root).resolve()
    if root != APPROVED_DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    folder = root / "2026" / alias
    return sorted((p for year in (2023, 2024)
                   for p in folder.glob(f"{alias}_{timeframe}_{year}_Q*.csv")), key=lambda p: p.name)


def load_development(data_root: Path, alias: str, timeframe: str) -> tuple[pd.DataFrame | None, list[Path]]:
    paths = discover_development_files(data_root, alias, timeframe)
    if not paths:
        return None, []
    loader = DataLoader(forbid_true_oos=True)
    frame = loader.close_index(loader.load_csv(paths), DURATIONS[timeframe])
    frame = frame.loc[(frame.index >= DEVELOPMENT_START) & (frame.index < TRUE_OOS_START)]
    reject_true_oos(frame.index)
    return (frame if len(frame) else None), paths


def causal_aggregate(frame: pd.DataFrame, lower: str, higher: str) -> pd.DataFrame:
    """Aggregate only complete, consecutive same-day blocks, labelled at close."""
    low, high = pd.Timedelta(DURATIONS[lower]), pd.Timedelta(DURATIONS[higher])
    if high % low or high <= low:
        raise ValueError("timeframes must have an integral higher/lower ratio")
    size = int(high / low)
    rows: list[tuple[pd.Timestamp, dict[str, float]]] = []
    for _, day in frame.groupby(frame.index.normalize(), sort=True):
        for offset in range(0, len(day), size):
            block = day.iloc[offset:offset + size]
            if len(block) != size or not (block.index.to_series().diff().iloc[1:] == low).all():
                continue
            row = {"Open": block.Open.iloc[0], "High": block.High.max(),
                   "Low": block.Low.min(), "Close": block.Close.iloc[-1]}
            if "Volume" in block:
                row["Volume"] = block.Volume.sum()
            rows.append((block.index[-1], row))
    columns = [c for c in ("Open", "High", "Low", "Close", "Volume") if c in frame.columns]
    out = pd.DataFrame([r for _, r in rows], index=[t for t, _ in rows], columns=columns)
    out.index = pd.DatetimeIndex(out.index, name="CloseTime")
    return out


class _T2HigherContext(T2TrendPullback):
    """Frozen T2 execution with its existing regime function evaluated on HTF."""
    def __init__(self, parameters: Any, context: pd.DataFrame, duration: str) -> None:
        super().__init__(parameters)
        indicators = super().calculate_indicators(context)
        self._regimes = {t: super().regime(row) for t, row in indicators.iterrows()}
        self._duration = duration

    def calculate_indicators(self, low: pd.DataFrame) -> pd.DataFrame:
        result = super().calculate_indicators(low)
        context = pd.DataFrame({"regime": pd.Series(self._regimes)})
        aligned = align_closed_context(result, context, self._duration)
        result["__higher_regime"] = aligned["regime"]
        result["context_time"] = aligned["context_time"]
        return result

    def regime(self, bar: pd.Series) -> str | None:
        return bar.get("__higher_regime") if pd.notna(bar.get("__higher_regime")) else None


def _execute(strategy: str, parameters: dict, alias: str, lower_tf: str,
             low: pd.DataFrame, high: pd.DataFrame) -> pd.DataFrame:
    params = replace(PARAMETERS[strategy], **parameters)
    spec = get_instrument_spec(alias)
    if strategy == "T2":
        raw = _T2HigherContext(params, high, DURATIONS[lower_tf]).run(low, alias, tick_size=spec.price_precision)
    else:
        # Backtester aligns at execution close. Delaying the close-labelled HTF
        # index by one execution duration makes it available on the first candle
        # whose open is at/after that HTF close, never on a simultaneous close.
        available_high = high.copy()
        available_high.index = available_high.index + pd.Timedelta(DURATIONS[lower_tf])
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=0,
                         tick_size=spec.price_precision).run(T3MTFTrend(params), alias, low, available_high).trades
        raw = _normalize_backtester(raw, strategy)
    if raw.empty:
        return raw.assign(instrument=pd.Series(dtype=str), strategy=pd.Series(dtype=str),
                          timeframe_pair=pd.Series(dtype=str), net_R=pd.Series(dtype=float))
    raw = raw.copy()
    reject_true_oos(raw.entry_time); reject_true_oos(raw.exit_time)
    raw["instrument"] = "USDRUBF" if alias == "Si" else "CNYRUBF"
    raw["strategy"] = strategy
    raw["timeframe_pair"] = ""  # populated by caller
    raw["net_R"] = raw.gross_R.astype(float) - 2 * COST_TICKS_PER_SIDE / raw.initial_risk_ticks.astype(float)
    raw["trade_id"] = [f"{strategy}-{alias}-{i:06d}" for i in range(1, len(raw) + 1)]
    return raw.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def _summary(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float)
    s = stats(values)
    holding = ((pd.to_datetime(frame.exit_time, utc=True) - pd.to_datetime(frame.entry_time, utc=True))
               .dt.total_seconds() / 3600) if len(frame) else pd.Series(dtype=float)
    return {"total_trades": s["trades"], "PF": s["PF_R"], "expectancy_R": s["expectancy"],
            "net_R": s["net_R"], "max_drawdown_R": s["max_DD_R"],
            "recovery_factor": s["recovery_factor"], "win_rate": s["winrate"],
            "average_holding_hours": finite(holding.mean()), "losing_streak": s["max_losing_streak"],
            "average_MAE_R": finite(frame.MAE_R.astype(float).mean()) if len(frame) else None,
            "average_MFE_R": finite(frame.MFE_R.astype(float).mean()) if len(frame) else None}


def _csv(path: Path, rows: Any) -> None:
    data = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    data.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _reports(target: Path, trades: pd.DataFrame, status_rows: list[dict], pair: str, strategy: str) -> dict:
    target.mkdir(parents=True, exist_ok=True)
    summary = _summary(trades)
    _csv(target / "trades.csv", trades)
    _json(target / "metrics.json", {"status": "AVAILABLE" if len(trades) else status_rows[0]["status"], **summary})
    def grouped(column: str, values: list[Any]) -> list[dict]:
        return [{column: value, **_summary(trades.loc[trades[column].eq(value)])} for value in values]
    _csv(target / "instrument_report.csv", grouped("instrument", [x[0] for x in INSTRUMENTS]))
    _csv(target / "direction_report.csv", grouped("direction", ["LONG", "SHORT"]))
    years = pd.to_datetime(trades.exit_time, utc=True).dt.year if len(trades) else pd.Series(dtype=int)
    year_frame = trades.assign(year=years)
    _csv(target / "yearly_report.csv", [{"year": y, **_summary(year_frame.loc[year_frame.year.eq(y)])} for y in (2023, 2024)])
    _csv(target / "mae_mfe_report.csv", grouped("instrument", [x[0] for x in INSTRUMENTS]))
    conc = concentration(trades.net_R) if len(trades) else concentration(pd.Series(dtype=float))
    _csv(target / "concentration_report.csv", [{**conc, "top_5_trade_removal_net_R": conc["net_R_without_top5"],
                                                   "top_5_trade_removal_PF": conc["PF_R_C1_without_top5"]}])
    lines = [f"# Phase 7.3 {pair} {strategy}", "", "Fixed frozen candidate; descriptive research only.", "",
             f"Status: {'AVAILABLE' if any(r['status'] == 'AVAILABLE' for r in status_rows) else 'DATA_UNAVAILABLE'}",
             "", "## Instrument availability", ""] + [f"- {r['instrument']}: {r['status']}" for r in status_rows]
    (target / "final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def run(data_root: Path = APPROVED_DATA_ROOT,
        output: Path = Path("TradingSystemLab/results/mtf_research")) -> dict:
    verify_frozen_strategies()
    candidates = frozen_candidates()
    protected_before = {str(p): hash_tree(p) for p in PROTECTED}
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    cache: dict[tuple[str, str], tuple[pd.DataFrame | None, list[Path]]] = {}
    comparison, sources = [], []
    for higher_tf, lower_tf in PAIRS:
        pair = f"{higher_tf}_{lower_tf}"
        for strategy in ("T2", "T3"):
            candidate = candidates[strategy]
            parameter_hash = stable_hash(candidate["parameters"])
            frames, statuses = [], []
            for instrument, alias in INSTRUMENTS:
                key = (alias, lower_tf)
                if key not in cache:
                    cache[key] = load_development(Path(data_root), alias, lower_tf)
                low, paths = cache[key]
                status = "DATA_UNAVAILABLE"
                if low is not None:
                    high = causal_aggregate(low, lower_tf, higher_tf)
                    if len(high):
                        frame = _execute(strategy, candidate["parameters"], alias, lower_tf, low, high)
                        frame["timeframe_pair"] = pair
                        frames.append(frame)
                        status = "AVAILABLE"
                statuses.append({"instrument": instrument, "status": status})
                sources.append({"instrument": instrument, "timeframe_pair": pair, "source_timeframe": lower_tf,
                                "status": status, "files": [{"name": p.name, "sha256": _sha(p)} for p in paths]})
            trades = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=[
                "trade_id", "instrument", "strategy", "timeframe_pair", "direction", "entry_time", "exit_time",
                "gross_R", "net_R", "initial_risk_ticks", "MAE_R", "MFE_R"])
            if len(trades):
                trades = trades.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
            metric = _reports(output / pair / strategy, trades, statuses, pair, strategy)
            comparison.append({"timeframe_pair": pair, "strategy": strategy,
                               "status": "AVAILABLE" if any(x["status"] == "AVAILABLE" for x in statuses) else "DATA_UNAVAILABLE",
                               **metric})
            if stable_hash(candidate["parameters"]) != parameter_hash:
                raise RuntimeError(f"{strategy}_FROZEN_PARAMETERS_MUTATED")
    _csv(output / "comparison.csv", comparison)
    protected_after = {str(p): hash_tree(p) for p in PROTECTED}
    if protected_before != protected_after:
        raise RuntimeError("PROTECTED_ARTIFACT_MUTATION")
    manifest = {"phase": "7.3", "status": "PHASE_7_3_TRUE_MTF_RESEARCH_COMPLETE",
        "timeframe_pairs": [f"{a}_{b}" for a, b in PAIRS],
        "future_compatible_pairs": [f"{a}_{b}" for a, b in FUTURE_PAIRS],
        "instruments": [x[0] for x in INSTRUMENTS], "development_period": ["2023-01-01", "2024-12-31"],
        "candidate_ids": [candidates[k]["candidate_id"] for k in ("T2", "T3")],
        "source_data_hashes": sources, "frozen_strategy_hashes": STRATEGY_SHA256,
        "frozen_parameter_hashes": {k: stable_hash(candidates[k]["parameters"]) for k in ("T2", "T3")},
        "timeframe_pair": [f"{a}_{b}" for a, b in PAIRS],
        "cost_model": {"cost_ticks_per_side": COST_TICKS_PER_SIDE, "round_trip_ticks": 2 * COST_TICKS_PER_SIDE,
                       "slippage_ticks_per_side": 0.0},
        "true_oos_blocked": True, "optimization": False, "ranking": False, "deterministic": True,
        "protected_artifact_hashes": protected_after}
    _json(output / "manifest.json", manifest)
    lines = ["# Phase 7.3 TRUE MTF Research", "", "## Methodology", "",
        "Frozen T2_candidate_v1 and T3_candidate_v1 parameters were evaluated on development data only. Higher-timeframe trend context filters lower-timeframe execution; no indicator, optimization, or ranking was added.", "",
        "## Tested timeframe pairs", "", *[f"- {a} → {b}" for a, b in PAIRS], "",
        "## Causal MTF rules", "", "Candles are close-labelled. A higher-timeframe candle is aligned only to an execution candle whose open is at or after that higher-timeframe close. Incomplete or non-consecutive aggregation blocks are dropped, and aggregation resets at each Moscow trading-day boundary.", "",
        "## Result summary", "", "| Pair | Strategy | Status | Trades | PF | Expectancy R | Net R | Max DD R |", "|---|---|---|---:|---:|---:|---:|---:|"]
    for row in comparison:
        fmt = lambda x: "" if x is None else (f"{x:.6g}" if isinstance(x, float) else str(x))
        lines.append("| " + " | ".join(fmt(row[k]) for k in ("timeframe_pair", "strategy", "status", "total_trades", "PF", "expectancy_R", "net_R", "max_drawdown_R")) + " |")
    lines += ["", "## Limitations", "", "Results cover only Si and CNY development observations from 2023–2024. Missing source resolutions return DATA_UNAVAILABLE; candles are never fabricated. Results are descriptive and are not a production promotion decision.", "", "## Safety", "", "optimization=false; ranking=false; true_oos_blocked=true. Phase 5 and Phase 6 artifact hashes were checked before and after execution.", ""]
    (output / "mtf_research_report.md").write_text("\n".join(lines), encoding="utf-8")
    return {"status": manifest["status"], "research_combinations": len(PAIRS) * 2 * len(INSTRUMENTS)}
