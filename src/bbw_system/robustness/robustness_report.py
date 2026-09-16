"""Markdown reporting and predeclared pass/fail policy for BBW robustness."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

MIN_TRADES = 30
MAX_TOP5_PROFIT_SHARE = 0.50
MIN_POSITIVE_NEIGHBOR_SHARE = 0.75
MIN_NEIGHBOR_MEDIAN_RATIO = 0.50


def _table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "(none)"
    def render(value: object) -> str:
        return f"{value:.6f}" if isinstance(value, float) else str(value)
    headings = [str(column) for column in frame.columns]
    lines = ["| " + " | ".join(headings) + " |",
             "| " + " | ".join("---" for _ in headings) + " |"]
    lines.extend("| " + " | ".join(render(value) for value in row) + " |"
                 for row in frame.itertuples(index=False, name=None))
    return "\n".join(lines)


def build_robustness_report(results: pd.DataFrame, trades: pd.DataFrame,
                            candidate_path: Path, candidate_hash: str,
                            train_start: pd.Timestamp, train_end: pd.Timestamp,
                            input_hashes: dict[str, str], results_hash: str) -> str:
    """Build a deterministic report including concentration and decision evidence."""
    work = trades.copy()
    work["entry_time"] = pd.to_datetime(work.get("entry_time"))
    work["exit_time"] = pd.to_datetime(work.get("exit_time"))
    work["year"] = work.entry_time.dt.year
    work["month"] = work.entry_time.dt.strftime("%Y-%m")
    yearly = work.groupby("year", sort=True).result_R.agg(["count", "sum", "mean"]).reset_index()
    monthly = work.groupby("month", sort=True).result_R.agg(["count", "sum", "mean"]).reset_index()
    directions = work.groupby("direction", sort=True).result_R.agg(["count", "sum", "mean"]).reset_index()
    positive = work.loc[work.result_R > 0, "result_R"]
    top5_share = float(positive.nlargest(5).sum() / positive.sum()) if positive.sum() > 0 else 1.0

    costs = results.loc[results.scenario_type == "cost_sensitivity"]
    neighbors = results.loc[results.scenario_type == "parameter_neighborhood"]
    c0_total = float(costs.loc[costs.scenario_id == "C0", "total_R"].iloc[0])
    positive_share = float((neighbors.total_R > 0).mean()) if len(neighbors) else 0.0
    median_ratio = float(neighbors.total_R.median() / c0_total) if c0_total > 0 else 0.0
    checks = {
        "sufficient trades": int(costs.iloc[0].trades) >= MIN_TRADES,
        "positive under C0/C0.5/C1": bool((costs.total_R > 0).all()),
        "stable neighbourhood": positive_share >= MIN_POSITIVE_NEIGHBOR_SHARE and median_ratio >= MIN_NEIGHBOR_MEDIAN_RATIO,
        "no critical top-5 concentration": top5_share <= MAX_TOP5_PROFIT_SHARE,
    }
    status = "ROBUSTNESS_PASS" if all(checks.values()) else "ROBUSTNESS_FAIL"
    checks_text = "\n".join(f"- {'PASS' if passed else 'FAIL'} — {name}" for name, passed in checks.items())
    hashes = "\n".join(f"- `{path}`: `{digest}`" for path, digest in sorted(input_hashes.items()))
    scenarios = "\n".join(f"- `{row.scenario_id}` — {row.scenario_type}: `{row.parameters}`"
                          for row in results.itertuples())
    distribution = costs.iloc[0]
    return f"""# BBW Candidate Baseline v1 Robustness Report

- Candidate source: `{candidate_path}` (Optimization R2; `RESEARCH_CANDIDATE`)
- Candidate SHA256: `{candidate_hash}`
- TRAIN period: {train_start.isoformat()} — {train_end.isoformat()}
- Results SHA256: `{results_hash}`
- Scope: deterministic TRAIN-only robustness; no optimization, promotion, Walk Forward, or TRUE OOS access.

## Input SHA256
{hashes}

## Checked scenarios
{scenarios}

## Cost sensitivity
{_table(costs[["scenario_id", "trades", "winrate", "mean_R", "PF", "total_R", "max_drawdown", "duration"]])}

## Parameter neighborhood stability
All 32 points in the predefined 2×2×2×2×2 design are reported without ranking or selection.

- Positive-result share: {positive_share:.6f}
- Median total-R / Candidate C0 total-R: {median_ratio:.6f}

{_table(neighbors[["scenario_id", "trades", "winrate", "mean_R", "PF", "total_R", "max_drawdown", "duration"]])}

## Concentration analysis

- Top-5 profitable-trade share of gross profits: {top5_share:.6f}

### Annual distribution
{_table(yearly)}

### Monthly distribution
{_table(monthly)}

### LONG/SHORT distribution
{_table(directions)}

## Trade distribution (Candidate C0)

- Trades: {int(distribution.trades)}
- Mean R: {float(distribution.mean_R):.6f}
- Median R: {(float(work.result_R.median()) if len(work) else 0.0):.6f}
- Win rate: {float(distribution.winrate):.6f}
- PF: {float(distribution.PF):.6f}
- Maximum drawdown: {float(distribution.max_drawdown):.6f}
- Mean duration (minutes): {float(distribution.duration):.6f}

## Classification
{checks_text}

Final status: **{status}**
"""
