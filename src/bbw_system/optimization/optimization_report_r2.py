"""Deterministic report for the BBW Optimization R2 experiment."""
from __future__ import annotations

import json
from typing import Any

import pandas as pd

PARAMETERS = (
    "bbw_period", "bbw_std", "squeeze_window", "ema_period",
    "ema_slope_threshold", "atr_min", "atr_max", "range_min_bars",
    "range_max_bars", "retest_min_bars", "retest_max_bars", "penetration",
)
ORDERED_VALUES = {
    "bbw_period": (10, 15, 20), "bbw_std": (1.5, 2.0), "squeeze_window": (5, 10),
    "ema_period": (20, 30, 50), "ema_slope_threshold": (0.0, 0.0005, 0.001),
    "atr_min": (0.5, 0.75, 1.0), "atr_max": (2.0, 3.0),
    "range_min_bars": (3, 4, 5, 6), "range_max_bars": (20, 30, 40),
    "retest_min_bars": (3, 5), "retest_max_bars": (30, 40, 50),
    "penetration": (0.1, 0.2),
}


def _number(value: Any) -> str:
    value = float(value)
    return "inf" if value == float("inf") else f"{value:.6f}"


def _metrics(row: pd.Series | dict[str, Any]) -> str:
    return (f"trades={int(row['trades'])}, winrate={_number(row['winrate'])}, "
            f"mean R={_number(row['mean_R'])}, PF={_number(row['profit_factor'])}, "
            f"total R={_number(row['total_R'])}, max drawdown={_number(row['max_drawdown'])}")


def _stable_candidates(results: pd.DataFrame) -> pd.DataFrame:
    """Require a viable point to have a similar, one-coordinate neighbour."""
    viable = results.loc[(results.trades >= 20) & (results.mean_R > 0) &
                         (results.profit_factor > 1.2) & (results.max_drawdown <= 10)].copy()
    if viable.empty:
        return viable
    params = {index: json.loads(row.parameters_json) for index, row in viable.iterrows()}
    stable: set[int] = set()
    for left_pos, (left_index, left) in enumerate(viable.iterrows()):
        for right_index, right in list(viable.iterrows())[left_pos + 1:]:
            changed = [key for key in PARAMETERS
                       if params[left_index][key] != params[right_index][key]]
            adjacent = len(changed) == 1 and abs(
                ORDERED_VALUES[changed[0]].index(params[left_index][changed[0]]) -
                ORDERED_VALUES[changed[0]].index(params[right_index][changed[0]])
            ) == 1
            similar = (abs(int(left.trades) - int(right.trades)) <= max(left.trades, right.trades) * .25 and
                       abs(float(left.mean_R) - float(right.mean_R)) <= .25 and
                       abs(float(left.profit_factor) - float(right.profit_factor)) <= .5)
            if adjacent and similar:
                stable.update((left_index, right_index))
    return viable.loc[sorted(stable)]


def build_r2_report(results: pd.DataFrame, baseline: dict[str, Any], digest: str,
                    transaction_cost_r: float, slippage_r: float) -> str:
    stable = _stable_candidates(results)
    best = results.sort_values(["total_R", "max_drawdown", "parameter_id"],
                               ascending=[False, True, True]).iloc[0]
    parsed = [json.loads(value) for value in stable.parameters_json]
    region_lines = []
    for key in PARAMETERS:
        values = sorted({item[key] for item in parsed})
        region_lines.append(f"- {key}: " + (", ".join(f"{value:g}" for value in values) if values else "none"))
    conclusion = "PARAMETERS_STABLE" if len(stable) >= 3 else "PARAMETERS_NOT_STABLE"
    return "\n".join([
        "# BBW Optimization R2 Report", "",
        "**Scope:** controlled TRAIN-only research (2023-01-03 through 2024-12-31).", "",
        f"- Tested combinations: {len(results)}", f"- Results SHA-256: `{digest}`",
        f"- Transaction cost: {transaction_cost_r:g} R", f"- Slippage: {slippage_r:g} R", "",
        "## Frozen Baseline", "", f"- Parameters: `{baseline['parameters_json']}`",
        f"- Metrics: {_metrics(baseline)}", "", "## Best observed result", "",
        f"- Parameters: `{best.parameters_json}`", f"- Metrics: {_metrics(best)}", "",
        "## Stable region", "",
        "Eligibility requires trades >= 20, mean R > 0, PF > 1.2, max drawdown <= 10 R, and a one-parameter neighbour with trades within 25%, mean R within 0.25, and PF within 0.5.", "",
        f"- Stable combinations: {len(stable)}", *region_lines, "",
        "## R1 vs R2", "", "- R1: 256 combinations; PARAMETERS_NOT_STABLE; Baseline had 1 trade.",
        f"- R2: {len(results)} combinations; {conclusion}; stable combinations={len(stable)}.", "",
        "## Conclusion", "", conclusion, "",
        "Baseline was too restrictive only if R2 produced a stable region with adequate trade count; the status above is the controlled answer.", "",
        "R2 is research only. Baseline was not changed, candidates are not applied automatically, and Robustness and Walk Forward were not performed.", "",
    ])
