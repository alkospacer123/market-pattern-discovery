#!/usr/bin/env python3
"""Separate research-only daywise ORB replay.

This does NOT reconcile an unknown real position.  It starts each subsequent
trading day as a separate conditional experiment.  All strict frozen Stage 2
artifacts and the robot fail-closed contract remain untouched.
"""
import argparse
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import audit_orb_false_break_fade as independent
import orb_false_break_fade_replay as engine
import run_orb_false_break_fade as strict_report

LAB = Path(__file__).resolve().parents[1]
OUT = LAB / "results" / "stage2_orb_false_break_fade_m5_v2_research" / "v1_daywise"
CONFIG = LAB / "config" / "stage2_orb_false_break_fade_m5_v1.json"
ZERO = Decimal(0)


def by_day(records):
    result = defaultdict(list)
    for item in records:
        result[item["date"]].append(item)
    return result


def evaluate_symbol(symbol, rows, events, architecture, spec, audit=True):
    """Never continue an unknown position into the next day's P&L.

    After an unresolved prior day, all following days explicitly assume a
    fresh flat state; they are COUNTERFACTUAL, not executed portfolio history.
    Within each day fail-closed behavior remains completely unchanged.
    """
    events_by_day = by_day(events)
    prices_by_day = defaultdict(dict)
    for timestamp, bar in rows.items():
        prices_by_day[str(timestamp.date())][timestamp] = bar
    signals, trades, day_rows = [], [], []
    unresolved_before = False
    compared = 0
    # Include observed research days with NO event, not just days with sweeps.
    # Missing full days remain represented by the separate source-coverage table.
    observed_research_days = {
        day for day in prices_by_day
        if engine.windows(date.fromisoformat(day))
    }
    for day in sorted(observed_research_days | set(events_by_day)):
        items = events_by_day.get(day, [])
        daily_prices = prices_by_day.get(day, {})
        if not daily_prices:
            # Preserve NO_OR and coverage for a physically absent whole day.
            if any(x['base_reason'] == 'SIGNAL' for x in items):
                raise AssertionError('Signal without any source history')
        ds, dt = engine.replay(symbol, daily_prices, items, architecture, spec)
        if audit and daily_prices:
            oracle_signals, oracle_trades = independent.oracle_trades(
                symbol, daily_prices, items, architecture, spec
            )
            failures = independent.compare_rows(
                ds, oracle_signals,
                independent.SIGNAL_KEYS +
                ("status", "reason", "order_admitted", "model_filled"),
                "daywise_signals"
            )
            failures += independent.compare_rows(
                dt, oracle_trades, independent.TRADE_KEYS, "daywise_trades"
            )
            if failures:
                raise AssertionError(
                    "Independent daywise oracle mismatch on " +
                    day + ": " + str(failures[:3])
                )
            compared += len(ds) + len(dt)
        for record in ds:
            record["research_mode"] = "DAY_ISOLATED_CONDITIONAL"
            record['initial_flat_assumed'] = True
            record['initial_flat_proven'] = False
            record["prior_unknown_requires_flat_assumption"] = unresolved_before
        for record in dt:
            record["research_mode"] = "DAY_ISOLATED_CONDITIONAL"
            record['initial_flat_assumed'] = True
            record['initial_flat_proven'] = False
            record["prior_unknown_requires_flat_assumption"] = unresolved_before
        unknown_today = any(t["status"] == "UNKNOWN" for t in dt)
        day_rows.append({
            "architecture": architecture,
            "instrument": symbol,
            "date": day,
            'initial_flat_assumed': True,
            'initial_flat_proven': False,
            'source_observed': bool(daily_prices),
            "signal_count": sum(s["base_reason"] == "SIGNAL" for s in ds),
            "model_fills": sum(t.get("model_filled", False) for t in dt),
            "closed": sum(t["status"] == "CLOSED" for t in dt),
            "unknown": sum(t["status"] == "UNKNOWN" for t in dt),
            "prior_unknown_requires_flat_assumption": unresolved_before,
            "any_unknown": unknown_today
        })
        signals.extend(ds)
        trades.extend(dt)
        unresolved_before |= unknown_today
    return signals, trades, day_rows, compared


