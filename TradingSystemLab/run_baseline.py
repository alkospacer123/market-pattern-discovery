"""Run the frozen T3 baseline without reading locked TRUE OOS data."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import pandas as pd

from .core.backtester import Backtester
from .core.data_loader import DataLoader
from .core.metrics import calculate_metrics
from .core.portfolio import FixedRiskPortfolio
from .strategies.trend.T3_MTF_Trend import T3MTFTrend


def run(data_root: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    all_trades, all_equity, periods = [], [], []
    for symbol, folder in (("Si", "Si"), ("CNY", "CNY")):
        # Explicit years are intentional: discovery code must not even read 2025.
        paths = [p for year in (2023, 2024) for p in
                 sorted((data_root / "2026" / folder).glob(f"{folder}_H1_{year}_Q*.csv"))]
        loader = DataLoader()
        h1 = loader.close_index(loader.load_csv(paths))
        h4 = loader.h4_from_h1(h1)
        result = Backtester(FixedRiskPortfolio(), commission_per_unit=0.0,
                            slippage_points=0.0).run(T3MTFTrend(), symbol, h1, h4)
        all_trades.append(result.trades)
        curve = result.equity_curve.reset_index()
        curve.insert(0, "symbol", symbol)
        all_equity.append(curve)
        periods.append((h1.index.min(), h1.index.max()))
    trades = pd.concat(all_trades, ignore_index=True)
    equity = pd.concat(all_equity, ignore_index=True)
    # Aggregate drawdown uses independent-symbol PnL in deterministic time order.
    portfolio_curve = (trades.sort_values(["exit_time", "symbol"], kind="mergesort")
                       .assign(equity=lambda x: 200_000.0 + x["net_profit"].cumsum())
                       .set_index("exit_time")[["equity"]])
    metrics = calculate_metrics(trades, portfolio_curve)
    trades.to_csv(output / "trades.csv", index=False)
    equity.to_csv(output / "equity_curve.csv", index=False)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n")
    readme = f"""# T3 baseline

Frozen, unoptimized baseline for **Si + CNY**. Source CSV files remain outside the repository.

## Parameters

EMA100; EMA slope 5; ADX(14) > 20; ATR(14) > ATR mean(20); breakout 20;
initial stop 2 ATR; trailing stop 3 ATR; fixed risk 1%; point value 1.
Commission and slippage are configurable and were both set to zero for this baseline.

## Period

{min(p[0] for p in periods).isoformat()} through {max(p[1] for p in periods).isoformat()}.
Calendar 2025 was neither selected nor loaded.

## Results

* Trades: {metrics['trades']}
* Win rate: {metrics['win_rate']:.4f}
* Profit factor: {metrics['profit_factor']}
* Average R: {metrics['average_R']:.4f}
* Net profit: {metrics['net_profit']:.2f}
* Max drawdown: {metrics['max_drawdown']:.2f}

## Known limitations

H4 candles are consecutive complete four-H1-bar blocks reset at each trading-day
boundary. Intrabar ordering is unknown, so a trailing level calculated from a bar's
extreme becomes active only on the next bar. Open positions at the end of the sample
remain unrealized. Contract multipliers, commissions, and slippage must be configured
to venue-accurate non-zero values before interpreting economic performance.
"""
    (output / "README.md").write_text(readme)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("TradingSystemLab/results/T3_baseline"))
    args = parser.parse_args()
    run(args.data_root, args.output)
