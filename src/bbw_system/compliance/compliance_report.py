"""Markdown rendering for the BBW Strategy Compliance Audit v1."""
from __future__ import annotations

from typing import Any


def _status(value: bool | None) -> str:
    return "UNKNOWN" if value is None else ("PASS" if value else "FAIL")


def _table(rows: list[tuple[object, ...]], headings: tuple[str, ...]) -> str:
    lines = ["| " + " | ".join(headings) + " |", "| " + " | ".join("---" for _ in headings) + " |"]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def build_compliance_report(audit: dict[str, Any]) -> str:
    """Render only facts collected by the audit (no trading decisions)."""
    hashes = "\n".join(f"- `{path}`: `{digest}`" for path, digest in sorted(audit["input_hashes"].items()))
    features = _table(audit["feature_rows"], ("Item", "Expected", "Actual", "Status"))
    exits = _table(audit["exit_rows"], ("Mechanism", "Expected", "Actual", "Status"))
    metrics = audit["metrics"]
    findings = "\n".join(f"- **{level}** — {message}" for level, message in audit["findings"])
    return f"""# BBW Strategy Compliance Audit v1

## Scope

- TRAIN period: {audit['train_start']} — {audit['train_end']}
- Instrument: `{audit['symbol']}`
- Mode: read-only diagnostic audit; no strategy parameter or input is modified.
- Files and SHA256:
{hashes}

# 1. Data Compliance

- H1 source: `{audit['h1_path']}`
- M15 source: `{audit['m15_path']}`
- Timestamp semantics: `{audit['timestamp_semantics']}` (candle open / START label)
- Ordered, unique timestamps: {_status(audit['timestamps_valid'])}
- TRUE OOS 2025 absent: {_status(audit['oos_absent'])}
- No observations at or after 2025-01-01: {_status(audit['train_only'])}

Status: **{_status(audit['data_compliance'])}**

# 2. BBW Feature Compliance

{features}

The candidate layer recalculates BBW, squeeze and EMA, while retaining the causal `atr14` column from the feature input. Range detection is performed later by the baseline routines.

Status: **{_status(audit['feature_compliance'])}**

# 3. Entry Logic Compliance

## Breakout

- Actual behavior: the H1 breakout bar is excluded from the range; its close must cross the range and agree with `trend_direction`. A START-labelled H1 bar is exposed one hour later.
- Look-ahead check: {_status(audit['causal_entry'])}.

## Retest

- Actual behavior: native M15, bars {audit['candidate']['retest_min_bars']} through {audit['candidate']['retest_max_bars']} inclusive; touch plus a close back beyond the frozen level; excessive penetration or a close inside cancels the setup.

## Entry price

- Expected by BBW CORE v1: next M15 bar open after confirmation.
- Actual behavior: confirmation M15 close, timestamped at that candle's close.

Status: **FAIL**

# 4. Exit Logic Compliance

{exits}

**Actual exit mechanism:** independent trades scan every later M15 bar until static structural STOP, TP3, or end of the complete dataset. Targets realize 50% at +1R, 30% at +2R, and 20% at +3R. The stop is checked first, but never advanced after a target. Open residual size is marked at the final M15 close and labelled `END_OF_DATA`. No time/session exit or portfolio-position reservation is applied.

Status: **FAIL**

# 5. Trade Simulation and Metric Compliance

- Trades replayed: {metrics['trades']}
- LONG / SHORT: {metrics['long']} / {metrics['short']}
- Win rate: {metrics['win_rate']:.6f}%
- Mean R: {metrics['mean_r']:.6f}
- Mean duration: {metrics['mean_duration_minutes']:.6f} minutes
- Median / maximum duration: {metrics['median_duration_minutes']:.6f} / {metrics['max_duration_minutes']:.6f} minutes
- `END_OF_DATA` exits: {metrics['end_of_data']} ({metrics['end_of_data_share']:.6f}%)
- Negative durations: {metrics['negative_durations']}
- Non-positive initial risks: {metrics['invalid_risks']}
- Independently replayed `result_R` mismatches: {metrics['r_mismatches']}
- Independently recomputed duration mismatches: {metrics['duration_mismatches']}

The duration formula itself is minutes (`(exit_time-entry_time).total_seconds()/60`). Extremely large values therefore reflect positions held until the dataset end, not a seconds/minutes conversion error. `result_R` is arithmetically consistent with the implemented static-stop partial-exit ledger, but that ledger is not compliant with the frozen BBW CORE stop-progression rules.

Status: **{_status(audit['metric_compliance'])}**

# 6. Findings and Root Cause

{findings}

# 7. Final Classification

Final status: **{audit['final_status']}**

This is a compliance classification, not an optimization or strategy-selection result. Candidate parameters and all source artifacts remain unchanged.
"""
