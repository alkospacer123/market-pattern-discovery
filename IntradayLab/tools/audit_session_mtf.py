#!/usr/bin/env python3
"""Offline, deterministic pre-2025 diagnostic audit using the frozen manifest.

Run with Python 3.12; --data-root points to read-only market-pattern-data/forever.
No whole-file reads/hashes, EOF probes, future-row counts, strategies or fills.
Only header + manifest['rows'] LF-terminated records are physically read.
Historical calendar comparisons are conditional on the unconfirmed start/MSK
hypothesis and never authorize SessionWindow or TimestampEvidence for real use.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

from session_mtf import (Bar, IMOEXF_QUARANTINE, TimestampEvidence, aggregate,
                         align_contexts, bounded_lines, interval)

MINUTES = {"M5": 5, "M15": 15, "M30": 30, "H1": 60}
HEADER = ["Ticker", "Datetime", "Open", "High", "Low", "Close", "Volume"]
CUTOFF = datetime(2025, 1, 1)
SOURCE_REF = "f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8"
WORKING_SATURDAYS = {date(2024, 4, 27), date(2024, 11, 2), date(2024, 12, 28)}
HOLIDAYS = {(1, 1), (1, 2), (1, 7), (2, 23), (3, 8), (5, 1), (5, 9), (6, 12), (11, 4)}
# Concise verified facts, not an assertion of an exhaustive event archive.
SOURCES = [
    {"id": "MOEX_2023_CALENDAR", "url": "https://www.moex.com/n51887",
     "fact": "2023 exchange holidays and exceptional trading weekdays"},
    {"id": "MOEX_2024_CALENDAR", "url": "https://www.moex.com/n64121",
     "published": "2023-09-20", "fact": "2024 exchange holidays, trading holidays and three working Saturdays"},
    {"id": "MOEX_DEC2024", "url": "https://www.moex.com/n75066",
     "fact": "No trading 29/31 December 2024; trading 28/30 December"},
    {"id": "CBR_CALENDAR", "url": "https://www.cbr.ru/other/holidays/",
     "fact": "2023/2024 civil holidays and 2024 working Saturdays; not an exchange session calendar"},
    {"id": "MOEX_MORNING", "url": "https://www.moex.com/n51095",
     "published": "2022-09-01", "fact": "From 12 September 2022: morning 09-10, main 10-19, evening 19:05-23:50 MSK"},
    {"id": "MOEX_ALL_INSTRUMENTS", "url": "https://www.moex.com/n51208",
     "published": "2022-09-06", "fact": "All instruments eligible for evening from 9 September and morning from 12 September 2022"},
    {"id": "MOEX_MAR2023_EXTENSION", "url": "https://www.moex.com/n55032",
     "published": "2023-03-13", "fact": "Announced clearing resumes at 14:15/19:15 for 13-24 March"},
    {"id": "MOEX_MAR2023_REVERSION", "url": "https://www.moex.com/n55200",
     "published": "2023-03-21", "fact": "Later notice restores 14:05/19:05 from 21 March"},
    {"id": "MOEX_CLEARING_STANDARD", "url": "https://www.moex.com/n73111",
     "published": "2024-09-17", "fact": "Standard evening clearing 18:50-19:05; 19 September 2024 extended to 19:20, possibly another 30 minutes"},
    {"id": "MOEX_SEP2023_FINAL", "url": "https://www.moex.com/n63905",
     "published": "2023-09-13", "fact": "Halt 09:30; morning trades 08:50-09:30 cancelled; final restart decision 13:30"},
    {"id": "MOEX_SEP2023_EARLIER", "url": "https://www.moex.com/n63887",
     "published": "2023-09-13", "fact": "Earlier planned restart 13:00, superseded by final notice"},
    {"id": "MOEX_NOV2024", "url": "https://www.moex.com/n75020",
     "published": "2024-11-19", "fact": "Halt 16:18; system ready 16:32; announced trading restart 16:50"},
    {"id": "MOEX_AUG2024_EQUITIES", "url": "https://www.moex.com/n71971",
     "published": "2024-08-14", "fact": "14 August equity-market interruption; derivatives reported operating normally; not evidence for 16 August IMOEXF"},
]


def is_trading_date(day: date) -> bool | None:
    if day.year not in (2023, 2024):
        return None
    if (day.month, day.day) in HOLIDAYS or day == date(2024, 12, 31):
        return False
    return day.weekday() < 5 or day in WORKING_SATURDAYS


def candidate_segments(day: date) -> list[tuple[datetime, datetime]]:
    """Diagnostic MSK/start hypothesis only. Not a confirmed session service.

    Standard daytime clearing start 14:00 lacks a complete dated archive.
    The 19 September actual extension endpoint is unresolved: conservatively
    exclude the whole possible extension through 19:50. Morning eligibility
    of later-listed contracts and all exceptional regimes remain unresolved.
    """
    if not is_trading_date(day):
        return []
    def at(h, m=0):
        return datetime(day.year, day.month, day.day, h, m)
    extended = date(2023, 3, 13) <= day < date(2023, 3, 21)
    afternoon = at(14, 15 if extended else 5)
    evening = at(19, 15 if extended else 5)
    segments = [(at(9), at(10)), (at(10), at(14)), (afternoon, at(18, 50)), (evening, at(23, 50))]
    if day == date(2023, 9, 13):
        segments = [(at(13, 30), at(14)), (afternoon, at(18, 50)), (evening, at(23, 50))]
    if day == date(2024, 9, 19):
        segments[-1] = (at(19, 50), at(23, 50))
    if day == date(2024, 11, 19):
        segments[2:3] = [(afternoon, at(16, 18)), (at(16, 50), at(18, 50))]
    return segments


def read_prefix(path: Path, symbol: str, tf: str, expected: dict) -> tuple[list[Bar], dict]:
    count = expected["rows"]
    if type(count) is not int or count < 1:
        raise ValueError("Invalid frozen row budget")
    if not (datetime.fromisoformat(expected["first"]) <= datetime.fromisoformat(expected["last"]) < CUTOFF):
        raise ValueError("Manifest crosses TRUE OOS")
    digest = hashlib.sha256()
    bars, nbytes = [], 0
    before = path.stat()
    # FileIO has no read-ahead. bounded_lines never requests beyond final LF.
    with path.open("rb", buffering=0) as raw:
        if not isinstance(raw, io.FileIO):
            raise TypeError("Unbuffered FileIO required")
        for i, line in enumerate(bounded_lines(raw, count + 1)):
            digest.update(line)
            nbytes += len(line)
            row = next(csv.reader([line.decode("utf-8-sig" if i == 0 else "utf-8")], delimiter=";"))
            if i == 0:
                if row != HEADER:
                    raise ValueError("Unexpected CSV header")
                continue
            if len(row) != 7 or row[0] != symbol:
                raise ValueError("Malformed record/ticker")
            t = datetime.fromisoformat(row[1])
            # Verify time BEFORE parsing numeric fields. Budget is independently
            # supplied by the already frozen manifest, never found via OOS scan.
            if t.tzinfo is not None or t >= CUTOFF or t.second or t.microsecond or (t.hour * 60 + t.minute) % MINUTES[tf]:
                raise ValueError("Protected or unaligned timestamp inside frozen prefix")
            values = tuple(Decimal(s) for s in row[2:])
            if (not all(v.is_finite() for v in values) or min(values[:4]) <= 0 or
                    values[1] < max(values[0], values[2], values[3]) or
                    values[2] > min(values[0], values[1], values[3]) or values[4] < 0):
                raise ValueError("Invalid OHLCV")
            if bars and t <= bars[-1].timestamp:
                raise ValueError("Duplicate/unordered timestamp")
            bars.append(Bar(t, *values, symbol=symbol))
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError("Source changed during read")
    if (len(bars) != count or str(bars[0].timestamp) != expected["first"] or
            str(bars[-1].timestamp) != expected["last"]):
        raise ValueError("Frozen prefix coverage mismatch")
    return bars, {"rows": len(bars), "first": str(bars[0].timestamp), "last": str(bars[-1].timestamp),
                  "prefix_bytes_read": nbytes, "prefix_sha256": digest.hexdigest(),
                  "frozen_blob_id": expected["blob"], "future_bytes_read": 0,
                  "year_rows": dict(sorted(Counter(str(b.timestamp.year) for b in bars).items()))}


def compare_labels(m5: list[Bar], parents: list[Bar], minutes: int, label: str) -> dict:
    groups = defaultdict(list)
    for b in m5:
        start, _ = interval(b, 5, label)
        anchor = start.replace(minute=(start.minute // minutes) * minutes, second=0)
        groups[anchor].append(b)
    low, high = interval(m5[0], 5, label)[0], interval(m5[-1], 5, label)[0]
    stats = Counter({k: 0 for k in ("parents_in_overlap", "complete_exact", "complete_mismatch",
                                   "partial_exact", "partial_mismatch", "no_m5_bucket", "m5_bucket_without_parent")})
    missing = []
    parent_starts = set()
    for p in parents:
        start, _ = interval(p, minutes, label)
        parent_starts.add(start)
        if not (low <= start <= high):
            continue
        stats["parents_in_overlap"] += 1
        children = groups.get(start, [])
        if not children:
            stats["no_m5_bucket"] += 1
            missing.append(str(p.timestamp))
            continue
        complete = [interval(b, 5, label)[0] for b in children] == [start + timedelta(minutes=5 * i) for i in range(minutes // 5)]
        equal = aggregate(children, p.timestamp).ohlcv == p.ohlcv
        stats[("complete" if complete else "partial") + ("_exact" if equal else "_mismatch")] += 1
    orphan_buckets = sorted(t for t in groups if t not in parent_starts)
    stats["m5_bucket_without_parent"] = len(orphan_buckets)
    def summary(labels):
        return {"count": len(labels), "first": labels[0] if labels else None,
                "last": labels[-1] if labels else None,
                "clock_counts": dict(sorted(Counter(t[11:] for t in labels).items())),
                "by_year": dict(sorted(Counter(t[:4] for t in labels).items())),
                "dates_with_multiple": {d: n for d, n in sorted(Counter(t[:10] for t in labels).items()) if n > 1}}
    return dict(stats) | {"missing_parent_labels": missing[:30],
                          "no_m5_summary": summary(missing),
                          "m5_bucket_without_parent_summary": summary([str(t) for t in orphan_buckets])}


def session_diagnostics(m5: list[Bar]) -> dict:
    bars = [b for b in m5 if b.timestamp.year in (2023, 2024)]
    observed = {b.timestamp.date() for b in bars}
    begin, end = min(observed), date(2024, 12, 31)
    expected = set()
    current = begin
    while current <= end:
        if is_trading_date(current):
            expected.add(current)
        current += timedelta(days=1)
    grid = {b.timestamp for b in bars}
    missing = Counter()
    outside = []
    for day in sorted(observed):
        for start, stop in candidate_segments(day):
            t = start
            while t + timedelta(minutes=5) <= stop:
                if t not in grid:
                    missing["morning" if t.hour < 10 else "evening" if t.hour >= 19 else "daytime"] += 1
                t += timedelta(minutes=5)
    for b in bars:
        t = b.timestamp
        if not any(a <= t and t + timedelta(minutes=5) <= z for a, z in candidate_segments(t.date())):
            outside.append(str(t))
    intraday_gaps = Counter()
    for left, right in zip(bars, bars[1:]):
        if left.timestamp.date() == right.timestamp.date() and right.timestamp - left.timestamp > timedelta(minutes=5):
            intraday_gaps[str(int((right.timestamp - left.timestamp).total_seconds() // 60))] += 1
    return {"calendar_status": "PASS" if observed <= expected and expected <= observed else "FAIL",
            "conditional_clock_hypothesis": "MSK/start (UNRESOLVED)",
            "dates_observed": len(observed), "expected_dates": len(expected),
            "unexpected_dates": sorted(str(d) for d in observed - expected),
            "missing_expected_dates": sorted(str(d) for d in expected - observed),
            "observed_working_saturdays": sorted(str(d) for d in observed & WORKING_SATURDAYS),
            "first_clock_label": min(b.timestamp.time().isoformat() for b in bars),
            "last_clock_label": max(b.timestamp.time().isoformat() for b in bars),
            "candidate_missing_m5_slots_UNRESOLVED": dict(sorted(missing.items())),
            "outside_candidate_full_bar_count_UNRESOLVED": len(outside),
            "outside_candidate_examples": outside[:20],
            "outside_candidate_clock_counts": dict(sorted(Counter(t[11:] for t in outside).items())),
            "intraday_gap_minutes_histogram_UNRESOLVED": dict(sorted(intraday_gaps.items(), key=lambda kv: int(kv[0])))}


def verify_index(data_root: Path, manifest: dict) -> None:
    repo = data_root.parent
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
    if git("rev-parse", "HEAD") != manifest["source_ref"]:
        raise ValueError("Data checkout differs from frozen source_ref")
    if len(list(data_root.rglob("*.csv"))) != 16:
        raise ValueError("Expected exactly 16 CSV files")
    for symbol, tfs in manifest["instruments"].items():
        for tf, info in tfs.items():
            entry = git("ls-files", "-s", "--", f"forever/{symbol}/{symbol}_{tf}.csv").split()
            if len(entry) != 4 or entry[1] != info["blob"] or entry[2] != "0":
                raise ValueError("Indexed CSV identity mismatch")


def audit(data_root: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest["source_ref"] != SOURCE_REF or
            manifest["development_exclusive_end"] != str(CUTOFF) or
            set(manifest["instruments"]) != {"USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"} or
            any(set(tfs) != set(MINUTES) for tfs in manifest["instruments"].values())):
        raise ValueError("Unexpected frozen manifest")
    verify_index(data_root, manifest)
    result = {"status": "STAGE1_2_IMPLEMENTED_PENDING_AUDIT", "stage1": "OPEN",
              "real_mtf_authorized": False, "admitted_real_contexts": 0,
              "cutoff_exclusive": str(CUTOFF), "source_ref": SOURCE_REF,
              "python_required": "3.12", "read_policy": "unbuffered frozen line budget; no next-row/EOF probe",
              "identity_limit": "Indexed blob IDs verified; whole blob content NOT rehashed because it includes TRUE OOS",
              "sources_checked_on": "2026-10-09", "sources": SOURCES,
              "gates": {"bounded_prefix_read": "PASS", "historical_calendar_dates": "PASS",
                        "complete_start_label_ohlcv_agreement": "PASS", "mtf_composition_coverage": "PASS",
                        "full_historical_session_archive": "UNRESOLVED", "csv_timezone": "UNRESOLVED",
                        "csv_start_or_end_label": "UNRESOLVED", "exchange_trading_day_mapping": "UNRESOLVED",
                        "IMOEXF_20240816_integrity": "FAIL", "IMOEXF_20240816_cause": "UNRESOLVED",
                        "real_mtf_readiness": "FAIL"},
              "quarantine": {"symbol": "IMOEXF", "start_in_csv_clock": str(IMOEXF_QUARANTINE.start),
                             "end_exclusive_in_csv_clock": str(IMOEXF_QUARANTINE.end), "timeframes": list(MINUTES),
                             "cause": "UNRESOLVED", "reason": IMOEXF_QUARANTINE.reason},
              "coverage": {}, "mtf_label_hypotheses": {}, "sessions": {}, "causal_real_diagnostics": {},
              "known_events_in_csv_clock_hypothesis": {}, "anomaly": {},
              "strategy_runs": 0, "real_orders": 0}
    total_rows = 0
    for symbol, tfs in manifest["instruments"].items():
        arrays = {}
        result["coverage"][symbol] = {}
        for tf in MINUTES:
            path = data_root / symbol / f"{symbol}_{tf}.csv"
            arrays[tf], stats = read_prefix(path, symbol, tf, tfs[tf])
            result["coverage"][symbol][tf] = stats
            total_rows += stats["rows"]
        m5 = arrays["M5"]
        result["sessions"][symbol] = session_diagnostics(m5)
        if result["sessions"][symbol]["calendar_status"] != "PASS":
            result["gates"]["historical_calendar_dates"] = "FAIL"
        result["mtf_label_hypotheses"][symbol] = {
            tf: {label: compare_labels(m5, arrays[tf], MINUTES[tf], label) for label in ("start", "end")}
            for tf in ("M15", "M30", "H1")}
        for labels in result["mtf_label_hypotheses"][symbol].values():
            stats = labels["start"]
            if stats["complete_mismatch"]:
                result["gates"]["complete_start_label_ohlcv_agreement"] = "FAIL"
            if stats["no_m5_bucket"] or stats["m5_bucket_without_parent"] or stats["partial_exact"] or stats["partial_mismatch"]:
                result["gates"]["mtf_composition_coverage"] = "FAIL"
        result["causal_real_diagnostics"][symbol] = {}
        for tf in ("M15", "M30", "H1"):
            decisions = align_contexts(m5, arrays[tf], MINUTES[tf], TimestampEvidence())
            result["causal_real_diagnostics"][symbol][tf] = {
                "admitted": sum(d.parent is not None for d in decisions),
                "blocked_reasons": dict(sorted(Counter(d.reason for d in decisions).items())),
                "zero_admissions_proves_readiness": False}
            result["admitted_real_contexts"] += result["causal_real_diagnostics"][symbol][tf]["admitted"]
        events = {}
        for day in (date(2023, 3, 13), date(2023, 3, 21), date(2023, 8, 31), date(2023, 9, 13),
                    date(2024, 8, 16), date(2024, 9, 19), date(2024, 11, 19)):
            events[str(day)] = {tf: {"rows": len(selected),
                                    "first": str(selected[0].timestamp) if selected else None,
                                    "last": str(selected[-1].timestamp) if selected else None,
                                    "labels_13_14": [str(b.timestamp.time()) for b in selected if b.timestamp.hour in (13, 14)],
                                    "labels_16_17": [str(b.timestamp.time()) for b in selected if b.timestamp.hour in (16, 17)],
                                    "labels_18_19": [str(b.timestamp.time()) for b in selected if b.timestamp.hour in (18, 19)]}
                                for tf, bars in arrays.items()
                                for selected in [[b for b in bars if b.timestamp.date() == day]]}
        result["known_events_in_csv_clock_hypothesis"][symbol] = events
        if symbol == "IMOEXF":
            day = date(2024, 8, 16)
            result["anomaly"] = {"date": str(day), "instrument": symbol,
                "last_label_by_tf": {tf: str(max(b.timestamp for b in bars if b.timestamp.date() == day)) for tf, bars in arrays.items()},
                "M15_evening_labels_without_M5": result["mtf_label_hypotheses"][symbol]["M15"]["start"]["missing_parent_labels"],
                "quarantined_rows_by_tf_under_start_hypothesis": {
                    tf: sum(interval(b, MINUTES[tf], "start")[0] < IMOEXF_QUARANTINE.end and
                            interval(b, MINUTES[tf], "start")[1] > IMOEXF_QUARANTINE.start for b in bars)
                    for tf, bars in arrays.items()},
                "other_instruments_20240816_last_labels": {}}
    result["total_historical_rows"] = total_rows
    result["rows_2022_validated_without_session_audit"] = sum(s["year_rows"].get("2022", 0) for tfs in result["coverage"].values() for s in tfs.values())
    result["rows_2023_2024"] = total_rows - result["rows_2022_validated_without_session_audit"]
    result["total_prefix_bytes_read"] = sum(s["prefix_bytes_read"] for tfs in result["coverage"].values() for s in tfs.values())
    result["future_bytes_read"] = 0
    for symbol in ("USDRUBF", "CNYRUBF", "GLDRUBF"):
        result["anomaly"]["other_instruments_20240816_last_labels"][symbol] = {
            tf: result["known_events_in_csv_clock_hypothesis"][symbol]["2024-08-16"][tf]["last"] for tf in MINUTES}
    return result


def main() -> None:
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Python 3.12 required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[1] / "data/forever_input_manifest_20261008.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Prevent accidentally overwriting source, frozen documentation or unrelated
    # projects. Only the Stage 1.2 JSON or IntradayLab/work/ diagnostics allowed.
    lab = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output != lab / "reports/STAGE1_2_SESSION_MTF_RESULTS.json" and not output.is_relative_to(lab / "work"):
        raise SystemExit("Output must be Stage 1.2 results or IntradayLab/work/")
    result = audit(args.data_root.resolve(), args.manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "total_historical_rows", "future_bytes_read", "admitted_real_contexts")}, sort_keys=True))


if __name__ == "__main__":
    main()
