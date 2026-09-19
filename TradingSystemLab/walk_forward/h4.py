"""Standalone H4 adaptation of the original H1 Phase 4 walk forward.

The two candidates are immutable inputs.  Training runs are descriptive only;
every train and test interval is a separate call to the audited H4 baseline
execution path and therefore begins with a fresh, FLAT strategy instance.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
import shutil
import subprocess
from typing import Any, Mapping

import pandas as pd

from ..core.unified_metrics import finite, stats
from ..core.backtester import Backtester
from ..core.instrument_specs import get_instrument_spec
from ..core.portfolio import FixedRiskPortfolio
from ..multitimeframe.phase71 import APPROVED_DATA_ROOT, STRATEGY_SHA256
from ..multitimeframe.phase73 import hash_tree
from ..optimization.experiment import stable_hash
from ..timeframe_validation import h4_baseline as baseline
from ..optimization.phase32 import PARAMETERS, _normalize_backtester
from ..strategies.trend.T2_Trend_Pullback import PullbackSetup, T2State, T2TrendPullback
from ..strategies.trend.T3_MTF_Trend import T3MTFTrend

PHASE = "H4_WALK_FORWARD"
METHODOLOGICAL_SOURCE = "H1_PHASE_4"
TIMEFRAME = "H4"
OUTPUT = Path("TradingSystemLab/results/walk_forward/H4")
BASELINE_ROOT = Path("TradingSystemLab/results/timeframe_validation/H4")
OPTIMIZATION_ROOT = Path("TradingSystemLab/results/timeframe_optimization/H4")
ROBUSTNESS_ROOT = Path("TradingSystemLab/results/timeframe_robustness/H4")
BASELINE_COMMIT = "9133c0f9ad8eddff82ea5b3af0e9532594dec20a"
OPTIMIZATION_COMMIT = "06805ef673607b3302715bf03903c534a3694b85"
ROBUSTNESS_COMMIT = "100aa045bbf9625dcec34067d387e21720c86223"
DEVELOPMENT_PERIOD = ["2023-01-01", "2024-12-31"]
SCHEDULE = (
    ("WF01", "2023-01-01", "2023-12-31 23:59:59", "2024-01-01", "2024-03-31 23:59:59"),
    ("WF02", "2023-01-01", "2024-03-31 23:59:59", "2024-04-01", "2024-06-30 23:59:59"),
    ("WF03", "2023-01-01", "2024-06-30 23:59:59", "2024-07-01", "2024-09-30 23:59:59"),
    ("WF04", "2023-01-01", "2024-09-30 23:59:59", "2024-10-01", "2024-12-31 23:59:59"),
)
FROZEN = {
    "T2": {"candidate_id": "T2_H4_candidate_v1", "configuration_id": "T2-H4-0008-2b0494cdd24b",
        "parameter_hash": "2b0494cdd24bfbfa8ce7d657d6f83d1408f07b9f565d38d093dec5b4856e3c00",
        "parameters": {"ema_fast": 20, "ema_trend": 50, "ema_slow": 200, "adx_threshold": 20,
            "impulse_distance_atr": .5, "confirmation_window": 3, "max_initial_stop_atr": 2.5, "trailing_atr": 3}},
    "T3": {"candidate_id": "T3_H4_candidate_v1", "configuration_id": "T3-H4-0003-9b1e60957d91",
        "parameter_hash": "9b1e60957d918a086d58a9a721faa60c5dbd66d73721b08c733be460c930215f",
        "parameters": {"ema_period": 100, "adx_threshold": 20, "breakout_period": 20,
            "atr_average_period": 20, "stop_atr": 2.0, "trail_atr": 3.0}},
}
PROTECTED = tuple(Path(p) for p in (
    "TradingSystemLab/results/optimization", "TradingSystemLab/results/robustness_validation",
    "TradingSystemLab/results/timeframe_validation", "TradingSystemLab/results/timeframe_optimization",
    "TradingSystemLab/results/timeframe_robustness", "TradingSystemLab/results/timeframe_analysis",
    "TradingSystemLab/results/timeframe_diagnostics", "TradingSystemLab/results/multitimeframe_research",
    "TradingSystemLab/results/true_oos_validation", "TradingSystemLab/results/mtf_research",
    "TradingSystemLab/results/walk_forward/M1", "TradingSystemLab/results/walk_forward/M5",
    "TradingSystemLab/results/walk_forward/M15", "TradingSystemLab/results/walk_forward/M30"))
STRATEGIES = tuple(Path(p) for p in ("TradingSystemLab/strategies/trend/T2_Trend_Pullback.py",
                                     "TradingSystemLab/strategies/trend/T3_MTF_Trend.py"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_sha256(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): _sha(p) for p in sorted(Path(root).rglob("*")) if p.is_file()}


def protected_snapshot() -> dict[str, Any]:
    # A later phase may add its own H4 TRUE OOS subtree.  It was not present
    # when this snapshot was frozen and is intentionally outside this phase's
    # protected-input set (all earlier TRUE OOS timeframes remain protected).
    result = {}
    for path in PROTECTED:
        tree = hash_tree(path)
        if path == Path("TradingSystemLab/results/true_oos_validation"):
            tree = {name: digest for name, digest in tree.items() if not name.startswith("H4/")}
        result[str(path)] = tree
    result.update({str(p): _sha(p) for p in STRATEGIES})
    return result


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _csv(path: Path, rows: Any, columns: list[str] | None = None) -> None:
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows, columns=columns)
    frame.map(finite).to_csv(path, index=False, lineterminator="\n", float_format="%.12g", na_rep="")


def _summary(frame: pd.DataFrame) -> dict[str, Any]:
    values = frame.net_R.astype(float) if len(frame) else pd.Series(dtype=float)
    m = stats(values)
    return {"trades": m["trades"], "PF_C1": m["PF_R"], "expectancy_C1": m["expectancy"],
        "net_R_C1": m["net_R"], "max_DD_C1": m["max_DD_R"], "recovery_factor": m["recovery_factor"],
        "win_rate": m["winrate"], "max_winning_streak": m["max_winning_streak"],
        "max_losing_streak": m["max_losing_streak"]}


def verify_provenance() -> tuple[dict[str, dict], dict[str, dict]]:
    """Verify every frozen link before any market-data file is opened."""
    paths = {"baseline": BASELINE_ROOT/"manifest.json", "optimization": OPTIMIZATION_ROOT/"manifest.json",
             "robustness": ROBUSTNESS_ROOT/"manifest.json", "registry": ROBUSTNESS_ROOT/"candidate_registry.json"}
    if any(not p.is_file() for p in paths.values()):
        raise RuntimeError("H4_WALK_FORWARD_PROVENANCE_MISSING")
    provenance = {k: json.loads(p.read_text()) for k, p in paths.items() if k != "registry"}
    registry = json.loads(paths["registry"].read_text())
    if (provenance["baseline"].get("status") != "PHASE_H4_BASELINE_COMPLETE" or
            provenance["optimization"].get("status") != "PHASE_H4_OPTIMIZATION_COMPLETE" or
            provenance["robustness"].get("status") != "PHASE_H4_ROBUSTNESS_COMPLETE" or
            provenance["robustness"].get("classifications") != {"T2": "BORDERLINE", "T3": "BORDERLINE"} or
            provenance["robustness"].get("baseline_merge_commit") != BASELINE_COMMIT or
            provenance["robustness"].get("optimization_merge_commit") != OPTIMIZATION_COMMIT):
        raise RuntimeError("H4_WALK_FORWARD_PROVENANCE_MISMATCH")
    if subprocess.run(["git", "diff", "--quiet", ROBUSTNESS_COMMIT, "--", str(ROBUSTNESS_ROOT)], check=False).returncode:
        raise RuntimeError("H4_ROBUSTNESS_COMMIT_PARITY_MISMATCH")
    by_key = {row.get("strategy"): row for row in registry}
    if set(by_key) != set(FROZEN):
        raise RuntimeError("H4_FROZEN_CANDIDATE_SET_MISMATCH")
    for key, expected in FROZEN.items():
        row = by_key[key]
        required = (row.get("candidate_id") == expected["candidate_id"] and
            row.get("source_h4_optimization_configuration_id") == expected["configuration_id"] and
            row.get("parameter_hash") == expected["parameter_hash"] and row.get("parameters") == expected["parameters"] and
            row.get("selection_locked_before_validation") is True and row.get("strategy_hash") == STRATEGY_SHA256[key] and
            _sha(STRATEGIES[("T2", "T3").index(key)]) == STRATEGY_SHA256[key] and
            stable_hash(row["parameters"]) == expected["parameter_hash"])
        if not required:
            raise RuntimeError(f"{key}_H4_FROZEN_CANDIDATE_MISMATCH")
    return provenance, by_key


def load_verified_development(data_root: Path, provenance: Mapping[str, dict]) -> tuple[dict[str, pd.DataFrame], list[dict]]:
    loaded = {alias: baseline.load_h1_development(Path(data_root), alias) for _, alias in baseline.INSTRUMENTS}
    verified = []
    for instrument, alias in baseline.INSTRUMENTS:
        frame, paths = loaded[alias]
        if frame is None:
            raise RuntimeError("H4_WALK_FORWARD_SOURCE_HASH_MISMATCH")
        verified.extend({"instrument": instrument, "alias": alias, "name": p.name, "sha256": _sha(p)} for p in paths)
    expected = (provenance["baseline"].get("source_files"), provenance["optimization"].get("source_files"),
                provenance["robustness"].get("verified_source_files"))
    if any(verified != item for item in expected):
        raise RuntimeError("H4_WALK_FORWARD_SOURCE_HASH_MISMATCH")
    return {alias: item[0] for alias, item in loaded.items()}, verified


def _interval(data: Mapping[str, pd.DataFrame], start: str, end: str) -> dict[str, pd.DataFrame]:
    return {alias: frame.loc[start:end].copy() for alias, frame in data.items()}


def _t2_causal_adapter(strategy: T2TrendPullback, h4: pd.DataFrame, symbol: str,
                       trade_start: pd.Timestamp, *, tick_size: float) -> pd.DataFrame:
    """Frozen T2 loop with indicator history, but deliberately fresh trading state."""
    data, p = strategy.calculate_indicators(h4), strategy.parameters
    portfolio = FixedRiskPortfolio()
    state, setup, position, records, equity = T2State.FLAT_NO_SETUP, None, None, [], portfolio.initial_capital
    first = int(data.index.searchsorted(trade_start))

    def close_trade(i: int, price: float, reason: str) -> None:
        nonlocal position, state, equity
        d, sign = position["direction"], 1 if position["direction"] == "LONG" else -1
        points, risk = sign * (price - position["entry_price"]), position["initial_risk_points"]
        cost_r, gross_r = 2.0 * tick_size / risk, points / risk
        records.append({**position["metadata"], "exit_time": data.index[i], "exit_price": price,
            "exit_reason": reason, "bars_held": position["bars_held"] + 1, "gross_R": gross_r,
            "cost_R_C1": cost_r, "net_R_C1": gross_r - cost_r,
            "MAE_R": max(0.0, position["entry_price"] - position["min_low"] if d == "LONG" else position["max_high"] - position["entry_price"]) / risk,
            "MFE_R": max(0.0, position["max_high"] - position["entry_price"] if d == "LONG" else position["entry_price"] - position["min_low"]) / risk,
            "quantity": position["quantity"]})
        equity += (gross_r - cost_r) * equity * portfolio.risk_fraction
        position, state = None, T2State.FLAT_NO_SETUP

    for i in range(first, len(data)):
        bar = data.iloc[i]; regime = strategy.regime(bar)
        if position is not None:
            old_stop = position["active_stop"]
            hit = bar.Low <= old_stop if position["direction"] == "LONG" else bar.High >= old_stop
            if hit:
                gap = min(float(bar.Open), old_stop) if position["direction"] == "LONG" else max(float(bar.Open), old_stop)
                close_trade(i, gap, "INITIAL_STOP" if old_stop == position["initial_stop"] else "ATR_TRAILING_STOP"); continue
            ema_loss = bar.Close < bar.EMA50 if position["direction"] == "LONG" else bar.Close > bar.EMA50
            if ema_loss:
                close_trade(i, float(bar.Close), "EMA50_TREND_LOSS"); continue
            position["bars_held"] += 1
            position["min_low"] = min(position["min_low"], float(bar.Low)); position["max_high"] = max(position["max_high"], float(bar.High))
            candidate = position["max_high"] - p.trailing_atr * bar.ATR if position["direction"] == "LONG" else position["min_low"] + p.trailing_atr * bar.ATR
            position["active_stop"] = max(old_stop, candidate) if position["direction"] == "LONG" else min(old_stop, candidate)
            continue
        if setup is not None:
            if i > setup.expiry_index or regime != setup.direction:
                setup, state = None, T2State.FLAT_NO_SETUP
            elif i > setup.pullback_start_index:
                setup.pullback_extreme = min(setup.pullback_extreme, float(bar.Low)) if setup.direction == "LONG" else max(setup.pullback_extreme, float(bar.High))
                if strategy.is_confirmation(bar, data.iloc[i - 1], setup.direction):
                    entry = float(bar.Close)
                    stop = setup.pullback_extreme - p.stop_buffer_atr * bar.ATR if setup.direction == "LONG" else setup.pullback_extreme + p.stop_buffer_atr * bar.ATR
                    risk = entry - stop if setup.direction == "LONG" else stop - entry
                    if risk > 0 and risk <= p.max_initial_stop_atr * bar.ATR:
                        metadata = {"trade_id": f"{symbol}-{len(records)+1:06d}", "strategy_id": strategy.name,
                            "symbol": symbol, "direction": setup.direction, "pullback_time": setup.pullback_start_time,
                            "confirmation_time": data.index[i], "entry_time": data.index[i], "entry_price": entry,
                            "initial_stop": stop, "initial_risk_points": risk, "initial_risk_ticks": risk / tick_size,
                            "impulse_reference_time": setup.impulse_reference_time, "setup_age_bars": i - setup.pullback_start_index}
                        position = {"direction": setup.direction, "entry_price": entry, "initial_stop": stop,
                            "initial_risk_points": risk, "active_stop": stop, "bars_held": 0, "min_low": entry,
                            "max_high": entry, "quantity": portfolio.size(equity, entry, stop), "metadata": metadata}
                        state = T2State.POSITION_OPEN
                    else: state = T2State.FLAT_NO_SETUP
                    setup = None
            continue
        if regime and i:
            reference = strategy.impulse_reference(data, i, regime)
            if reference is not None and strategy.is_pullback(bar, regime):
                extreme = float(bar.Low if regime == "LONG" else bar.High)
                setup = PullbackSetup(regime, data.index[i], i, i + p.confirmation_window, extreme, reference)
                state = T2State.LONG_PULLBACK_ARMED if regime == "LONG" else T2State.SHORT_PULLBACK_ARMED
    return pd.DataFrame(records, columns=[
        "trade_id", "strategy_id", "symbol", "direction", "pullback_time", "confirmation_time", "entry_time",
        "entry_price", "initial_stop", "initial_risk_points", "initial_risk_ticks", "exit_time", "exit_price",
        "exit_reason", "bars_held", "gross_R", "cost_R_C1", "net_R_C1", "MAE_R", "MFE_R",
        "impulse_reference_time", "setup_age_bars", "quantity"])


def _execute_interval(key: str, parameters: dict, data: Mapping[str, pd.DataFrame], start: str, end: str,
                      *, context_start: str | None = None) -> pd.DataFrame:
    lo, hi = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    context_start = context_start or start
    pieces = []
    for alias, h1 in _interval(data, context_start, end).items():
        if h1.empty: continue
        params, tick, execution = replace(PARAMETERS[key], **parameters), get_instrument_spec(alias).price_precision, baseline.causal_h4(h1)
        if key == "T2":
            frame = _t2_causal_adapter(T2TrendPullback(params), execution, alias, lo, tick_size=tick)
        else:
            raw = Backtester(FixedRiskPortfolio(), cost_ticks_per_side=0, tick_size=tick).run(
                T3MTFTrend(params), alias, execution, baseline.causal_d1(h1), entry_start=lo,
                entry_end=hi + pd.Timedelta(seconds=1)).trades
            frame = _normalize_backtester(raw, key)
        if frame.empty: continue
        frame = frame.copy(); frame["instrument"] = "USDRUBF" if alias == "Si" else "CNYRUBF"
        frame["strategy"], frame["timeframe"] = key, TIMEFRAME
        frame["net_R"] = frame.gross_R.astype(float) - 2 / frame.initial_risk_ticks.astype(float)
        pieces.append(frame)
    result = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=baseline.TRADE_COLUMNS)
    if len(result):
        entry, exit_ = pd.to_datetime(result.entry_time, utc=True), pd.to_datetime(result.exit_time, utc=True)
        result = result.loc[entry.ge(lo) & exit_.le(hi)].copy()
    return result.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)


def classify(aggregate: dict, positive_share: float, complete_folds: int,
             best_fold_contribution: float | None, instrument_expectancies: list[float | None]) -> str:
    nonnegative_instruments = all(value is not None and value >= 0 for value in instrument_expectancies)
    passed = (aggregate["trades"] >= 50 and aggregate["expectancy_C1"] is not None and aggregate["expectancy_C1"] > 0 and
        positive_share >= .60 and (best_fold_contribution is None or best_fold_contribution <= .70) and
        nonnegative_instruments and complete_folds > 0)
    failed = ((aggregate["expectancy_C1"] is not None and aggregate["expectancy_C1"] < 0) or
              (complete_folds > 0 and positive_share < .50))
    return "WALK_FORWARD_PASS" if passed else ("WALK_FORWARD_FAIL" if failed else "WALK_FORWARD_BORDERLINE")


def _diagnostics(target: Path, trades: pd.DataFrame) -> tuple[list[dict], dict]:
    def grouped(column: str, values: tuple) -> list[dict]:
        return [{column: value, **_summary(trades.loc[trades[column].eq(value)])} for value in values]
    instruments = grouped("symbol", ("Si", "CNY")); _csv(target/"instrument_report.csv", instruments)
    _csv(target/"direction_report.csv", grouped("direction", ("LONG", "SHORT")))
    years = pd.to_datetime(trades.entry_time, utc=True).dt.year if len(trades) else pd.Series(dtype=int)
    _csv(target/"year_report.csv", [{"year": year, **_summary(trades.loc[years.eq(year)])} for year in (2023, 2024)])
    positive = trades.loc[trades.net_R.gt(0), "net_R"].sort_values(ascending=False); total_positive = positive.sum()
    fold_net = trades.groupby("fold", sort=True).net_R.sum() if len(trades) else pd.Series(dtype=float)
    total_net = trades.net_R.sum() if len(trades) else 0
    best = finite(fold_net.max()/total_net) if len(fold_net) and total_net > 0 else None
    concentration = {f"top_{n}_positive_trade_share": finite(positive.head(n).sum()/total_positive) if total_positive > 0 else None for n in (1, 3, 10)}
    concentration["best_fold_contribution"] = best; _csv(target/"concentration.csv", [concentration])
    _csv(target/"leave_one_fold_out.csv", [{"omitted_fold": fold, **_summary(trades.loc[trades.fold.ne(fold)])} for fold, *_ in SCHEDULE])
    rows=[]
    for scope, mask in (("ALL", pd.Series(True, index=trades.index)), ("WINNERS", trades.net_R.gt(0)), ("LOSERS", trades.net_R.lt(0))):
        for metric in ("MAE_R", "MFE_R"):
            values = pd.to_numeric(trades.loc[mask, metric], errors="coerce").dropna()
            rows.append({"scope": scope, "metric": metric, "trades": len(values), "mean": finite(values.mean()),
                "median": finite(values.median()), "p75": finite(values.quantile(.75)), "p90": finite(values.quantile(.90))})
    _csv(target/"mae_mfe.csv", rows)
    return instruments, concentration


def run(data_root: Path = APPROVED_DATA_ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    before = protected_snapshot()
    provenance, candidates = verify_provenance()  # Must precede all market-data reads.
    data, sources = load_verified_development(Path(data_root), provenance)
    coverage = {alias: {"first_source_close": frame.index.min().isoformat(), "last_source_close": frame.index.max().isoformat(),
                         "bars": len(frame)} for alias, frame in data.items()}
    insufficient = any(pd.Timestamp(v["first_source_close"]) >= pd.Timestamp("2023-01-08", tz="UTC") or
                       pd.Timestamp(v["last_source_close"]) < pd.Timestamp("2024-12-30", tz="UTC") for v in coverage.values())
    if insufficient:
        raise RuntimeError("DATA_COVERAGE_INSUFFICIENT")
    output = Path(output)
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    _json(output/"DATA_COVERAGE_REPORT.json", {"status": "SUFFICIENT", "minimum": ["2023-01-01", "2025-01-01"],
        "end_exclusive": True, "actual": coverage, "source_files": sources, "true_oos_blocked": True})
    comparison=[]; verdicts={}
    for key in ("T2", "T3"):
        candidate=candidates[key]; target=output/key; target.mkdir(); folds=[]; decay=[]; pieces=[]; warmups=[]
        for fold, train_start, train_end, test_start, test_end in SCHEDULE:
            complete = all(frame.index.min() <= pd.Timestamp(train_start, tz="UTC") and
                           frame.index.max() >= pd.Timestamp(test_end, tz="UTC") for frame in data.values())
            train = _execute_interval(key, candidate["parameters"], data, train_start, train_end)
            test = _execute_interval(key, candidate["parameters"], data, test_start, test_end,
                                     context_start=DEVELOPMENT_PERIOD[0])
            context = _interval(data, DEVELOPMENT_PERIOD[0], test_end)
            h4_context = {alias: baseline.causal_h4(frame) for alias, frame in context.items()}
            d1_context = {alias: baseline.causal_d1(frame) for alias, frame in context.items()} if key == "T3" else {}
            start_ts = pd.Timestamp(test_start, tz="UTC")
            test_h4 = {alias: frame.loc[frame.index >= start_ts] for alias, frame in h4_context.items()}
            first_admitted = min((frame.index.min() for frame in test_h4.values() if len(frame)), default=None)
            warmup_sufficient = (all(len(frame.loc[frame.index < start_ts]) >= 200 for frame in h4_context.values())
                                 if key == "T2" else
                                 all(len(frame.loc[frame.index < start_ts]) >= 200 for frame in d1_context.values()))
            warmups.append({"fold": fold, "context_start": DEVELOPMENT_PERIOD[0], "trade_start": test_start,
                "trade_end": test_end, "h1_context_bars": sum(map(len, context.values())),
                "h4_context_bars": sum(map(len, h4_context.values())),
                "d1_context_bars": sum(map(len, d1_context.values())) if key == "T3" else None,
                "test_h4_bars": sum(map(len, test_h4.values())),
                "first_admitted_trading_timestamp": first_admitted.isoformat() if first_admitted is not None else None,
                "flat_start": True, "pretest_entries": 0, "future_context_used": False,
                "warmup_sufficient": warmup_sufficient})
            test["fold"], test["fold_start_state"] = fold, "FLAT"
            test["trade_id"] = [f"{key}-H4-{fold}-{n:06d}" for n in range(1, len(test)+1)]
            pieces.append(test); train_metric, test_metric = _summary(train), _summary(test)
            folds.append({"fold": fold, "train_start": train_start, "train_end": train_end, "test_start": test_start,
                "test_end": test_end, "status": "complete" if complete else "incomplete", "included_in_pass": complete,
                "reason": "" if complete else "requested train/test calendar is not fully covered", "fold_start_state": "FLAT", **test_metric})
            decay.append({"fold": fold, "train_expectancy_C1": train_metric["expectancy_C1"], "test_expectancy_C1": test_metric["expectancy_C1"],
                "expectancy_decay": finite(test_metric["expectancy_C1"]-train_metric["expectancy_C1"]) if None not in (test_metric["expectancy_C1"],train_metric["expectancy_C1"]) else None,
                "train_PF_C1": train_metric["PF_C1"], "test_PF_C1": test_metric["PF_C1"],
                "PF_change": finite(test_metric["PF_C1"]-train_metric["PF_C1"]) if None not in (test_metric["PF_C1"],train_metric["PF_C1"]) else None,
                "train_win_rate": train_metric["win_rate"], "test_win_rate": test_metric["win_rate"],
                "win_rate_change": finite(test_metric["win_rate"]-train_metric["win_rate"]) if None not in (test_metric["win_rate"],train_metric["win_rate"]) else None})
        trades=pd.concat(pieces,ignore_index=True).sort_values(["exit_time","instrument","fold","trade_id"],kind="mergesort").reset_index(drop=True)
        if trades.trade_id.duplicated().any(): raise RuntimeError("NON_UNIQUE_STITCHED_TRADE_ID")
        _csv(target/"folds.csv",folds); _csv(target/"trades.csv",trades); _csv(target/"train_test_decay.csv",decay)
        _csv(target/"warmup_report.csv",warmups)
        if not len(trades): raise RuntimeError(f"{key}_ZERO_TRADES_AFTER_CAUSAL_WARMUP")
        instruments, concentration = _diagnostics(target,trades); aggregate=_summary(trades)
        included=[row for row in folds if row["included_in_pass"]]
        positive_share=sum(row["expectancy_C1"] is not None and row["expectancy_C1"]>0 for row in included)/len(included) if included else 0
        verdict=classify(aggregate,positive_share,len(included),concentration["best_fold_contribution"],[r["expectancy_C1"] for r in instruments])
        metrics={"candidate_id":candidate["candidate_id"],"parameter_hash":candidate["parameter_hash"],"cost_scenario":"C1",
            "aggregate":aggregate,"positive_complete_fold_share":positive_share,"complete_folds":len(included),
            "best_fold_contribution":concentration["best_fold_contribution"],"verdict":verdict}
        _json(target/"metrics.json",metrics)
        (target/"final_report.md").write_text(f"# {candidate['candidate_id']} H4 Walk Forward\n\n**{verdict}**\n\nC1 only. Frozen parameters; no fitting, optimization, ranking, or selection. Every interval began FLAT. TRUE OOS remained blocked.\n",encoding="utf-8")
        comparison.append({"strategy":key,"candidate_id":candidate["candidate_id"],"verdict":verdict,**aggregate,
                           "positive_complete_fold_share":positive_share,"best_fold_contribution":concentration["best_fold_contribution"]})
        verdicts[key]=verdict
    _csv(output/"comparison.csv",comparison)
    status="PHASE_H4_WALK_FORWARD_COMPLETE" if all(v=="WALK_FORWARD_PASS" for v in verdicts.values()) else "PHASE_H4_WALK_FORWARD_BORDERLINE"
    after=protected_snapshot()
    if before != after: raise RuntimeError("PROTECTED_RESEARCH_ARTIFACT_MUTATION")
    manifest={"phase":PHASE,"status":status,"methodological_source":METHODOLOGICAL_SOURCE,"timeframe":TIMEFRAME,
        "candidate_ids":{k:candidates[k]["candidate_id"] for k in candidates},
        "parameter_hashes":{k:candidates[k]["parameter_hash"] for k in candidates},"parameters_frozen":True,
        "optimization":False,"ranking":False,"candidate_selection":False,"development_coverage":DEVELOPMENT_PERIOD,
        "fold_schedule":[{"fold":x[0],"train":[x[1],x[2]],"test":[x[3],x[4]]} for x in SCHEDULE],
        "cost_model":"H1_C1","cost_scenarios":["C1"],"true_oos_cutoff":"2025-01-01","true_oos_read":False,
        "true_oos_blocked":True,"verified_source_files":sources,"source_count":len(sources),
        "provenance":{"baseline":{"commit":BASELINE_COMMIT,"status":"PHASE_H4_BASELINE_COMPLETE"},
            "optimization":{"commit":OPTIMIZATION_COMMIT,"status":"PHASE_H4_OPTIMIZATION_COMPLETE"},
            "robustness":{"commit":ROBUSTNESS_COMMIT,"status":"PHASE_H4_ROBUSTNESS_COMPLETE","classifications":{"T2":"BORDERLINE","T3":"BORDERLINE"}}},
        "strategy_hashes":STRATEGY_SHA256,"protected_artifact_hashes":after,"deterministic":True,"verdicts":verdicts}
    _json(output/"manifest.json",manifest)
    lines=["# H4 Walk Forward Validation","",f"**{status}**","","## Previous invalid run","",
           "T2 stitched trades = 0; T3 stitched trades = 0. Cause: isolated test-slice indicator warm-up failure.","",
           "## Corrected causal-warm-up run",""]
    for key in ("T2", "T3"):
        lines += [f"### {key}","","| Fold | Trades | PF C1 | Expectancy C1 | Net R | DD | Status | Included in pass |",
                  "|---|---:|---:|---:|---:|---:|---|---|"]
        for row in pd.read_csv(output/key/"folds.csv").to_dict("records"):
            lines.append(f"| {row['fold']} | {row['trades']} | {row['PF_C1']} | {row['expectancy_C1']} | "
                         f"{row['net_R_C1']} | {row['max_DD_C1']} | {row['status']} | {row['included_in_pass']} |")
        aggregate = json.loads((output/key/"metrics.json").read_text())["aggregate"]
        lines += ["",f"Stitched: {aggregate['trades']} trades; PF {aggregate['PF_C1']}; expectancy "
                  f"{aggregate['expectancy_C1']}; net R {aggregate['net_R_C1']}; DD {aggregate['max_DD_C1']}; "
                  f"recovery {aggregate['recovery_factor']}; win rate {aggregate['win_rate']}.",
                  f"Verdict: **{verdicts[key]}**. Known full-development 2024 robustness activity: "
                  f"{15 if key == 'T2' else 14} trades (comparison diagnostic only).",""]
    lines += ["Every fold starts FLAT while indicators receive only causal development history through its test end. "
              "Incomplete folds remain in the stitched diagnostic ledger but are excluded from pass-fold statistics.","",
              "C1 only; frozen candidates; 12 source hashes verified; no optimization, ranking, selection, or TRUE OOS read.",""]
    (output/"walk_forward_report.md").write_text("\n".join(lines),encoding="utf-8")
    return manifest
