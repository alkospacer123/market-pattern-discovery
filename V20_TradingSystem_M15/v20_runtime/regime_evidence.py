"""V20 offline evidence-only regime change check.

Tests change in frozen FP2 probability; not a suitability classifier.
Uses fixed chronological, nonoverlapping raw horizons and exact conditional
binomial tests with a lifetime (repeated-look) error budget per instrument.

Its 5% error bound is conditional on iid/exchangeable Bernoulli null;
futures observations are not proven iid. This module never places orders.
"""
from __future__ import annotations
from datetime import datetime
from math import comb, isfinite
from statistics import mean

BASELINE = 80
LATEST = 80
STRIDE = 40
FAMILY_ALPHA = 0.05
STALENESS_DAYS = 90


def time_of(v):
    t = datetime.fromisoformat(v) if isinstance(v, str) else v
    if not isinstance(t, datetime) or t.tzinfo is not None:
        raise ValueError("MSK_NAIVE_REQUIRED")
    return t


def exact_lower_tail(base_n, base_yes, latest_n, latest_yes):
    """P(Hypergeom <= observed recent successes | pooled successes)."""
    n, m = int(base_n), int(latest_n)
    a, b = int(base_yes), int(latest_yes)
    if min(n, m) <= 0 or not (0 <= a <= n and 0 <= b <= m):
        raise ValueError("INVALID_FP2_COUNTS")
    successes = a + b
    denominator = comb(n + m, successes)
    return min(1.0, sum(
        comb(m, j) * comb(n, successes - j) / denominator
        for j in range(max(0, successes - n), b + 1)
        if j <= m and successes - j <= n))


def observed_independent_events(rows, instrument, as_of):
    at = time_of(as_of)
    offered = []
    keys = set()
    for row in rows:
        if row["instrument"].upper() != instrument.upper():
            continue
        end = time_of(row["available"])
        if end > at:
            continue  # do NOT read future FP2 values before the horizon is complete
        start = time_of(row["signal"])
        key = (start, row["contract"])
        if key in keys:
            raise ValueError("DUPLICATE_PUBLISHED_MARKET_EVENT")
        keys.add(key)
        if start >= end or row["fp2"] not in (0, 1, False, True):
            raise ValueError("INVALID_COMPLETED_FP2_PATH")
        offered.append(dict(start=start, end=end, fp2=int(row["fp2"])))
    offered.sort(key=lambda e: (e["start"], e["end"]))
    selected = []
    last_end = None
    for event in offered:
        if last_end is None or event["start"] >= last_end:
            selected.append(event)
            last_end = event["end"]
    return selected


def evidence_card(rows, instrument, as_of):
    """Only confirmed movement of FP2; silence is NOT a favorable market."""
    at = time_of(as_of)
    if not instrument or not instrument.replace("_", "").isalnum():
        raise ValueError("INVALID_SYMBOL")
    selected = observed_independent_events(rows, instrument, at)
    checks = []
    for n in range(BASELINE + LATEST, len(selected) + 1, STRIDE):
        base = selected[:BASELINE]
        recent = selected[n-LATEST:n]
        old_successes = sum(e["fp2"] for e in base)
        new_successes = sum(e["fp2"] for e in recent)
        down_p = exact_lower_tail(BASELINE, old_successes, LATEST, new_successes)
        up_p = exact_lower_tail(LATEST, LATEST-new_successes,
                                BASELINE, BASELINE-old_successes)
        number = len(checks) + 1
        # Sum_{k>=1} 1/(k*(k+1)) = 1. Split 5% between both directions.
        alpha_each = (FAMILY_ALPHA / 2) / (number * (number + 1))
        direction = ("FP2_DROP_EVIDENCE" if down_p <= alpha_each else
                     "FP2_RECOVERY_EVIDENCE" if up_p <= alpha_each else
                     "UNPROVEN")
        checks.append(dict(index=number, n=n, observed_at=selected[n-1]["end"].isoformat(),
                           ref_fp2=old_successes / BASELINE,
                           latest_fp2=new_successes / LATEST,
                           p_down=down_p, p_up=up_p, alpha=alpha_each,
                           direction=direction))
    last_check = checks[-1] if checks else None
    old = selected[:BASELINE]
    latest = selected[-min(LATEST, len(selected)):]
    last_seen = selected[-1]["end"] if selected else None
    status = "INSUFFICIENT_EVIDENCE"
    if last_check and last_seen is not None and (at-last_seen).days <= STALENESS_DAYS:
        status = last_check["direction"]
    return dict(schema="v20.regime_evidence.offline.v1", symbol=instrument.upper(),
                as_of_msk=at.isoformat(), independent_completed_paths=len(selected),
                baseline_n=len(old), latest_n=len(latest),
                baseline_fp2=mean(x["fp2"] for x in old) if old else None,
                latest_fp2=mean(x["fp2"] for x in latest) if latest else None,
                last_path_completed=last_seen.isoformat() if last_seen else None,
                checks=checks, last_status=status,
                alpha_assuming_exchangeable_null=FAMILY_ALPHA,
                predictive_reliability_validated=False,
                iid_exchangeability_validated=False,
                affects_orders_or_risk=False)


def main(argv=None):
    """Independent research invocation; never changes the operator card."""
    import argparse
    import csv
    import hashlib
    import json
    from pathlib import Path
    from zoneinfo import ZoneInfo

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbol", required=True)
    p.add_argument("--as-of", default=None)
    p.add_argument("--events", type=Path, default=Path(__file__).resolve().parents[1] /
                   "V20-04/REGIME_EVENTS.csv")
    opts = p.parse_args(argv)
    as_of = (time_of(opts.as_of) if opts.as_of
             else datetime.now(ZoneInfo("Europe/Moscow")).replace(
                 tzinfo=None, second=0, microsecond=0))
    expected = "35cf524fda42d025feec35a39c9605669fc532d6d1107b23b698ecff3d348a5b"
    if hashlib.sha256(opts.events.read_bytes()).hexdigest() != expected:
        raise ValueError("PUBLISHED_REGIME_EVENTS_SHA_MISMATCH")
    rows = []
    with opts.events.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["instrument"].upper() != opts.symbol.upper():
                continue
            if time_of(row["available"]) <= as_of:
                row["fp2"] = int(row["fp2"])
            rows.append(row)
    print(json.dumps(evidence_card(rows, opts.symbol, as_of),
                     ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
