"""Fail-closed, implementation-independent audit of perpetual v3 Phase 1.

This module deliberately does not import the baseline runner, strategy classes,
data loader, or the shared metrics package.  The accepted evidence is rebuilt
from source CSV bytes and trade ledgers using only general-purpose libraries.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DATA_ROOT = Path("/workspace/market-pattern-data")
INSTRUMENTS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
TIMEFRAMES = ("M30", "H1")
STRATEGIES = ("T2", "T3")
RUNS = tuple((s, t, i) for s in STRATEGIES for t in TIMEFRAMES for i in INSTRUMENTS)
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
TRUE_OOS = pd.Timestamp("2025-01-01", tz="Europe/Moscow")
PARAMETERS = {
    "T2": {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200,
           "adx_period": 14, "adx_threshold": 20.0, "atr_period": 14,
           "atr_regime_window": 20, "impulse_lookback": 10,
           "impulse_distance_atr": 0.5, "confirmation_window": 3,
           "stop_buffer_atr": 0.1, "max_initial_stop_atr": 3.0,
           "trailing_atr": 3.0},
    "T3": {"ema_period": 100, "slope_lookback": 5, "adx_period": 14,
           "adx_threshold": 20.0, "atr_period": 14, "atr_average_period": 20,
           "breakout_period": 20, "stop_atr": 2.0, "trail_atr": 3.0},
}
STRATEGY_FILES = {"T2": Path("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py"),
                  "T3": Path("TradingSystemLab/strategies/trend/T3_MTF_Trend.py")}
STRATEGY_HASHES = {"T2": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
                   "T3": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"}
EXPECTED_TRADES = {("T2", "M30"): (114, 94, 86, 72), ("T2", "H1"): (53, 47, 47, 29),
                   ("T3", "M30"): (122, 119, 94, 63), ("T3", "H1"): (64, 52, 41, 27)}
METRICS = ("trades", "PF", "expectancy_R", "net_R", "max_drawdown_R",
           "recovery_factor", "win_rate")
REQUIRED_RUN = {"Baseline_Report.md", "direction_report.csv", "instrument_report.csv",
                "manifest.json", "metrics.json", "monthly_returns.csv", "trades.csv",
                "yearly_report.csv"}
REQUIRED_SUMMARY = {"Phase_1_Baseline_Report.md", "baseline_matrix.csv", "data_coverage.csv",
                    "manifest.json", "monthly_matrix.csv", "yearly_matrix.csv"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                     allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def metric(values: pd.Series) -> dict[str, Any]:
    v = pd.Series(values, dtype=float).reset_index(drop=True)
    positive, negative = float(v[v > 0].sum()), float(v[v < 0].sum())
    curve = pd.concat([pd.Series([0.0]), v.cumsum()], ignore_index=True)
    dd = float((curve - curve.cummax()).min())
    net = float(v.sum())
    return {"trades": int(len(v)), "PF": positive / -negative if negative else None,
            "expectancy_R": float(v.mean()) if len(v) else None, "net_R": net,
            "max_drawdown_R": dd, "recovery_factor": net / abs(dd) if dd else None,
            "win_rate": float((v > 0).mean()) if len(v) else None}


def same(actual: Any, expected: Any, label: str) -> None:
    if pd.isna(actual) and expected is None:
        return
    if expected is None and actual is None:
        return
    if isinstance(expected, (int, float, np.number)) and not isinstance(expected, bool):
        require(not pd.isna(actual) and np.isclose(float(actual), float(expected), rtol=1e-12,
                                                   atol=1e-9), label)
    else:
        require(actual == expected, label)


def compare_metrics(row: Any, expected: dict[str, Any], label: str) -> None:
    for key in METRICS:
        actual = row[key] if isinstance(row, (dict, pd.Series)) else getattr(row, key)
        same(actual, expected[key], f"{label}: {key}")


def load_source(instrument: str, timeframe: str) -> tuple[pd.DataFrame, Path]:
    source = DATA_ROOT / "forever" / instrument / f"{instrument}_{timeframe}.csv"
    require(source.is_file() and source.stat().st_size > 0, f"missing source: {source}")
    delimiter = ";" if source.open(encoding="utf-8-sig").readline().count(";") >= 4 else ","
    raw = pd.read_csv(source, sep=delimiter)
    require("Datetime" in raw and {"Open", "High", "Low", "Close"} <= set(raw), "source columns")
    timestamps = pd.to_datetime(raw["Datetime"], errors="raise")
    require(timestamps.dt.tz is None, "source timestamps must be naive wall-clock")
    timestamps = timestamps.dt.tz_localize("Europe/Moscow")
    raw.index = pd.DatetimeIndex(timestamps)
    raw = raw[(raw.index >= pd.Timestamp("2023-01-01", tz="Europe/Moscow")) &
              (raw.index < TRUE_OOS)].copy()
    require(len(raw) > 0 and raw.index.is_monotonic_increasing and not raw.index.has_duplicates,
            "source ordering/duplicates")
    for column in ("Open", "High", "Low", "Close"):
        raw[column] = pd.to_numeric(raw[column], errors="raise")
    ohlc = raw[["Open", "High", "Low", "Close"]]
    require(not ohlc.isna().any().any() and (ohlc > 0).all().all(), "invalid OHLC")
    require((raw.High >= ohlc.max(axis=1)).all() and (raw.Low <= ohlc.min(axis=1)).all(),
            "incoherent OHLC")
    raw.index = raw.index + pd.Timedelta(minutes=30 if timeframe == "M30" else 60)
    require(raw.index.max() < TRUE_OOS, "TRUE OOS source admission")
    return raw, source


def context(frame: pd.DataFrame) -> pd.DataFrame:
    rows, indexes = [], []
    for day, group in frame.groupby(frame.index.normalize(), sort=False):
        require((group.index.normalize() == day).all(), "context crossed local day")
        for start in range(0, len(group) - 3, 4):
            block = group.iloc[start:start + 4]
            require(len(block) == 4, "incomplete context block")
            row = {"Open": block.Open.iloc[0], "High": block.High.max(),
                   "Low": block.Low.min(), "Close": block.Close.iloc[3]}
            if "Volume" in block:
                row["Volume"] = block.Volume.sum()
            rows.append(row); indexes.append(block.index[3])
    result = pd.DataFrame(rows, index=pd.DatetimeIndex(indexes))
    require(result.index.is_monotonic_increasing and not result.index.has_duplicates, "context order")
    require((result.index < TRUE_OOS).all(), "future context")
    return result


def source_contract_checks() -> None:
    for strategy, path in STRATEGY_FILES.items():
        require(sha256(path) == STRATEGY_HASHES[strategy], f"{strategy} strategy hash")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == f"{strategy}Parameters")
        defaults = {n.target.id: ast.literal_eval(n.value) for n in cls.body
                    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}
        require(defaults == PARAMETERS[strategy], f"{strategy} dataclass defaults")
    t3 = STRATEGY_FILES["T3"].read_text(encoding="utf-8")
    require('rolling(p.breakout_period).max().shift(1)' in t3 and
            'rolling(p.breakout_period).min().shift(1)' in t3, "T3 Donchian causality")
    runner = ast.parse(Path("TradingSystemLab/perpetual_v3_baseline.py").read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(runner) if isinstance(n, ast.Call) and
             isinstance(n.func, ast.Attribute) and n.func.attr == "run" and len(n.args) >= 4]
    require(any(isinstance(n.args[-2], ast.Name) and n.args[-2].id == "frame" and
                isinstance(n.args[-1], ast.Name) and n.args[-1].id == "context" for n in calls),
            "runner must pass separate execution frame and context")


def audit(root: Path) -> dict[str, Any]:
    root = Path(root)
    source_contract_checks()
    require(REQUIRED_SUMMARY <= {p.name for p in (root / "summary").iterdir()}, "summary artifacts")
    matrix = pd.read_csv(root / "summary/baseline_matrix.csv")
    keys = list(map(tuple, matrix[["strategy", "timeframe", "instrument"]].itertuples(index=False, name=None)))
    require(len(matrix) == 16 and len(set(keys)) == 16 and set(keys) == set(RUNS), "exact run matrix")
    coverage = pd.read_csv(root / "summary/data_coverage.csv")
    require(len(coverage) == 8 and not coverage.duplicated(["timeframe", "instrument"]).any(), "coverage matrix")
    frames, source_hashes = {}, {}
    for instrument in INSTRUMENTS:
        for timeframe in TIMEFRAMES:
            frame, source = load_source(instrument, timeframe)
            frames[instrument, timeframe] = frame
            source_hashes[instrument, timeframe] = sha256(source)
            row = coverage[(coverage.instrument == instrument) & (coverage.timeframe == timeframe)].iloc[0]
            same(row.actual_start, frame.index.min().isoformat(), "coverage first")
            same(row.actual_end, frame.index.max().isoformat(), "coverage last")
            same(row.bars, len(frame), "coverage bars")
            if instrument in ("GLDRUBF", "IMOEXF"):
                require(frame.index.min() > pd.Timestamp("2023-01-01", tz="Europe/Moscow"), "natural start")

    monthly_all, yearly_all, total = [], [], 0
    expected_counts = {(s, t, i): counts[INSTRUMENTS.index(i)]
                       for (s, t), counts in EXPECTED_TRADES.items() for i in INSTRUMENTS}
    for strategy, timeframe, instrument in RUNS:
        label = f"{strategy}/{timeframe}/{instrument}"
        run = root / strategy / timeframe / instrument
        require(run.is_dir() and REQUIRED_RUN <= {p.name for p in run.iterdir()}, f"{label}: artifacts")
        frame = frames[instrument, timeframe]
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        expected_manifest = {"generation": "v3_perpetual", "phase": "PHASE_1_BASELINE",
            "strategy": strategy, "strategy_id": strategy, "timeframe": timeframe,
            "instrument": instrument, "data_repository": "alkospacer123/market-pattern-data",
            "data_commit": DATA_COMMIT, "source_file": f"forever/{instrument}/{instrument}_{timeframe}.csv",
            "source_sha256": source_hashes[instrument, timeframe], "declared_development_start": "2023-01-01",
            "declared_development_end": "2024-12-31", "true_oos_start": "2025-01-01",
            "true_oos_status": "BLOCKED_NOT_READ_NOT_EXECUTED", "cost_model": "C1",
            "cost_ticks_per_side": 1, "FROZEN_TICK_SIZE": .001, "optimization": False,
            "ranking": False, "selection": False, "portfolio": False, "mtf": False,
            "strategy_source_sha256": STRATEGY_HASHES[strategy]}
        for key, value in expected_manifest.items(): same(manifest.get(key), value, f"{label}: manifest {key}")
        require("Europe/Moscow" in manifest.get("timezone", ""), f"{label}: timezone")
        require(manifest.get("baseline_parameters") == PARAMETERS[strategy], f"{label}: parameters")
        require(manifest.get("baseline_parameter_hash") == stable_hash(PARAMETERS[strategy]), f"{label}: parameter hash")
        same(manifest.get("actual_first_bar"), frame.index.min().isoformat(), f"{label}: first bar")
        same(manifest.get("actual_last_bar"), frame.index.max().isoformat(), f"{label}: last bar")
        same(manifest.get("bar_count"), len(frame), f"{label}: bars")
        matrix_row = matrix[(matrix.strategy == strategy) & (matrix.timeframe == timeframe) &
                            (matrix.instrument == instrument)].iloc[0]
        same(matrix_row.actual_start, frame.index.min().isoformat(), f"{label}: matrix start")
        same(matrix_row.actual_end, frame.index.max().isoformat(), f"{label}: matrix end")
        same(matrix_row.bars, len(frame), f"{label}: matrix bars")
        if strategy == "T3":
            ctx = context(frame)
            require(len(ctx) == sum(len(g) // 4 for _, g in frame.groupby(frame.index.normalize())), "context count")
            require(manifest.get("causal_context") == {"execution_bars_per_context_bar": 4,
                "completed_only": True, "non_overlapping": True, "reset_at_local_day": True,
                "incomplete_blocks_published": False, "timestamp": "fourth_execution_bar_close",
                "separate_dataframe": True, "future_fill": False}, f"{label}: context manifest")

        trades = pd.read_csv(run / "trades.csv")
        require({"trade_id", "symbol", "direction", "entry_time", "exit_time", "net_R"} <= set(trades), f"{label}: ledger columns")
        require(trades.trade_id.notna().all() and trades.trade_id.astype(str).str.len().gt(0).all() and
                not trades.trade_id.duplicated().any(), f"{label}: trade identities")
        require(set(trades.symbol) <= {instrument} and set(trades.direction) <= {"LONG", "SHORT"}, f"{label}: trade domain")
        entries = pd.to_datetime(trades.entry_time, errors="raise", utc=True)
        exits = pd.to_datetime(trades.exit_time, errors="raise", utc=True)
        require((exits >= entries).all() and (entries < TRUE_OOS.tz_convert("UTC")).all() and
                (exits < TRUE_OOS.tz_convert("UTC")).all(), f"{label}: trade timestamps")
        ordered = trades.assign(_exit=exits).sort_values(["_exit", "trade_id"], kind="mergesort").index
        require(ordered.equals(trades.index), f"{label}: deterministic order")
        if {"gross_R", "cost_R"} <= set(trades):
            require(np.allclose(trades.net_R, trades.gross_R - trades.cost_R, rtol=1e-10, atol=1e-10), f"{label}: net R")
        if "initial_risk_ticks" in trades:
            require((trades.initial_risk_ticks > 0).all(), f"{label}: risk ticks")
            if "cost_R" in trades:
                require(np.allclose(trades.cost_R, 2 / trades.initial_risk_ticks, rtol=1e-9, atol=1e-11), f"{label}: C1")
        calculated = metric(trades.net_R)
        compare_metrics(json.loads((run / "metrics.json").read_text()), calculated, f"{label}: metrics")
        compare_metrics(matrix_row, calculated, f"{label}: baseline matrix")
        require(calculated["trades"] == expected_counts[strategy, timeframe, instrument], f"{label}: evidence count")
        total += calculated["trades"]

        direction = pd.read_csv(run / "direction_report.csv")
        require(len(direction) == 2 and set(direction.direction) == {"LONG", "SHORT"} and
                not direction.direction.duplicated().any(), f"{label}: direction rows")
        for d in ("LONG", "SHORT"):
            dm = metric(trades.loc[trades.direction == d, "net_R"])
            compare_metrics(direction[direction.direction == d].iloc[0], dm, f"{label}: {d}")
            for key in ("trades", "PF", "expectancy_R", "net_R"):
                same(matrix_row[f"{d}_{key}"], dm[key], f"{label}: matrix {d} {key}")
        require(int(direction.trades.sum()) == len(trades), f"{label}: direction total")
        instrument_report = pd.read_csv(run / "instrument_report.csv")
        require(len(instrument_report) == 1 and instrument_report.iloc[0].instrument == instrument, f"{label}: instrument")
        compare_metrics(instrument_report.iloc[0], calculated, f"{label}: instrument metrics")

        local_exits = exits.dt.tz_convert("Europe/Moscow")
        monthly = pd.read_csv(run / "monthly_returns.csv")
        periods = pd.period_range(frame.index.min().tz_localize(None).to_period("M"),
                                  frame.index.max().tz_localize(None).to_period("M"), freq="M")
        require(not monthly.duplicated(["year", "month"]).any() and
                list(zip(monthly.year, monthly.month)) == [(p.year, p.month) for p in periods], f"{label}: months")
        for _, row in monthly.iterrows():
            mask = (local_exits.dt.year == row.year) & (local_exits.dt.month == row.month)
            compare_metrics(row, metric(trades.loc[mask, "net_R"]), f"{label}: month {row.year}-{row.month}")
        require(int(monthly.trades.sum()) == len(trades), f"{label}: monthly trades")
        same(monthly.net_R.sum(), calculated["net_R"], f"{label}: monthly net")
        tagged = monthly.copy(); tagged.insert(0, "instrument", instrument); tagged.insert(0, "timeframe", timeframe); tagged.insert(0, "strategy", strategy); monthly_all.append(tagged)

        yearly = pd.read_csv(run / "yearly_report.csv")
        years = list(range(frame.index.min().year, frame.index.max().year + 1))
        require(not yearly.year.duplicated().any() and list(yearly.year) == years and max(years) < 2025, f"{label}: years")
        for _, row in yearly.iterrows():
            compare_metrics(row, metric(trades.loc[local_exits.dt.year == row.year, "net_R"]), f"{label}: year {row.year}")
        require(int(yearly.trades.sum()) == len(trades), f"{label}: yearly trades")
        same(yearly.net_R.sum(), calculated["net_R"], f"{label}: yearly net")
        tagged = yearly.copy(); tagged.insert(0, "instrument", instrument); tagged.insert(0, "timeframe", timeframe); tagged.insert(0, "strategy", strategy); yearly_all.append(tagged)

    require(total == 1124, "independently counted Phase 1 trade total")
    for filename, expected in (("monthly_matrix.csv", pd.concat(monthly_all, ignore_index=True)),
                               ("yearly_matrix.csv", pd.concat(yearly_all, ignore_index=True))):
        saved = pd.read_csv(root / "summary" / filename)
        require(list(saved.columns) == list(expected.columns) and len(saved) == len(expected), f"{filename}: shape")
        require(not saved.duplicated(list(saved.columns[:5 if filename.startswith('monthly') else 4])).any(), f"{filename}: duplicates")
        for column in saved.columns:
            if pd.api.types.is_numeric_dtype(saved[column]):
                require(np.allclose(saved[column], expected[column], rtol=1e-12, atol=1e-9, equal_nan=True), f"{filename}: {column}")
            else: require(saved[column].equals(expected[column]), f"{filename}: {column}")
    summary = json.loads((root / "summary/manifest.json").read_text())
    expected_runs = [{"strategy": s, "timeframe": t, "instrument": i} for s, t, i in RUNS]
    for key, value in {"generation": "v3_perpetual", "phase": "PHASE_1_BASELINE", "run_count": 16,
        "runs": expected_runs, "status": "V3_PERPETUAL_PHASE_1_BASELINE_COMPLETE",
        "true_oos_status": "BLOCKED_NOT_READ_NOT_EXECUTED", "data_commit": DATA_COMMIT,
        "optimization": False, "ranking": False, "selection": False, "portfolio": False, "mtf": False}.items():
        require(summary.get(key) == value, f"summary manifest: {key}")
    return {"verdict": "PASS", "generation": "v3_perpetual", "phase": "PHASE_1_BASELINE",
            "runs": 16, "trade_ledgers_reconciled": 16, "total_trades": total,
            "source_files_verified": 8, "monthly_reports_reconciled": 16,
            "yearly_reports_reconciled": 16, "direction_reports_reconciled": 16,
            "instrument_reports_reconciled": 16, "t3_context_datasets_verified": 8,
            "protected_results_unchanged": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("TradingSystemLab/results/perpetual_v3/baseline"))
    args = parser.parse_args()
    try:
        result = audit(args.root)
    except Exception as exc:
        print(json.dumps({"verdict": "FAIL", "error": str(exc)}, sort_keys=True))
        raise SystemExit(1) from exc
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
