"""Predeclared calendar proxies / causal gap diagnostics, never input filters."""
import calendar
import math
import numpy as np
import pandas as pd
from exploratory_core import metrics

GROUPS = {"PRIMARY4": ["Si", "CNY", "GD", "MIX"], "ADDITIONAL2": ["BR", "NG"],
          "ALL6": ["Si", "CNY", "GD", "MIX", "BR", "NG"]}
DEFINITIONS = {"quarter_3d": ([3, 6, 9, 12], 3), "quarter_7d": ([3, 6, 9, 12], 7),
               "monthly_3d": (list(range(1, 13)), 3)}


def windows():
    result = []
    for year in range(2020, 2027):
        for name, (months, width) in DEFINITIONS.items():
            for month in months:
                days = [d for d in range(1, calendar.monthrange(year, month)[1]+1)
                        if calendar.weekday(year, month, d) == 3]
                anchor = pd.Timestamp(year=year, month=month, day=days[2], tz="Europe/Moscow")
                result.append({"definition": name, "anchor": anchor, "start": anchor-pd.Timedelta(days=width),
                    "end": anchor+pd.Timedelta(days=width+1)-pd.Timedelta(nanoseconds=1),
                    "actual_roll_date_confirmed": False})
    return result


def near(time, win):
    return any(w["start"] <= time <= w["end"] for w in win)


