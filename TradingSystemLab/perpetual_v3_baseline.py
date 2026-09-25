"""TradingSystemLab v3 perpetual Phase 1: frozen, development-only baseline."""
from __future__ import annotations

from dataclasses import asdict
import argparse, hashlib, json, shutil
from pathlib import Path
from typing import Any

import pandas as pd

from .core.backtester import Backtester
from .core.data_loader import DataLoader
from .core.portfolio import FixedRiskPortfolio
from .core.unified_metrics import finite, stats
from .optimization.experiment import stable_hash
from .optimization.phase32 import _normalize_backtester
from .strategies.trend.T2_Trend_Pullback import T2Parameters, T2TrendPullback
from .strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters

DATA_ROOT = Path("/workspace/market-pattern-data/forever")
OUTPUT_ROOT = Path("TradingSystemLab/results/perpetual_v3/baseline")
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
INSTRUMENTS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
TIMEFRAMES = ("M30", "H1")
STRATEGIES = ("T2", "T3")
RUNS = tuple((s, t, i) for s in STRATEGIES for t in TIMEFRAMES for i in INSTRUMENTS)
DEVELOPMENT_START = pd.Timestamp("2023-01-01", tz="Europe/Moscow")
TRUE_OOS_START = pd.Timestamp("2025-01-01", tz="Europe/Moscow")
FROZEN_TICK_SIZE = 0.001
COST_MODEL = {"name": "C1", "ticks_per_side": 1, "round_trip_ticks": 2,
              "additional_slippage_ticks": 0}
