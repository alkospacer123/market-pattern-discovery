"""Run the frozen T2 implementation check on development data only."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

from .core.data_loader import DataLoader
from .strategies.trend.T2_Trend_Pullback import STRATEGY_ID, T2TrendPullback


def load_h1(root: Path, symbol: str) -> pd.DataFrame:
    paths = [p for year in (2023, 2024) for p in sorted((root / "2026" / symbol).glob(f"{symbol}_H1_{year}_Q*.csv"))]
    if not paths:
        raise FileNotFoundError(f"no 2023-2024 H1 data for {symbol} under {root}")
    return DataLoader().close_index(DataLoader().load_csv(paths))


def _pf(values: pd.Series) -> float | None:
    gains, losses = values[values > 0].sum(), -values[values < 0].sum()
    return float(gains / losses) if losses else (None if gains == 0 else None)


def metrics_for(trades: pd.DataFrame) -> dict:
    gross = trades.gross_R if len(trades) else pd.Series(dtype=float)
    net = trades.net_R_C1 if len(trades) else pd.Series(dtype=float)
    curve = pd.concat([pd.Series([0.0]), net.reset_index(drop=True).cumsum()], ignore_index=True)
    dd = curve - curve.cummax()
    return {"trades": len(trades), "LONG_trades": int((trades.direction == "LONG").sum()),
        "SHORT_trades": int((trades.direction == "SHORT").sum()),
        "Si_trades": int((trades.symbol == "Si").sum()), "CNY_trades": int((trades.symbol == "CNY").sum()),
        "gross_R": float(gross.sum()), "net_R_C1": float(net.sum()), "PF_C0": _pf(gross), "PF_C1": _pf(net),
        "expectancy_C0": float(gross.mean()) if len(gross) else 0.0,
        "expectancy_C1": float(net.mean()) if len(net) else 0.0,
        "winrate": float((gross > 0).mean()) if len(gross) else 0.0,
        "max_DD_R_C1": float(dd.min()) if len(dd) else 0.0,
        "initial_stop_exit_count": int((trades.exit_reason == "INITIAL_STOP").sum()),
        "trailing_exit_count": int((trades.exit_reason == "ATR_TRAILING_STOP").sum()),
        "EMA50_exit_count": int((trades.exit_reason == "EMA50_TREND_LOSS").sum())}


def run(data_root: Path, output: Path) -> dict:
    strategy, pieces = T2TrendPullback(), []
    for symbol in ("Si", "CNY"):
        pieces.append(strategy.run(load_h1(data_root, symbol), symbol, tick_size=0.001))
    trades = pd.concat(pieces, ignore_index=True).sort_values(["exit_time", "symbol", "trade_id"], kind="mergesort").reset_index(drop=True)
    output.mkdir(parents=True, exist_ok=True)
    metrics = metrics_for(trades)
    trades.to_csv(output / "trades.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    manifest = {"strategy_id": STRATEGY_ID, "implementation_version": "1.0", "symbols": ["Si", "CNY"],
        "development_start": "2023-01-01", "development_end": "2024-12-31", "timeframe": "H1",
        "frozen_parameters": strategy.frozen_parameters(), "cost_scenarios": {"C0": "zero cost", "C1": "1 tick per side"},
        "true_oos_blocked": "timestamp >= 2025-01-01", "implementation_check_only": True,
        "optimization_performed": False, "walk_forward_performed": False}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summary = f"""# T2 Trend Pullback Continuation v1.0

## Hypothesis
An established trend may offer better entry price and initial risk after a controlled pullback.

## Frozen Rules
H1 only; one position; fixed-risk sizing; parameters are frozen in the manifest.

## Trend Regime
LONG/SHORT requires EMA50 above/below EMA200, ADX(14) > 20, and ATR(14) >= its 20-bar SMA.

## Impulse Definition
At least one of the 10 bars strictly before the pullback is at least 0.5 ATR beyond EMA20 in trend direction.

## Pullback Definition
LONG: Low <= EMA20 and Close >= EMA50. SHORT is exactly mirrored.

## Confirmation
Within the next three bars, Close crosses the already-known previous High/Low and EMA20 in trend direction.

## Initial Stop
Pullback-to-confirmation extreme plus a 0.10 ATR outward buffer; risks over 3 ATR are skipped.

## Exit Logic
Three-ATR causal trailing stop or EMA50 close trend loss; an executable intrabar stop has priority.

## Causality
All inputs are current/past closed H1 bars. Entry is confirmation Close. Calendar 2025+ is hard-blocked.

## Development Coverage
Si and CNY, 2023-01-01 through 2024-12-31 only.

## Implementation Check Results
IMPLEMENTATION_CHECK_ONLY

NO STRATEGY VERDICT
Trades: {metrics['trades']} (LONG {metrics['LONG_trades']}, SHORT {metrics['SHORT_trades']}).

## Limitations
This is neither optimization nor validation; open positions at sample end are not force-closed.

## Status
STATUS: IMPLEMENTED — NOT YET OPTIMIZED OR VALIDATED
"""
    (output / "summary.md").write_text(summary, encoding="utf-8")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("TradingSystemLab/results/T2_implementation_check"))
    args = parser.parse_args(); run(args.data_root, args.output)
