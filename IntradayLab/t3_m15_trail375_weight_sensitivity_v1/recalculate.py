#!/usr/bin/env python3
"""Read-only, descriptive weight sensitivity for frozen IntradayLab TRAIL_375.

Source: pinned PR #513 full historical results/primary/trades.csv.
No changes to signals/exits, no broker operations, no capital/GO/fee simulation.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

SOURCE_BLOB_SHA1 = "17750384d7eb8279724905f38f973d9051f095fc"
INSTRUMENTS = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
WEIGHTS = {
    "N4_EQUAL": (0.25, 0.25, 0.25, 0.25),
    "N4_BALANCED": (1 / 3, 1 / 3, 1 / 6, 1 / 6),
    "N2_CURRENCY": (0.5, 0.5, 0, 0),
}
CONTROL_PF = {
    "2023": 2.207278,
    "2024": 1.772134,
    "2025": 1.581308,
    "2026": 2.062109,
}


def read_trades(path):
    raw = Path(path).read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob != SOURCE_BLOB_SHA1:
        raise ValueError(f"Source Git blob differs from pinned PR #513: {blob}")
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    if len(rows) != 1026 or len({r["trade_id"] for r in rows}) != 1026:
        raise ValueError("Expected 1026 distinct CLOSED trades")
    if set(r["instrument"] for r in rows) != set(INSTRUMENTS):
        raise ValueError("Different instrument universe")
    if any(r["version"] != "TRAIL_375" or r["mode"] != "NEXT_OPEN"
           or r["rule"] != "C1" for r in rows):
        raise ValueError("Frozen strategy identity changed")
    return rows, blob


def aggregate(rows, weights):
    ordered = sorted((r for r in rows if weights[r["instrument"]] > 0),
                     key=lambda r: (r["exit_time"], r["instrument"], r["trade_id"]))
    vals = [float(r["gross_R"]) * weights[r["instrument"]] for r in ordered]
    wins = math.fsum(v for v in vals if v > 0)
    losses = -math.fsum(v for v in vals if v < 0)
    equity = peak = max_dd = 0.0
    by_month = {}
    for row, val in zip(ordered, vals):
        equity += val
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
        by_month.setdefault(row["exit_time"][:7], []).append(val)
    monthly = {m: math.fsum(vs) for m, vs in sorted(by_month.items())}
    return {
        "closed": len(ordered),
        "gross_pf": round(wins / losses, 6) if losses else None,
        "weighted_gross_r_budget_units": round(math.fsum(vals), 6),
        "max_closed_r_dd_budget_units": round(max_dd, 6),
        "positive_months": sum(v > 1e-9 for v in monthly.values()),
        "covered_months": len(monthly),
        "monthly_budget_r": {m: round(v, 6) for m, v in monthly.items()},
    }


def calculate(rows, blob):
    output = {
        "status": "POST_HOC_DESCRIPTIVE_GROSS_ONLY_NOT_LIVE_READY",
        "source_pr": 513,
        "source_blob_sha1": blob,
        "input_closed_trades": len(rows),
        "account_capital_sizing_simulated": False,
        "fees_spread_slippage_simulated": False,
        "cases": {},
    }
    for case, fractions in WEIGHTS.items():
        weights = dict(zip(INSTRUMENTS, fractions))
        if abs(sum(weights.values()) - 1) > 1e-12:
            raise AssertionError("Budget must sum to one")
        result = {"fixed_budget_fractions": weights, "ALL": aggregate(rows, weights)}
        for year in CONTROL_PF:
            result[year] = aggregate(
                [r for r in rows if r["exit_time"].startswith(year)], weights)
        output["cases"][case] = result
    control = output["cases"]["N4_EQUAL"]
    if control["ALL"]["closed"] != 1026:
        raise AssertionError("Control CLOSED count")
    for year, expected_pf in CONTROL_PF.items():
        if abs(control[year]["gross_pf"] - expected_pf) > 0.000005:
            raise AssertionError(f"Control PF mismatch: {year}")
    if control["ALL"]["positive_months"] != 35 or abs(
        control["ALL"]["max_closed_r_dd_budget_units"] - 28.637394 / 4
    ) > 2e-5:
        raise AssertionError("Control monthly regularity or DD mismatch")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trades", required=True,
                        help="Unmodified PR #513 results/primary/trades.csv")
    args = parser.parse_args()
    rows, blob = read_trades(args.trades)
    print(json.dumps(calculate(rows, blob), indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
