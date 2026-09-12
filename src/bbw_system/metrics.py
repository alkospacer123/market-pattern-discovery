from __future__ import annotations
import math
import pandas as pd


def trade_metrics(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"trades_count": 0, "win_rate": 0.0, "net_r": 0.0, "profit_factor": 0.0, "by_year": {}, "by_instrument": {}}
    r = trades["net_r"].astype(float)
    equity = trades.get("net_pnl", r).astype(float).cumsum()
    drawdown = equity - equity.cummax()
    losses, streak, maximum = r.lt(0), 0, 0
    for loss in losses:
        streak = streak + 1 if loss else 0
        maximum = max(maximum, streak)
    gross_profit, gross_loss = r[r > 0].sum(), -r[r < 0].sum()
    duration = pd.to_datetime(trades.exit_time) - pd.to_datetime(trades.entry_time) if {"entry_time", "exit_time"} <= set(trades) else pd.Series([], dtype="timedelta64[ns]")
    years = pd.to_datetime(trades.exit_time).dt.year if "exit_time" in trades else pd.Series([0] * len(trades))
    return {
        "trades_count": len(trades), "win_rate": float(r.gt(0).mean()), "net_r": float(r.sum()),
        "avg_r": float(r.mean()), "median_r": float(r.median()),
        "profit_factor": float(gross_profit / gross_loss) if gross_loss else math.inf,
        "max_drawdown": float(drawdown.min()), "max_drawdown_r": float((r.cumsum() - r.cumsum().cummax()).min()),
        "average_trade_duration": str(duration.mean()) if len(duration) else None,
        "max_consecutive_losses": maximum, "long_short_split": trades.direction.value_counts().to_dict(),
        "by_year": trades.assign(_year=years).groupby("_year").net_r.agg(["count", "sum", "mean"]).to_dict("index"),
        "by_instrument": trades.groupby("instrument").net_r.agg(["count", "sum", "mean"]).to_dict("index") if "instrument" in trades else {},
        "avg_mae": float(trades.mae.mean()) if "mae" in trades else None, "avg_mfe": float(trades.mfe.mean()) if "mfe" in trades else None,
    }