def compact_metrics(trades):
    closed = [t for t in trades if t["status"] == "CLOSED"]
    c1 = strict_report.summary(trades, "c1")
    c2 = strict_report.summary(trades, "c2")
    return {
        "conditional_closed_only_c1": c1,
        "conditional_closed_only_c2": c2,
        "closed": len(closed),
        "model_fills": sum(t.get("model_filled", False) for t in trades),
        "unknown": sum(t["status"] == "UNKNOWN" for t in trades),
        "unknown_possible_entry": sum(
            t["status"] == "UNKNOWN" and not t.get("model_filled", False)
            for t in trades
        ),
        "post_unknown_assumption_closed": sum(
            t["status"] == "CLOSED" and
            t["prior_unknown_requires_flat_assumption"] for t in trades
        ),
        "annual_complete": False,
        "annual_net": None,
        "annual_pf": None,
        "annual_drawdown": None,
        "no_portfolio_or_real_execution_claim": True
    }


def monthly(symbol, architecture, trades, coverage):
    result = []
    for month in range(1, 13):
        ym = "2023-%02d" % month
        cohort = [t for t in trades if str(t["signal_at"]).startswith(ym)]
        source_month = [c for c in coverage
                        if c["instrument"] == symbol and c["date"].startswith(ym)]
        has_source = any(c['valid_bars'] > 0 for c in source_month)
        all_complete = bool(source_month) and all(
            c["status"] == "COMPLETE" for c in source_month
        )
        has_unknown = any(t["status"] == "UNKNOWN" for t in cohort)
        conditional_after_unknown = any(
            t["prior_unknown_requires_flat_assumption"] for t in cohort
        )
        c1 = strict_report.summary(cohort, "c1")
        c2 = strict_report.summary(cohort, "c2")
        result.append({
            "architecture": architecture,
            "instrument": symbol,
            "month": ym,
            "classification": (
                "NO_COVERAGE" if not has_source else
                "UNKNOWN" if has_unknown else
                "PARTIAL_DATA" if not all_complete else
                "CONDITIONAL_DAYWISE"
            ),
            "closed": c1["closed_trades"],
            "unknown": sum(t["status"] == "UNKNOWN" for t in cohort),
            "conditional_after_prior_unknown": conditional_after_unknown,
            "diagnostic_net_R_c1": c1["net_R"],
            "diagnostic_expectancy_R_c1": c1["expectancy_R"],
            "diagnostic_PF_c1": c1["net_PF"],
            "diagnostic_PF_R_c1": c1["net_PF_R"],
            "diagnostic_PF_c2": c2["net_PF"],
            'diagnostic_net_R_c2': c2['net_R'],
            'diagnostic_expectancy_R_c2': c2['expectancy_R'],
            'diagnostic_PF_R_c2': c2['net_PF_R'],
            'diagnostic_net_c1': c1['net'],
            'diagnostic_net_c2': c2['net'],
            'diagnostic_sign': 'NO_COVERAGE' if not has_source else 'POSITIVE' if c1['net'] > 0 else 'NEGATIVE' if c1['net'] < 0 else 'ZERO',
            'covered_days': sum(c['valid_bars'] > 0 for c in source_month),
            'missing_expected_bars': sum(c['missing_bars'] for c in source_month),
            "full_net": None,
            "full_PF": None,
            "full_DD": None
        })
    return result


