"""Closed-trade tables and strictly sourced comparisons (no strategy selection)."""
import json
import math
from dataclasses import replace
import numpy as np
import pandas as pd
from exploratory_core import metrics, metric_audit, METRIC_FIELDS
from roll_diagnostics import GROUPS
from preflight import ROOT, POST, INSTRUMENTS, PAIRS


def standardize(frame):
    f = frame.copy()
    if "instrument" not in f: f["instrument"] = f["symbol"]
    for key in ["entry_time", "exit_time"]:
        f[key] = pd.to_datetime(f[key], utc=True).dt.tz_convert("Europe/Moscow")
    return f


def annual_tables(trades, frames):
    names = {s: [s] for s in INSTRUMENTS} | GROUPS
    rows = []
    for name, members in names.items():
        for year in list(range(2020, 2027))+["2020-2026"]:
            available = [s for s in members if year == "2020-2026" or any(frames[s].index.year == year)]
            f = trades[trades.instrument.isin(members)]
            if year != "2020-2026": f = f[f.exit_time.dt.year == year]
            for side in ["ALL", "LONG", "SHORT"]:
                selected = f if side == "ALL" else f[f.direction == side]
                status = "NO_DATA" if not available else "PARTIAL_SOURCE_COVERAGE" if len(available) < len(members) else "AVAILABLE_SOURCE"
                result = metrics(selected) if available else dict.fromkeys(METRIC_FIELDS)
                metric_audit(selected)
                rows.append({"year": year, "instrument": name, "direction": side, "coverage": status,
                    "covered_instruments": ";".join(available),
                    "coverage_note": "CNY_NO_DATA_BEFORE_2022_04_21" if "CNY" in members and (year == "2020-2026" or year <= 2022) else "SOURCE_END_2026_09_16" if year == 2026 else "",
                    "scenario": "PRIMARY_C1_EXPLORATORY", **result})
    result = pd.DataFrame(rows)
    files = {"annual_combined.csv": result, "annual_by_instrument.csv": result[result.instrument.isin(INSTRUMENTS)]}
    for key, group in [("annual_primary4.csv", "PRIMARY4"), ("annual_additional2.csv", "ADDITIONAL2"), ("annual_all6.csv", "ALL6")]:
        files[key] = result[result.instrument == group]
    for label, fmt, frequency in [("monthly", "%Y-%m", "M"), ("quarterly", None, "Q")]:
        rows = []
        for name, members in names.items():
            subset = trades[trades.instrument.isin(members)]
            periods = pd.period_range("2020-01", "2026-09", freq=frequency)
            keys = subset.exit_time.dt.strftime(fmt) if fmt else subset.exit_time.dt.tz_localize(None).dt.to_period("Q").astype(str)
            for period in periods:
                selected = subset[keys == str(period)]
                start, end = period.start_time.tz_localize("Europe/Moscow"), period.end_time.tz_localize("Europe/Moscow")
                covered = [s for s in members if frames[s].index[0] <= end and frames[s].index[-1] >= start]
                rows.append({"month" if label == "monthly" else "quarter": str(period), "instrument": name,
                    "coverage": "NO_DATA" if not covered else "AVAILABLE_SOURCE",
                    **(metrics(selected) if covered else dict.fromkeys(METRIC_FIELDS))})
        # Explicit column name avoids relying on plural stripping.
        table = pd.DataFrame(rows)
        files[label+".csv"] = table
    robustness = []
    for name, members in names.items():
        for side in ["ALL", "LONG", "SHORT"]:
            f = trades[trades.instrument.isin(members)]
            if side != "ALL": f = f[f.direction == side]
            m = metrics(f)
            worst = {}
            for key, labels in [("year", f.exit_time.dt.strftime("%Y")), ("quarter", f.exit_time.dt.tz_localize(None).dt.to_period("Q").astype(str)), ("month", f.exit_time.dt.strftime("%Y-%m"))]:
                sums = f.groupby(labels, sort=True).net_R_C1.sum()
                worst["worst_"+key] = sums.idxmin() if len(sums) else None
                worst["worst_"+key+"_net_R"] = float(sums.min()) if len(sums) else None
                if key == "year": worst.update(positive_years=int(sum(sums > 0)), negative_years=int(sum(sums < 0)), flat_years=int(sum(sums == 0)))
            positive = f[f.net_R_C1 > 0].sort_values(["net_R_C1", "trade_id"], ascending=[False, True])
            for n in [1, 3, 5]:
                remain = f.drop(positive.head(n).index)
                worst[f"net_R_without_top{n}"] = metrics(remain)["net_R"]
                worst[f"net_pf_without_top{n}"] = metrics(remain)["net_pf"]
                worst[f"top{n}_positive_profit_share"] = math.fsum(positive.head(n).net_R_C1)/math.fsum(positive.net_R_C1) if len(positive) else None
            robustness.append({"instrument": name, "direction": side, **m, **worst})
    files["robustness.csv"] = pd.DataFrame(robustness)
    # Independent count/sum additivity, including year and direction attribution.
    assert len(trades) == sum(len(trades[trades.instrument == s]) for s in INSTRUMENTS)
    assert len(trades) == sum(len(trades[trades.exit_time.dt.year == y]) for y in range(2020, 2027))
    net = math.fsum(trades.net_R_C1)
    assert math.isclose(net, math.fsum(metrics(trades[trades.exit_time.dt.year == y])["net_R"] for y in range(2020, 2027)), abs_tol=1e-9)
    assert math.isclose(net, math.fsum(metrics(trades[trades.instrument.isin(m)])["net_R"] for m in [GROUPS["PRIMARY4"], GROUPS["ADDITIONAL2"]]), abs_tol=1e-9)
    return files


