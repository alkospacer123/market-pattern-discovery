"""Independent, fail-closed audit of v3 perpetual Phase 1 artifacts."""
from __future__ import annotations

import argparse, json
from pathlib import Path
import pandas as pd

from .core.unified_metrics import stats
from .perpetual_v3_baseline import (BASELINE_PARAMETERS, DATA_COMMIT, DATA_ROOT,
    FROZEN_TICK_SIZE, INSTRUMENTS, RUNS, STRATEGIES, STRATEGY_SHA256, TIMEFRAMES,
    four_bar_context, load_development, sha256, STRATEGY_FILES)


def require(condition: bool, message: str) -> None:
    if not condition: raise AssertionError(message)


def audit(root: Path) -> dict:
    root = Path(root); matrix = pd.read_csv(root / "summary/baseline_matrix.csv")
    require(len(matrix) == 16, "run count")
    require(set(matrix.instrument) == set(INSTRUMENTS), "universe")
    require(set(matrix.timeframe) == set(TIMEFRAMES), "timeframes")
    require(set(matrix.strategy) == set(STRATEGIES), "strategies")
    require(set(map(tuple, matrix[["strategy", "timeframe", "instrument"]].itertuples(index=False, name=None))) == set(RUNS), "matrix")
    require(BASELINE_PARAMETERS["T2"]["max_initial_stop_atr"] == 3.0, "T2 baseline")
    require(BASELINE_PARAMETERS["T3"]["ema_period"] == 100, "T3 baseline")
    for strategy in STRATEGIES:
        require(sha256(STRATEGY_FILES[strategy]) == STRATEGY_SHA256[strategy], "strategy hash")
    for strategy, timeframe, instrument in RUNS:
        run = root / strategy / timeframe / instrument
        required = {"trades.csv", "metrics.json", "direction_report.csv", "instrument_report.csv",
                    "monthly_returns.csv", "yearly_report.csv", "Baseline_Report.md", "manifest.json"}
        require(required <= {p.name for p in run.iterdir()}, "missing artifact")
        manifest = json.loads((run / "manifest.json").read_text())
        require(manifest["data_commit"] == DATA_COMMIT and manifest["cost_model"] == "C1", "provenance/cost")
        require(manifest["FROZEN_TICK_SIZE"] == FROZEN_TICK_SIZE and manifest["cost_ticks_per_side"] == 1, "cost units")
        require(manifest["declared_development_start"] == "2023-01-01" and manifest["declared_development_end"] == "2024-12-31", "development")
        require(manifest["true_oos_status"] == "BLOCKED_NOT_READ_NOT_EXECUTED", "TRUE OOS")
        require(not any(manifest[x] for x in ("optimization", "ranking", "selection", "portfolio", "mtf")), "prohibited activity")
        frame, source = load_development(DATA_ROOT, instrument, timeframe)
        require(manifest["source_sha256"] == sha256(source), "source hash")
        require(manifest["bar_count"] == len(frame) and manifest["actual_first_bar"] == frame.index.min().isoformat(), "coverage")
        if instrument in ("GLDRUBF", "IMOEXF"): require(frame.index.min().year == 2023 and frame.index.min() > pd.Timestamp("2023-01-01", tz="Europe/Moscow"), "natural late start")
        if strategy == "T3":
            context = four_bar_context(frame)
            require(context is not frame and len(context), "separate context")
            expected = sum(len(day) // 4 for _, day in frame.groupby(frame.index.normalize()))
            require(len(context) == expected, "context grouping")
            require(manifest["causal_context"]["execution_bars_per_context_bar"] == 4, "causal context manifest")
        trades = pd.read_csv(run / "trades.csv")
        if len(trades): require(pd.to_datetime(trades.exit_time, utc=True).max() < pd.Timestamp("2025-01-01", tz="UTC"), "OOS trade")
        values = trades.net_R.astype(float) if len(trades) else pd.Series(dtype=float); calc = stats(values)
        saved = json.loads((run / "metrics.json").read_text())
        require(saved["trades"] == len(trades) and abs(saved["net_R"] - calc["net_R"]) < 1e-9, "metrics reconciliation")
        direction = pd.read_csv(run / "direction_report.csv")
        require(int(direction.trades.sum()) == len(trades), "direction reconciliation")
        instrument_report = pd.read_csv(run / "instrument_report.csv")
        require(int(instrument_report.trades.sum()) == len(trades), "instrument reconciliation")
        monthly = pd.read_csv(run / "monthly_returns.csv")
        expected_months = len(pd.period_range(frame.index.min().to_period("M"), frame.index.max().to_period("M"), freq="M"))
        require(len(monthly) == expected_months and int(monthly.trades.sum()) == len(trades), "monthly reconciliation")
        yearly = pd.read_csv(run / "yearly_report.csv")
        require(int(yearly.trades.sum()) == len(trades), "yearly reconciliation")
    summary = json.loads((root / "summary/manifest.json").read_text())
    require(summary["status"] == "V3_PERPETUAL_PHASE_1_BASELINE_COMPLETE", "status")
    return {"verdict": "PASS", "runs": 16, "checks": 31}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path("TradingSystemLab/results/perpetual_v3/baseline")); args = parser.parse_args()
    print(json.dumps(audit(args.root), sort_keys=True))


if __name__ == "__main__": main()
