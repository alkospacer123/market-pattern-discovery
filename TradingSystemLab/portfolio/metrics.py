"""Pure portfolio diagnostics; no parameter-search API is intentionally exposed."""
from __future__ import annotations

import numpy as np
import pandas as pd


def performance(values: pd.Series, holding_hours: pd.Series) -> dict:
    x = values.astype(float)
    gains, losses = x[x > 0].sum(), -x[x < 0].sum()
    equity = x.cumsum(); drawdown = equity - equity.cummax().clip(lower=0)
    max_dd = float(drawdown.min()) if len(x) else 0.0
    losing, longest = 0, 0
    for value in x:
        losing = losing + 1 if value < 0 else 0; longest = max(longest, losing)
    underwater, duration = 0, 0
    for value in drawdown:
        underwater = underwater + 1 if value < 0 else 0; duration = max(duration, underwater)
    net = float(x.sum())
    return {"total_trades": int(len(x)), "PF": float(gains / losses) if losses else None,
            "expectancy": float(x.mean()) if len(x) else None, "net_R": net,
            "win_rate": float((x > 0).mean()) if len(x) else None, "max_drawdown": max_dd,
            "recovery_factor": float(net / abs(max_dd)) if max_dd else None,
            "average_holding_hours": float(holding_hours.mean()) if len(holding_hours) else None,
            "losing_streak": longest, "drawdown_duration_trades": duration}


def risk(daily: pd.Series) -> dict:
    x = daily.astype(float)
    vol = float(x.std(ddof=0)) if len(x) else 0.0
    return {"volatility_daily_R": vol,
            "sharpe_like_R": float(x.mean() / vol * np.sqrt(252)) if vol else None}


def concentration(values: pd.Series) -> dict:
    x = values.astype(float); ranked = x.sort_values(ascending=False)
    net = float(x.sum()); top1 = float(ranked.head(1).sum()); top5 = float(ranked.head(5).sum())
    return {"top_1_trade_R": top1, "top_1_contribution": top1 / net if net else None,
            "top_5_trade_R": top5, "top_5_contribution": top5 / net if net else None,
            "net_R_without_best_trade": net - top1, "net_R_without_top_5_trades": net - top5}


def period_report(trades: pd.DataFrame, frequency: str, label: str) -> pd.DataFrame:
    periods = trades.exit_time.dt.tz_localize(None).dt.to_period(frequency).astype(str)
    rows = []
    for period, part in trades.assign(_period=periods).groupby("_period", sort=True):
        rows.append({"portfolio_id": part.portfolio_id.iloc[0], label: period,
                     **performance(part.weighted_R, part.holding_hours)})
    return pd.DataFrame(rows)
