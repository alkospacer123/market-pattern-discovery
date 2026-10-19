"""Instrumented frozen T3/TRAIL1 transcription and independent historical checks.

Uses unchanged source candles. No broker, network, portfolio sizing or optimizer.
The scalar answer is supplied by scalar_audit, without shared indicator/state math.
"""
from __future__ import annotations
import math
from decimal import Decimal
import numpy as np
import pandas as pd
import scalar_audit as scalar
from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3MTFTrend
from TradingSystemLab.stage8_robot.authority_replay import frozen_parameters, replay_authority
from TradingSystemLab.stage8_robot.production_replay import replay_production
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_execution import Trail1State


def signal_array(low, high):
    h = high.reindex(low.index, method="ffill")
    valid = h[["Close", "EMA100", "EMA100Slope", "ADX", "ATR", "ATRMean20"]].notna().all(axis=1)
    valid &= (h.ADX > 20) & (h.ATR > h.ATRMean20)
    long = valid & (h.Close > h.EMA100) & (h.EMA100Slope > 0) & (low.Close > low.PriorHigh)
    short = valid & (h.Close < h.EMA100) & (h.EMA100Slope < 0) & (low.Close < low.PriorLow)
    return np.where(long, "LONG", np.where(short, "SHORT", ""))


def replay_instrument(frame, symbol):
    strategy = T3MTFTrend(frozen_parameters())
    low, high = strategy.calculate_indicators(frame, DataLoader.h4_from_h1(frame))
    signals = signal_array(low, high)
    position, trades, trace, eligible = None, [], [], []
    sequence = 0
    for i, bar in enumerate(low.itertuples()):
        time = bar.Index
        if position is not None:
            p, state = position, position["state"]
            old = p["stop"]
            was_triggered, was_active = state.triggered, state.activated
            test_stop = state.activate_before_event(time, old)
            hit = bar.Low <= test_stop if p["direction"] == "LONG" else bar.High >= test_stop
            candidate, fill = None, None
            if hit:
                fill = state.stop_fill(float(bar.Open), test_stop)
                sign = 1 if p["direction"] == "LONG" else -1
                gross, cost = sign*(fill-p["entry_price"])/p["initial_risk_price"], .002/p["initial_risk_price"]
                trades.append({k: v for k, v in p.items() if k not in ("state", "stop", "extreme", "bars")})
                trades[-1].update(exit_time=time, exit_price=fill,
                    exit_reason="INITIAL_STOP" if test_stop == p["initial_stop_price"] else "ATR_TRAILING_STOP",
                    gross_R=gross, cost_R=cost, net_R_C1=gross-cost, bars_held=p["bars"]+1,
                    stop_at_exit=test_stop, gap_stop_penalty_R=abs(fill-test_stop)/p["initial_risk_price"],
                    **state.event_fields())
                p["stop"] = test_stop
            else:
                p["bars"] += 1
                p["extreme"] = max(p["extreme"], bar.High) if p["direction"] == "LONG" else min(p["extreme"], bar.Low)
                candidate = float(strategy.manage_position(p["direction"], p["extreme"], bar.ATR))
                state.observe_completed_bar(time, float(bar.High), float(bar.Low), candidate, test_stop)
                p["stop"] = state.candidate_after_bar(test_stop, candidate)
            trace.append({"instrument": symbol, "trade_id": p["trade_id"], "direction": p["direction"],
                "event_time": time, "event_type": "EXIT" if hit else "HOLD", "stop_before": old,
                "stop_test": test_stop, "stop_after": p["stop"], "candidate": candidate, "fill": fill,
                "triggered_now": state.triggered and not was_triggered,
                "activated_now": state.activated and not was_active, "tightened": p["stop"] != old,
                "triggered": state.triggered, "activated": state.activated,
                "trigger_time": state.trigger_bar_time, "activation_time": state.activation_time,
                "initial_risk_price": p["initial_risk_price"]})
            if hit:
                position = None
        sig = str(signals[i])
        entered = False
        if position is None and sig and math.isfinite(bar.ATR):
            sequence += 1
            stop = float(strategy.calculate_stop_loss(sig, float(bar.Close), float(bar.ATR)))
            state = Trail1State(sig, float(bar.Close), stop)
            position = {"instrument": symbol, "trade_id": f"T3-H1-{symbol}-{sequence:06d}",
                "direction": sig, "entry_time": time, "entry_price": float(bar.Close),
                "initial_stop_price": stop, "initial_risk_price": abs(float(bar.Close)-stop),
                "state": state, "stop": stop, "extreme": float(bar.Close), "bars": 0}
            trace.append({"instrument": symbol, "trade_id": position["trade_id"], "direction": sig,
                "event_time": time, "event_type": "ENTRY", "stop_before": stop, "stop_test": stop,
                "stop_after": stop, "candidate": None, "fill": None, "triggered_now": False,
                "activated_now": False, "tightened": False, "triggered": False, "activated": False,
                "trigger_time": None, "activation_time": None, "initial_risk_price": position["initial_risk_price"]})
            entered = True
        if sig:
            eligible.append({"instrument": symbol, "signal_time": time, "direction": sig,
                             "entered": entered, "trade_id": position["trade_id"] if entered else ""})
    opened = []
    if position:
        p = position
        opened.append({k: v for k, v in p.items() if k not in ("state", "bars", "extreme")})
        opened[-1].update(as_of=frame.index[-1], **p["state"].event_fields())
    return low, high, signals, trades, trace, eligible, opened


