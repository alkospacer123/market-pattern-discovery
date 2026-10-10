#!/usr/bin/env python3
"""Level Rejection v1: strictly no-P&L M5 opportunities, never a backtest.

Only a future, pre-scheduled entry M5 OPEN is inspected. There is no exit,
Stop/Take hit, forward high/low, PF, MFE/MAE or earnings calculation here.
"""
import argparse
from collections import Counter, deque
from datetime import date, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m5_baseline import allowed, next_slot, rounded, tick, window_at, windows, FIVE, SYMBOLS

LAB = Path(__file__).resolve().parents[1]
CONFIG = LAB / "config/stage2_level_rejection_m5_opportunity_v1.json"
D = Decimal
KEYS = ("symbol", "scenario", "status", "direction", "signal_at", "available_at", "target_at", "level", "stop", "entry_open", "risk", "tick", "legacy_take", "full_net_take", "within_known_range", "reason")
SCHEMES = (10, 15)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def load_bars(root, manifest):
    """Read exactly the pinned 2023 byte prefix; never load 2024+ market bytes."""
    if git(root, "rev-parse", "HEAD") != manifest["source_ref"]:
        raise RuntimeError("SOURCE_REF_MISMATCH")
    if git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise RuntimeError("SOURCE_DIRTY")
    result = {}
    for symbol in SYMBOLS:
        spec = manifest["inputs"][symbol]
        if git(root, "ls-files", "--stage", "--", spec["path"]).split()[1] != spec["blob"]:
            raise RuntimeError("SOURCE_BLOB_MISMATCH")
        source = root / spec["path"]
        before = source.stat()
        with source.open("rb", buffering=0) as f:
            content = f.read(spec["prefix_bytes"])
        after = source.stat()
        if any(getattr(before,k) != getattr(after,k) for k in ("st_size","st_mtime_ns","st_ctime_ns","st_ino")):
            raise RuntimeError("SOURCE_CHANGED_DURING_READ")
        if len(content) != spec["prefix_bytes"] or not content.endswith(b"\n"):
            raise RuntimeError("SOURCE_PREFIX_INCOMPLETE")
        if hashlib.sha256(content).hexdigest() != spec["prefix_sha256"]:
            raise RuntimeError("SOURCE_PREFIX_HASH_MISMATCH")
        lines = content.decode("utf-8-sig").splitlines()
        if lines[0] != "Ticker;Datetime;Open;High;Low;Close;Volume":
            raise RuntimeError("SOURCE_CSV_HEADER")
        if len(lines) - 1 != spec["rows_2023"]:
            raise RuntimeError("SOURCE_ROW_BUDGET")
        rows, previous = [], None
        for line in lines[1:]:
            fields = line.split(";")
            if len(fields) != 7 or fields[0] != symbol:
                raise RuntimeError("SOURCE_CSV_SCHEMA")
            stamp = datetime.fromisoformat(fields[1])
            if (stamp.year != 2023 or stamp.tzinfo is not None or stamp.minute % 5
                    or stamp.second or stamp.microsecond
                    or (previous is not None and stamp <= previous)):
                raise RuntimeError("SOURCE_DATE_OR_ORDER")
            previous = stamp
            o,h,l,c,v = [D(x) for x in fields[2:]]
            if not (all(x.is_finite() for x in (o,h,l,c,v)) and l > 0
                    and l <= min(o,c) <= max(o,c) <= h and v >= 0):
                raise RuntimeError("SOURCE_OHLCV")
            step = tick(symbol,stamp)
            if any(price % step for price in (o,h,l,c)):
                raise RuntimeError("SOURCE_PRICE_GRID")
            rows.append((stamp,o,h,l,c,v))
        if rows[0][0] != datetime.fromisoformat(spec["first"]):
            raise RuntimeError("SOURCE_FIRST_DATE")
        result[symbol] = rows
    return result


