"""Causal BBW CORE v1 replay, independent from the frozen Baseline.

The state machine is Range -> Breakout -> Retest -> next-bar Entry ->
Structural Stop -> Position Management -> Exit.  Both inputs use START labels:
an H1 candle is observable at ``timestamp + 1h`` and an M15 candle at
``timestamp + 15m``.  No function in this module mutates or writes its inputs.
"""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from .models import CoreExecutionConfig, CoreReplayResult

TRAIN_END_EXCLUSIVE = pd.Timestamp("2025-01-01")
REQUIRED_CANDIDATE = {"range_min_bars", "range_max_bars", "atr_min", "atr_max",
                      "retest_min_bars", "retest_max_bars", "penetration"}
TRADE_COLUMNS = ("setup_id", "entry_time", "exit_time", "direction", "entry_price",
                 "initial_stop", "final_stop", "initial_risk", "result_R", "net_pnl",
                 "exit_reason", "bars_held")


class CoreExecutionError(ValueError):
    """A fail-closed CORE input or causal-contract violation."""


def _candidate(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        result = dict(value)
    elif hasattr(value, "__dataclass_fields__"):
        result = asdict(value)
    else:
        raise CoreExecutionError("candidate must be a mapping or dataclass")
    if missing := REQUIRED_CANDIDATE - result.keys():
        raise CoreExecutionError(f"candidate missing parameters: {sorted(missing)}")
    if not 1 <= int(result["range_min_bars"]) <= int(result["range_max_bars"]):
        raise CoreExecutionError("invalid candidate range window")
    if not 1 <= int(result["retest_min_bars"]) <= int(result["retest_max_bars"]):
        raise CoreExecutionError("invalid candidate retest window")
    if not 0 < float(result["atr_min"]) <= float(result["atr_max"]):
        raise CoreExecutionError("invalid candidate ATR range")
    if not 0 <= float(result["penetration"]):
        raise CoreExecutionError("candidate penetration cannot be negative")
    return result


def _frame(source: pd.DataFrame, required: set[str], name: str) -> pd.DataFrame:
    if missing := required - set(source):
        raise CoreExecutionError(f"{name} missing columns: {sorted(missing)}")
    work = source.copy(deep=True).reset_index(drop=True)
    work["timestamp"] = pd.to_datetime(work.timestamp, errors="raise")
    if work.empty or work.timestamp.duplicated().any() or not work.timestamp.is_monotonic_increasing:
        raise CoreExecutionError(f"{name} timestamps must be non-empty, unique, and increasing")
    if work.timestamp.max() >= TRAIN_END_EXCLUSIVE:
        raise CoreExecutionError(f"{name} contains locked TRUE OOS or post-TRAIN observations")
    for column in required - {"timestamp", "bbw_squeeze", "trend_direction"}:
        work[column] = pd.to_numeric(work[column], errors="raise")
    if ((work.high < work.low) | (work.high < work[["open", "close"]].max(axis=1)) |
            (work.low > work[["open", "close"]].min(axis=1))).any():
        raise CoreExecutionError(f"{name} contains invalid OHLC geometry")
    return work


def _bool_squeeze(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(bool)
    converted = series.astype(str).str.lower().str.strip().map({"true": True, "false": False})
    if converted.isna().any():
        raise CoreExecutionError("bbw_squeeze must contain only TRUE/FALSE")
    return converted.astype(bool)


def _detect_ranges(h1: pd.DataFrame, candidate: dict[str, Any], config: CoreExecutionConfig
                   ) -> tuple[pd.DataFrame, pd.DataFrame]:
    ranges: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    active: int | None = None
    for i, bar in h1.iterrows():
        if active is None and bool(bar.bbw_squeeze):
            active = i
            continue
        if active is None:
            continue
        if bar.timestamp.date() != h1.at[active, "timestamp"].date() or i - active > int(candidate["range_max_bars"]):
            active = i if bool(bar.bbw_squeeze) else None
            continue
        source = h1.iloc[active:i]
        if len(source) < int(candidate["range_min_bars"]):
            continue
        atr = float(bar.atr14)
        high, low = float(source.high.max()), float(source.low.min())
        width = high - low
        width_atr = width / atr if atr > 0 else np.inf
        width_pct = width / abs(float(source.close.iloc[-1])) if source.close.iloc[-1] else np.inf
        direction = "LONG" if bar.close > high else "SHORT" if bar.close < low else None
        if direction is None:
            continue
        reason = None
        maximum_atr = min(float(candidate["atr_max"]), config.max_range_width_atr or np.inf)
        if not np.isfinite(width_atr) or not float(candidate["atr_min"]) <= width_atr <= maximum_atr:
            reason = "RANGE_WIDTH_ATR"
        elif config.max_range_width_pct is not None and width_pct > config.max_range_width_pct:
            reason = "RANGE_WIDTH_PCT"
        elif str(bar.trend_direction) != direction:
            reason = "TREND_MISMATCH"
        boundary = high if direction == "LONG" else low
        extension = (float(bar.close) - boundary) * (1 if direction == "LONG" else -1)
        candle_range = float(bar.high - bar.low)
        if reason is None and (extension > config.max_breakout_extension_atr * atr + 1e-12 or
                               extension > config.max_breakout_extension_range * width + 1e-12):
            reason = "BREAKOUT_OVEREXTENDED"
        elif reason is None and candle_range > config.max_confirmation_range_atr * atr + 1e-12:
            reason = "BREAKOUT_CANDLE_TOO_LARGE"
        record = {"setup_id": len(ranges), "range_start": source.timestamp.iloc[0],
                  "range_end": source.timestamp.iloc[-1] + pd.Timedelta(hours=1),
                  "breakout_time": bar.timestamp + pd.Timedelta(hours=1), "direction": direction,
                  "range_high": high, "range_low": low, "range_width": width,
                  "range_bars": len(source), "range_atr": atr, "range_width_atr": width_atr,
                  "range_width_pct": width_pct, "squeeze_state": bool(h1.at[active, "bbw_squeeze"]),
                  "breakout_extension": extension}
        if reason:
            rejected.append({"stage": "BREAKOUT", "time": record["breakout_time"], "reason": reason})
        else:
            ranges.append(record)
        active = None
    return pd.DataFrame(ranges), pd.DataFrame(rejected, columns=("stage", "time", "reason"))


def _setups(ranges: pd.DataFrame, m15: pd.DataFrame, candidate: dict[str, Any],
            config: CoreExecutionConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, rejected = [], []
    for event in ranges.itertuples(index=False):
        eligible = m15.loc[m15.timestamp.ge(event.breakout_time)]
        eligible = eligible.loc[eligible.timestamp.dt.date.eq(pd.Timestamp(event.breakout_time).date())]
        eligible = eligible.head(int(candidate["retest_max_bars"]))
        completed = False
        level = event.range_high if event.direction == "LONG" else event.range_low
        sign = 1 if event.direction == "LONG" else -1
        for ordinal, (index, bar) in enumerate(eligible.iterrows(), 1):
            penetration = max(0.0, level - float(bar.low)) if sign == 1 else max(0.0, float(bar.high) - level)
            touched = bar.low <= level if sign == 1 else bar.high >= level
            inside = bar.close < level if sign == 1 else bar.close > level
            if penetration > float(candidate["penetration"]) * event.range_width + 1e-12 or inside:
                rejected.append({"stage": "RETEST", "time": bar.timestamp + pd.Timedelta(minutes=15),
                                 "reason": "RETEST_TOO_DEEP"})
                completed = True
                break
            confirms = bar.close > level if sign == 1 else bar.close < level
            if touched and ordinal >= int(candidate["retest_min_bars"]) and confirms:
                next_index = index + 1
                if next_index >= len(m15) or m15.at[next_index, "timestamp"].date() != bar.timestamp.date():
                    rejected.append({"stage": "ENTRY", "time": bar.timestamp + pd.Timedelta(minutes=15),
                                     "reason": "NO_CAUSAL_NEXT_OPEN"})
                    completed = True
                    break
                entry_bar = m15.iloc[next_index]
                entry = float(entry_bar.open) + sign * config.slippage
                extension = (entry - level) * sign
                if (extension > config.max_breakout_extension_atr * event.range_atr + 1e-12 or
                        extension > config.max_breakout_extension_range * event.range_width + 1e-12):
                    rejected.append({"stage": "ENTRY", "time": entry_bar.timestamp,
                                     "reason": "ENTRY_OVEREXTENDED"})
                else:
                    rows.append({**event._asdict(), "confirmation_time": bar.timestamp + pd.Timedelta(minutes=15),
                                 "entry_index": next_index, "entry_time": entry_bar.timestamp,
                                 "entry_price": entry})
                completed = True
                break
        if not completed:
            rejected.append({"stage": "RETEST", "time": event.breakout_time, "reason": "RETEST_TIMEOUT"})
    return pd.DataFrame(rows), pd.DataFrame(rejected, columns=("stage", "time", "reason"))


def _simulate(setups: pd.DataFrame, m15: pd.DataFrame, config: CoreExecutionConfig
              ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trades, fills, rejected = [], [], []
    if setups.empty:
        return (pd.DataFrame(columns=TRADE_COLUMNS),
                pd.DataFrame(columns=("setup_id", "time", "kind", "price", "fraction", "stop_after")),
                pd.DataFrame(columns=("stage", "time", "reason")))
    # Wilder ATR is based only on completed bars; shift makes the value used on
    # a bar unavailable until the preceding bar has closed.
    previous = m15.close.shift(1)
    tr = pd.concat((m15.high - m15.low, (m15.high - previous).abs(), (m15.low - previous).abs()), axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / config.m15_atr_period, adjust=False, min_periods=config.m15_atr_period).mean().shift(1)
    occupied_until = pd.Timestamp.min
    for setup in setups.sort_values(["entry_time", "setup_id"], kind="stable").itertuples(index=False):
        if setup.entry_time < occupied_until:
            rejected.append({"stage": "ENTRY", "time": setup.entry_time, "reason": "POSITION_ALREADY_OPEN"})
            continue
        sign = 1 if setup.direction == "LONG" else -1
        structural = setup.range_low - config.stop_offset if sign == 1 else setup.range_high + config.stop_offset
        stop = structural - sign * config.slippage
        risk = (setup.entry_price - stop) * sign
        if risk <= 0:
            rejected.append({"stage": "ENTRY", "time": setup.entry_time, "reason": "NON_POSITIVE_RISK"})
            continue
        targets = [setup.entry_price + sign * level * risk for level in config.target_levels]
        remaining, gross, reached = 1.0, 0.0, 0
        trade_fills = [{"setup_id": setup.setup_id, "time": setup.entry_time, "kind": "ENTRY",
                        "price": setup.entry_price, "fraction": 1.0, "stop_after": stop}]
        day = pd.Timestamp(setup.entry_time).date()
        future = m15.iloc[int(setup.entry_index):]
        final = None
        for held, (index, bar) in enumerate(future.iterrows(), 1):
            if bar.timestamp.date() != day or held > config.max_holding_bars:
                prior = m15.iloc[index - 1]
                price = float(prior.close) - sign * config.slippage
                gross += remaining * (price - setup.entry_price) * sign
                final = (prior.timestamp + pd.Timedelta(minutes=15), "TIME_EXIT", held - 1, price)
                trade_fills.append({"setup_id": setup.setup_id, "time": final[0], "kind": "TIME_EXIT",
                                    "price": price, "fraction": remaining, "stop_after": stop})
                remaining = 0.0
                break
            stop_hit = bar.low <= stop if sign == 1 else bar.high >= stop
            if stop_hit:
                price = stop - sign * config.slippage
                gross += remaining * (price - setup.entry_price) * sign
                final = (bar.timestamp + pd.Timedelta(minutes=15), "STOP", held, price)
                trade_fills.append({"setup_id": setup.setup_id, "time": final[0], "kind": "STOP",
                                    "price": price, "fraction": remaining, "stop_after": stop})
                remaining = 0.0
                break
            while reached < len(targets) and ((bar.high >= targets[reached]) if sign == 1 else (bar.low <= targets[reached])):
                fraction = config.partial_fractions[reached]
                price = targets[reached] - sign * config.slippage
                gross += fraction * (price - setup.entry_price) * sign
                remaining -= fraction
                reached += 1
                if reached >= config.breakeven_after_target:
                    stop = max(stop, setup.entry_price) if sign == 1 else min(stop, setup.entry_price)
                if reached >= config.lock_r_after_target:
                    locked = setup.entry_price + sign * config.lock_r * risk
                    stop = max(stop, locked) if sign == 1 else min(stop, locked)
                trade_fills.append({"setup_id": setup.setup_id, "time": bar.timestamp + pd.Timedelta(minutes=15),
                                    "kind": f"TP{reached}", "price": price, "fraction": fraction,
                                    "stop_after": stop})
            if remaining <= 1e-12:
                final = (bar.timestamp + pd.Timedelta(minutes=15), f"TP{reached}", held, targets[reached - 1])
                break
            if config.trailing_atr_multiple is not None and pd.notna(atr.at[index]):
                candidate_stop = float(bar.close) - sign * config.trailing_atr_multiple * float(atr.at[index])
                stop = max(stop, candidate_stop) if sign == 1 else min(stop, candidate_stop)
        if final is None:
            if config.drop_incomplete_trades:
                rejected.append({"stage": "EXIT", "time": setup.entry_time, "reason": "INCOMPLETE_DATA_WINDOW"})
                continue
            last = future.iloc[-1]
            price = float(last.close) - sign * config.slippage
            gross += remaining * (price - setup.entry_price) * sign
            final = (last.timestamp + pd.Timedelta(minutes=15), "DATA_BOUNDARY", len(future), price)
            trade_fills.append({"setup_id": setup.setup_id, "time": final[0], "kind": "DATA_BOUNDARY",
                                "price": price, "fraction": remaining, "stop_after": stop})
        commissions = config.commission_per_unit * (1.0 + sum(fill["fraction"] for fill in trade_fills[1:]))
        net = gross - commissions
        trades.append({"setup_id": setup.setup_id, "entry_time": setup.entry_time, "exit_time": final[0],
                       "direction": setup.direction, "entry_price": setup.entry_price,
                       "initial_stop": structural, "final_stop": stop, "initial_risk": risk,
                       "result_R": net / risk, "net_pnl": net, "exit_reason": final[1], "bars_held": final[2]})
        fills.extend(trade_fills)
        occupied_until = final[0]
    return (pd.DataFrame(trades, columns=TRADE_COLUMNS),
            pd.DataFrame(fills, columns=("setup_id", "time", "kind", "price", "fraction", "stop_after")),
            pd.DataFrame(rejected, columns=("stage", "time", "reason")))


def replay_core_v1(h1_features: pd.DataFrame, m15: pd.DataFrame,
                   candidate: Mapping[str, Any] | Any,
                   config: CoreExecutionConfig | None = None) -> CoreReplayResult:
    """Replay CORE v1 from TRAIN inputs without mutating either DataFrame."""
    config = config or CoreExecutionConfig()
    parameters = _candidate(candidate)
    h1 = _frame(h1_features, {"timestamp", "open", "high", "low", "close", "volume",
                              "bbw_squeeze", "trend_direction", "atr14"}, "H1 features")
    bars = _frame(m15, {"timestamp", "open", "high", "low", "close", "volume"}, "M15")
    h1["bbw_squeeze"] = _bool_squeeze(h1.bbw_squeeze)
    ranges, first_rejections = _detect_ranges(h1, parameters, config)
    setups, second_rejections = _setups(ranges, bars, parameters, config)
    trades, fills, third_rejections = _simulate(setups, bars, config)
    rejections = pd.concat((first_rejections, second_rejections, third_rejections), ignore_index=True)
    return CoreReplayResult(ranges, setups, trades, fills, rejections)


def run_core_execution(feature_path: Path, m15_path: Path, candidate_path: Path,
                       output_root: Path, config: CoreExecutionConfig | None = None) -> dict[str, Any]:
    """File adapter with byte-level proof that all research inputs stayed read-only."""
    paths = (Path(feature_path), Path(m15_path), Path(candidate_path))
    before = {path: sha256(path.read_bytes()).hexdigest() for path in paths}
    candidate = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
    result = replay_core_v1(pd.read_csv(feature_path), pd.read_csv(m15_path), candidate, config)
    output_root.mkdir(parents=True, exist_ok=True)
    outputs = {"RANGES.csv": result.ranges, "SETUPS.csv": result.setups,
               "TRADES.csv": result.trades, "FILLS.csv": result.fills,
               "REJECTIONS.csv": result.rejections}
    for name, frame in outputs.items():
        frame.to_csv(output_root / name, index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S",
                     float_format="%.15g")
    manifest = {"engine": "BBW_CORE_V1", "train_only": True, "input_sha256": {str(p.resolve()): h for p, h in before.items()},
                "config": asdict(config or CoreExecutionConfig()), "counts": {name: len(frame) for name, frame in outputs.items()}}
    (output_root / "CORE_EXECUTION_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if any(sha256(path.read_bytes()).hexdigest() != digest for path, digest in before.items()):
        raise CoreExecutionError("an input was modified during CORE execution")
    return manifest
