"""Run the frozen R3 implementation check on development data only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import pandas as pd

from .core.data_loader import DataLoader
from .strategies.range.R3_Round_Level_Rejection import STRATEGY_ID, R3RoundLevelRejection

CONFIG_ROOT = Path(__file__).resolve().parent / "configs"
SYMBOLS = ("Si", "CNY")
ROUND_LEVEL_STEPS = {"Si": .10, "CNY": .05}


def instrument_tick_size(symbol: str) -> float:
    text = (CONFIG_ROOT / f"{symbol}.yaml").read_text(encoding="utf-8")
    match = re.search(r"(?m)^tick_size:\s*([0-9]+(?:\.[0-9]+)?)", text)
    if match is None or float(match.group(1)) <= 0:
        raise ValueError(f"positive tick_size missing for {symbol}")
    return float(match.group(1))


def load_timeframe(root: Path, symbol: str, timeframe: str, *, optional: bool = False) -> pd.DataFrame | None:
    paths = [p for year in (2023, 2024) for p in sorted((root / "2026" / symbol).glob(f"{symbol}_{timeframe}_{year}_Q*.csv"))]
    if not paths:
        if optional:
            return None
        raise FileNotFoundError(f"no 2023-2024 {timeframe} source data for {symbol} under {root}")
    data = DataLoader().close_index(DataLoader().load_csv(paths), "1h" if timeframe == "H1" else "15min")
    start, locked = pd.Timestamp("2023-01-01", tz=data.index.tz), pd.Timestamp("2025-01-01", tz=data.index.tz)
    if data.index.min() < start or (data.index >= locked).any():
        raise ValueError("R3 development coverage must contain 2023-2024 only")
    return data


def _pf(values: pd.Series) -> float | None:
    gains, losses = float(values[values > 0].sum()), float(-values[values < 0].sum())
    return gains / losses if losses else None


def metrics_for(trades: pd.DataFrame) -> dict:
    gross, net = trades.gross_R, trades.net_R_C1
    curve = pd.concat([pd.Series([0.]), net.reset_index(drop=True).cumsum()], ignore_index=True)
    count = lambda value: int((trades.exit_reason == value).sum())
    mean = lambda values: float(values.mean()) if len(values) else 0.
    median = lambda values: float(values.median()) if len(values) else 0.
    return {"total_trades": len(trades), "LONG_trades": int((trades.direction == "LONG").sum()),
            "SHORT_trades": int((trades.direction == "SHORT").sum()),
            "Si_trades": int((trades.symbol == "Si").sum()), "CNY_trades": int((trades.symbol == "CNY").sum()),
            "gross_R": float(gross.sum()), "PF_C0": _pf(gross), "expectancy_C0": mean(gross),
            "PF_C1": _pf(net), "expectancy_C1": mean(net), "net_R_C1": float(net.sum()),
            "winrate_C1": float((net > 0).mean()) if len(net) else 0.,
            "max_DD_R_C1": float((curve - curve.cummax()).min()), "STOP_exits": count("STOP"),
            "ROUND_LEVEL_MIDPOINT_TARGET_exits": count("ROUND_LEVEL_MIDPOINT_TARGET"),
            "LEVEL_FAILURE_exits": count("LEVEL_FAILURE"), "TIME_EXIT_exits": count("TIME_EXIT"),
            "median_holding_bars": median(trades.bars_held), "mean_MAE_R": mean(trades.MAE_R),
            "median_MAE_R": median(trades.MAE_R), "mean_MFE_R": mean(trades.MFE_R),
            "median_MFE_R": median(trades.MFE_R)}


def run(data_root: Path, output: Path) -> dict:
    strategy = R3RoundLevelRejection()
    pieces = []
    for symbol in SYMBOLS:
        pieces.append(strategy.run(load_timeframe(data_root, symbol, "M15"), symbol,
                                   round_level_step=ROUND_LEVEL_STEPS[symbol],
                                   tick_size=instrument_tick_size(symbol),
                                   h1=load_timeframe(data_root, symbol, "H1", optional=True)))
    trades = pd.concat(pieces, ignore_index=True).sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
    metrics = metrics_for(trades)
    output.mkdir(parents=True, exist_ok=True)
    trades.to_csv(output / "trades.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    manifest = {"strategy_id": STRATEGY_ID, "implementation_version": "1.0", "symbols": list(SYMBOLS),
                "execution_timeframe": "M15", "round_level_steps": ROUND_LEVEL_STEPS,
                "development_start": "2023-01-01", "development_end": "2024-12-31",
                "frozen_parameters": strategy.frozen_parameters(),
                "cost_scenarios": {"C0": "zero cost", "C1": "1 execution tick per side"},
                "true_oos_blocked": True, "implementation_check_only": True,
                "optimization_performed": False, "walk_forward_performed": False}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summary = f"""# R3 Round Level Rejection v1.0

## Hypothesis
Penetration and same-bar reclaim of a psychological price level may move away from that level.

## Round Level Construction
Decimal floor/ceiling of signal Open; an exact level is both its lower and upper candidate.

## Instrument Level Spacing
Si 0.10 RUB; CNY 0.05 RUB. Execution tick size remains separately configured at 0.001.

## Rejection Definition
LONG opens at/above, penetrates below, and closes above its candidate; SHORT is the mirror.

## Penetration Rules
Inclusive 0.05--0.75 M15 ATR14, without reaching the next full level interval.

## Entry
Signal M15 Close. Exits first become executable on the next bar; one position maximum.

## Initial Stop
Signal extreme plus an outward 0.10 ATR buffer; risk over 1.25 ATR is skipped.

## Structural Target
Frozen midpoint between the rejected level and next level in trade direction.

## Level Failure
A post-entry M15 Close through the rejected level exits at that Close.

## Time Exit
Close of the twelfth executable M15 bar.

## Causality
Only closed M15 bars are signals. Optional H1 values are causally aligned diagnostics and never filters.

## Development Coverage
Si and CNY native M15, 2023-01-01 through 2024-12-31. TRUE OOS 2025+ is hard blocked.

## Implementation Check Results
IMPLEMENTATION_CHECK_ONLY

Trades: {metrics['total_trades']} (LONG {metrics['LONG_trades']}, SHORT {metrics['SHORT_trades']}; Si {metrics['Si_trades']}, CNY {metrics['CNY_trades']}).

## Limitations
No optimization, parameter search, walk-forward, Monte Carlo, comparison, or trading verdict.

## Status
STATUS: IMPLEMENTED — NOT YET OPTIMIZED OR VALIDATED
"""
    (output / "summary.md").write_text(summary, encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("TradingSystemLab/results/R3_implementation_check"))
    args = parser.parse_args()
    run(args.data_root, args.output)
