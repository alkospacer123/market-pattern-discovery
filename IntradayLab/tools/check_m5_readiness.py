#!/usr/bin/env python3
"""M5-only coverage diagnostic, NOT a session/entry allowlist or backtest.

Reuses the unchanged frozen-prefix reader and Stage 1.2 candidate calendar.
All clock comparisons assume MSK; that assumption remains UNCONFIRMED.
Only four M5 prefixes are read. JSON is printed; source files are read-only.
"""
import argparse
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
import subprocess

from audit_session_mtf import (CUTOFF, SOURCE_REF, candidate_segments,
                               is_trading_date, read_prefix, verify_index)
from session_mtf import FIVE, IMOEXF_QUARANTINE

LAB = Path(__file__).resolve().parents[1]
CNY_SWITCH = datetime(2023, 9, 27, 19)
BUFFER = FIVE


def envelope(label):
    """Union of [t,t+5) and [t-5,t); conditional on these two meanings."""
    return label - FIVE, label + FIVE


def assumed_available_at(label):
    """Latest possible close + one M5 buffer, not measured feed latency."""
    return label + FIVE + BUFFER


def daytime_windows(day):
    # The existing calendar remains diagnostic, never confirmed=True.
    return [(a, z) for a, z in candidate_segments(day)
            if a.hour >= 10 and z.hour <= 19]


def exclusion(bar):
    a, z = envelope(bar.timestamp)
    q = IMOEXF_QUARANTINE
    if bar.symbol == "IMOEXF" and a < q.end and z > q.start:
        return "quarantine"
    windows = daytime_windows(bar.timestamp.date())
    if not any(s <= bar.timestamp < e for s, e in windows):
        return "outside_candidate_daytime"
    if not any(s <= a and z <= e for s, e in windows):
        return "crosses_candidate_boundary"
    if bar.volume <= 0:
        return "zero_volume"
    return None


def candidate_entry_timing(bar):
    """Schedule-only timing count; does not consult future bar existence/prices.

    At t+10 assume the observation is available and additional decision/order
    delay is zero. Label t+20 has earliest possible start t+15 > t+10.
    Its entire ambiguity envelope must finish by the B-30 no-entry cutoff.
    This is an unapproved model bound, not permission or a guaranteed fill.
    """
    if exclusion(bar):
        return False
    a, z = envelope(bar.timestamp)
    execution_start, execution_end = envelope(bar.timestamp + 4 * FIVE)
    return any(s <= a and z <= e and
               execution_start > assumed_available_at(bar.timestamp) and
               execution_end <= e - timedelta(minutes=30)
               for s, e in daytime_windows(bar.timestamp.date()))


def dated_cny_grid(bars):
    counts = Counter({"old_grid_bars": 0, "new_grid_bars": 0,
                      "switch_ambiguous_bars": 0, "off_grid_price_fields": 0})
    for b in bars:
        a, z = envelope(b.timestamp)
        if a < CNY_SWITCH < z:
            counts["switch_ambiguous_bars"] += 1
            continue
        old = z <= CNY_SWITCH
        counts["old_grid_bars" if old else "new_grid_bars"] += 1
        step = Decimal("0.01" if old else "0.001")
        counts["off_grid_price_fields"] += sum(v % step != 0 for v in b.ohlcv[:4])
    return dict(counts)


def summarize(bars):
    reasons = Counter({k: 0 for k in ("quarantine", "outside_candidate_daytime",
                                     "crosses_candidate_boundary", "zero_volume")})
    kept = []
    for b in bars:
        reason = exclusion(b)
        if reason:
            reasons[reason] += 1
        else:
            kept.append(b)
    observed = {b.timestamp.date() for b in bars}
    expected = set()
    day = bars[0].timestamp.date()
    while day < CUTOFF.date():
        if is_trading_date(day):
            expected.add(day)
        day += timedelta(days=1)
    # Missing slots are diagnostic, not inserted candles or advance knowledge
    # for a strategy. No future bar is consulted to authorize a current signal.
    slots = set()
    for day in sorted(expected):
        for a, z in daytime_windows(day):
            t = a + FIVE
            while t + FIVE <= z:
                slots.add(t)
                t += FIVE
    labels = {b.timestamp for b in bars}
    missing = slots - labels
    timing = [b for b in kept if candidate_entry_timing(b)]
    return {
        "raw_bars": len(bars), "raw_dates": len(observed),
        "potential_observation_bars": len(kept),
        "potential_dates": len({b.timestamp.date() for b in kept}),
        "potential_entry_timing_bars": len(timing),
        "potential_entry_timing_dates": len({b.timestamp.date() for b in timing}),
        "flat_reserve_timing_exclusions": len(kept) - len(timing),
        "first_potential_label": str(kept[0].timestamp) if kept else None,
        "last_potential_label": str(kept[-1].timestamp) if kept else None,
        "exclusive_exclusion_reasons": dict(sorted(reasons.items())),
        "missing_candidate_slots": len(missing),
        "missing_slots_on_absent_dates": sum(t.date() not in observed for t in missing),
        "missing_expected_dates": sorted(str(d) for d in expected - observed),
        "authorized_bars": 0, "authorized_dates": 0,
    }


def check(data_root):
    manifest = json.loads((LAB / "data/forever_input_manifest_20261008.json").read_text())
    prior = json.loads((LAB / "reports/STAGE1_2_SESSION_MTF_RESULTS.json").read_text())
    if (manifest["source_ref"] != SOURCE_REF or
            manifest["development_exclusive_end"] != str(CUTOFF)):
        raise ValueError("Unexpected frozen manifest")
    verify_index(data_root, manifest)
    def status():
        return subprocess.check_output(["git", "-C", str(data_root.parent), "status",
                                        "--porcelain=v1", "--untracked-files=all"], text=True)
    if status():
        raise ValueError("Data checkout must be clean")
    result = {"verdict": "STAGE1_M5_READINESS_BLOCKED", "source_ref": SOURCE_REF,
              "clock_hypothesis": "MSK, start OR end; UNCONFIRMED",
              "availability_assumption": "label + 10 minutes; UNAPPROVED",
              "counts_are_entry_allowlist": False, "future_bytes_read": 0,
              "strategy_runs": 0, "orders": 0, "coverage": {}}
    for symbol, tfs in manifest["instruments"].items():
        path = data_root / symbol / f"{symbol}_M5.csv"
        before = path.stat()
        bars, stats = read_prefix(path, symbol, "M5", tfs["M5"])
        previous = prior["coverage"][symbol]["M5"]
        for key in ("prefix_bytes_read", "prefix_sha256", "rows", "first", "last"):
            if stats[key] != previous[key]:
                raise ValueError("M5 prefix differs from Stage 1.2")
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns,
                before.st_ino, before.st_mode) != (after.st_size, after.st_mtime_ns,
                after.st_ctime_ns, after.st_ino, after.st_mode):
            raise ValueError("Data metadata changed")
        result["coverage"][symbol] = summarize(bars) | {"prefix": stats}
        if symbol == "CNYRUBF":
            result["coverage"][symbol]["dated_tick_grid_under_clock_hypothesis"] = dated_cny_grid(bars)
    if status():
        raise ValueError("Data checkout changed")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.data_root.resolve()), indent=2, sort_keys=True))
