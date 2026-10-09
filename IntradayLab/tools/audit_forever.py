#!/usr/bin/env python3
"""Read-only OHLCV audit for the exact IntradayLab forever inputs.

Usage:
  python IntradayLab/tools/audit_forever.py \
      --data-root /path/to/market-pattern-data/forever \
      --output /path/to/stage1_audit.json

No dependencies, no network, no strategy execution. Git blob SHA-1 is verified
for each CSV. Numeric prices from 2025+ are never parsed. Times are treated
as naive timestamp labels; this script does not establish their timezone.
"""
import argparse
import csv
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path


TIMEFRAME_MINUTES = {"M5": 5, "M15": 15, "M30": 30, "H1": 60}
EXPECTED_HEADER = ["Ticker", "Datetime", "Open", "High", "Low", "Close", "Volume"]


def blob_sha(raw):
    payload = b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    return hashlib.sha1(payload).hexdigest()


def parse_csv(path, symbol, tf, expected, cutoff):
    raw = path.read_bytes()
    actual_sha = blob_sha(raw)
    if actual_sha != expected["blob"]:
        raise ValueError(f"Git blob SHA mismatch for {path}: {actual_sha}")
    text = raw.decode("utf-8-sig")
    rows = csv.reader(text.splitlines(), delimiter=";")
    if next(rows, None) != EXPECTED_HEADER:
        raise ValueError(f"Unexpected CSV header in {path}")
    bars, first, last = [], None, None
    problems = {"bad_column_count": 0, "wrong_ticker": 0,
                "bad_numeric": 0, "bad_timestamp": 0, "bad_ohlc": 0,
                "negative_volume": 0, "zero_volume": 0,
                "unaligned_timestamp": 0, "duplicate_timestamp": 0,
                "out_of_order": 0}
    future_rows_skipped = 0
    prior = ""
    years = {}
    days = set()
    for row in rows:
        if not row:
            continue
        # This is intentional: never parse OHLCV from the untouched TRUE OOS.
        timestamp = row[1] if len(row) > 1 else ""
        if timestamp >= cutoff:
            future_rows_skipped += 1
            continue
        if len(row) != 7:
            problems["bad_column_count"] += 1
            continue
        if row[0] != symbol:
            problems["wrong_ticker"] += 1
            continue
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            problems["bad_timestamp"] += 1
            continue
        try:
            o, h, l, c, v = [float(s) for s in row[2:]]
            if not all(__import__("math").isfinite(x) for x in (o, h, l, c, v)):
                raise ValueError("non-finite")
        except ValueError:
            problems["bad_numeric"] += 1
            continue
        if h < max(o, l, c) - 1e-8 or l > min(o, h, c) + 1e-8:
            problems["bad_ohlc"] += 1
        if v < 0:
            problems["negative_volume"] += 1
        elif v == 0:
            problems["zero_volume"] += 1
        if dt.minute % TIMEFRAME_MINUTES[tf] or dt.second:
            problems["unaligned_timestamp"] += 1
        if timestamp == prior:
            problems["duplicate_timestamp"] += 1
        if prior and timestamp < prior:
            problems["out_of_order"] += 1
        prior = timestamp
        if first is None:
            first = timestamp
        last = timestamp
        years[str(dt.year)] = years.get(str(dt.year), 0) + 1
        days.add(timestamp[:10])
        bars.append((dt, o, h, l, c, v))
    result = {"blob_sha": actual_sha, "rows_pre_2025": len(bars),
              "post_2024_rows_skipped_without_price_parsing": future_rows_skipped,
              "first": first, "last": last, "years": years,
              "trading_dates": len(days), "problems": problems}
    for field in ("rows", "first", "last"):
        actual = result["rows_pre_2025"] if field == "rows" else result[field]
        if actual != expected[field]:
            raise ValueError(f"Manifest mismatch: {symbol}/{tf} {field}: {actual}")
    return result, bars


def compare(m5, parent, minutes):
    groups = {}
    for dt, o, h, l, c, v in m5:
        anchor = dt.replace(hour=0, minute=0, second=0)
        key = anchor + timedelta(minutes=((dt.hour * 60 + dt.minute) // minutes) * minutes)
        g = groups.get(key)
        if g is None:
            groups[key] = {"o": o, "h": h, "l": l, "c": c, "v": v,
                           "n": 1, "first": dt, "last": dt}
        else:
            g["h"] = max(g["h"], h)
            g["l"] = min(g["l"], l)
            g["c"] = c
            g["v"] += v
            g["n"] += 1
            g["last"] = dt
    stats = {"parents_in_overlap": 0, "matched": 0, "missing_m5_bucket": 0,
             "complete_m5_bucket": 0, "partial_m5_bucket": 0,
             "ohlc_mismatch": 0, "volume_mismatch": 0,
             "missing_examples": [], "mismatch_examples": []}
    if not m5:
        return stats
    low, high = m5[0][0], m5[-1][0]
    for dt, o, h, l, c, v in parent:
        if dt < low or dt > high:
            continue
        stats["parents_in_overlap"] += 1
        g = groups.get(dt)
        if g is None:
            stats["missing_m5_bucket"] += 1
            if len(stats["missing_examples"]) < 30:
                stats["missing_examples"].append(dt.isoformat(sep=" "))
            continue
        stats["matched"] += 1
        complete = g["n"] == minutes // 5 and (g["last"] - g["first"]).total_seconds() == (minutes - 5) * 60
        stats["complete_m5_bucket" if complete else "partial_m5_bucket"] += 1
        price_equal = all(abs(a - b) <= 1e-6 for a, b in
                          zip((g["o"], g["h"], g["l"], g["c"]), (o, h, l, c)))
        vol_equal = abs(g["v"] - v) <= 1e-6
        if not price_equal:
            stats["ohlc_mismatch"] += 1
        if not vol_equal:
            stats["volume_mismatch"] += 1
        if (not price_equal or not vol_equal) and len(stats["mismatch_examples"]) < 5:
            stats["mismatch_examples"].append(dt.isoformat(sep=" "))
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True,
                        help="Local read-only forever/ folder")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[1] /
                        "data/forever_input_manifest_20261008.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = {"source_repo": manifest["source_repo"],
              "source_ref": manifest["source_ref"],
              "cutoff": manifest["development_exclusive_end"],
              "coverage": {}, "mtf": {}, "status": "AUDIT_ONLY"}
    for symbol, configs in manifest["instruments"].items():
        arrays = {}
        result["coverage"][symbol] = {}
        for tf in ("M5", "M15", "M30", "H1"):
            path = args.data_root / symbol / f"{symbol}_{tf}.csv"
            stats, arrays[tf] = parse_csv(path, symbol, tf, configs[tf],
                                          manifest["development_exclusive_end"])
            result["coverage"][symbol][tf] = stats
        result["mtf"][symbol] = {
            tf: compare(arrays["M5"], arrays[tf], TIMEFRAME_MINUTES[tf])
            for tf in ("M15", "M30", "H1")
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    problems = sum(sum(s["problems"].values()) for inst in result["coverage"].values() for s in inst.values())
    cross_faults = sum(c["missing_m5_bucket"] + c["ohlc_mismatch"] + c["volume_mismatch"]
                       for inst in result["mtf"].values() for c in inst.values())
    print(f"Audited 16 files, pre-2025 quality counts = {problems}, MTF gaps/mismatches = {cross_faults}")
    print(f"Report: {args.output}")
    if problems or cross_faults:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
