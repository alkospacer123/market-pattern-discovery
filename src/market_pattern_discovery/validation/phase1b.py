"""Validate only the explicitly enumerated 2026 Phase 1B sources, read-only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from market_pattern_discovery.data.finam import file_sha256, stitch_finam
from market_pattern_discovery.validation.causal import causal_alignment

ROOT = Path("/workspace/market-pattern-data/2026")
FILES = {
    "CNY": {"M1": [ROOT/"CNY/CNY_2026_Q1_M1.csv", ROOT/"CNY/CNY_2026_Q2_M1.csv"],
            "M5": [ROOT/"CNY/CNY_2026_Q1.csv", ROOT/"CNY/CNY_2026_Q2.csv"]},
    "Si": {"M1": [ROOT/"Si/Si_2026_Q1_M1.csv", ROOT/"Si/Si_2026_Q2_M1.csv"],
           "M5": [ROOT/"Si/Si_2026_Q1.csv", ROOT/"Si/Si_2026_Q2.csv"]},
}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Strictly validate the eight enumerated 2026 Phase 1B CSV files."
    )
    return parser.parse_args()

def main() -> None:
    parse_args()
    paths = [p for groups in FILES.values() for paths in groups.values() for p in paths]
    before = {str(p): file_sha256(p) for p in paths}
    report: dict = {"datasets": {}, "causal": {}}
    expected = {("CNY", "M1"): (106745,105869,876), ("CNY", "M5"): (22092,21913,179),
                ("Si", "M1"): (105209,104343,866), ("Si", "M5"): (22069,21890,179)}
    loaded = {}
    for name, groups in FILES.items():
        loaded[name] = {}
        for timeframe, group in groups.items():
            result = stitch_finam(group, name, timeframe)
            values = (result.raw_rows, len(result.frame), result.equivalent_duplicates)
            if values != expected[(name, timeframe)]:
                raise RuntimeError(f"reference discrepancy {name} {timeframe}: got {values}, expected {expected[(name,timeframe)]}")
            loaded[name][timeframe] = result.frame
            report["datasets"][f"{name}_{timeframe}"] = {"raw": values[0], "deduplicated": values[1],
                "equivalent_duplicates": values[2], "conflicts": 0, "provenance": result.provenance,
                "gaps": int(result.frame.gap_from_previous.sum()), "weekend_rows": int(result.frame.is_weekend.sum())}
        aligned = causal_alignment(loaded[name]["M1"], loaded[name]["M5"])
        causal = {"available_closed_m5": int(aligned.matched_m5_close.notna().sum()),
                  "without_prior_closed_m5": int(aligned.matched_m5_close.isna().sum()),
                  "violations": int(aligned.causal_violation.sum())}
        # M1 features are decided at the current candle close. Exact equality
        # makes the first native M5 close available to its coincident M1 close.
        expected_causal = (len(loaded[name]["M1"]), 0, 0)
        if tuple(causal.values()) != expected_causal:
            raise RuntimeError(f"causal discrepancy {name}: {causal}")
        report["causal"][name] = causal
    after = {str(p): file_sha256(p) for p in paths}
    if before != after:
        raise RuntimeError("source hashes changed")
    report["source_hashes_unchanged"] = True
    report["source_sha256"] = after
    output = Path("results/phase1b_2026_validation.json")
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