def diagnose(frames, lows, trades, trace, signals):
    w = windows()
    by_def = {name: [v for v in w if v["definition"] == name] for name in DEFINITIONS}
    gaps, gap_times = [], {}
    for symbol, frame in frames.items():
        previous_close, previous_atr = frame.Close.shift(1), lows[symbol].ATR.shift(1)
        absolute = (frame.Open-previous_close).abs()
        percent = absolute/previous_close
        atr_multiple = absolute/previous_atr
        large = (percent >= .03) | (atr_multiple >= 2.5)
        gap_times[symbol] = frame.index[large].to_list()
        for t in frame.index[large]:
            gaps.append({"instrument": symbol, "event_time": t, "absolute_gap_fraction": float(percent.loc[t]),
                "gap_in_previous_ATR": float(atr_multiple.loc[t]) if math.isfinite(atr_multiple.loc[t]) else None,
                "criterion": "ABS_GAP_GE_3PCT_OR_GE_2_5_PREVIOUS_ATR",
                "near_quarter_3d": near(t, by_def["quarter_3d"]), "cause": "UNCLASSIFIED"})
    flags = []
    for r in trades.to_dict("records"):
        touched = [v for v in by_def["quarter_3d"] if r["entry_time"] <= v["end"] and r["exit_time"] >= v["start"]]
        crossed = [v for v in by_def["quarter_3d"] if r["entry_time"] <= v["anchor"] <= r["exit_time"]]
        touched7 = [v for v in by_def["quarter_7d"] if r["entry_time"] <= v["end"] and r["exit_time"] >= v["start"]]
        gt = gap_times[r["instrument"]]
        affected = [t for t in gt if r["entry_time"] < t <= r["exit_time"]]
        flags.append({"instrument": r["instrument"], "trade_id": r["trade_id"], "entry_time": r["entry_time"], "exit_time": r["exit_time"],
            "touches_quarter_3d": bool(touched), "touches_quarter_7d": bool(touched7), "crosses_quarter_anchor": bool(crossed),
            "potential_windows_touched": ";".join(v["anchor"].date().isoformat() for v in touched),
            "potential_anchors_crossed": ";".join(v["anchor"].date().isoformat() for v in crossed),
            "entry_near_quarter_3d": near(r["entry_time"], by_def["quarter_3d"]),
            "exit_near_quarter_3d": near(r["exit_time"], by_def["quarter_3d"]),
            "large_gap_while_open": bool(affected), "large_gap_count_while_open": len(affected),
            "large_gap_on_entry_bar": r["entry_time"] in gt, "gap_stop_penalty_R": r["gap_stop_penalty_R"],
            "net_R_C1": r["net_R_C1"]})
    flag_frame = pd.DataFrame(flags)
    tagged = trades.merge(flag_frame[["trade_id", "touches_quarter_3d", "touches_quarter_7d", "crosses_quarter_anchor", "large_gap_while_open", "large_gap_on_entry_bar"]], on="trade_id", validate="one_to_one")
    concentration, window_details, sensitivity = [], [], []
    baskets = {s: [s] for s in frames} | GROUPS
    for name, members in baskets.items():
        f = tagged[tagged.instrument.isin(members)]
        sg = signals[signals.instrument.isin(members)]
        tr = trace[trace.instrument.isin(members)]
        observed = [t for s in members for t in frames[s].index]
        for definition, win in by_def.items():
            for year in list(range(2020, 2027))+["ALL"]:
                local = [v for v in win if year == "ALL" or v["anchor"].year == year]
                ts = [t for t in observed if year == "ALL" or t.year == year]
                if not ts: continue
                fs = f if year == "ALL" else f[f.exit_time.dt.year == year]
                ss = sg if year == "ALL" else sg[sg.signal_time.dt.year == year]
                tt = tr if year == "ALL" else tr[tr.event_time.dt.year == year]
                near_bars = sum(near(t, local) for t in ts)
                signal_count = sum(near(t, local) for t in ss.signal_time)
                entries = tt[tt.event_type == "ENTRY"]
                stop_tests = tt[tt.event_type != "ENTRY"]
                selected = fs.loc[np.array([near(t, local) for t in fs.exit_time], dtype=bool)]
                positive = math.fsum(fs.loc[fs.net_R_C1 > 0, "net_R_C1"])
                concentration.append({"instrument": name, "year": year, "definition": definition,
                    "observed_bars": len(ts), "near_window_bars": near_bars,
                    "observed_bar_share": near_bars/len(ts), "all_signals": len(ss), "near_signals": signal_count,
                    "near_signal_share": signal_count/len(ss) if len(ss) else None,
                    "near_signals_per_1000_bars": 1000*signal_count/near_bars if near_bars else None,
                    "outside_signals_per_1000_bars": 1000*(len(ss)-signal_count)/(len(ts)-near_bars) if len(ts) > near_bars else None,
                    "all_entries": len(entries), "near_entries": sum(near(t, local) for t in entries.event_time),
                    "all_exits": len(fs), "near_exits": len(selected), "all_stop_tests": len(stop_tests),
                    "near_stop_tests": sum(near(t, local) for t in stop_tests.event_time),
                    "near_tighten_events": sum(near(r.event_time, local) and r.tightened for r in stop_tests.itertuples()),
                    "near_triggers": sum(near(r.event_time, local) and r.triggered_now for r in stop_tests.itertuples()),
                    "near_activations": sum(near(r.event_time, local) and r.activated_now for r in stop_tests.itertuples()),
                    "net_R_exiting_near": math.fsum(selected.net_R_C1), "net_R_all": math.fsum(fs.net_R_C1),
                    "positive_R_share_exiting_near": math.fsum(selected.loc[selected.net_R_C1 > 0, "net_R_C1"])/positive if positive else None})
            if name in frames:
                for v in win:
                    if v["end"] < min(observed) or v["start"] > max(observed): continue
                    exits = f[(f.exit_time >= v["start"]) & (f.exit_time <= v["end"])]
                    window_details.append({"instrument": name, **v,
                        "signals": int(((sg.signal_time >= v["start"]) & (sg.signal_time <= v["end"])).sum()),
                        "entries": int(((f.entry_time >= v["start"]) & (f.entry_time <= v["end"])).sum()),
                        "crossing_trades": int(((f.entry_time <= v["end"]) & (f.exit_time >= v["start"])).sum()),
                        **metrics(exits)})
        scenarios = {"ORIGINAL_CONTINUOUS_SERIES": f,
            "ATTRIBUTION_OMIT_TOUCH_QUARTER_3D": f[~f.touches_quarter_3d],
            "ATTRIBUTION_OMIT_TOUCH_QUARTER_7D": f[~f.touches_quarter_7d],
            "ATTRIBUTION_OMIT_LARGE_GAP_WHILE_OPEN": f[~f.large_gap_while_open],
            "ATTRIBUTION_OMIT_ENTRY_OR_HOLDING_LARGE_GAP": f[~(f.large_gap_while_open | f.large_gap_on_entry_bar)]}
        credit = f.copy()
        credit["gross_R"] += credit.gap_stop_penalty_R
        credit["net_R_C1"] += credit.gap_stop_penalty_R
        scenarios["STOP_LEVEL_FILL_ARITHMETIC_CREDIT_ONLY"] = credit
        for scenario, selected in scenarios.items():
            sensitivity.append({"instrument": name, "scenario": scenario, "original_trade_count": len(f),
                "omitted_closed_trades": len(f)-len(selected), "is_new_strategy_replay": False,
                "gap_stop_penalty_R_original": math.fsum(f.gap_stop_penalty_R), **metrics(selected)})
    gap_frame = pd.DataFrame(gaps)
    return {"potential_expiry_windows.csv": pd.DataFrame(w), "gap_events.csv": gap_frame,
            "trade_roll_flags.csv": flag_frame, "roll_concentration.csv": pd.DataFrame(concentration),
            "potential_window_metrics.csv": pd.DataFrame(window_details), "roll_sensitivity.csv": pd.DataFrame(sensitivity)}
