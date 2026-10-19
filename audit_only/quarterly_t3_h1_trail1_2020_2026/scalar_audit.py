"""Independent scalar calculations on deterministic SYNTHETIC fixtures only.

No source market candles, shared indicator functions, or shared TRAIL1 state are
used to compute the scalar answer. Frozen implementations are comparators only.
This does not certify the economics or provenance of any historical series.
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

NAN = float("nan")


def ewm(values, alpha, minimum):
    """adjust=False, ignore_na=False, counting finite observations, scalar form."""
    answer, weighted, count, weight = [], NAN, 0, 1.0
    for value in values:
        finite = math.isfinite(value)
        count += finite
        if math.isfinite(weighted):
            weight *= 1 - alpha
            if finite:
                if weighted != value:
                    weighted = (weight * weighted + alpha * value) / (weight + alpha)
                weight = 1.0
        elif finite:
            weighted = value
        answer.append(weighted if count >= minimum else NAN)
    return answer


def indicator_rows(rows):
    tr, plus, minus = [], [], []
    for i, row in enumerate(rows):
        tr.append(max(row["High"] - row["Low"],
                      abs(row["High"] - rows[i-1]["Close"]) if i else 0,
                      abs(row["Low"] - rows[i-1]["Close"]) if i else 0))
        up = row["High"] - rows[i-1]["High"] if i else 0
        down = rows[i-1]["Low"] - row["Low"] if i else 0
        plus.append(up if up > down and up > 0 else 0.0)
        minus.append(down if down > up and down > 0 else 0.0)
    atr = ewm(tr, 1/14, 14)
    p, m = ewm(plus, 1/14, 14), ewm(minus, 1/14, 14)
    dx = [100 * abs(a-b)/(a+b) if a+b > 0 else NAN for a, b in zip(p, m)]
    adx = ewm(dx, 1/14, 14)
    ema = ewm([r["Close"] for r in rows], 2/101, 100)
    result = []
    for i, row in enumerate(rows):
        window = rows[max(0, i-20):i]
        average = atr[max(0, i-19):i+1]
        result.append({**row, "ATR": atr[i], "ADX": adx[i], "EMA100": ema[i],
                       "EMA100Slope": ema[i]-ema[i-5] if i >= 5 else NAN,
                       "ATRMean20": sum(average)/20 if len(average) == 20 else NAN,
                       "PriorHigh": max(r["High"] for r in window) if len(window) == 20 else NAN,
                       "PriorLow": min(r["Low"] for r in window) if len(window) == 20 else NAN})
    return result


def context(rows):
    days = {}
    for row in rows:
        days.setdefault(row["time"].date(), []).append(row)
    result = []
    for day in days.values():
        for start in range(0, len(day)-3, 4):
            block = day[start:start+4]
            result.append({"time": block[-1]["time"], "Open": block[0]["Open"],
                           "High": max(r["High"] for r in block),
                           "Low": min(r["Low"] for r in block), "Close": block[-1]["Close"]})
    return result


def direction(low, high):
    if high is None:
        return None
    fields = [high[k] for k in ("Close", "EMA100", "EMA100Slope", "ADX", "ATR", "ATRMean20")]
    if not all(math.isfinite(x) for x in fields) or high["ADX"] <= 20 or high["ATR"] <= high["ATRMean20"]:
        return None
    if high["Close"] > high["EMA100"] and high["EMA100Slope"] > 0 and low["Close"] > low["PriorHigh"]:
        return "LONG"
    if high["Close"] < high["EMA100"] and high["EMA100Slope"] < 0 and low["Close"] < low["PriorLow"]:
        return "SHORT"
    return None


class ScalarPosition:
    def __init__(self, side, entry, stop, time):
        self.side, self.entry, self.initial, self.time = side, entry, stop, time
        self.risk, self.stop, self.extreme = abs(entry-stop), stop, entry
        self.triggered = self.activated = False
        self.trigger_time = self.activation_time = self.stored = None

    def step(self, row):
        long = self.side == "LONG"
        tight = max if long else min
        time = row["time"]
        if self.triggered and not self.activated and time > self.trigger_time:
            self.activated, self.activation_time = True, time
            self.stop = tight(self.stop, self.stored)
        if (row["Low"] <= self.stop if long else row["High"] >= self.stop):
            return min(row["Open"], self.stop) if long else max(row["Open"], self.stop)
        self.extreme = tight(self.extreme, row["High"] if long else row["Low"])
        candidate = self.extreme + (-3 if long else 3) * row["ATR"]
        if not self.triggered and (row["High"] >= self.entry+self.risk if long else row["Low"] <= self.entry-self.risk):
            self.triggered, self.trigger_time, self.stored = True, time, candidate
        if self.activated:
            self.stop = tight(self.stop, candidate)
        return None


def replay(rows):
    low, high = indicator_rows(rows), indicator_rows(context(rows))
    cursor, position, trades, signals = -1, None, [], []
    for row in low:
        while cursor+1 < len(high) and high[cursor+1]["time"] <= row["time"]:
            cursor += 1
        signal = direction(row, high[cursor] if cursor >= 0 else None)
        signals.append(signal)
        if position:
            fill = position.step(row)
            if fill is not None:
                sign = 1 if position.side == "LONG" else -1
                gross = sign * (fill-position.entry)/position.risk
                trades.append({"direction": position.side, "entry_time": position.time,
                               "entry_price": position.entry, "initial_stop_price": position.initial,
                               "initial_risk_price": position.risk, "exit_time": row["time"],
                               "exit_price": fill, "gross_R": gross, "cost_R": .002/position.risk,
                               "net_R_C1": gross-.002/position.risk,
                               "trail1_triggered": position.triggered,
                               "trail1_activated": position.activated,
                               "trigger_bar_time": position.trigger_time,
                               "trail1_activation_time": position.activation_time,
                               "stored_trail_candidate": position.stored,
                               "exit_reason": "INITIAL_STOP" if position.stop == position.initial else "ATR_TRAILING_STOP"})
                position = None
        if position is None and signal and math.isfinite(row["ATR"]):
            stop = row["Close"] + (-2.5 if signal == "LONG" else 2.5)*row["ATR"]
            position = ScalarPosition(signal, row["Close"], stop, row["time"])
    return low, high, signals, trades


def fixture(size=1800):
    rng, rows, price = random.Random(7381), [], 100.0
    stamp = datetime(2021, 1, 1, 11, tzinfo=ZoneInfo("Europe/Moscow"))
    while len(rows) < size:
        if stamp.weekday() < 5 and (stamp.hour >= 10 or stamp.hour == 0):
            i = len(rows)
            drift = (.18 if (i//180) % 2 == 0 else -.18) * (1 + .65*math.sin(i/41))
            close = price + drift + rng.uniform(-.42, .42)
            high, low = max(price, close)+rng.uniform(.02, .6), min(price, close)-rng.uniform(.02, .6)
            rows.append({"time": stamp, "Open": price, "High": high, "Low": low, "Close": close})
            price = close
        stamp += timedelta(hours=1)
    return rows


def equal(a, b):
    if a is None or b is None:
        return a is b or (a is None and isinstance(b, float) and math.isnan(b))
    if isinstance(a, bool) or isinstance(a, str):
        return a == b
    if isinstance(a, (int, float)):
        return (math.isnan(a) and math.isnan(float(b))) or math.isclose(a, float(b), abs_tol=2e-10, rel_tol=2e-12)
    if isinstance(a, datetime) and isinstance(b, str):
        return a == datetime.fromisoformat(b)
    return a == b


def run_audit():
    # Imports below are reference comparisons, never scalar calculation inputs.
    import pandas as pd
    from TradingSystemLab.core.data_loader import DataLoader
    from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3MTFTrend
    from TradingSystemLab.stage8_robot.authority_replay import frozen_parameters, replay_authority
    from TradingSystemLab.stage8_robot.production_replay import replay_production
    from TradingSystemLab.stage8_robot.strategy_core import CompletedBar, DecisionCore, PositionState
    from TradingSystemLab.stage8_robot.trail1_state import Trail1State as ProductionTrail
    from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_execution import Trail1State

    rows = fixture()
    frame = pd.DataFrame([{k: v for k, v in r.items() if k != "time"} for r in rows], index=pd.DatetimeIndex([r["time"] for r in rows]))
    low, high, signals, trades = replay(rows)
    strategy = T3MTFTrend(frozen_parameters())
    actual_low, actual_high = strategy.calculate_indicators(frame, DataLoader.h4_from_h1(frame))
    comparisons, maximum = 0, 0.0
    for expected, actual, columns in [(low, actual_low, ["ATR", "PriorHigh", "PriorLow"]),
                                      (high, actual_high, ["Open", "High", "Low", "Close", "ATR", "EMA100", "EMA100Slope", "ADX", "ATRMean20"])]:
        assert len(expected) == len(actual)
        for row, (time, values) in zip(expected, actual.iterrows()):
            assert row["time"] == time
            for key in columns:
                assert equal(row[key], values[key]), (time, key, row[key], values[key])
                if math.isfinite(row[key]):
                    maximum = max(maximum, abs(row[key]-values[key]))
                comparisons += 1
    cursor = -1
    for i, (time, row) in enumerate(actual_low.iterrows()):
        while cursor+1 < len(actual_high) and actual_high.index[cursor+1] <= time:
            cursor += 1
        regime = strategy.regime(actual_high.iloc[cursor]) if cursor >= 0 else None
        assert signals[i] == strategy.generate_signal(row, regime)
    assert "LONG" in signals and "SHORT" in signals and len(trades) >= 5
    meta = {"lifecycle": "synthetic_fixture", "fold_id": "", "instrument": "SYNTHETIC"}
    counts = {}
    for label, reference in [("research_authority", replay_authority(frame, "SYNTHETIC", meta)),
                             ("production_replay", replay_production(frame, "SYNTHETIC", meta))]:
        assert len(trades) == len(reference), (label, len(trades), len(reference))
        for expected, actual in zip(trades, reference):
            for key, value in expected.items():
                assert equal(value, actual[key]), (label, key, value, actual[key])
                comparisons += 1
        counts[label] = len(reference)

    # Actual prefixes and arbitrarily changed future candles must preserve history.
    prefix_checks = 0
    for cut in [807, 1111, 1403]:
        truncated = replay(rows[:cut])
        assert truncated[2] == signals[:cut]
        assert truncated[3] == [r for r in trades if r["exit_time"] <= rows[cut-1]["time"]]
        changed = [dict(r) for r in rows]
        for r in changed[cut:]:
            for key in ("Open", "High", "Low", "Close"):
                r[key] += 1000
        assert replay(changed)[2][:cut] == signals[:cut]
        frozen_prefix = replay_authority(frame.iloc[:cut], "SYNTHETIC", meta)
        assert len(frozen_prefix) == len(truncated[3])
        for expected, actual in zip(truncated[3], frozen_prefix):
            assert all(equal(v, actual[k]) for k, v in expected.items())
        prefix_checks += 1

    # Adversarial trigger-bar crossing: stored stop 105 cannot fill on that bar.
    state_checks = 0
    for side in ("LONG", "SHORT"):
        sign = 1 if side == "LONG" else -1
        stop = 100-sign*10
        scalar = ScalarPosition(side, 100, stop, rows[0]["time"])
        frozen = Trail1State(side, 100, stop)
        prod = PositionState("SYNTHETIC", side, 100, stop, stop, 100, ProductionTrail(side, 100, stop))
        core = DecisionCore()
        bar1 = {"time": rows[1]["time"], "Open": 100., "High": 111. if sign == 1 else 101.,
                "Low": 99. if sign == 1 else 89., "Close": 110. if sign == 1 else 90., "ATR": 2.}
        assert scalar.step(bar1) is None
        assert scalar.triggered and not scalar.activated and scalar.stop == stop
        result = core.manage(prod, CompletedBar(bar1["time"], bar1["Open"], bar1["High"], bar1["Low"], bar1["Close"], 2.))
        assert result["event"] == "HOLD" and not result["activated"]
        assert frozen.observe_completed_bar(bar1["time"], bar1["High"], bar1["Low"], scalar.stored, stop)
        assert frozen.activate_before_event(bar1["time"], stop) == stop
        assert frozen.candidate_after_bar(stop, scalar.stored) == stop
        open2 = 103. if sign == 1 else 97.
        bar2 = {"time": rows[2]["time"], "Open": open2, "High": open2+1, "Low": open2-1, "Close": open2, "ATR": 2.}
        assert scalar.step(bar2) == open2
        result = core.manage(prod, CompletedBar(bar2["time"], open2, open2+1, open2-1, open2, 2.))
        assert result["event"] == "EXIT" and result["fill"] == open2
        active_stop = frozen.activate_before_event(bar2["time"], stop)
        assert active_stop == scalar.stop and frozen.stop_fill(open2, active_stop) == open2
        assert scalar.activation_time > scalar.trigger_time
        state_checks += 1
    return {"scope": "SYNTHETIC_ONLY_NOT_HISTORICAL_CERTIFICATION", "status": "PASS",
            "fixture_bars": len(rows), "fixture_closed_trades": len(trades),
            "reference_trade_counts": counts, "indicator_and_trade_field_comparisons": comparisons,
            "maximum_indicator_absolute_error": maximum, "signal_comparisons": len(signals),
            "causal_prefix_and_future_perturbation_checks": prefix_checks,
            "adversarial_long_short_trigger_gap_checks": state_checks,
            "shared_indicator_or_lifecycle_calculation_in_scalar_answer": False,
            "historical_quarterly_replay_executed": False}