STRATEGY_FILES = {
    "T2": Path("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py"),
    "T3": Path("TradingSystemLab/strategies/trend/T3_MTF_Trend.py"),
}
STRATEGY_SHA256 = {
    "T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
    "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c",
}
BASELINE_PARAMETERS = {"T2": asdict(T2Parameters()), "T3": asdict(T3Parameters())}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_strategy_identity() -> None:
    for strategy, expected in STRATEGY_SHA256.items():
        actual = sha256(STRATEGY_FILES[strategy])
        if actual != expected:
            raise RuntimeError(f"{strategy}_STRATEGY_SHA256_MISMATCH: {actual}")


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def load_development(data_root: Path, instrument: str, timeframe: str):
    root = Path(data_root).resolve()
    if root != DATA_ROOT.resolve():
        raise ValueError("UNAPPROVED_MARKET_DATA_ROOT")
    source = root / instrument / f"{instrument}_{timeframe}.csv"
    if not source.is_file() or not source.stat().st_size:
        raise FileNotFoundError(source)
    frame = DataLoader(forbid_true_oos=True).load_csv_prefix(
        source, start=DEVELOPMENT_START, end_exclusive=TRUE_OOS_START)
    if frame.isna().any().any() or (frame[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise ValueError(f"{source}: invalid or missing positive OHLC")
    frame = DataLoader.close_index(frame, "30min" if timeframe == "M30" else "1h")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError(f"{source}: invalid timestamp ordering")
    if frame.index.max() >= TRUE_OOS_START:
        raise ValueError("TRUE_OOS_BARRIER_VIOLATION")
    return frame, source


def four_bar_context(execution: pd.DataFrame) -> pd.DataFrame:
    """Four completed non-overlapping bars, reset on each Moscow trading day."""
    return DataLoader.h4_from_h1(execution)


def execute(strategy: str, instrument: str, timeframe: str, frame: pd.DataFrame) -> pd.DataFrame:
    if strategy == "T2":
        trades = T2TrendPullback(T2Parameters()).run(frame, instrument, tick_size=FROZEN_TICK_SIZE)
        trades = trades.rename(columns={"net_R_C1": "net_R", "cost_R_C1": "cost_R"})
    else:
        context = four_bar_context(frame)
        if context is frame:
            raise RuntimeError("T3_EXECUTION_CONTEXT_ALIAS")
        raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=1,
                         tick_size=FROZEN_TICK_SIZE).run(
            T3MTFTrend(T3Parameters()), instrument, frame, context).trades
        trades = _normalize_backtester(raw, strategy)
        trades["net_R"] = trades["gross_R"] - trades["cost_R"]
    trades = trades.copy()
    if len(trades):
        for column in ("entry_time", "exit_time"):
            if (pd.to_datetime(trades[column], utc=True) >= TRUE_OOS_START.tz_convert("UTC")).any():
                raise ValueError("TRUE_OOS_TRADE_VIOLATION")
        trades["trade_id"] = [f"{strategy}-{timeframe}-{instrument}-{n:06d}" for n in range(1, len(trades)+1)]
        trades = trades.sort_values(["exit_time", "trade_id"], kind="mergesort")
    return trades.reset_index(drop=True)


def metrics(trades: pd.DataFrame) -> dict[str, Any]:
    result = stats(trades.net_R.astype(float) if len(trades) else pd.Series(dtype=float))
    return {"trades": result["trades"], "PF": result["PF_R"], "expectancy_R": result["expectancy"],
            "net_R": result["net_R"], "max_drawdown_R": result["max_DD_R"],
            "recovery_factor": result["recovery_factor"], "win_rate": result["winrate"]}


def report_rows(trades: pd.DataFrame, groups: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    return pd.DataFrame([{**{"group": name}, **metrics(part)} for name, part in groups])


def write_run(target: Path, strategy: str, timeframe: str, instrument: str,
              frame: pd.DataFrame, source: Path, trades: pd.DataFrame) -> dict[str, Any]:
    target.mkdir(parents=True)
    m = metrics(trades)
    trades.map(finite).to_csv(target / "trades.csv", index=False, lineterminator="\n", float_format="%.12g", na_rep="")
    _json(target / "metrics.json", m)
    directions = report_rows(trades, [(d, trades[trades.direction == d]) for d in ("LONG", "SHORT")]).rename(columns={"group": "direction"})
    directions.to_csv(target / "direction_report.csv", index=False, float_format="%.12g")
    report_rows(trades, [(instrument, trades)]).rename(columns={"group": "instrument"}).to_csv(
        target / "instrument_report.csv", index=False, float_format="%.12g")
    first_month = frame.index.min().to_period("M")
    last_month = frame.index.max().to_period("M")
    month_rows = []
    exits = pd.to_datetime(trades.exit_time, utc=True).dt.tz_convert("Europe/Moscow") if len(trades) else pd.Series(dtype="datetime64[ns, Europe/Moscow]")
    for period in pd.period_range(first_month, last_month, freq="M"):
        part = trades[(exits.dt.year == period.year) & (exits.dt.month == period.month)] if len(trades) else trades
        month_rows.append({"year": period.year, "month": period.month, **metrics(part)})
    pd.DataFrame(month_rows).to_csv(target / "monthly_returns.csv", index=False, float_format="%.12g")
    year_rows = []
    for year in range(frame.index.min().year, frame.index.max().year + 1):
        part = trades[exits.dt.year == year] if len(trades) else trades
        year_rows.append({"year": year, **metrics(part)})
    pd.DataFrame(year_rows).to_csv(target / "yearly_report.csv", index=False, float_format="%.12g")
    parameter_hash = stable_hash(BASELINE_PARAMETERS[strategy])
    manifest = {
        "generation": "v3_perpetual", "phase": "PHASE_1_BASELINE", "strategy": strategy,
        "strategy_id": strategy, "strategy_source_sha256": STRATEGY_SHA256[strategy],
        "timeframe": timeframe, "instrument": instrument,
        "baseline_parameters": BASELINE_PARAMETERS[strategy], "baseline_parameter_hash": parameter_hash,
        "data_repository": "alkospacer123/market-pattern-data", "data_commit": DATA_COMMIT,
        "source_file": f"forever/{instrument}/{instrument}_{timeframe}.csv", "source_sha256": sha256(source),
        "timezone": "Europe/Moscow; input wall-clock localized without UTC shift; index labels are bar closes",
        "declared_development_start": "2023-01-01", "declared_development_end": "2024-12-31",
        "actual_first_bar": frame.index.min().isoformat(), "actual_last_bar": frame.index.max().isoformat(),
        "bar_count": len(frame), "true_oos_start": "2025-01-01", "true_oos_status": "BLOCKED_NOT_READ_NOT_EXECUTED",
        "cost_model": "C1", "cost_ticks_per_side": 1, "FROZEN_TICK_SIZE": FROZEN_TICK_SIZE,
        "optimization": False, "ranking": False, "selection": False, "portfolio": False, "mtf": False,
    }
    if strategy == "T3":
        manifest["causal_context"] = {"execution_bars_per_context_bar": 4, "completed_only": True,
            "non_overlapping": True, "reset_at_local_day": True, "incomplete_blocks_published": False,
            "timestamp": "fourth_execution_bar_close", "separate_dataframe": True, "future_fill": False}
    _json(target / "manifest.json", manifest)
    (target / "Baseline_Report.md").write_text(
        f"# v3 perpetual Phase 1 Baseline — {strategy} / {timeframe} / {instrument}\n\n"
        f"Development: 2023-01-01 through 2024-12-31; actual coverage: {frame.index.min().isoformat()} through {frame.index.max().isoformat()} ({len(frame)} bars).\n\n"
        f"Source: `{manifest['source_file']}` at data commit `{DATA_COMMIT}`. Strategy SHA-256: `{STRATEGY_SHA256[strategy]}`. Baseline parameter hash: `{parameter_hash}`.\n\n"
        f"C1 only; FROZEN_TICK_SIZE = 0.001. TRUE OOS >= 2025-01-01 is BLOCKED / NOT READ / NOT EXECUTED. No optimization, ranking, or selection.\n\n"
        f"Results: trades={m['trades']}, PF={m['PF']}, expectancy_R={m['expectancy_R']}, net_R={m['net_R']}, max_drawdown_R={m['max_drawdown_R']}, recovery_factor={m['recovery_factor']}, win_rate={m['win_rate']}.\n",
        encoding="utf-8")
    direction = directions.set_index("direction")
    return {"strategy": strategy, "timeframe": timeframe, "instrument": instrument,
            "actual_start": frame.index.min().isoformat(), "actual_end": frame.index.max().isoformat(),
            "bars": len(frame), **m,
            **{f"{d}_{k}": direction.loc[d, k] for d in ("LONG", "SHORT") for k in ("trades", "PF", "expectancy_R", "net_R")}}


def run(data_root: Path = DATA_ROOT, output: Path = OUTPUT_ROOT) -> dict[str, Any]:
    verify_strategy_identity()
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    cache, rows = {}, []
    for strategy, timeframe, instrument in RUNS:
        key = instrument, timeframe
        if key not in cache: cache[key] = load_development(data_root, instrument, timeframe)
        frame, source = cache[key]
        rows.append(write_run(output / strategy / timeframe / instrument, strategy, timeframe,
                              instrument, frame, source, execute(strategy, instrument, timeframe, frame)))
    summary = output / "summary"; summary.mkdir()
    matrix = pd.DataFrame(rows)
    matrix.to_csv(summary / "baseline_matrix.csv", index=False, float_format="%.12g")
    matrix[["timeframe", "instrument", "actual_start", "actual_end", "bars"]].drop_duplicates().to_csv(summary / "data_coverage.csv", index=False)
    monthly, yearly = [], []
    for s, t, i in RUNS:
        root = output / s / t / i
        for name, sink in (("monthly_returns.csv", monthly), ("yearly_report.csv", yearly)):
            x = pd.read_csv(root / name); x.insert(0, "instrument", i); x.insert(0, "timeframe", t); x.insert(0, "strategy", s); sink.append(x)
    pd.concat(monthly).to_csv(summary / "monthly_matrix.csv", index=False, float_format="%.12g")
    pd.concat(yearly).to_csv(summary / "yearly_matrix.csv", index=False, float_format="%.12g")
    _json(summary / "manifest.json", {"generation": "v3_perpetual", "phase": "PHASE_1_BASELINE",
        "run_count": 16, "runs": [{"strategy": s, "timeframe": t, "instrument": i} for s,t,i in RUNS],
        "data_commit": DATA_COMMIT, "true_oos_status": "BLOCKED_NOT_READ_NOT_EXECUTED",
        "optimization": False, "ranking": False, "selection": False, "portfolio": False, "mtf": False,
        "status": "V3_PERPETUAL_PHASE_1_BASELINE_COMPLETE"})
    lines = ["# TradingSystemLab — v3 Perpetual Phase 1 Baseline", "", "**V3_PERPETUAL_PHASE_1_BASELINE_COMPLETE**", "",
             "16 frozen C1 baseline runs. TRUE OOS >=2025 is blocked; no optimization, ranking, selection, portfolio, or MTF research.", "",
             "```csv", matrix.to_csv(index=False, float_format="%.12g").rstrip(), "```"]
    (summary / "Phase_1_Baseline_Report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"status": "V3_PERPETUAL_PHASE_1_BASELINE_COMPLETE", "runs": 16}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--data-root", type=Path, default=DATA_ROOT); parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(); print(json.dumps(run(args.data_root, args.output), sort_keys=True))


if __name__ == "__main__": main()
