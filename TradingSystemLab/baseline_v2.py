"""Frozen, development-only TradingSystemLab v2 Phase 1 baseline matrix."""
from __future__ import annotations

from dataclasses import replace
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from .core.backtester import Backtester
from .core.data_loader import DataLoader
from .core.instrument_specs import InstrumentSpec, get_instrument_spec
from .core.portfolio import FixedRiskPortfolio
from .core.unified_metrics import finite, stats
from .multitimeframe.phase71 import STRATEGY_SHA256, verify_frozen_strategies
from .optimization.experiment import stable_hash
from .optimization.phase32 import PARAMETERS, _normalize_backtester
from .strategies.trend.T2_Trend_Pullback import T2TrendPullback
from .strategies.trend.T3_MTF_Trend import T3MTFTrend

DATA_ROOT = Path("/workspace/market-pattern-data/futures_quarterly")
OUTPUT_ROOT = Path("TradingSystemLab/results/baseline_v2")
INSTRUMENTS = ("Si", "CNY", "GD", "BR", "MIX", "NG")
TIMEFRAMES = ("M30", "H1")
STRATEGIES = ("T2", "T3")
DEVELOPMENT_START = pd.Timestamp("2020-01-01", tz="Europe/Moscow")
TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="Europe/Moscow")
COST_MODEL = {"name": "C1", "ticks_per_side": 1, "round_trip_ticks": 2,
              "additional_slippage_ticks": 0}
RUNS = tuple((strategy, instrument, timeframe) for strategy in STRATEGIES
             for instrument in INSTRUMENTS for timeframe in TIMEFRAMES)
FROZEN_PARAMETERS = {
    "T2": {"adx_threshold": 20, "confirmation_window": 3, "ema_fast": 20,
           "ema_slow": 200, "ema_trend": 50, "impulse_distance_atr": .5,
           "max_initial_stop_atr": 2.5, "trailing_atr": 3},
    "T3": {"adx_threshold": 20, "atr_average_period": 20, "breakout_period": 20,
           "ema_period": 75, "stop_atr": 2.0, "trail_atr": 3.0},
}


def _frame_sha(frame: pd.DataFrame) -> str:
    """Hash only the already admitted development frame, never the source tail."""
    values = pd.util.hash_pandas_object(frame, index=True).values.tobytes()
    return hashlib.sha256(values).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf-8")


def _source(data_root: Path, instrument: str, timeframe: str) -> Path:
    root = Path(data_root).resolve()
    if root != DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    path = root / instrument / f"{instrument}_{timeframe}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"required baseline source is missing: {path}")
    return path


def load_development(data_root: Path, instrument: str, timeframe: str) -> tuple[pd.DataFrame, Path]:
    """Read only the development prefix and stop before the first TRUE OOS row."""
    path = _source(data_root, instrument, timeframe)
    loader = DataLoader(forbid_true_oos=True)
    frame = loader.load_csv_prefix(path, start=DEVELOPMENT_START, end_exclusive=TRUE_OOS_START)
    frame = loader.close_index(frame, "30min" if timeframe == "M30" else "1h")
    if frame.empty or frame.index.max() >= TRUE_OOS_START:
        raise ValueError("TRUE_OOS_BARRIER_VIOLATION")
    aligned = frame.index.minute % (30 if timeframe == "M30" else 60) == 0
    if not (aligned & (frame.index.second == 0)).all():
        raise ValueError(f"{timeframe}_CLOSE_ALIGNMENT_VIOLATION")
    return frame, path


def _instrument_spec(spec: InstrumentSpec) -> dict[str, Any]:
    """Return the execution fields required in baseline audit artifacts."""
    return {"price_step": spec.price_step, "tick_value_rub": spec.tick_value_rub,
            "currency": spec.currency, "lot_size": spec.lot_size}


def _execute(strategy: str, instrument: str, timeframe: str, frame: pd.DataFrame,
             spec: InstrumentSpec) -> pd.DataFrame:
    parameters = replace(PARAMETERS[strategy], **FROZEN_PARAMETERS[strategy])
    if strategy == "T2":
        trades = T2TrendPullback(parameters).run(frame, instrument, tick_size=spec.price_step)
        trades = trades.rename(columns={"net_R_C1": "net_R", "cost_R_C1": "cost_R"})
    else:
        # Phase 1 is explicitly single-timeframe: T3 receives the same closed-bar
        # stream for execution and regime calculation. No derived MTF series exists.
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=1,
                         tick_size=spec.price_step).run(
                             T3MTFTrend(parameters), instrument, frame, frame).trades
        trades = _normalize_backtester(raw, strategy)
        trades["net_R"] = trades["gross_R"] - trades["cost_R"]
    if len(trades):
        if (pd.to_datetime(trades.entry_time, utc=True) >= TRUE_OOS_START.tz_convert("UTC")).any():
            raise ValueError("TRUE_OOS_TRADE_VIOLATION")
        trades = trades.copy()
        trades["trade_id"] = [f"{strategy}-{instrument}-{timeframe}-{n:06d}"
                              for n in range(1, len(trades) + 1)]
        trades = trades.sort_values(["exit_time", "trade_id"], kind="mergesort")
    return trades.reset_index(drop=True)