def close_enough(a, b, label):
    assert scalar.equal(a, b), (label, a, b)


def historical_audit(frame, symbol, result):
    from TradingSystemLab.stage8_robot.strategy_core import CompletedBar, DecisionCore, PositionState
    from TradingSystemLab.stage8_robot.trail1_state import Trail1State as ProductionTrail
    low, high, signals, trades, trace, _, _ = result
    meta = {"lifecycle": "continuous_exploratory", "fold_id": "", "instrument": symbol}
    fields = ["direction", "entry_time", "entry_price", "initial_stop_price", "initial_risk_price", "exit_time",
        "exit_price", "exit_reason", "gross_R", "cost_R", "net_R_C1", "trail1_triggered", "trail1_activated",
        "trigger_bar_time", "trail1_activation_time", "stored_trail_candidate", "bars_held"]
    reference_counts = {}
    for name, reference in [("research_authority", replay_authority(frame, symbol, meta)),
                             ("production_replay", replay_production(frame, symbol, meta))]:
        assert len(reference) == len(trades), (name, symbol, len(reference), len(trades))
        for a, b in zip(trades, reference):
            for key in fields:
                close_enough(a[key], b[key], (symbol, name, a["trade_id"], key))
        reference_counts[name] = len(reference)
    raw = [{"time": t.to_pydatetime(), **{k: float(row[k]) for k in ["Open", "High", "Low", "Close"]}}
           for t, row in frame.iterrows()]
    slo, shi, scalar_signals, scalar_trades = scalar.replay(raw)
    assert list(signals) == [s or "" for s in scalar_signals], (symbol, "SIGNALS")
    assert len(scalar_trades) == len(trades)
    maximum_error, indicator_checks = 0., 0
    for expected, actual, keys in [(slo, low, ["ATR", "PriorHigh", "PriorLow"]),
                                    (shi, high, ["ATR", "ADX", "EMA100", "EMA100Slope", "ATRMean20", "Open", "High", "Low", "Close"])]:
        assert len(expected) == len(actual)
        for a, (t, b) in zip(expected, actual.iterrows()):
            assert a["time"] == t
            for key in keys:
                close_enough(a[key], b[key], (symbol, t, key))
                if math.isfinite(a[key]): maximum_error = max(maximum_error, abs(a[key]-b[key]))
                indicator_checks += 1
    for a, b in zip(scalar_trades, trades):
        for key in a: close_enough(a[key], b[key], (symbol, "scalar_trade", key))

    # Every real management event, not just final trade outputs.
    p = prod = None
    core, managed, gap_exits = DecisionCore(), 0, 0
    entries = {t["trade_id"]: t for t in trades}
    raw_by_time = {r["time"]: r for r in slo}
    for event in trace:
        row = raw_by_time[event["event_time"]]
        if event["event_type"] == "ENTRY":
            assert p is None, (symbol, "OVERLAPPING_POSITION")
            p = scalar.ScalarPosition(event["direction"], row["Close"], event["stop_after"], row["time"])
            prod = PositionState(symbol, p.side, p.entry, p.initial, p.initial, p.entry, ProductionTrail(p.side, p.entry, p.initial))
            continue
        assert p is not None and row["time"] > p.time
        before = p.stop
        fill = p.step(row)
        r = core.manage(prod, CompletedBar(row["time"], row["Open"], row["High"], row["Low"], row["Close"], row["ATR"]))
        for label, a, b in [("stop_before", before, event["stop_before"]), ("stop_after", p.stop, event["stop_after"]),
                            ("risk", p.risk, event["initial_risk_price"]), ("triggered", p.triggered, event["triggered"]),
                            ("activated", p.activated, event["activated"]), ("trigger_time", p.trigger_time, event["trigger_time"]),
                            ("activation_time", p.activation_time, event["activation_time"])]:
            close_enough(a, b, (symbol, row["time"], label))
        close_enough(prod.current_stop, p.stop, (symbol, "prod_scalar_stop"))
        assert (fill is not None) == (event["event_type"] == "EXIT") == (r["event"] == "EXIT")
        if p.activated: assert p.activation_time > p.trigger_time
        assert (p.stop >= before if p.side == "LONG" else p.stop <= before)
        if fill is not None:
            close_enough(fill, event["fill"], (symbol, "gap_fill"))
            close_enough(fill, r["fill"], (symbol, "prod_fill"))
            gap_exits += fill != event["stop_test"]
            p = prod = None
        managed += 1

    # Recompute causal prefixes independently at dates from both old/new periods.
    prefix_checks = []
    for date in ["2021-06-15", "2023-11-15", "2025-06-15", "2026-03-15"]:
        cut = int(frame.index.searchsorted(pd.Timestamp(date, tz="Europe/Moscow")))
        if cut < 500 or cut >= len(frame): continue
        fl, fh = T3MTFTrend(frozen_parameters()).calculate_indicators(frame.iloc[:cut], DataLoader.h4_from_h1(frame.iloc[:cut]))
        assert np.array_equal(signal_array(fl, fh), signals[:cut])
        pd.testing.assert_frame_equal(fl, low.iloc[:cut])
        pd.testing.assert_frame_equal(fh, high.loc[high.index <= fl.index[-1]])
        _, _, sig, closed = scalar.replay(raw[:cut])
        assert sig == scalar_signals[:cut]
        assert closed == [t for t in scalar_trades if t["exit_time"] <= raw[cut-1]["time"]]
        prefix_checks.append(date)
    arithmetic = 0
    for t in trades:
        d = lambda x: Decimal(str(x))
        sign = Decimal(1 if t["direction"] == "LONG" else -1)
        gross = sign*(d(t["exit_price"])-d(t["entry_price"]))/d(t["initial_risk_price"])
        cost = Decimal("0.002")/d(t["initial_risk_price"])
        assert math.isclose(float(gross-cost), t["net_R_C1"], rel_tol=2e-10, abs_tol=2e-9)
        assert t["entry_time"] < t["exit_time"]
        arithmetic += 1
    return {"instrument": symbol, "bars": len(frame), "closed_trades": len(trades), "full_reference_trade_counts": reference_counts,
            "scalar_signal_comparisons": len(signals), "scalar_indicator_comparisons": indicator_checks,
            "maximum_indicator_absolute_error": maximum_error, "all_real_management_events_checked": managed,
            "gap_stop_exits_checked": gap_exits, "independent_decimal_trade_arithmetic": arithmetic,
            "causal_prefix_checks": prefix_checks, "status": "PASS"}


