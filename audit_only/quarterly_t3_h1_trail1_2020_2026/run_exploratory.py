"""Authorized EXPLORATORY REPLAY on exactly six authenticated original streams.

Unknown roll provenance is accepted for description only. Not contract execution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import preflight
from exploratory_core import DataLoader, replay_instrument, historical_audit, metrics, metric_audit
from exploratory_tables import annual_tables, compare_n4, compare_v2, standardize
from roll_diagnostics import diagnose, GROUPS, DEFINITIONS


def clean(value):
    if isinstance(value, dict): return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    if isinstance(value, (pd.Timestamp,)): return value.isoformat()
    if hasattr(value, "item"): return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value): return None
    return value


def dump(path, value):
    path.write_text(json.dumps(clean(value), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def save(path, frame):
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.17g", na_rep="")


def run(data_root, out):
    data_root, out = Path(data_root).resolve(), Path(out).resolve()
    if out == data_root or data_root in out.parents or out == ROOT or ROOT in out.parents:
        raise ValueError("RUN_OUTPUT_MUST_BE_SCRATCH_OUTSIDE_DATA_AND_CODE_REPOSITORIES")
    out.mkdir(parents=True, exist_ok=False)
    auth, authority_sources = preflight.authenticate()
    assert auth["status"] == "PASS"
    prior_quality = json.loads((HERE/"prior_preflight/data_quality.json").read_text())
    expected = {x["instrument"]: x["sha256"] for x in prior_quality["instruments"]}
    frames, lows, audits, source_rows = {}, {}, [], []
    all_trades, all_trace, all_signals, all_open = [], [], [], []
    for symbol in preflight.INSTRUMENTS:
        path = data_root/f"futures_quarterly/{symbol}/{symbol}_H1.csv"
        quality = preflight.inspect_csv(path)
        assert quality["sha256"] == expected[symbol]
        assert all(quality[k] == 0 for k in ["duplicate_timestamps", "non_increasing_transitions", "nonfinite_numeric_rows", "invalid_ohlc_rows", "nonpositive_price_rows"])
        frame = DataLoader(forbid_true_oos=False).load_csv(path)
        frame = DataLoader.close_index(frame, "1h")
        assert frame.index.min() >= pd.Timestamp("2020-01-01", tz="Europe/Moscow")
        assert frame.index.max() <= pd.Timestamp("2026-10-19 23:59:59", tz="Europe/Moscow")
        frames[symbol] = frame
        result = replay_instrument(frame, symbol)
        low, _, _, trades, trace, signals, opened = result
        print(f"{symbol}: {len(frame)} completed H1; {len(trades)} closed trades; historical audit", flush=True)
        audit = historical_audit(frame, symbol, result)
        print(f"{symbol}: authority/production/scalar/events/prefixes PASS", flush=True)
        audits.append(audit)
        lows[symbol] = low
        all_trades.extend(trades); all_trace.extend(trace); all_signals.extend(signals); all_open.extend(opened)
        assert preflight.sha(path) == expected[symbol]
        source_rows.append({"instrument": symbol, "path": str(path.relative_to(data_root)),
            "sha256": expected[symbol], "source_rows": len(frame), "first_close": frame.index[0], "last_close": frame.index[-1],
            "timestamp_convention": "ASSUMED_OPEN_LABELLED_EUROPE_MOSCOW_PLUS_1H", "roll_provenance": "UNVERIFIED"})
    trades = standardize(pd.DataFrame(all_trades)).sort_values(["exit_time", "instrument", "trade_id"], kind="mergesort").reset_index(drop=True)
    trace = pd.DataFrame(all_trace)
    trace["order"] = trace.event_type.map({"EXIT": 0, "HOLD": 1, "ENTRY": 2})
    trace = trace.sort_values(["event_time", "order", "instrument", "trade_id"], kind="mergesort").drop(columns="order").reset_index(drop=True)
    signals = pd.DataFrame(all_signals).sort_values(["signal_time", "instrument"], kind="mergesort")
    files = {"trades.csv": trades, "trail1_trace.csv": trace, "signals.csv": signals,
             "open_positions.csv": pd.DataFrame(all_open)}
    files.update(annual_tables(trades, frames))
    print("Annual, monthly, quarterly, direction, robustness and Decimal PF audit complete", flush=True)
    files.update(diagnose(frames, lows, trades, trace, signals))
    print("Predeclared calendar / large-gap diagnostics complete", flush=True)
    comparison, n4 = compare_n4(trades, frames)
    files["quarterly_vs_perpetual_n4.csv"] = comparison
    print("N4 common-interval comparison complete; no Walk Forward duplication", flush=True)
    v2_comparison, v2, v2_audit = compare_v2(trades, frames)
    files["v2_vs_v3_comparison.csv"] = v2_comparison
    v2_fields = ["trade_id", "instrument", "lifecycle", "direction", "entry_time", "exit_time", "entry_price", "exit_price", "gross_R", "cost_R", "published_net_R_C1", "normalized_single_C1_net_R", "true_gross_R"]
    files["v2_comparator_trades.csv"] = v2[v2_fields]
    print("Published v2 years reconciled; legacy cost accounting disclosed", flush=True)
    annual = files["annual_combined.csv"]
    subsets = {s: [s] for s in preflight.INSTRUMENTS} | GROUPS
    totals = {s: metrics(trades[trades.instrument.isin(m)]) for s, m in subsets.items()}
    for members in subsets.values(): metric_audit(trades[trades.instrument.isin(members)])
    states = {"COMPUTATIONAL_AUDIT": "PASS", "SOURCE_INTEGRITY": "PASS", "ROLL_PROVENANCE": "UNVERIFIED",
              "EXPLORATORY_REPLAY": "COMPLETE", "TRADABLE_QUARTERLY_PERFORMANCE": "NOT_VALIDATED"}
    summary = {**states, "original_main_commit": preflight.BASE, "prior_preflight_commit": "7404fc23f2e92344fd5aea66924b74410f777ebe",
        "research_acceptance_change": "Explicit user authorization in this thread for descriptive replay without roll passport",
        "production_identity_reference": "TRAIL1__N4_01__FULL__R15", "configuration": "T3-H1-4e73cdb77246",
        "actual_coverage": source_rows, "totals": totals, "closed_trades": len(trades), "unclosed_positions": len(all_open),
        "positions_or_indicators_reset_at_year_boundaries": False,
        "positive_instruments": sum(totals[s]["net_R"] > 0 for s in preflight.INSTRUMENTS),
        "positive_years_by_basket": {s: int(((annual.instrument == s) & (annual.direction == "ALL") & (annual.year != "2020-2026") & (annual.net_R > 0)).sum()) for s in GROUPS},
        "observed_all6_mean_R_positive": totals["ALL6"]["average_R"] > 0,
        "clean_true_oos": False, "secondary_execution": "NOT_RUN_NO_HISTORICAL_CONTRACT_SPECS",
        "capital_model": "NOT_RUN", "economic_inference": "DESCRIPTIVE_ON_PROVIDED_SERIES_ONLY",
        "roll_diagnostic_definitions": DEFINITIONS}
    audit = {**states, "frozen_authentication": auth, "historical_independent_checks": audits,
        "metric_audit": "INDEPENDENT_DECIMAL_PF_SUMS_DRAWDOWN_ON_INSTRUMENT_YEAR_DIRECTION_AND_BASKET",
        "year_attribution": "EXIT_TIME_EUROPE_MOSCOW", "aggregation_reconciliation": "PASS",
        "v2_reconciliation": v2_audit, "n4_source_ledger_physical_rows": 418,
        "n4_comparison_source_rows": len(n4), "n4_walk_forward_rows_excluded": 63,
        "source_price_and_gap_repairs": False, "roll_causality_of_source_construction": "UNVERIFIED",
        "two_full_replays": "RECORDED_SEPARATELY_IN_REPRODUCIBILITY_JSON"}
    extra = ["TradingSystemLab/results/robustness_v2/T3/H1/year_report.csv", "TradingSystemLab/results/robustness_v2/T3/H1/instrument_report.csv",
        "TradingSystemLab/results/true_oos_v2/T3/H1/trades.csv", "TradingSystemLab/results/true_oos_v2/T3/H1/manifest.json",
        "TradingSystemLab/optimization/phase2b_t3.py", "TradingSystemLab/optimization/phase32.py", "TradingSystemLab/core/backtester.py"]
    for rel in extra:
        digest = preflight.sha(ROOT/rel)
        blob = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{preflight.BASE}:{rel}"])
        assert hashlib.sha256(blob).hexdigest() == digest, rel
        authority_sources.append({"path": rel, "actual_sha256": digest, "matches_original_main_bytes": True})
    source_manifest = {**states, "original_main": preflight.BASE, "original_data_reference": preflight.DATA_COMMIT,
        "data_checkout": preflight.git(data_root, "rev-parse", "HEAD"), "inputs": source_rows,
        "frozen_sources": authority_sources, "raw_candles_published": False,
        "audit_code_sha256": {p.name: preflight.sha(p) for p in sorted(HERE.glob("*.py"))},
        "prior_preflight_preserved_under": "prior_preflight/"}
    for name, frame in files.items(): save(out/name, frame)
    dump(out/"summary.json", summary); dump(out/"independent_audit.json", audit); dump(out/"source_manifest.json", source_manifest)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.data_root, args.out)
    print(json.dumps({k: clean(result[k]) for k in ["COMPUTATIONAL_AUDIT", "SOURCE_INTEGRITY", "ROLL_PROVENANCE", "EXPLORATORY_REPLAY", "TRADABLE_QUARTERLY_PERFORMANCE", "closed_trades", "positive_instruments"]}, sort_keys=True), flush=True)