def compare_n4(trades, frames):
    path = POST/"stage6_fixed_basket_reassessment/trail1_authoritative_trades.csv"
    ledger = standardize(pd.read_csv(path))
    ledger = ledger[ledger.lifecycle.isin(["baseline", "historical_true_oos"])].copy()
    assert len(ledger) == 355 and not ledger.lifecycle.eq("walk_forward").any()
    assert ledger.trail1_strategy_identity.eq("T3_TRAIL1_H4_02_PROFIT_PROTECTION_TRAIL1").all()
    registry = pd.read_csv(POST/"stage5_structural_validation/canonical_lifecycle_registry.csv")
    registry = registry[(registry.generation == "v3_perpetual") & (registry.strategy == "T3") & (registry.timeframe == "H1")]
    rows = []
    for year in range(2020, 2027):
        life = "baseline" if year < 2025 else "historical_true_oos"
        for q, p in list(PAIRS.items())+[("PRIMARY4", "N4")]:
            members = GROUPS["PRIMARY4"] if q == "PRIMARY4" else [q]
            perps = [PAIRS[s] for s in members]
            for mode in ["EXIT_DATE_WINDOW", "FULLY_CONTAINED_TRADES"]:
                base = {"year": year, "quarterly": q, "perpetual": p, "comparison_mode": mode,
                    "n4_lifecycle": life, "n4_cold_start_at_2025": True}
                if year < 2023:
                    rows.append({**base, "status": "NO_COMMON_COVERAGE", "n4_status": "NO_DATA"})
                    continue
                r = registry[(registry.lifecycle == life) & registry.instrument.isin(perps)]
                assert len(r) == len(members)
                start = max([pd.Timestamp(year=year, month=1, day=1, tz="Europe/Moscow")]+[pd.Timestamp(x) for x in r.start_timestamp]+[frames[s].index[0] for s in members])
                end = min([pd.Timestamp(year=year+1, month=1, day=1, tz="Europe/Moscow")-pd.Timedelta(nanoseconds=1)]+[pd.Timestamp(x) for x in r.end_timestamp]+[frames[s].index[-1] for s in members])
                if start > end:
                    rows.append({**base, "status": "NO_COMMON_COVERAGE", "n4_status": "AVAILABLE"}); continue
                a = trades[trades.instrument.isin(members) & (trades.exit_time >= start) & (trades.exit_time <= end)]
                b = ledger[ledger.instrument.isin(perps) & ledger.lifecycle.eq(life) & (ledger.exit_time >= start) & (ledger.exit_time <= end)]
                if mode == "FULLY_CONTAINED_TRADES": a, b = a[a.entry_time >= start], b[b.entry_time >= start]
                ma, mb = metrics(a), metrics(b)
                span = (end-start).total_seconds()/86400+1/86400
                rows.append({**base, "status": "PARTIAL_YEAR" if year in (2023, 2026) else "COMMON_SOURCE_INTERVAL",
                    "n4_status": "AVAILABLE", "common_start": start, "common_end": end, "calendar_days": span,
                    **{"quarterly_"+k: v for k, v in ma.items()}, **{"perpetual_"+k: v for k, v in mb.items()},
                    "delta_average_R": ma["average_R"]-mb["average_R"] if len(a) and len(b) else None,
                    "quarterly_frequency_per_365_25_days": len(a)*365.25/span,
                    "perpetual_frequency_per_365_25_days": len(b)*365.25/span})
    return pd.DataFrame(rows), ledger