METRIC_FIELDS = ["trades", "gross_pf", "net_pf", "gross_R", "cost_R", "net_R", "average_R", "win_pct", "average_win_R", "average_loss_R", "max_closed_R_drawdown", "max_losing_streak"]


def metrics(frame):
    f = frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort") if len(frame) else frame
    x = f.net_R_C1.to_numpy(float) if len(f) else np.array([])
    gross = f.gross_R.to_numpy(float) if len(f) else np.array([])
    def pf(values):
        losses = -math.fsum(v for v in values if v < 0)
        return math.fsum(v for v in values if v > 0)/losses if losses else None
    curve = np.r_[0., np.cumsum(x)]
    longest = streak = 0
    for v in x:
        streak = streak+1 if v < 0 else 0
        longest = max(streak, longest)
    return dict(trades=len(x), gross_pf=pf(gross), net_pf=pf(x), gross_R=math.fsum(gross),
                cost_R=math.fsum(f.cost_R) if len(f) else 0., net_R=math.fsum(x),
                average_R=math.fsum(x)/len(x) if len(x) else None, win_pct=100*sum(x>0)/len(x) if len(x) else None,
                average_win_R=float(np.mean(x[x>0])) if sum(x>0) else None,
                average_loss_R=float(np.mean(x[x<0])) if sum(x<0) else None,
                max_closed_R_drawdown=float(min(curve-np.maximum.accumulate(curve))), max_losing_streak=longest)


def metric_audit(frame):
    # Decimal scalar PF/sums/DD is independent of numpy curve/float aggregation.
    ordered = frame.sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort")
    x = [Decimal(str(v)) for v in ordered.net_R_C1]
    gross = [Decimal(str(v)) for v in ordered.gross_R]
    equity = peak = drawdown = Decimal(0)
    for v in x:
        equity += v; peak = max(peak, equity); drawdown = min(drawdown, equity-peak)
    m = metrics(frame)
    for key, v in [("net_R", sum(x)), ("gross_R", sum(gross)), ("max_closed_R_drawdown", drawdown)]:
        assert math.isclose(m[key], float(v), rel_tol=1e-10, abs_tol=1e-9), key
    for key, seq in [("net_pf", x), ("gross_pf", gross)]:
        losses = -sum(v for v in seq if v < 0)
        if losses: assert math.isclose(m[key], float(sum(v for v in seq if v > 0)/losses), abs_tol=1e-10)
        else: assert m[key] is None
    return True
