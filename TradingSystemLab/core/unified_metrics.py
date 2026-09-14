"""Deterministic, strategy-agnostic R diagnostics for the unified audit."""
from __future__ import annotations

import math
import numpy as np
import pandas as pd


def profit_factor(values: pd.Series) -> float | None:
    values = pd.Series(values, dtype=float)
    gains, losses = values[values > 0].sum(), -values[values < 0].sum()
    return float(gains / losses) if losses else None


def max_drawdown(values: pd.Series) -> float:
    curve = pd.concat([pd.Series([0.0]), pd.Series(values, dtype=float).reset_index(drop=True).cumsum()])
    return float((curve - curve.cummax()).min())


def streaks(values: pd.Series) -> tuple[int, int]:
    best_win = best_loss = win = loss = 0
    for value in values:
        win, loss = (win + 1, 0) if value > 0 else ((0, loss + 1) if value < 0 else (0, 0))
        best_win, best_loss = max(best_win, win), max(best_loss, loss)
    return best_win, best_loss


def stats(values: pd.Series) -> dict:
    values = pd.Series(values, dtype=float)
    dd = max_drawdown(values)
    net = float(values.sum())
    winners, losers = values[values > 0], values[values < 0]
    aw = float(winners.mean()) if len(winners) else None
    al = float(losers.mean()) if len(losers) else None
    ws, ls = streaks(values)
    return {"trades": len(values), "PF_R": profit_factor(values),
            "expectancy": float(values.mean()) if len(values) else None, "net_R": net,
            "average_R": float(values.mean()) if len(values) else None,
            "median_R": float(values.median()) if len(values) else None,
            "winrate": float((values > 0).mean()) if len(values) else None,
            "average_win_R": aw, "average_loss_R": al,
            "payoff_ratio": aw / abs(al) if aw is not None and al not in (None, 0) else None,
            "max_DD_R": dd, "recovery_factor": net / abs(dd) if dd else None,
            "max_winning_streak": ws, "max_losing_streak": ls}


def concentration(values: pd.Series) -> dict:
    values = pd.Series(values, dtype=float)
    positive = values[values > 0].sort_values(ascending=False)
    denominator = float(positive.sum())
    result = {f"top_{n}_positive_R_share": (float(positive.head(n).sum()/denominator) if denominator else None)
              for n in (1, 3, 5, 10)}
    for n, label in ((1, "best_trade"), (3, "top3"), (5, "top5")):
        remaining = values.drop(positive.head(n).index)
        s = stats(remaining)
        result.update({f"net_R_without_{label}": s["net_R"],
                       f"PF_R_C1_without_{label}": s["PF_R"],
                       f"expectancy_C1_without_{label}": s["expectancy"]})
    return result


def break_even_round_trip_ticks(gross_r: pd.Series, initial_risk_ticks: pd.Series) -> float | None:
    """Solve sum(gross_R - ticks/risk_ticks)=0 for round-trip ticks."""
    gross = float(pd.Series(gross_r, dtype=float).sum())
    if gross <= 0:
        return None
    reciprocal_risk = float((1.0 / pd.Series(initial_risk_ticks, dtype=float)).sum())
    return gross / reciprocal_risk if reciprocal_risk else None


def quantiles(values: pd.Series, prefix: str = "R") -> dict:
    s = pd.Series(values, dtype=float)
    return {f"{prefix}_{name}": (float(s.quantile(q)) if len(s) else None)
            for name, q in (("p05", .05), ("p10", .1), ("p25", .25), ("median", .5),
                            ("p75", .75), ("p90", .9), ("p95", .95))}


def finite(value):
    return None if value is None or (isinstance(value, float) and not math.isfinite(value)) else value
