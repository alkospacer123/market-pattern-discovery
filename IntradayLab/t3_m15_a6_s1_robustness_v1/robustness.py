#!/usr/bin/env python3
"""Deterministic read-only robustness sensitivity for the frozen TRAIL_375 ledger.

Run from the checked-out repository:
    python IntradayLab/t3_m15_a6_s1_robustness_v1/robustness.py

This does NOT rerun historical OHLC or simulate actual transaction costs.
Requires Python 3 stdlib only. Outputs solely inside this study's results/.
"""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "t3_m15_early_risk_protection_v1" / "results" / "control" / "trades.csv"
OUT = ROOT / "results"
INSTRUMENTS = ["USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"]
HAIRCUTS = (0.0, 0.05, 0.10)
MONTHS = [f"{y}-{m:02d}" for y in (2023, 2024) for m in range(1, 13)]

def load():
    with SOURCE.open(newline="", encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    for row in data:
        row["r"] = float(row["gross_R"])
        row["month"] = row["exit_time"][:7]
        row["year"] = row["exit_time"][:4]
        assert math.isfinite(row["r"]) and row["year"] in ("2023", "2024")
        assert row["instrument"] in INSTRUMENTS
        assert row["version"] == "TRAIL_375" and row["mode"] == "NEXT_OPEN"
    data.sort(key=lambda r: (r["exit_time"], r["instrument"], r["trade_id"]))
    keys = [(r["instrument"], r["trade_id"]) for r in data]
    assert len(data) == len(set(keys)) == 480
    return data

def annual_months(year):
    return MONTHS if year == "ALL" else [m for m in MONTHS if m.startswith(year)]

def stats(rows, year="ALL", haircut=0.0):
    ss = [r for r in rows if year == "ALL" or r["year"] == year]
    pos = neg = gross = eq = peak = max_dd = 0.0
    month_r = {m: 0.0 for m in annual_months(year)}
    month_n = {m: 0 for m in annual_months(year)}
    for row in ss:
        v = row["r"] - haircut
        gross += v
        if v > 0:
            pos += v
        elif v < 0:
            neg += -v
        eq += v
        peak = max(peak, eq)
        max_dd = max(max_dd, peak - eq)
        month_r[row["month"]] += v
        month_n[row["month"]] += 1
    vals = list(month_r.values())
    neg_streak = cur = 0
    for v in vals:
        if v < -1e-10:
            cur += 1
            neg_streak = max(neg_streak, cur)
        else:
            cur = 0
    return dict(year=year, closed=len(ss), gross_PF=pos / neg if neg else None,
                gross_R=gross, expectancy_R=gross / len(ss) if ss else None,
                positive_R=pos, negative_R=neg, closed_R_DD=max_dd,
                positive_months=sum(v > 1e-10 for v in vals),
                negative_months=sum(v < -1e-10 for v in vals),
                zero_months=sum(abs(v) <= 1e-10 for v in vals),
                months=len(vals), max_negative_month_run=neg_streak,
                monthly=month_r, month_count=month_n)

def item_id(row):
    return (row["instrument"], row["trade_id"])

def concentration(rows, year):
    st = stats(rows, year)
    data = [r for r in rows if r["year"] == year or year == "ALL"]
    sorted_winners = sorted((r for r in data if r["r"] > 0),
                            key=lambda r: (-r["r"], r["instrument"], r["trade_id"]))
    months_sorted = sorted(st["monthly"], key=lambda m: (-st["monthly"][m], m))
    result = {"year": year, "gross_R": st["gross_R"],
              "original_GE2": sum(r["r"] >= 2 for r in data),
              "original_GE5": sum(r["r"] >= 5 for r in data)}
    for k in (1, 3, 5, 10):
        top = sorted_winners[:k]
        identities = {item_id(r) for r in top}
        after = stats([r for r in data if item_id(r) not in identities])
        result[f"top{k}_winner_R"] = sum(r["r"] for r in top)
        result[f"top{k}_winner_share_of_positive_R"] = (sum(r["r"] for r in top) / st["positive_R"]
                                                        if st["positive_R"] > 0 else None)
        result[f"ex_top{k}_winner_PF"] = after["gross_PF"]
        result[f"ex_top{k}_winner_R"] = after["gross_R"]
    for k in (1, 3):
        best = months_sorted[:k]
        after = stats([r for r in data if r["month"] not in best])
        result[f"top{k}_months"] = "|".join(best)
        result[f"top{k}_month_R"] = sum(st["monthly"][m] for m in best)
        result[f"top{k}_month_share_signed_year_R"] = (result[f"top{k}_month_R"] / st["gross_R"]
                                                        if st["gross_R"] > 0 else None)
        result[f"ex_top{k}_month_PF"] = after["gross_PF"]
        result[f"ex_top{k}_month_R"] = after["gross_R"]
    return result

def write_csv(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    assert records
    columns = list(records[0])
    with path.open("w", newline="", encoding="utf-8") as f:
        out = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        out.writeheader()
        out.writerows(records)

def strip_extra(obj):
    return {k: v for k, v in obj.items() if k not in ("monthly", "month_count")}

def run():
    rows = load()
    assert SOURCE.read_bytes()  # ensures read-only input is present
    original = {y: stats(rows, y) for y in ("2023", "2024", "ALL")}
    assert abs(original["2023"]["gross_PF"] - 2.2072776313642746) < 1e-10
    assert abs(original["2024"]["gross_PF"] - 1.7721337045362484) < 1e-10
    assert abs(original["ALL"]["gross_R"] - 212.52265622369515) < 1e-8
    assert abs(original["ALL"]["closed_R_DD"] - 12.628056181602872) < 1e-8
    assert original["ALL"]["positive_months"] == 20
    assert sum(original[y]["closed"] for y in ("2023", "2024")) == 480
    assert len([r for r in rows if r["r"] >= 2]) == 83
    assert len([r for r in rows if r["r"] >= 5]) == 21

    yearly = []
    monthly = []
    for cost in HAIRCUTS:
        for year in ("2023", "2024", "ALL"):
            s = stats(rows, year, cost)
            yearly.append(dict(scenario=f"HAIRCUT_{cost:g}", per_closed_R_haircut=cost,
                               **strip_extra(s)))
        s = stats(rows, "ALL", cost)
        for month in MONTHS:
            sub = [r for r in rows if r["month"] == month]
            sm = stats(sub, month[:4], cost)
            monthly.append(dict(scenario=f"HAIRCUT_{cost:g}", month=month, closed=len(sub),
                                gross_R=s["monthly"][month], gross_PF=sm["gross_PF"]))
    write_csv(OUT / "yearly_stress.csv", yearly)
    write_csv(OUT / "monthly_stress.csv", monthly)

    loo = []
    for exclude in INSTRUMENTS:
        remaining = [r for r in rows if r["instrument"] != exclude]
        for year in ("2023", "2024", "ALL"):
            loo.append(dict(excluded_instrument=exclude, **strip_extra(stats(remaining, year))))
    write_csv(OUT / "leave_one_out.csv", loo)

    direction_rows = []
    instrument_rows = []
    for side in ("LONG", "SHORT"):
        side_rows = [r for r in rows if r["direction"] == side]
        for year in ("2023", "2024", "ALL"):
            direction_rows.append(dict(direction=side, **strip_extra(stats(side_rows, year))))
    write_csv(OUT / "directions.csv", direction_rows)
    for name in INSTRUMENTS:
        inst_rows = [r for r in rows if r["instrument"] == name]
        for year in ("2023", "2024", "ALL"):
            instrument_rows.append(dict(instrument=name, **strip_extra(stats(inst_rows, year))))
    write_csv(OUT / "instruments.csv", instrument_rows)

    concentration_rows = [concentration(rows, y) for y in ("2023", "2024", "ALL")]
    write_csv(OUT / "concentration.csv", concentration_rows)

    nov = stats([r for r in rows if r["month"] != "2024-11"], "2024")
    control = dict(original={year: strip_extra(s) for year, s in original.items()},
                   without_november_2024=strip_extra(nov),
                   source=str(SOURCE.relative_to(ROOT.parent.parent)),
                   archived_control_only=True, raw_OHLC_replay="NOT_RUN",
                   independent_full_raw_backtest="NOT_RUN", audit_status="LEDGER_ARITHMETIC_ONLY",
                   cost_model="FIXED_ARITHMETIC_HAIRCUT_NOT_BROKER_COST",
                   classifications=["DEVELOPMENT_EXPOSED","GROSS_ONLY","COSTS_DEFERRED","NOT_LIVE_READY"])
    (OUT / "CONTROL_LEDGER_CHECK.json").write_text(
        json.dumps(control, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return control

if __name__ == "__main__":
    result = run()
    print("ARCHIVED_CONTROL_RECALCULATED", result["original"]["ALL"]["gross_R"])
    print("RAW_OHLC_FULL_REPLAY_NOT_RUN")
