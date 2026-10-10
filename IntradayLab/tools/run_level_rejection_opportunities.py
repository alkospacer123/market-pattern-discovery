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
        with (root / spec["path"]).open("rb") as f:
            content = f.read(spec["prefix_bytes"])
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
            if stamp.year != 2023 or (previous is not None and stamp <= previous):
                raise RuntimeError("SOURCE_DATE_OR_ORDER")
            previous = stamp
            o,h,l,c,v = [D(x) for x in fields[2:]]
            if not (l <= min(o,c) <= max(o,c) <= h and v >= 0):
                raise RuntimeError("SOURCE_OHLCV")
            step = tick(symbol,stamp)
            if any(price % step for price in (o,h,l,c)):
                raise RuntimeError("SOURCE_PRICE_GRID")
            rows.append((stamp,o,h,l,c,v))
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
    """One time-ordered pass. Future candle inspection: Open only, target pre-scheduled."""
    params = config["parameters"]
    idx = {bar[0]: bar for bar in rows}
    historic = deque(maxlen=params["level_lookback_completed_m5"])
    last_seen, last_window = None, None
    last_confirmed = {}
    counts = Counter()
    events = []
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
        common = dict(symbol=symbol,scenario=delay,status="",direction=side,signal_at=at.isoformat(sep=" "),available_at=available_at.isoformat(sep=" "),target_at=target_at.isoformat(sep=" "),level=str(signal["level"]),stop=str(signal["stop"]),entry_open=None,risk=None,tick=str(tick(symbol, at)),legacy_take=None,full_net_take=None,within_known_range=None,reason="")
        if window_at(target_at)!=w or not allowed(symbol,target_at) or target_at+timedelta(minutes=params["max_session_entry_slack_minutes"])>w[1]:
            common.update(status="NONFILL",reason="SESSION_ENTRY_CUTOFF")
            counts["SESSION_ENTRY_CUTOFF"]+=1
            events.append(common)
            continue
        target = idx.get(target_at)
        # The target bar is NOT used in event_signal(). Only its scheduled OPEN,
        # known at its own existence event, can conditionally establish geometry.
        if target is None or target[5]<=0:
            common.update(status="UNKNOWN",reason="MISSING_SCHEDULED_M5_OPEN")
            counts["UNKNOWN_POSSIBLE_FILL"]+=1
            events.append(common)
            continue
        openprice = target[1]
        step = tick(symbol,target_at)
        common["entry_open"] = str(openprice)
        if direction * (openprice-signal["level"]) < step:
            common.update(status="NONFILL",reason="OPEN_RECLAIM_NOT_PERSISTENT")
            counts["OPEN_RECLAIM_NOT_PERSISTENT"]+=1
            events.append(common)
            continue
        risk = direction * (openprice-signal["stop"])
        common["risk"] = str(risk)
        if risk < params["min_initial_price_risk_ticks"]*step:
            common.update(status="NONFILL",reason="RISK_BELOW_FOUR_TICKS")
            counts["RISK_BELOW_FOUR_TICKS"]+=1
            events.append(common)
            continue
        if risk <= 0:
            common.update(status="NONFILL",reason="INVALID_RISK")
            counts["INVALID_RISK"]+=1
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
                      within_known_range=bool(boundary_room>=full_distance))
        counts["eligible_geometry"]+=1
        events.append(common)
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
    daily_rows=[]
    for (symbol,delay,day),n in sorted(daily.items()):
        daily_rows.append(dict(symbol=symbol,scenario=delay,day=day,eligible_geometry=n))
    summary={}
    for delay in SCHEMES:
        sub=[x for x in eligible if x["scenario"]==delay]
        days=set().union(*(set(coverage[s]["observed_allowed_window_dates"]) for s in SYMBOLS))
        concurrent={}
        # This is NOT a filled-positions model. Same instrument entry timing duplicates
        # are collapsed only for a capacity proxy; no exit path is examined.
        for row in sorted(sub,key=lambda x:(x["target_at"],x["symbol"])):
            t=datetime.fromisoformat(row["target_at"])
            old=concurrent.get(row["symbol"])
            if old is not None and t-old < timedelta(minutes=30):
                continue
            concurrent[row["symbol"]]=t
            day=row["signal_at"][:10]
            summary.setdefault(f"scenario_{delay}_capacity_proxy_daily",{})
            proxy=summary[f"scenario_{delay}_capacity_proxy_daily"]
            proxy[day]=proxy.get(day,0)+1
        summary[f"scenario_{delay}"]=dict(eligible_upper_bound=len(sub),observed_union_days=len(days),
                                         eligible_per_observed_union_day=len(sub)/len(days) if days else None,
                                         observed_union_days_with_no_eligible=len(days)-len(set(x["signal_at"][:10] for x in sub)),
                                         capacity_proxy_entries=sum(summary.get(f"scenario_{delay}_capacity_proxy_daily",{}).values()),
                                         note="No PnL, no guaranteed venue fills, no position-busy simulation; theoretical upper bound.")
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
