"""Read-only, fail-closed source preflight; deliberately NOT a historical backtest.

Run from the repository root. All output must stay in the isolated audit folder
or a scratch directory outside the source-data repository. No network clients.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import subprocess
import sys
from dataclasses import asdict, replace
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
BASE = "38489db7e69336548a583f968f13aab49c20913b"
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
PARAM_SHA = "4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a"
POST = ROOT / "TradingSystemLab/results/post_v3_analysis"
SPEC = POST / "stage7_production_specification_freeze"
INSTRUMENTS = ["Si", "CNY", "GD", "MIX", "BR", "NG"]
PAIRS = dict(zip(INSTRUMENTS[:4], ["USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"]))
METRICS = ["trades", "net_pf", "gross_pf", "net_R", "average_R", "win_pct",
           "average_win_R", "average_loss_R", "max_closed_R_drawdown"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(directory, *args):
    return subprocess.check_output(["git", "-C", str(directory), *args], text=True).strip()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def inspect_csv(path):
    """Inspect the unmodified, unsorted stream before any library normalization."""
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        columns = reader.fieldnames
        if columns != ["Datetime", "Open", "High", "Low", "Close", "Volume"]:
            raise ValueError("UNEXPECTED_SOURCE_SCHEMA")
        rows = list(reader)
    stamps = [datetime.fromisoformat(r["Datetime"]) for r in rows]
    if not rows:
        raise ValueError("EMPTY_SOURCE")
    values = [[float(r[k]) for k in columns[1:]] for r in rows]
    finite = sum(not all(math.isfinite(v) for v in row) for row in values)
    geometry = sum(h < max(o, l, c) or l > min(o, h, c) for o, h, l, c, _ in values)
    positive = sum(any(v <= 0 for v in row[:4]) for row in values)
    duplicates = len(stamps)-len(set(stamps))
    conflicting = 0
    seen = {}
    for stamp, value in zip(stamps, values):
        if stamp in seen and seen[stamp] != value:
            conflicting += 1
        seen[stamp] = value
    deltas = [(stamps[i]-stamps[i-1]).total_seconds()/3600 for i in range(1, len(stamps))]
    intraday = [delta for i, delta in enumerate(deltas, 1) if stamps[i].date() == stamps[i-1].date() and delta > 1]
    gaps = sorted([{"open_timestamp_as_stored": stamps[i].isoformat(),
                    "absolute_open_vs_previous_close_fraction": abs(values[i][0]/values[i-1][3]-1)}
                   for i in range(1, len(stamps)) if values[i-1][3] != 0],
                  key=lambda x: (-x["absolute_open_vs_previous_close_fraction"], x["open_timestamp_as_stored"]))[:5]
    year_rows = []
    for year in range(2020, 2027):
        selected = [t for t in stamps if t.year == year]
        year_rows.append({"year": year, "source_rows": len(selected),
                          "first_timestamp_as_stored": selected[0].isoformat() if selected else None,
                          "last_timestamp_as_stored": selected[-1].isoformat() if selected else None})
    return {"columns": columns, "delimiter": ";", "encoding": "UTF8_COMPATIBLE",
            "rows": len(rows), "sha256": sha(path), "bytes": path.stat().st_size,
            "first_timestamp_as_stored": stamps[0].isoformat(), "last_timestamp_as_stored": stamps[-1].isoformat(),
            "naive_timestamps": sum(t.tzinfo is None for t in stamps),
            "non_hour_aligned_timestamps": sum(t.minute != 0 or t.second != 0 or t.microsecond != 0 for t in stamps),
            "duplicate_timestamps": duplicates, "conflicting_duplicates": conflicting,
            "non_increasing_transitions": sum(x <= 0 for x in deltas),
            "nonfinite_numeric_rows": finite, "invalid_ohlc_rows": geometry, "nonpositive_price_rows": positive,
            "zero_volume_rows": sum(row[4] == 0 for row in values),
            "negative_volume_rows": sum(row[4] < 0 for row in values),
            "fractional_ohlc_rows": sum(any(v % 1 != 0 for v in row[:4]) for row in values),
            "hours_as_stored": sorted(set(t.hour for t in stamps)),
            "weekday_counts": dict(sorted(collections.Counter(t.weekday() for t in stamps).items())),
            "interval_hours_histogram": dict(sorted(collections.Counter(deltas).items())),
            "intraday_intervals_over_one_hour": len(intraday),
            "intraday_unobserved_hour_slots": sum(int(x)-1 for x in intraday),
            "missing_trading_bars": None, "missing_trading_bars_reason": "NO_AUTHENTICATED_SESSION_CALENDAR",
            "largest_observed_gaps_not_classified_as_rollovers": gaps,
            "coverage_by_year": year_rows,
            "series_form": "ONE_MULTIYEAR_OHLC_STREAM_WITHOUT_CONTRACT_IDENTIFIERS",
            "continuous_contract_construction": "UNVERIFIED",
            "supplier": None, "roll_rule": None, "roll_dates": None, "price_adjustment": None,
            "indicator_and_stop_causality_across_rolls": "UNVERIFIABLE_WITHOUT_CONSTRUCTION_METADATA",
            "timezone_provider_confirmation": None, "timestamp_label_provider_confirmation": None,
            "frozen_loader_convention_only": "OPEN_LABELLED_EUROPE_MOSCOW_PLUS_ONE_HOUR",
            "conditional_last_available_close": (stamps[-1]+timedelta(hours=1)).isoformat()+"+03:00"}


def authenticate():
    from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3Parameters
    spec = json.loads((SPEC / "production_specification.json").read_text())
    provenance = json.loads((SPEC / "source_provenance.json").read_text())
    checks, sources = [], []
    for key, item in provenance.items():
        if "path" in item:
            actual = sha(ROOT/item["path"])
            checks.append({"check": key, "pass": actual == item["sha256"]})
            sources.append({"role": key, "path": item["path"], "expected_sha256": item["sha256"], "actual_sha256": actual})
    registry = ROOT / "TradingSystemLab/results/perpetual_v3/phase3_candidate_freeze/candidate_registry.json"
    candidate = next(x for x in json.loads(registry.read_text())["candidates"] if x["candidate_id"] == "T3_H1_candidate_v3")
    parameter_bytes = json.dumps(candidate["parameters"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    digest = hashlib.sha256(parameter_bytes).hexdigest()
    full = asdict(replace(T3Parameters(), **candidate["parameters"]))
    checks.extend([{"check": "candidate_parameter_serialization_sha256", "pass": digest == PARAM_SHA == spec["strategy"]["parameter_sha256"]},
                   {"check": "all_effective_parameters_equal_stage7", "pass": full == spec["strategy"]["parameters"]},
                   {"check": "production_identity", "pass": spec["identity"] == "TRAIL1__N4_01__FULL__R15"},
                   {"check": "configuration", "pass": candidate["phase2_configuration_id"] == spec["strategy"]["configuration_id"] == "T3-H1-4e73cdb77246"},
                   {"check": "C1", "pass": spec["cost_evidence_contract"]["normalized_research_tick"] == .001 and spec["cost_evidence_contract"]["ticks_per_side"] == 1 and spec["cost_evidence_contract"]["round_trip_ticks"] == 2}])
    v2_registry = ROOT/"TradingSystemLab/results/phase3_candidate_freeze/candidate_registry.json"
    v2 = next(x for x in json.loads(v2_registry.read_text())["candidates"] if x["candidate_id"] == "T3_H1_candidate_v2")
    v2_digest = hashlib.sha256(json.dumps(v2["parameters"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    checks.append({"check": "published_v2_parameter_identity", "pass": v2_digest == v2["parameter_hash"] == "aeeb96942cf33d9551b5635f33d2f2745aefad572f57f7ea92b9791c2d992a39" and v2["parameters"]["stop_atr"] == 2.0 and v2["parameters"]["atr_average_period"] == 30})
    from TradingSystemLab.results.post_v3_analysis.stage7_production_specification_freeze.audit_production_specification import audit
    stage7 = audit(SPEC, write_result=False)
    checks.append({"check": "existing_stage7_check_only_auditor", "pass": stage7["status"] == "PASS"})
    ledger = POST / "stage6_fixed_basket_reassessment/trail1_authoritative_trades.csv"
    manifest = json.loads(ledger.with_name("trail1_authoritative_ledger_manifest.json").read_text())
    rows = read_csv(ledger)
    checks.append({"check": "stage6_physical_ledger_bytes", "pass": sha(ledger) == manifest["committed_file_sha256"]})
    selected = [r for r in rows if r["lifecycle"] != "walk_forward"]
    # Published ledger uses the configuration ID for baseline and the frozen
    # candidate ID for historical_true_oos; the authenticated registry links both.
    lifecycle_identity = {"baseline": candidate["phase2_configuration_id"],
                          "historical_true_oos": candidate["candidate_id"]}
    checks.append({"check": "stage6_selected_rows_identity", "pass": all(r["candidate_config_identity"] == lifecycle_identity.get(r["lifecycle"]) and r["trail1_strategy_identity"] == "T3_TRAIL1_H4_02_PROFIT_PROTECTION_TRAIL1" for r in selected)})
    extra = [SPEC/"production_specification.json", SPEC/"source_provenance.json", registry, v2_registry,
             ROOT/"TradingSystemLab/results/true_oos_v2/T3/H1/manifest.json",
             ROOT/"TradingSystemLab/core/indicators.py", ROOT/"TradingSystemLab/core/data_loader.py",
             ROOT/"TradingSystemLab/stage8_robot/production_replay.py", ROOT/"TradingSystemLab/stage8_robot/authority_replay.py",
             ROOT/"TradingSystemLab/stage8_robot/context_builder.py", ROOT/"TradingSystemLab/stage8_robot/strategy_core.py",
             ROOT/"TradingSystemLab/stage8_robot/trail1_state.py", ledger, ledger.with_name("trail1_authoritative_ledger_manifest.json")]
    sources += [{"role": "additional_readonly_authority", "path": str(p.relative_to(ROOT)), "actual_sha256": sha(p)} for p in extra]
    return {"status": "PASS" if all(x["pass"] for x in checks) else "FAIL", "checks": checks,
            "candidate_parameter_sha256": digest, "parameter_hash_scope": "SIX_FIELD_FROZEN_CANDIDATE_PAYLOAD",
            "effective_nine_parameters": full, "stage7_check_only": stage7,
            "stage6_ledger": {"path": str(ledger.relative_to(ROOT)), "sha256": sha(ledger),
                              "physical_rows": len(rows), "non_walk_forward_rows": len(selected),
                              "walk_forward_rows_excluded": len(rows)-len(selected),
                              "identity_labels_by_lifecycle": lifecycle_identity,
                              "aggregation_executed": False,
                              "stage7_digest_scope": "ALL_STAGE5_LIFECYCLES_NOT_THIS_STAGE6_N4_FILE"}}, sources


def placeholders(out):
    def row(year, instrument):
        return {"year": year, "instrument": instrument, "status": "DATA_BLOCKED", **dict.fromkeys(METRICS, "")}
    fields = ["year", "instrument", "status"]+METRICS
    years = list(range(2020, 2027))+["2020-2026"]
    write_csv(out/"annual_by_instrument.csv", fields, [row(y, s) for y in years for s in INSTRUMENTS])
    for filename, group in [("annual_primary4.csv", "PRIMARY4"), ("annual_additional2.csv", "ADDITIONAL2"), ("annual_all6.csv", "ALL6")]:
        write_csv(out/filename, fields, [row(y, group) for y in years])
    write_csv(out/"monthly.csv", ["month", "instrument", "status"]+METRICS, [])
    write_csv(out/"quarterly.csv", ["quarter", "instrument", "status"]+METRICS, [])
    write_csv(out/"trades.csv", ["instrument", "trade_id", "direction", "entry_time", "entry_price", "initial_stop_price", "initial_risk_price", "exit_time", "exit_price", "exit_reason", "gross_R", "cost_R", "net_R_C1"], [])
    write_csv(out/"trail1_trace.csv", ["instrument", "trade_id", "event_time", "event_type", "stop_before", "stop_after", "trigger_time", "activation_time"], [])
    write_csv(out/"robustness.csv", ["instrument", "direction", "status", "trades", "net_R", "worst_year", "worst_quarter", "worst_month", "max_drawdown_R", "max_losing_streak", "net_R_without_top1", "net_R_without_top3", "net_R_without_top5", "top1_positive_profit_share", "top3_positive_profit_share", "top5_positive_profit_share", "positive_years", "negative_years", "net_R_after_costs"],
              [{"instrument": s, "direction": d, "status": "DATA_BLOCKED"} for s in INSTRUMENTS+["PRIMARY4", "ADDITIONAL2", "ALL6"] for d in ["ALL", "LONG", "SHORT"]])
    rows = []
    for year in range(2020, 2027):
        for q, p in list(PAIRS.items())+[("PRIMARY4", "N4")]:
            rows.append({"year": year, "quarterly": q, "perpetual": p,
                         "status": "DATA_BLOCKED", "n4_status": "NO_DATA" if year < 2023 else "AUTHENTICATED_LEDGER_NOT_AGGREGATED",
                         "common_interval_status": "NO_COMMON_COVERAGE" if year < 2023 else "NOT_CERTIFIED_ROLL_METADATA_MISSING"})
    write_csv(out/"quarterly_vs_perpetual_n4.csv", ["year", "quarterly", "perpetual", "status", "n4_status", "common_interval_status", "common_start", "common_end", "quarterly_trades", "quarterly_pf", "quarterly_net_R", "quarterly_average_R", "perpetual_trades", "perpetual_pf", "perpetual_net_R", "perpetual_average_R", "delta_average_R", "quarterly_trade_frequency_per_year", "perpetual_trade_frequency_per_year"], rows)
    write_csv(out/"v2_vs_v3_comparison.csv", ["year", "instrument", "status", "v2_candidate", "v2_stop_atr", "v2_atr_average_period", "v2_trail1_identical", "v2_trades", "v2_pf", "v2_net_R", "v2_average_R", "v2_max_drawdown_R", "v3_trades", "v3_pf", "v3_net_R", "v3_average_R", "v3_max_drawdown_R"],
              [{"year": y, "instrument": s, "status": "DATA_BLOCKED", "v2_candidate": "T3_H1_candidate_v2", "v2_stop_atr": 2.0, "v2_atr_average_period": 30, "v2_trail1_identical": False} for y in years for s in INSTRUMENTS])


def execute(data_root, out):
    data_root, out = Path(data_root).resolve(), Path(out).resolve()
    if out == ROOT or data_root == out or data_root in out.parents:
        raise ValueError("OUTPUT_MUST_NOT_OVERWRITE_REPOSITORY_ROOT_OR_SOURCE_DATA")
    if ROOT in out.parents and HERE != out and HERE not in out.parents:
        raise ValueError("REPOSITORY_OUTPUT_MUST_STAY_IN_ISOLATED_AUDIT_DIRECTORY")
    out.mkdir(parents=True, exist_ok=True)
    registry = read_csv(POST/"stage5_structural_validation/canonical_lifecycle_registry.csv")
    expected = {r["instrument"]: r["source_market_data_identity"] for r in registry if r["generation"] == "v2_quarterly" and r["strategy"] == "T3" and r["timeframe"] == "H1" and r["lifecycle"] == "baseline"}
    data, missing, quality_errors = [], [], []
    for symbol in INSTRUMENTS:
        rel = f"futures_quarterly/{symbol}/{symbol}_H1.csv"
        path = data_root/rel
        if not path.is_file():
            missing.append(rel)
            continue
        item = inspect_csv(path)
        item.update(instrument=symbol, group="PRIMARY" if symbol in PAIRS else "ADDITIONAL", relative_path=rel,
                    registry_identity=expected[symbol], hash_matches_registry=item["sha256"] == expected[symbol].rsplit(":", 1)[1])
        historical = subprocess.check_output(["git", "-C", str(data_root), "show", f"{DATA_COMMIT}:{rel}"])
        item["hash_matches_frozen_data_commit"] = hashlib.sha256(historical).hexdigest() == item["sha256"]
        readme = path.with_name("README.md")
        item["readme_sha256"] = sha(readme) if readme.exists() else None
        item["readme_nonwhitespace_bytes"] = len(readme.read_bytes().strip()) if readme.exists() else None
        if not item["hash_matches_registry"] or not item["hash_matches_frozen_data_commit"]:
            quality_errors.append(f"HASH_MISMATCH:{symbol}")
        for key in ["duplicate_timestamps", "non_increasing_transitions", "nonfinite_numeric_rows", "invalid_ohlc_rows", "nonpositive_price_rows", "negative_volume_rows"]:
            if item[key]:
                quality_errors.append(f"{key}:{symbol}")
        data.append(item)
    authentication, sources = authenticate()
    from scalar_audit import run_audit
    scalar = run_audit()
    blockers = [{"code": "ROLL_CONSTRUCTION_UNAUTHENTICATED", "instruments": INSTRUMENTS,
                 "required": ["provider and export version", "constituent contract identifiers and effective switch timestamps", "selection rule known at the time", "additive/multiplicative/unadjusted treatment and adjustment factors", "point-in-time availability of adjustments", "timezone and open/close timestamp labels", "historical session calendars", "position/stop and rollover cash-flow interpretation"]}]
    if missing:
        blockers.append({"code": "SOURCE_FILES_MISSING", "files": missing})
    if quality_errors:
        blockers.append({"code": "SOURCE_INTEGRITY_ERRORS", "errors": quality_errors})
    technical = "AUDIT_FAIL" if authentication["status"] != "PASS" or quality_errors else "DATA_BLOCKED"
    summary = {"technical_status": technical, "economic_conclusion": "INCONCLUSIVE", "base_commit": BASE,
               "request_end_date_moscow": "2026-10-19", "actual_source_end_as_stored": max((x["last_timestamp_as_stored"] for x in data), default=None),
               "historical_quarterly_replay_executed": False, "historical_trade_count": None,
               "profitability": None, "net_pf": None, "net_R": None, "positive_instruments": None, "positive_years": None,
               "missing_source_files": missing, "blockers": blockers,
               "secondary_execution_sensitivity": "NOT_RUN_HISTORICAL_CONTRACT_SPECS_UNAUTHENTICATED",
               "capital_model": "NOT_RUN", "clean_true_oos_claim": False,
               "synthetic_scalar_audit": scalar["status"], "tables_contain_uncomputed_blank_metrics": True}
    audit_result = {"technical_status": technical, "economic_conclusion": "INCONCLUSIVE", "authentication": authentication,
                    "synthetic_independent_scalar": scalar,
                    "historical_checks": {k: "NOT_RUN_DATA_BLOCKED" for k in ["signals", "trail1_trace", "roll_causality", "no_future_data", "activation", "gaps", "one_position", "gross_cost_net_pf_arithmetic", "exit_year_assignment", "instrument_year_aggregate_reconciliation", "two_historical_replays"]},
                    "not_a_full_historical_audit_pass": True}
    manifest = {"repository_base_commit": BASE, "data_frozen_reference_commit": DATA_COMMIT,
                "data_checkout_commit": git(data_root, "rev-parse", "HEAD"),
                "data_checkout_clean": not bool(git(data_root, "status", "--porcelain")),
                "raw_candles_in_artifacts": False, "sources": sources,
                "quarterly_inputs": [{k: x[k] for k in ["relative_path", "sha256", "bytes", "registry_identity", "hash_matches_registry", "hash_matches_frozen_data_commit"]} for x in data],
                "audit_code_sha256": {p.name: sha(p) for p in sorted(HERE.glob("*.py"))}}
    dump(out/"source_manifest.json", manifest)
    dump(out/"data_quality.json", {"instruments": data, "missing_source_files": missing, "quality_errors": quality_errors,
                                   "session_gap_interpretation": "Unobserved slots are diagnostics, not certified missing market bars; no padding or smoothing."})
    dump(out/"independent_audit.json", audit_result)
    dump(out/"summary.json", summary)
    placeholders(out)
    coverage = [{"instrument": x["instrument"], **r} for x in data for r in x["coverage_by_year"]]
    write_csv(out/"source_coverage.csv", ["instrument", "year", "source_rows", "first_timestamp_as_stored", "last_timestamp_as_stored"], coverage)
    observed = [{"instrument": x["instrument"], "rows": x["rows"], "sha256_matches": x["hash_matches_registry"],
                 "readme_nonwhitespace_bytes": x["readme_nonwhitespace_bytes"], "intraday_unobserved_hour_slots": x["intraday_unobserved_hour_slots"]} for x in data]
    (out/"preflight.log").write_text("READONLY_PREFLIGHT\n"+json.dumps({"technical_status": technical, "sources": observed, "authentication": authentication["status"], "scalar_fixture_audit": scalar["status"], "historical_replay": "NOT_RUN", "source_files_missing": missing}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summary = execute(args.data_root, args.out)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    # A successful preflight execution must never look like a successful backtest.
    raise SystemExit(2 if summary["technical_status"] == "DATA_BLOCKED" else 1)