def event_signal(symbol, bar, previous, params):
    """Evaluates ONLY completed test bar and six strictly earlier bars."""
    if len(previous) != params["level_lookback_completed_m5"]:
        return None, "WARMUP"
    high = max(x[2] for x in previous)
    low = min(x[3] for x in previous)
    time = bar[0]
    step = tick(symbol, time)
    up = bar[2] >= high + step*params["min_level_penetration_ticks"] and bar[4] <= high - step*params["min_close_reentry_ticks"]
    down = bar[3] <= low - step*params["min_level_penetration_ticks"] and bar[4] >= low + step*params["min_close_reentry_ticks"]
    if up and down:
        return None, "AMBIGUOUS_BOTH_SIDES"
    if not (up or down):
        return None, "NO_REJECTION"
    direction = -1 if up else 1
    boundary = high if up else low
    stop = bar[2]+step if up else bar[3]-step
    return dict(symbol=symbol, direction=direction, level=boundary, opposite=low if up else high, stop=stop, signal_at=time, window=window_at(time)), None


def analyze(symbol, rows, delay, config):
    """Causal admission pass followed by a separate scheduled-Open-only adapter."""
    params = config["parameters"]
    # Execution adapter exposes no target High/Low/Close. Volume is a retrospective
    # observed-bar flag, not information available to a real order at the Open.
    openings = {bar[0]: (bar[1],bar[5]>0) for bar in rows}
    historic = deque(maxlen=params["level_lookback_completed_m5"])
    last_seen, last_window = None, None
    last_confirmed = {}
    counts = Counter()
    events = []
    scheduled = []
    valid_days = set()
    for bar in rows:
        at = bar[0]
        w = window_at(at) if allowed(symbol, at) else None
        usable = bool(w and bar[5]>0)
        continuous = bool(usable and last_window == w and last_seen is not None and at-last_seen == FIVE)
        if not continuous:
            historic.clear()
            last_confirmed.clear()
        last_seen = at if usable else None
        last_window = w if usable else None
        if not usable:
            continue
        valid_days.add(at.date().isoformat())
        counts["observed_m5"] += 1
        if len(historic) == params["level_lookback_completed_m5"]:
            counts["evaluated_test_bars"] += 1
            step=tick(symbol,at)
            if (bar[2] >= max(x[2] for x in historic)+step
                    or bar[3] <= min(x[3] for x in historic)-step):
                counts["level_penetration_bars"] += 1
        signal, reason = event_signal(symbol,bar,historic,params)
        historic.append(bar)
        if reason == "WARMUP":
            counts["warmup"] += 1
            continue
        if reason == "AMBIGUOUS_BOTH_SIDES":
            counts[reason] += 1
            continue
        if signal is None:
            continue
        counts["raw_rejections"] += 1
        direction = signal["direction"]
        side = "LONG" if direction == 1 else "SHORT"
        if direction in last_confirmed and (at-last_confirmed[direction]).total_seconds() < 60*params["dedup_same_instrument_same_direction_minutes"]:
            counts["DEDUP_30MIN"] += 1
            continue
        last_confirmed[direction] = at
        counts["unique_confirmed"] += 1
        available_at = at + FIVE + timedelta(minutes=delay)
        target_at = next_slot(available_at)
        common = dict(symbol=symbol,scenario=delay,status="",direction=side,signal_at=at.isoformat(sep=" "),available_at=available_at.isoformat(sep=" "),target_at=target_at.isoformat(sep=" "),level=str(signal["level"]),opposite=str(signal["opposite"]),stop=str(signal["stop"]),entry_open=None,risk=None,tick=str(tick(symbol, at)),legacy_take=None,full_net_take=None,legacy_net_reward_to_gross_risk=None,full_net_reward_to_net_stop_loss=None,within_known_range=None,reason="")
        if window_at(target_at)!=w or not allowed(symbol,target_at) or target_at+timedelta(minutes=params["max_session_entry_slack_minutes"])>w[1]:
            common.update(status="NONFILL",reason="SESSION_ENTRY_CUTOFF")
            counts["SESSION_ENTRY_CUTOFF"]+=1
            events.append(common)
            continue
        counts["scheduled_in_window"] += 1
        # Freeze the admission before the execution adapter sees future data.
        scheduled.append((common,signal))
    # Independent conditional execution phase; no feature state can be changed.
    for common,signal in scheduled:
        at=signal["signal_at"]
        target_at=datetime.fromisoformat(common["target_at"])
        direction=signal["direction"]
        target = openings.get(target_at)
        # The target bar is NOT used in event_signal(). Only its scheduled OPEN,
        # known at its own existence event, can conditionally establish geometry.
        if target is None or not target[1]:
            common.update(status="UNKNOWN",reason="MISSING_SCHEDULED_M5_OPEN" if target is None else "ZERO_VOLUME_SCHEDULED_M5")
            counts["UNKNOWN_POSSIBLE_FILL"]+=1
            events.append(common)
            continue
        # Reset pending decisions only for gaps already observable by this Open.
        # With strict future scheduling the next source slot's delivery deadline
        # equals the entry time. Later gaps must never affect this opportunity.
        check = at + FIVE
        known_gap = False
        while check + FIVE + timedelta(minutes=delay) <= target_at:
            observation = openings.get(check)
            if observation is None or not observation[1]:
                known_gap = True
            check += FIVE
        if known_gap:
            common.update(status="NONFILL",reason="OBSERVABLE_GAP_RESET_BEFORE_ENTRY")
            counts["OBSERVABLE_GAP_RESET_BEFORE_ENTRY"] += 1
            events.append(common)
            continue
        openprice = target[0]
        step = tick(symbol,target_at)
        common["entry_open"] = str(openprice)
        if direction * (openprice-signal["level"]) < step:
            common.update(status="NONFILL",reason="OPEN_RECLAIM_NOT_PERSISTENT")
            counts["OPEN_RECLAIM_NOT_PERSISTENT"]+=1
            events.append(common)
            continue
        risk = direction * (openprice-signal["stop"])
        common["risk"] = str(risk)
        if risk <= 0:
            common.update(status="NONFILL",reason="INVALID_RISK")
            counts["INVALID_RISK"]+=1
            events.append(common)
            continue
        if risk < params["min_initial_price_risk_ticks"]*step:
            common.update(status="NONFILL",reason="RISK_BELOW_FOUR_TICKS")
            counts["RISK_BELOW_FOUR_TICKS"]+=1
            events.append(common)
            continue
        # Take prices are purely theoretical; NOTHING after target bar's Open is used.
        legacy_distance = D(3)*risk + D(2)*step
        full_distance = D(3)*risk + D(8)*step
        take_legacy = rounded(openprice+direction*legacy_distance,step,direction==1)
        take_full = rounded(openprice+direction*full_distance,step,direction==1)
        boundary_room = direction*(signal["opposite"]-openprice)
        common.update(status="ELIGIBLE_GEOMETRY",reason="",risk=str(risk),tick=str(step),
                      legacy_take=str(take_legacy),full_net_take=str(take_full),
                      legacy_net_reward_to_gross_risk=str((direction*(take_legacy-openprice)-2*step)/risk),
                      full_net_reward_to_net_stop_loss=str((direction*(take_full-openprice)-2*step)/(risk+2*step)),
                      within_known_range=bool(boundary_room>=full_distance))
        counts["eligible_geometry"]+=1
        events.append(common)
    events.sort(key=lambda row: row["signal_at"])
    return events,counts,valid_days


