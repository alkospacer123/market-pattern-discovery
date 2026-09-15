"""Markdown reporting for controlled BBW parameter sensitivity."""
from __future__ import annotations

import json
from typing import Any

import pandas as pd


def _metric(metrics: dict[str, Any], key: str) -> str:
    value = float(metrics[key])
    return "inf" if value == float("inf") else f"{value:.6f}"


def build_report(results: pd.DataFrame, baseline: dict[str, Any], digest: str,
                 transaction_cost_r: float, slippage_r: float) -> str:
    """Describe viable regions rather than declaring a single winning point."""
    viable = results.loc[(results.trades >= 20) & (results.mean_R > 0) &
                         (results.profit_factor > 1.2)].copy()
    # Drawdown is explicitly constrained to the better half of otherwise viable
    # candidates; this is selection for stability, not maximization of trades/PF.
    if not viable.empty:
        viable = viable.loc[viable.max_drawdown <= viable.max_drawdown.median()]
    parsed = [json.loads(value) for value in viable.parameters_json]
    def region(key: str) -> str:
        values = sorted({item[key] for item in parsed})
        return "none" if not values else f"{values[0]:g}-{values[-1]:g}"
    aggregate = {
        "trades": float(viable.trades.median()) if len(viable) else 0,
        "profit_factor": float(viable.profit_factor.replace(float("inf"), pd.NA).dropna().median()) if len(viable) else 0,
        "mean_R": float(viable.mean_R.median()) if len(viable) else 0,
    }
    conclusion = "PARAMETERS_STABLE" if len(viable) >= 3 else "PARAMETERS_NOT_STABLE"
    return "\n".join([
        "# BBW Controlled Optimization Report", "",
        "**Scope:** deterministic TRAIN-only parameter sensitivity; the frozen Baseline is unchanged.", "",
        f"- Tested combinations: {len(results)}", f"- Stable candidate count: {len(viable)}",
        f"- Results SHA-256: `{digest}`",
        f"- Per-trade transaction cost: {transaction_cost_r:g} R",
        f"- Per-trade slippage: {slippage_r:g} R", "",
        "## Stable parameter regions", "",
        "Regions include candidates with at least 20 trades, positive mean R, PF above 1.2, and drawdown no worse than the median of qualifying candidates.", "",
        f"- BBW period: {region('bbw_period')}", f"- EMA period: {region('ema_period')}",
        f"- ATR minimum: {region('atr_min')}", f"- ATR maximum: {region('atr_max')}",
        f"- Range minimum bars: {region('range_min_bars')}", f"- Range maximum bars: {region('range_max_bars')}",
        "", "## Baseline comparison", "",
        f"- Baseline: trades={int(baseline['trades'])}, PF={_metric(baseline, 'profit_factor')}, mean R={_metric(baseline, 'mean_R')}",
        f"- Optimization region (median): trades={aggregate['trades']:.0f}, PF={aggregate['profit_factor']:.6f}, mean R={aggregate['mean_R']:.6f}",
        "", "## Conclusion", "", conclusion, "",
        "This report does not update strategy parameters. Robustness and Walk Forward have not been performed; no result is promoted automatically.", "",
    ])
