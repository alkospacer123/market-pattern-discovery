#!/usr/bin/env python3
"""Limited M5 clock controls; no strategies, fills or trading allowlist.

The user attests FINAM / MSK / start labels. This tool checks consistency,
not FINAM metadata, feed finalization or historical execution. Only the four
frozen pre-2025 M5 prefixes are read through the unchanged Stage 1.2 reader.
"""
import argparse
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
import json
from pathlib import Path
import subprocess

from audit_session_mtf import CUTOFF, SOURCE_REF, is_trading_date, read_prefix, verify_index
from check_m5_readiness import CNY_SWITCH, LAB
from session_mtf import FIVE, IMOEXF_QUARANTINE

CONTROL_DATES = (
    date(2023, 3, 13), date(2023, 3, 21), date(2023, 8, 31), date(2023, 9, 13),
    date(2024, 6, 13), date(2024, 6, 14), date(2024, 8, 16), date(2024, 9, 19),
    date(2024, 11, 19), date(2024, 12, 28),
)


def start_label_cny_grid(bars):
    counts = Counter(old_grid_bars=0, new_grid_bars=0,
                     crosses_tick_switch=0, off_grid_price_fields=0)
    for b in bars:
        if b.timestamp < CNY_SWITCH < b.timestamp + FIVE:
            counts["crosses_tick_switch"] += 1
            continue
        old = b.timestamp < CNY_SWITCH
        counts["old_grid_bars" if old else "new_grid_bars"] += 1
        step = Decimal("0.01" if old else "0.001")
        counts["off_grid_price_fields"] += sum(p % step != 0 for p in b.ohlcv[:4])
    return dict(counts)


def control_labels(bars, day):
    selected = [b for b in bars if b.timestamp.date() == day]
    def labels(a, z):
        return [str(b.timestamp.time()) for b in selected
                if a <= b.timestamp.hour * 60 + b.timestamp.minute < z]
    return {
        "rows": len(selected),
        "first": str(selected[0].timestamp) if selected else None,
        "last": str(selected[-1].timestamp) if selected else None,
        "labels_0950_1000": labels(590, 600),
        "labels_1400_1420": labels(840, 860),
        "labels_1610_1700": labels(970, 1020),
        "labels_1900_1925": labels(1140, 1165),
    }


def check(data_root):
    manifest = json.loads((LAB / "data/forever_input_manifest_20261008.json").read_text())
    prior = json.loads((LAB / "reports/STAGE1_2_SESSION_MTF_RESULTS.json").read_text())
    if manifest["source_ref"] != SOURCE_REF or manifest["development_exclusive_end"] != str(CUTOFF):
        raise ValueError("Unexpected frozen manifest")
    def status():
        return subprocess.check_output(["git", "-C", str(data_root.parent), "status",
                                        "--porcelain=v1", "--untracked-files=all"], text=True)
    if status():
        raise ValueError("Source checkout must be clean")
    verify_index(data_root, manifest)
    result = {
        "source_ref": SOURCE_REF,
        "clock_evidence": {
            "level": "USER_EXPORTER_ATTESTATION", "attested_on": "2026-10-09",
            "source": "https://www.finam.ru/quote/moex/imoex/export/",
            "timezone": "MSK UTC+3", "label": "start",
            "same_settings_for_all_16_csv": True,
            "automatically_verified_finam_metadata": False,
        },
        "counts_are_entry_allowlist": False,
        "authorized_baseline_bars": 0, "authorized_mtf_contexts": 0,
        "strategy_runs": 0, "orders": 0, "coverage": {},
    }
    for symbol, tfs in manifest["instruments"].items():
        path = data_root / symbol / f"{symbol}_M5.csv"
        before = path.stat()
        bars, stats = read_prefix(path, symbol, "M5", tfs["M5"])
        for key in ("prefix_bytes_read", "prefix_sha256", "rows", "first", "last"):
            if stats[key] != prior["coverage"][symbol]["M5"][key]:
                raise ValueError("M5 prefix differs from Stage 1.2")
        after = path.stat()
        attrs = ("st_size", "st_mtime_ns", "st_ctime_ns", "st_ino", "st_mode")
        if any(getattr(before, k) != getattr(after, k) for k in attrs):
            raise ValueError("Source metadata changed")
        days = {b.timestamp.date() for b in bars}
        q = IMOEXF_QUARANTINE
        result["coverage"][symbol] = {
            "prefix": stats, "observed_dates": len(days),
            "dates_outside_existing_calendar": sorted(str(d) for d in days if not is_trading_date(d)),
            "zero_volume_bars": sum(b.volume == 0 for b in bars),
            "noninteger_volume_bars": sum(b.volume != b.volume.to_integral_value() for b in bars),
            "quarantined_start_label_bars": sum(
                symbol == "IMOEXF" and b.timestamp < q.end and b.timestamp + FIVE > q.start for b in bars),
            "controls": {str(d): control_labels(bars, d) for d in CONTROL_DATES},
        }
        if symbol == "CNYRUBF":
            result["coverage"][symbol]["dated_tick_grid"] = start_label_cny_grid(bars)
    if status():
        raise ValueError("Source checkout changed")
    result["total_historical_rows"] = sum(v["prefix"]["rows"] for v in result["coverage"].values())
    result["total_prefix_bytes_read"] = sum(v["prefix"]["prefix_bytes_read"] for v in result["coverage"].values())
    result["future_bytes_read"] = sum(v["prefix"]["future_bytes_read"] for v in result["coverage"].values())
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.data_root.resolve()), indent=2, sort_keys=True))
