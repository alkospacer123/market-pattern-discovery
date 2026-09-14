"""Run the frozen R2 implementation check on development data only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import pandas as pd

from .core.data_loader import DataLoader
from .strategies.range.R2_Liquidity_Sweep import STRATEGY_ID, R2LiquiditySweep

CONFIG_ROOT = Path(__file__).resolve().parent / "configs"
SYMBOLS = ("Si", "CNY")


def instrument_tick_size(symbol: str) -> float:
    text = (CONFIG_ROOT / f"{symbol}.yaml").read_text(encoding="utf-8")
    match = re.search(r"(?m)^tick_size:\s*([0-9]+(?:\.[0-9]+)?)", text)
    if match is None or float(match.group(1)) <= 0:
        raise ValueError(f"positive tick_size missing for {symbol}")
    return float(match.group(1))


def load_timeframe(root: Path, symbol: str, timeframe: str) -> pd.DataFrame:
    paths = [p for year in (2023, 2024) for p in sorted((root / "2026" / symbol).glob(f"{symbol}_{timeframe}_{year}_Q*.csv"))]
    if not paths:
        raise FileNotFoundError(f"no 2023-2024 {timeframe} source data for {symbol} under {root}")
    loader = DataLoader()
    data = loader.close_index(loader.load_csv(paths), "1h" if timeframe == "H1" else "15min")
    start = pd.Timestamp("2023-01-01", tz=data.index.tz)
    locked = pd.Timestamp("2025-01-01", tz=data.index.tz)
    if data.index.min() < start or (data.index >= locked).any():
        raise ValueError("R2 development coverage must contain 2023-2024 only")
    return data


def _pf(values: pd.Series) -> float | None:
    gains, losses = float(values[values > 0].sum()), float(-values[values < 0].sum())
    return gains / losses if losses else None


def metrics_for(trades: pd.DataFrame) -> dict:
    gross = trades.gross_R if len(trades) else pd.Series(dtype=float)
    net = trades.net_R_C1 if len(trades) else pd.Series(dtype=float)
    curve = pd.concat([pd.Series([0.]), net.reset_index(drop=True).cumsum()], ignore_index=True)
    drawdown = curve - curve.cummax()
    count = lambda value: int((trades.exit_reason == value).sum())
    mean = lambda values: float(values.mean()) if len(values) else 0.
    median = lambda values: float(values.median()) if len(values) else 0.
    return {
        "total_trades": len(trades), "LONG_trades": int((trades.direction == "LONG").sum()),
        "SHORT_trades": int((trades.direction == "SHORT").sum()),
        "Si_trades": int((trades.symbol == "Si").sum()), "CNY_trades": int((trades.symbol == "CNY").sum()),
        "gross_R": float(gross.sum()), "PF_C0": _pf(gross), "expectancy_C0": mean(gross),
        "PF_C1": _pf(net), "expectancy_C1": mean(net), "net_R_C1": float(net.sum()),
        "winrate_C1": float((net > 0).mean()) if len(net) else 0., "max_DD_R_C1": float(drawdown.min()),
        "STOP_exits": count("STOP"), "RANGE_MIDPOINT_TARGET_exits": count("RANGE_MIDPOINT_TARGET"),
        "RANGE_FAILURE_exits": count("RANGE_FAILURE"), "TIME_EXIT_exits": count("TIME_EXIT"),
        "median_holding_bars": median(trades.bars_held), "mean_MAE_R": mean(trades.MAE_R),
        "median_MAE_R": median(trades.MAE_R), "mean_MFE_R": mean(trades.MFE_R),
        "median_MFE_R": median(trades.MFE_R),
    }


def run(data_root: Path, output: Path) -> dict:
    strategy = R2LiquiditySweep()
    pieces = [strategy.run(load_timeframe(data_root, s, "H1"), load_timeframe(data_root, s, "M15"), s,
                           tick_size=instrument_tick_size(s)) for s in SYMBOLS]
    trades = pd.concat(pieces, ignore_index=True).sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
    output.mkdir(parents=True, exist_ok=True)
    metrics = metrics_for(trades)
    trades.to_csv(output / "trades.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    manifest = {"strategy_id": STRATEGY_ID, "implementation_version": "1.0", "symbols": list(SYMBOLS),
                "context_timeframe": "H1", "execution_timeframe": "M15", "development_start": "2023-01-01",
                "development_end": "2024-12-31", "frozen_parameters": strategy.frozen_parameters(),
                "cost_scenarios": {"C0": "zero cost", "C1": "1 tick per side"}, "true_oos_blocked": True,
                "implementation_check_only": True, "optimization_performed": False, "walk_forward_performed": False}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summary = f"""# R2 Liquidity Sweep / False Breakout v1.0

## Hypothesis
A same-bar sweep and reclaim of a pre-existing price-range boundary may revert toward range equilibrium.

## H1 Range Context
ADX(14) <= 25 and absolute 10-bar EMA200 slope / ATR14 <= 0.35.

## Causal Range Boundaries
Highest High and lowest Low of the previous 20 completed H1 bars (`shift(1)`), with their midpoint.

## M15 Sweep
An M15 extreme penetrates the relevant boundary by 0.05 through 1.00 ATR14_M15.

## Same-Bar Reclaim
The signal M15 Close is strictly back inside the frozen H1 range.

## Rejection Requirement
LONG closes at or above its candle midpoint; SHORT closes at or below it.

## Entry
At the closed signal M15 candle, one position maximum.

## Initial Stop
Signal extreme plus a 0.10 ATR outward buffer; initial risk above 1.50 ATR is skipped.

## Frozen Range Midpoint Target
The entry context midpoint is fixed for the trade and must be on the profitable side of entry.

## Range Failure Exit
A newly completed H1 Close beyond the frozen setup boundary exits at the corresponding M15 Close.

## Time Exit
Exit at the Close of the sixteenth executable M15 bar after entry.

## Multi-Timeframe Causality
Entry sees only H1 closes available at or before M15 bar open; no partial H1 candle is visible.

## Development Coverage
Si and CNY source H1 and M15 data, 2023-01-01 through 2024-12-31. No resampling was used.

## Implementation Check Results
IMPLEMENTATION_CHECK_ONLY

Trades: {metrics['total_trades']} (LONG {metrics['LONG_trades']}, SHORT {metrics['SHORT_trades']}; Si {metrics['Si_trades']}, CNY {metrics['CNY_trades']}).

## Limitations
No optimization, parameter search, walk-forward, Monte Carlo, comparison, or edge verdict was performed.

## Status
STATUS: IMPLEMENTED — NOT YET OPTIMIZED OR VALIDATED
"""
    (output / "summary.md").write_text(summary, encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("TradingSystemLab/results/R2_implementation_check"))
    args = parser.parse_args()
    run(args.data_root, args.output)