def _metrics(trades: pd.DataFrame) -> dict[str, Any]:
    values = trades.net_R.astype(float) if len(trades) else pd.Series(dtype=float)
    result = stats(values)
    return {"trades": result["trades"], "PF": result["PF_R"],
            "expectancy_R": result["expectancy"], "net_R": result["net_R"],
            "max_drawdown_R": result["max_DD_R"], "win_rate": result["winrate"]}


def _write_run(target: Path, strategy: str, instrument: str, timeframe: str,
               frame: pd.DataFrame, source: Path, trades: pd.DataFrame,
               spec: InstrumentSpec) -> dict[str, Any]:
    target.mkdir(parents=True)
    metrics = _metrics(trades)
    trades.map(finite).to_csv(target / "trades.csv", index=False, lineterminator="\n",
                              float_format="%.12g", na_rep="")
    _json(target / "metrics.json", metrics)
    quality = {"rows": len(frame), "first_close": frame.index.min().isoformat(),
               "last_close": frame.index.max().isoformat(), "timezone": str(frame.index.tz),
               "monotonic": bool(frame.index.is_monotonic_increasing),
               "duplicate_timestamps": int(frame.index.duplicated().sum()),
               "true_oos_rows_read": 0, "development_frame_sha256": _frame_sha(frame)}
    _json(target / "data_quality.json", quality)
    manifest = {"phase": "PHASE_1_BASELINE", "strategy": strategy,
                "instrument": instrument, "timeframe": timeframe,
                "instrument_spec": _instrument_spec(spec),
                "development_period": ["2020-01-01", "2024-12-31"],
                "true_oos_cutoff": "2025-01-01", "true_oos_blocked": True,
                "cost_model": COST_MODEL, "strategy_hash": STRATEGY_SHA256[strategy],
                "parameter_hash": stable_hash(FROZEN_PARAMETERS[strategy]),
                "parameters": FROZEN_PARAMETERS[strategy], "source_file": str(source),
                "source_data_copied": False, "optimization": False, "ranking": False,
                "selection": False, "walk_forward": False, "mtf": False,
                "status": "COMPLETE"}
    _json(target / "manifest.json", manifest)
    (target / "report.md").write_text(
        f"# {strategy} / {instrument} / {timeframe}\n\n"
        f"Frozen Phase 1 baseline, C1 only. Status: **COMPLETE**.\n\n"
        f"Trades: {metrics['trades']}; PF: {metrics['PF']}; expectancy: "
        f"{metrics['expectancy_R']}; Net R: {metrics['net_R']}; DD: "
        f"{metrics['max_drawdown_R']}; win rate: {metrics['win_rate']}.\n\n"
        "No optimization, ranking, selection, walk-forward, MTF, or TRUE OOS access.\n",
        encoding="utf-8")
    return {"strategy": strategy, "instrument": instrument, "timeframe": timeframe,
            **metrics, "status": "COMPLETE"}


def run(data_root: Path = DATA_ROOT, output: Path = OUTPUT_ROOT) -> dict[str, Any]:
    """Execute exactly the frozen 24-run matrix and write its audit bundle."""
    verify_frozen_strategies()
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    cache: dict[tuple[str, str], tuple[pd.DataFrame, Path]] = {}
    rows = []
    for strategy, instrument, timeframe in RUNS:
        spec = get_instrument_spec(instrument)
        key = (instrument, timeframe)
        if key not in cache:
            cache[key] = load_development(Path(data_root), instrument, timeframe)
        frame, source = cache[key]
        trades = _execute(strategy, instrument, timeframe, frame, spec)
        rows.append(_write_run(output / strategy / instrument / timeframe, strategy,
                               instrument, timeframe, frame, source, trades, spec))
    if len(rows) != 24:
        raise RuntimeError("BASELINE_MATRIX_INCOMPLETE")
    lines = ["# TradingSystemLab v2 — Phase 1 Baseline", "",
             "Frozen development-only baseline. C1 only; no optimization, ranking, selection, "
             "walk-forward, MTF, or TRUE OOS access.", "",
             "| Strategy | Instrument | Timeframe | Trades | PF | Expectancy | Net R | DD | Win rate | Status |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|---|"]
    fmt = lambda value: "" if value is None else (f"{value:.6g}" if isinstance(value, float) else str(value))
    for row in rows:
        lines.append("| " + " | ".join(fmt(row[k]) for k in
                     ("strategy", "instrument", "timeframe", "trades", "PF", "expectancy_R",
                      "net_R", "max_drawdown_R", "win_rate", "status")) + " |")
    (output / "Baseline_Report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _json(output / "manifest.json", {"phase": "PHASE_1_BASELINE", "run_count": 24,
          "declared_runs": [{"strategy": s, "instrument": i, "timeframe": t,
                             "instrument_spec": _instrument_spec(get_instrument_spec(i))}
                            for s, i, t in RUNS],
          "strategies": list(STRATEGIES), "instruments": list(INSTRUMENTS),
          "timeframes": list(TIMEFRAMES), "cost_models": [COST_MODEL],
          "frozen_strategy_hashes": STRATEGY_SHA256, "optimization": False,
          "ranking": False, "selection": False, "walk_forward": False, "mtf": False,
          "true_oos_blocked": True, "status": "PHASE_1_BASELINE_COMPLETE"})
    return {"status": "PHASE_1_BASELINE_COMPLETE", "runs": 24}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    print(json.dumps(run(args.data_root, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