def aggregate(results):
    by_month,by_day=Counter(),Counter()
    accepted=[]
    for row in results:
        if row["status"] != "ELIGIBLE_GEOMETRY":
            continue
        key=(row["symbol"],row["scenario"],row["signal_at"][:7])
        by_month[key]+=1
        by_day[(row["symbol"],row["scenario"],row["signal_at"][:10])]+=1
        accepted.append(row)
    return by_month,by_day,accepted


def run(all_rows, manifest):
    records, counters,coverage = [],{},{}
    for symbol in SYMBOLS:
        observed_days=set()
        for delay in SCHEMES:
            rows,counts,days=analyze(symbol,all_rows[symbol],delay,manifest)
            records.extend(rows)
            counters[f"{symbol}_{delay}"]=dict(counts)
            observed_days |= days
        coverage[symbol]=dict(source_first=all_rows[symbol][0][0].isoformat(sep=" "),
                              source_last=all_rows[symbol][-1][0].isoformat(sep=" "),
                              observed_allowed_window_dates=sorted(observed_days),
                              rows_2023=len(all_rows[symbol]),protected_year_bytes_read=0)
    monthly,daily,eligible=aggregate(records)
    months=[f"2023-{m:02d}" for m in range(1,13)]
    calendar=[]
    for symbol in SYMBOLS:
        first=all_rows[symbol][0][0]
        last=all_rows[symbol][-1][0]
        for delay in SCHEMES:
            for month in months:
                year,mon=[int(x) for x in month.split("-")]
                obs=sum(d[:7]==month for d in coverage[symbol]["observed_allowed_window_dates"])
                state="NO_COVERAGE" if obs==0 else "PARTIAL_OR_UNVERIFIED_COVERAGE"
                if first.year==year and first.month>mon:
                    state="PRE_INCEPTION_NO_COVERAGE"
                if last.year==year and last.month<mon:
                    state="POST_SOURCE_NO_COVERAGE"
                calendar.append(dict(symbol=symbol,scenario=delay,month=month,observed_dates=obs,coverage=state,
                                     eligible_geometry=monthly.get((symbol,delay,month),0)))
    daily_rows=[dict(symbol=symbol,scenario=delay,day=day,
                     eligible_geometry=daily.get((symbol,delay,day),0))
                for symbol in SYMBOLS for delay in SCHEMES
                for day in coverage[symbol]["observed_allowed_window_dates"]]
    summary={}
    for delay in SCHEMES:
        sub=[x for x in eligible if x["scenario"]==delay]
        days=set().union(*(set(coverage[s]["observed_allowed_window_dates"]) for s in SYMBOLS))
        keys={(x["symbol"],x["direction"],x["signal_at"]) for x in sub}
        if len(keys) != len(sub):
            raise RuntimeError("DUPLICATE_OPPORTUNITY")
        slots=Counter(x["target_at"] for x in sub)
        summary[f"scenario_{delay}"]=dict(eligible_upper_bound=len(sub),observed_union_days=len(days),
                                         eligible_per_observed_union_day=len(sub)/len(days) if days else None,
                                         observed_union_days_with_no_eligible=len(days)-len(set(x["signal_at"][:10] for x in sub)),
                                         distinct_instrument_entry_slots=len({(x["symbol"],x["target_at"]) for x in sub}),
                                         distinct_wall_clock_entry_slots=len(slots),
                                         simultaneous_slots=sum(n>1 for n in slots.values()),
                                         note="No PnL, no guaranteed venue fills, no position-busy simulation; theoretical upper bound.")
        for symbol in SYMBOLS:
            own=[x for x in sub if x["symbol"]==symbol]
            observed=coverage[symbol]["observed_allowed_window_dates"]
            summary[f"{symbol}_{delay}"]=dict(eligible=len(own),observed_days=len(observed),
                eligible_per_observed_day=len(own)/len(observed) if observed else None,
                days_without_opportunities=len(observed)-len({x["signal_at"][:10] for x in own}),
                full_net_3R_within_known_range=sum(x["within_known_range"] for x in own))
    return dict(status="STAGE2_LEVEL_REJECTION_OPPORTUNITIES_ONLY_NO_ECONOMIC_BASELINE_PASS",
                manifest_id=manifest["id"],run_count=len(SCHEMES)*len(SYMBOLS),scenarios=list(SCHEMES),
                summary=summary,counters=counters,coverage=coverage,calendar=calendar,daily=daily_rows,signals=records,
                annual_net=None,annual_pf=None,annual_drawdown=None,
                caveat="No simulated stops/take/profit, unknown scheduled openings are NOT nonfills. No full-year net return or executed trades claimed.")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data-root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    raw=CONFIG.read_bytes()
    manifest=json.loads(raw)
    if manifest["strategy"]!="LEVEL_REJECTION_M5" or manifest["research_mode"]!="NO_FORWARD_PNL_OPPORTUNITY_GEOMETRY_ONLY":
        raise RuntimeError("WRONG_MANIFEST_MODE")
    bars=load_bars(args.data_root,manifest)
    report=run(bars,manifest)
    report["config_sha256"]=hashlib.sha256(raw).hexdigest()
    report["data_provenance"]={symbol:dict(prefix_sha256=manifest["inputs"][symbol]["prefix_sha256"],
                                          prefix_bytes=manifest["inputs"][symbol]["prefix_bytes"],
                                          prefix_rows=manifest["inputs"][symbol]["rows_2023"],source_ref=manifest["source_ref"],
                                          bytes_2024_plus_read=0,bytes_2025_plus_read=0) for symbol in SYMBOLS}
    args.output.mkdir(parents=True,exist_ok=True)
    path=args.output/"opportunity_funnel.json"
    path.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"LEVEL_REJECTION_PREFLIGHT_DATA_ONLY: {path} (NO P&L / NO ECONOMIC PASS)")


if __name__=="__main__":
    main()