def compare_v2(trades, frames):
    from TradingSystemLab.optimization.phase2b_t3 import _execute
    registry = json.loads((ROOT/"TradingSystemLab/results/phase3_candidate_freeze/candidate_registry.json").read_text())
    v2 = next(x for x in registry["candidates"] if x["candidate_id"] == "T3_H1_candidate_v2")
    dev_frames = {s: f.loc[f.index < pd.Timestamp("2025-01-01", tz="Europe/Moscow")] for s, f in frames.items()}
    # Reexecute only the already-published frozen candidate, never a grid/search.
    dev = standardize(_execute(v2["parameters"], dev_frames))
    published_years = pd.read_csv(ROOT/"TradingSystemLab/results/robustness_v2/T3/H1/year_report.csv")
    for r in published_years.itertuples():
        actual = metrics(dev[dev.exit_time.dt.year == r.year])
        for key, val in [("trades", r.trade_count), ("net_pf", r.PF), ("net_R", r.net_R), ("average_R", r.expectancy), ("max_closed_R_drawdown", r.max_DD)]:
            assert math.isclose(actual[key], val, rel_tol=2e-9, abs_tol=2e-8), ("v2_published", r.year, key, actual[key], val)
    # Existing 2025+ ledger, authenticated by base-commit bytes in source manifest.
    later = standardize(pd.read_csv(ROOT/"TradingSystemLab/results/true_oos_v2/T3/H1/trades.csv"))
    old = pd.concat([dev.assign(lifecycle="v2_development"), later.assign(lifecycle="v2_historical_true_oos")], ignore_index=True)
    old["trade_id"] = [f"V2-{i:06d}" for i in range(1, len(old)+1)]
    # Legacy v2 normalizer copied already-net profit_R into gross_R, then charged
    # cost_R again. Keep published numbers intact; disclose single-C1 normalization.
    old["published_net_R_C1"] = old.net_R_C1
    old["published_gross_R_field"] = old.gross_R
    old["normalized_single_C1_net_R"] = old.net_R_C1+old.cost_R
    old["true_gross_R"] = old.net_R_C1+2*old.cost_R
    old["gross_R"] = old.true_gross_R
    rows = []
    for year in range(2020, 2027):
        for name, members in ({s: [s] for s in INSTRUMENTS} | GROUPS).items():
            a = trades[trades.instrument.isin(members) & (trades.exit_time.dt.year == year)]
            b = old[old.instrument.isin(members) & (old.exit_time.dt.year == year)]
            if name == "CNY" and year < 2022:
                rows.append({"year": year, "instrument": name, "status": "NO_DATA"}); continue
            ma, mb = metrics(a), metrics(b)
            normalized = b.copy(); normalized["net_R_C1"] = b.normalized_single_C1_net_R
            mn = metrics(normalized)
            rows.append({"year": year, "instrument": name, "status": "EXIT_YEAR_MATCHED_SOURCE_LIFECYCLES_DIFFER",
                "common_start": max(pd.Timestamp(year=year, month=1, day=1, tz="Europe/Moscow"), min(frames[s].index[0] for s in members)),
                "common_end": min(pd.Timestamp(year=year+1, month=1, day=1, tz="Europe/Moscow")-pd.Timedelta(nanoseconds=1), max(frames[s].index[-1] for s in members)),
                "v2_lifecycle": "cold_start_2025" if year >= 2025 else "development_2020_2024",
                "v2_stop_atr": 2.0, "v2_atr_average_period": 30, "v2_trail1_identical": False,
                "v2_published_cost_accounting": "LEGACY_EFFECTIVE_TWO_C1", "v3_cost_accounting": "SINGLE_C1",
                **{"v3_"+k: v for k, v in ma.items()}, **{"v2_published_"+k: v for k, v in mb.items()},
                **{"v2_single_C1_"+k: mn[k] for k in ["net_pf", "net_R", "average_R", "max_closed_R_drawdown"]}})
    return pd.DataFrame(rows), old, {"published_2020_2024_years_reconciled": 5, "v2_development_closed_trades": len(dev),
        "v2_existing_2025_2026_closed_trades": len(later), "published_legacy_double_C1_disclosed": True}
