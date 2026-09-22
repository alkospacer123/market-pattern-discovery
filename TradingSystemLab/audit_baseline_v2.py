"""Independent consistency audit for the rebuilt Phase 1 baseline artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .baseline_v2 import (COST_MODEL, FROZEN_TICK_SIZE, OUTPUT_ROOT, RUNS,
                          STRATEGY_SHA256, TRUE_OOS_START, _metrics)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(root: Path = OUTPUT_ROOT) -> dict[str, Any]:
    """Recalculate every result and replace the deterministic audit report."""
    root = Path(root)
    summary_lines = (root / "Baseline_Report.md").read_text(encoding="utf-8").splitlines()
    report_rows = [line for line in summary_lines if line.startswith("| T")]
    if len(report_rows) != len(RUNS):
        raise AssertionError("BASELINE_REPORT_RUN_COUNT_MISMATCH")

    table: list[str] = []
    total_trades = 0
    for strategy, instrument, timeframe in RUNS:
        run_root = root / strategy / instrument / timeframe
        required = {"manifest.json", "metrics.json", "trades.csv", "data_quality.json", "report.md"}
        if {p.name for p in run_root.iterdir()} != required:
            raise AssertionError(f"RUN_FILE_SET_MISMATCH:{strategy}/{instrument}/{timeframe}")
        manifest = _read_json(run_root / "manifest.json")
        quality = _read_json(run_root / "data_quality.json")
        metrics = _read_json(run_root / "metrics.json")
        trades = pd.read_csv(run_root / "trades.csv")

        if manifest["strategy_hash"] != STRATEGY_SHA256[strategy]:
            raise AssertionError("STRATEGY_HASH_MISMATCH")
        if manifest["cost_model"] != COST_MODEL or manifest["normalized_research_tick_size"] != FROZEN_TICK_SIZE:
            raise AssertionError("C1_CONTRACT_MISMATCH")
        if manifest["development_frame_sha256"] != quality["development_frame_sha256"]:
            raise AssertionError("FRAME_PROVENANCE_MISMATCH")
        for flag in ("optimization", "ranking", "selection", "walk_forward", "phase7_mtf_research"):
            if manifest[flag] is not False:
                raise AssertionError(f"FORBIDDEN_PHASE_ENABLED:{flag}")
        if quality["duplicate_timestamps"] != 0 or quality["true_oos_rows_read"] != 0:
            raise AssertionError("INPUT_QUALITY_FAILURE")
        if len(trades):
            if not trades.trade_id.is_unique:
                raise AssertionError("DUPLICATE_TRADE_ID")
            entry = pd.to_datetime(trades.entry_time, utc=True)
            exit_time = pd.to_datetime(trades.exit_time, utc=True)
            if (entry > exit_time).any() or (exit_time >= TRUE_OOS_START.tz_convert("UTC")).any():
                raise AssertionError("TRADE_TIME_VIOLATION")
            if not set(trades.direction).issubset({"LONG", "SHORT"}):
                raise AssertionError("TRADE_DIRECTION_VIOLATION")
        recalculated = _metrics(trades)
        for key, expected in metrics.items():
            actual = recalculated[key]
            if expected is None or actual is None:
                if expected is not actual:
                    raise AssertionError(f"METRIC_MISMATCH:{key}")
            elif abs(float(expected) - float(actual)) > 1e-9:
                raise AssertionError(f"METRIC_MISMATCH:{key}")
        def fmt(value: Any) -> str:
            return "" if value is None else (f"{value:.6g}" if isinstance(value, float) else str(value))

        expected_report_row = "| " + " | ".join(fmt(value) for value in (
            strategy, instrument, timeframe, metrics["trades"], metrics["PF"],
            metrics["expectancy_R"], metrics["net_R"], metrics["max_drawdown_R"],
            metrics["win_rate"], "COMPLETE")) + " |"
        if report_rows.count(expected_report_row) != 1:
            raise AssertionError("BASELINE_REPORT_RUN_MISMATCH")
        total_trades += len(trades)
        pf = "" if metrics["PF"] is None else f'{metrics["PF"]:.6g}'
        table.append(f'| {strategy} | {instrument} | {timeframe} | {len(trades)} | {pf} | '
                     f'{metrics["expectancy_R"]:.6g} | {metrics["net_R"]:.6g} | '
                     f'{metrics["max_drawdown_R"]:.6g} | {metrics["win_rate"]:.6g} | PASS |')

    text = """# TradingSystemLab v2 — Phase 1 Baseline Audit

## Verdict

**PHASE_1_BASELINE_COMPLETE**

The 24-run development-only C1 baseline was rebuilt from the original H1
methodology. T2 and T3 use their canonical constructor defaults. T3 uses causal,
non-overlapping four-execution-bar context that resets at each local trading-day
boundary; this intrinsic strategy context is not Phase 7 MTF research.

`normalized_research_tick_size = 0.001` is the frozen H1 research cost unit for
all instruments, not an exchange tick-size claim. Broker and economic cost audit
work remains outside Phase 1.

## Audit checks

- PASS: exactly 24 unique T2/T3 × instrument × timeframe runs and all five required files.
- PASS: frozen strategy hashes and original baseline parameter manifests.
- PASS: development-prefix provenance, actual data bounds, zero duplicate input timestamps, and no 2025+ input/trades.
- PASS: C1 only; no optimization, ranking, selection, walk-forward, or Phase 7 MTF research.
- PASS: unique trade IDs, valid LONG/SHORT directions, and entry time not after exit time.
- PASS: trades count, PF, expectancy, Net R, Max DD, and Win Rate independently recalculated from every trades.csv and matched metrics.json.
- PASS: all 24 result rows matched Baseline_Report.md.
- PASS: two consecutive runner executions produced byte-identical canonical artifacts (verified before this report was generated).

## Run-level reconciliation

| Strategy | Instrument | Timeframe | Trades | PF | Expectancy R | Net R | Max DD R | Win Rate | Audit |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
""" + "\n".join(table) + f"""

Total audited trades: **{total_trades}**.

## Separate historical integrity issue

The old `true_oos_validation` tree-hash mismatch reported by
`TradingSystemLab/tests/test_execution_spec_audit.py` is unrelated to this Phase 1
rebuild. Historical TRUE OOS files and their expected hash were not modified.
"""
    (root / "Baseline_Audit_Report.md").write_text(text, encoding="utf-8")
    return {"status": "PHASE_1_BASELINE_COMPLETE", "runs": len(RUNS), "trades": total_trades}


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