def run(data_root, output_dir=OUT):
    if output_dir.resolve() != OUT.resolve():
        raise ValueError("Output must be in isolated IntradayLab daywise directory")
    config = json.loads(CONFIG.read_text())
    if config["id"] != "stage2_orb_false_break_fade_m5_v1":
        raise ValueError("Unexpected frozen strategy config")
    raw, receipts = engine.read_source(data_root, config)
    # Use a distinct raw reader for the independent oracle as well.
    reread = independent.source(data_root, config)
    for sym in config["instruments"]:
        if raw[sym] != reread[sym]:
            raise AssertionError("Independent source mismatch " + sym)

    signals = []
    trades = []
    day_rows = []
    metrics = {}
    months = []
    audit_count = 0
    raw_event_count = 0
    for symbol in config["instruments"]:
        events, _, coverage = engine.base_signals(symbol, raw[symbol])
        expected_events = independent.oracle_signals(symbol, reread[symbol])
        problems = independent.compare_rows(
            events, expected_events, independent.SIGNAL_KEYS, "base_signal"
        )
        if problems:
            raise AssertionError("Independent signal mismatch " + str(problems[:3]))
        raw_event_count += len(events)
        for arch, spec in config["architectures"].items():
            ss, tt, dd, checked = evaluate_symbol(
                symbol, raw[symbol], events, arch, spec
            )
            key = arch + "_" + symbol
            metrics[key] = compact_metrics(tt)
            metrics[key]["signals"] = sum(
                s["base_reason"] == "SIGNAL" for s in ss
            )
            metrics[key]["reasons"] = dict(Counter(
                s["reason"] for s in ss if s["base_reason"] == "SIGNAL"
            ))
            metrics[key]["atr_available_on_signal"] = sum(
                s["atr_ready"] for s in ss if s["base_reason"] == "SIGNAL"
            )
            metrics[key]["mtf_aligned_on_signal"] = sum(
                s.get("m15_direction") == s["direction"]
                for s in ss if s["base_reason"] == "SIGNAL"
            )
            metrics[key]["daily_independent_experiments"] = len(dd)
            metrics[key]["counterfactual_days_after_unknown"] = sum(
                x["prior_unknown_requires_flat_assumption"] for x in dd
            )
            metrics[key]["unknown_days"] = sum(x["any_unknown"] for x in dd)
            signals.extend(ss)
            trades.extend(tt)
            day_rows.extend(dd)
            months.extend(monthly(symbol, arch, tt, coverage))
            audit_count += checked

    # The original strict file is never overwritten or reclassified.
    strict_path = LAB / "results/stage2_orb_false_break_fade_m5_v1/metrics.json"
    strict_metrics = json.loads(strict_path.read_text())
    comparisons = []
    for key, metric in metrics.items():
        original = strict_metrics[key]
        old_count = original["model_fills"]
        old_closed = original["closed_trades"]
        comparisons.append({
            "architecture_instrument": key,
            "strict_model_fills": old_count,
            "strict_closed": old_closed,
            "strict_unknown": original["unknown"],
            "daywise_model_fills": metric["model_fills"],
            "daywise_closed": metric["closed"],
            "daywise_unknown": metric["unknown"],
            "extra_conditional_fills": metric["model_fills"] - old_count,
            "conditional_after_unknown_closed":
                metric["post_unknown_assumption_closed"],
            "NOT_a_portfolio_performance_comparison": True
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    strict_report.write_csv(output_dir / "signals.csv", signals)
    strict_report.write_csv(output_dir / "trades.csv", trades)
    strict_report.write_csv(output_dir / "daily.csv", day_rows)
    strict_report.write_csv(output_dir / "monthly.csv", months)
    strict_report.write_csv(output_dir / "strict_vs_daywise.csv", comparisons)
    engine.dump(output_dir / "metrics.json", metrics)
    engine.dump(output_dir / "audit.json", {
        "independent_oracle": "PASS",
        "daywise_signal_trade_records_compared": audit_count,
        "source_price_rows_rechecked_independently": True,
        "raw_signal_event_records": raw_event_count,
        "original_strict_artifacts_modified": False,
        "no_2024_plus_bytes": True,
        "unknowns_never_resolved": True,
        "result_type": "COUNTERFACTUAL_INDEPENDENT_DAYS_NOT_PORTFOLIO"
    })
    engine.dump(output_dir / "provenance.json", {
        "strict_reference": "stage2_orb_false_break_fade_m5_v1",
        "source_ref": config["source_ref"],
        "input_receipts": receipts,
        "model": "reset ONLY at next calendar trading day; unknown persists "
                 "within its own day; future days start with an explicitly "
                 "UNVERIFIED flat assumption",
        "all_annual_net_pf_dd": None
    })
    hashes = {
        x.name: hashlib.sha256(x.read_bytes()).hexdigest()
        for x in output_dir.iterdir() if x.is_file() and x.name != 'file_hashes.json'
    }
    engine.dump(output_dir / "file_hashes.json", hashes)
    print(json.dumps({
        "status": "DAYWISE_DIAGNOSTIC_ONLY",
        "independent_oracle": "PASS",
        "scenarios": len(metrics),
        "strict_vs_daywise": comparisons,
        "result_dir": str(output_dir)
    }, indent=2))
    return metrics, comparisons


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True,
                        help="Clean, pinned market-pattern-data repository root")
    args = parser.parse_args()
    run(args.data_root.resolve())
