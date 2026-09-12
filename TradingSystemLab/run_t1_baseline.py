"""Run the frozen T1 baseline on development years only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

from .core.backtester import Backtester
from .core.data_loader import DataLoader
from .core.metrics import calculate_metrics
from .core.portfolio import FixedRiskPortfolio
from .strategies.trend.T1_BBW_Donchian import T1BBWDonchian


def load_h1(data_root: Path, symbol: str) -> pd.DataFrame:
    paths = [path for year in (2023, 2024) for path in sorted(
        (data_root / "2026" / symbol).glob(f"{symbol}_H1_{year}_Q*.csv"))]
    return DataLoader().close_index(DataLoader().load_csv(paths))


def run(data_root: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    pieces, curves = [], []
    for symbol in ("Si", "CNY"):
        h1 = load_h1(data_root, symbol)
        result = Backtester(FixedRiskPortfolio()).run(T1BBWDonchian(), symbol, h1, h1)
        pieces.append(result.trades)
        curve = result.equity_curve.reset_index()
        curve.insert(0, "symbol", symbol)
        curves.append(curve)
    trades = pd.concat(pieces).sort_values(
        ["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
    equity = pd.concat(curves, ignore_index=True)
    portfolio = (trades.assign(equity=200_000.0 + trades.net_profit.cumsum())
                 .set_index("exit_time")[["equity"]])
    metrics = calculate_metrics(trades, portfolio)
    trades.to_csv(output / "trades.csv", index=False)
    equity.to_csv(output / "equity_curve.csv", index=False)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n")
    (output / "summary.md").write_text(f"""# T1 frozen baseline

`T1_BBW_Donchian_v1.0`, Si and CNY, H1, 2023–2024. Parameters are frozen in
`configs/T1_BBW_Donchian.yaml`; no optimization was performed. C0 uses zero cost,
while costs and slippage remain configurable in the shared backtester.

* Trades: {metrics['trades']}
* LONG / SHORT: {metrics['long_trades']} / {metrics['short_trades']}
* PF: {metrics['profit_factor']:.6f}
* Expectancy: {metrics['expectancy']:.6f}
* Average R: {metrics['average_R']:.6f}
* Max DD: {metrics['max_drawdown']:.6f}
* Net profit: {metrics['net_profit']:.6f}

Calendar 2025+ was neither selected nor read. Open positions at sample end remain
unrealized. Signal-candle entries use the close; trailing updates become active on
the next bar because OHLC cannot reveal intrabar ordering.
""", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("TradingSystemLab/results/T1_baseline"))
    args = parser.parse_args()
    run(args.data_root, args.output)
