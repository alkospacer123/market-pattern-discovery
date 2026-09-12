"""Trade and equity statistics expressed in net, cost-adjusted terms."""
from __future__ import annotations
import math
import pandas as pd


def calculate_metrics(trades: pd.DataFrame, equity: pd.DataFrame) -> dict[str, float | int | None]:
    pnl = trades["net_profit"] if not trades.empty else pd.Series(dtype=float)
    r = trades["profit_R"] if not trades.empty else pd.Series(dtype=float)
    gross_profit, gross_loss = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    pf = (float(gross_profit / gross_loss) if gross_loss else
          (None if gross_profit == 0 else math.inf))
    curve = equity["equity"] if not equity.empty else pd.Series(dtype=float)
    drawdown = curve - curve.cummax()
    return {"trades": int(len(trades)), "win_rate": float((pnl > 0).mean()) if len(pnl) else 0.0,
            "profit_factor": pf, "expectancy": float(pnl.mean()) if len(pnl) else 0.0,
            "average_R": float(r.mean()) if len(r) else 0.0,
            "max_drawdown": float(drawdown.min()) if len(drawdown) else 0.0,
            "net_profit": float(pnl.sum()),
            "long_trades": int((trades.get("direction", pd.Series(dtype=str)) == "LONG").sum()),
            "short_trades": int((trades.get("direction", pd.Series(dtype=str)) == "SHORT").sum())}
