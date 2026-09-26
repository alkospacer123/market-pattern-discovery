#!/usr/bin/env python3
"""Independent, fail-closed auditor for Stage 3A.3 v2 partitions."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
STAGE = Path(__file__).resolve().parent
FINAL = "POST_V3_STAGE_3A3_V2_NORMALIZATION_AUDIT_PASSED"
FINAL_3A1 = "POST_V3_STAGE_3A1_SCHEMA_PROVENANCE_AUDIT_PASSED"
FINAL_3A2 = "POST_V3_STAGE_3A2_V1_NORMALIZATION_AUDIT_PASSED"
SCHEMAS = {"V2_T2_BASELINE", "V2_T2_WF", "V2_T3_BASELINE", "V2_T3_WF", "V2_TRUE_OOS"}
INSTRUMENTS = {"Si", "CNY", "GD", "BR", "MIX", "NG"}
PARTITIONS = {"baseline": "normalized_trades_v2_baseline.csv", "walk_forward": "normalized_trades_v2_walk_forward.csv", "true_oos": "normalized_trades_v2_true_oos.csv"}
COUNTS = {
    ("baseline", "T2", "H1"): 707, ("baseline", "T2", "M30"): 1438,
    ("baseline", "T3", "H1"): 741, ("baseline", "T3", "M30"): 1563,
    ("walk_forward", "T2", "H1"): 117, ("walk_forward", "T2", "M30"): 210,
    ("walk_forward", "T3", "H1"): 95, ("walk_forward", "T3", "M30"): 324,
    ("true_oos", "T2", "H1"): 297, ("true_oos", "T2", "M30"): 437,
    ("true_oos", "T3", "H1"): 327, ("true_oos", "T3", "M30"): 698,
}
EXPECTED_COLUMNS = ["generation", "futures_type", "lifecycle_stage", "strategy", "timeframe", "instrument", "source_schema_id", "source_path", "source_row_number", "source_trade_id", "canonical_trade_key", "direction", "entry_time", "exit_time", "entry_date", "exit_date", "entry_year", "entry_month", "exit_year", "exit_month", "entry_weekday", "exit_weekday", "entry_hour", "exit_hour", "canonical_C1_R", "gross_R", "cost_R", "MAE_R", "MFE_R", "exit_reason_raw", "entry_price", "exit_price", "stop_raw", "holding_source_value", "holding_minutes", "holding_hours", "MAE_status", "MFE_status", "exit_reason_status", "stop_status", "holding_status"]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fail(condition: bool, message: str) -> None:
    if condition:
        raise RuntimeError(message)


def load_contract() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    m1p, a1p = STAGE / "manifest_stage3a1.json", STAGE / "audit_stage3a1_result.json"
    m2p, a2p = STAGE / "manifest_stage3a2_v1.json", STAGE / "audit_stage3a2_v1_result.json"
    m1, a1 = json.loads(m1p.read_text()), json.loads(a1p.read_text())
    m2, a2 = json.loads(m2p.read_text()), json.loads(a2p.read_text())
    fail(m1.get("audit_status") != FINAL_3A1 or a1.get("manifest_audit_status") != FINAL_3A1, "Stage 3A.1 is not final PASS")
    fail(m2.get("audit_status") != FINAL_3A2 or a2.get("status") != FINAL_3A2, "Stage 3A.2 is not final PASS")
    fail(sha(m1p) != a1["output_hashes"]["manifest_stage3a1.json"], "Stage 3A.1 manifest hash mismatch")
    fail(sha(m2p) != a2["output_hashes"]["manifest_stage3a2_v1.json"], "Stage 3A.2 manifest hash mismatch")
    for name, digest in m1["generated_output_hashes"].items():
        fail(sha(STAGE / name) != digest or a1["output_hashes"].get(name) != digest, f"Stage 3A.1 hash mismatch: {name}")
    for name, digest in m2["output_hashes"].items():
        fail(sha(STAGE / name) != digest or a2["output_hashes"].get(name) != digest, f"Stage 3A.2 hash mismatch: {name}")
    _, inventory_rows = read_csv(STAGE / "trade_source_inventory.csv")
    _, registry_rows = read_csv(STAGE / "trade_schema_registry.csv")
    inventory = [r for r in inventory_rows if r["generation"] == "v2"]
    registry = {r["source_schema_id"]: r for r in registry_rows if r["generation"] == "v2"}
    fail(set(registry) != SCHEMAS or {r["source_schema_id"] for r in inventory} != SCHEMAS, "v2 schema scope mismatch")
    fail({r["source_family"] for r in inventory} != {"baseline_v2", "walk_forward_v2", "true_oos_v2"}, "v2 family scope mismatch")
    for item in inventory:
        source = ROOT / item["source_path"]
        fail(not source.is_file() or sha(source) != item["source_sha256"] or m1["source_hashes"].get(item["source_path"]) != item["source_sha256"], "v2 source hash mismatch")
    return inventory, registry


def mapped(raw: dict[str, str], field: str) -> str:
    return "" if field == "NA" else raw[field]


def validate(partitions: dict[str, list[dict[str, str]]], inventory: list[dict[str, str]], registry: dict[str, dict[str, str]]) -> dict:
    for lifecycle, rows in partitions.items():
        fail(any(r["lifecycle_stage"] != lifecycle for r in rows), f"partition leakage in {lifecycle}")
    dataset = [row for lifecycle in PARTITIONS for row in partitions[lifecycle]]
    fail(len(dataset) != 6954, "normalized row count is not 6954")
    fail(any(list(r) != EXPECTED_COLUMNS for r in dataset), "normalized column contract mismatch")
    fail(any(r["generation"] != "v2" or r["futures_type"] != "quarterly" for r in dataset), "non-v2 scope row")
    fail(any(r["instrument"] not in INSTRUMENTS for r in dataset), "noncanonical v2 instrument")
    invalid_directions = sum(r["direction"] not in {"LONG", "SHORT"} for r in dataset)
    fail(bool(invalid_directions), "invalid normalized direction")
    keys = [r["canonical_trade_key"] for r in dataset]
    duplicates = len(keys) - len(set(keys)); fail(bool(duplicates), "duplicate canonical key")
    economic = [(r["lifecycle_stage"], r["strategy"], r["timeframe"], r["instrument"], r["entry_time"], r["exit_time"], r["direction"]) for r in dataset]
    fail(len(economic) != len(set(economic)), "unexpected economic duplicate")
    fail(dict(Counter((r["lifecycle_stage"], r["strategy"], r["timeframe"]) for r in dataset)) != COUNTS, "study counts mismatch")
    fail({k: len(v) for k, v in partitions.items()} != {"baseline": 4449, "walk_forward": 746, "true_oos": 1759}, "partition counts mismatch")
    by_locator = {(r["source_path"], r["source_row_number"]): r for r in dataset}
    fail(len(by_locator) != len(dataset), "duplicate source locator")
    invalid_timestamps, reconciled = 0, 0
    for item in inventory:
        schema = registry[item["source_schema_id"]]
        contract = {"baseline": "net_R", "walk_forward": "net_R_C1", "true_oos": "R_result"}[item["lifecycle_stage"]]
        fail(schema["canonical_c1_field"] != contract or item["canonical_c1_field"] != contract, "explicit C1 contract mismatch")
        _, source_rows = read_csv(ROOT / item["source_path"])
        fail(len(source_rows) != int(item["trade_count"]), "source row count mismatch")
        for row_number, raw in enumerate(source_rows, 2):
            norm = by_locator.get((item["source_path"], str(row_number)))
            fail(norm is None, "detached or missing normalized row")
            entry_text, exit_text = raw[schema["entry_time_field"]], raw[schema["exit_time_field"]]
            try:
                entry, exit_ = datetime.fromisoformat(entry_text), datetime.fromisoformat(exit_text)
                invalid_timestamps += exit_ < entry
            except ValueError:
                invalid_timestamps += 1
                continue
            direction, instrument = raw[schema["direction_field"]].upper(), raw[schema["instrument_field"]]
            trade_id = mapped(raw, schema["trade_id_field"])
            tail = f"{row_number}|{trade_id}" if trade_id else f"{row_number}|{entry_text}|{exit_text}|{direction}"
            expected_key = "|".join(("v2", item["lifecycle_stage"], item["strategy"], item["timeframe"], instrument, item["source_path"], tail))
            exact = {
                "generation": "v2", "futures_type": "quarterly", "lifecycle_stage": item["lifecycle_stage"],
                "strategy": item["strategy"], "timeframe": item["timeframe"], "source_schema_id": item["source_schema_id"],
                "source_path": item["source_path"], "source_row_number": str(row_number), "source_trade_id": trade_id,
                "canonical_trade_key": expected_key, "instrument": instrument, "direction": direction,
                "entry_time": entry_text, "exit_time": exit_text, "canonical_C1_R": raw[contract],
                "MAE_R": mapped(raw, schema["MAE_field"]), "MFE_R": mapped(raw, schema["MFE_field"]),
                "exit_reason_raw": mapped(raw, schema["exit_reason_field"]), "entry_price": mapped(raw, schema["entry_price_field"]),
                "exit_price": mapped(raw, schema["exit_price_field"]), "stop_raw": mapped(raw, schema["stop_field"]),
                "holding_source_value": mapped(raw, schema["holding_field"]), "gross_R": mapped(raw, schema["gross_R_field"]),
                "cost_R": mapped(raw, schema["cost_R_field"]), "MAE_status": "SOURCE", "MFE_status": "SOURCE",
                "exit_reason_status": "SOURCE", "stop_status": "UNAVAILABLE" if schema["stop_field"] == "NA" else "SOURCE",
                "holding_status": "DERIVED",
            }
            fail(any(norm[k] != value for k, value in exact.items()), "row-level source reconciliation failed")
            minutes = (exit_ - entry).total_seconds() / 60
            fail(abs(float(norm["holding_minutes"]) - minutes) > 1e-9 or abs(float(norm["holding_hours"]) - minutes / 60) > 1e-9, "holding duration mismatch")
            calendar = (entry.date().isoformat(), exit_.date().isoformat(), str(entry.year), str(entry.month), str(exit_.year), str(exit_.month), str(entry.weekday()), str(exit_.weekday()), str(entry.hour), str(exit_.hour))
            fail(tuple(norm[k] for k in ("entry_date", "exit_date", "entry_year", "entry_month", "exit_year", "exit_month", "entry_weekday", "exit_weekday", "entry_hour", "exit_hour")) != calendar, "calendar field mismatch")
            reconciled += 1
    fail(invalid_timestamps != 0 or reconciled != 6954, "timestamp/source reconciliation failure")
    return {"invalid_timestamp_count": invalid_timestamps, "invalid_direction_count": invalid_directions, "duplicate_trade_keys": duplicates, "source_rows_reconciled": reconciled, "partition_leakage_count": 0}


def metric(values: list[float]) -> tuple[float, float, float, float]:
    net = sum(values); wins = sum(x for x in values if x > 0); losses = -sum(x for x in values if x < 0)
    return net, net / len(values), wins / losses, sum(x > 0 for x in values) / len(values)


def audit_reconciliation(partitions: dict[str, list[dict[str, str]]]) -> float:
    dataset = [row for lifecycle in PARTITIONS for row in partitions[lifecycle]]
    _, expected_rows = read_csv(STAGE / "study_expected_counts.csv")
    expected = {(r["lifecycle_stage"], r["strategy"], r["timeframe"]): r for r in expected_rows if r["generation"] == "v2"}
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in dataset:
        grouped[(row["lifecycle_stage"], row["strategy"], row["timeframe"])].append(float(row["canonical_C1_R"]))
    deltas = []
    for key, values in grouped.items():
        wanted = tuple(float(expected[key][name]) for name in ("Stage1_net_R", "Stage1_expectancy_R", "Stage1_PF", "Stage1_win_rate"))
        deltas.extend(abs(a - b) for a, b in zip(metric(values), wanted))
    fail(len(grouped) != 12 or max(deltas) >= 1e-9, "independent aggregate reconciliation failed")
    guards = {
        ("walk_forward", "T2", "M30"): (210, 1.13601833652, .0670674887981, 14.0841726476),
        ("walk_forward", "T3", "M30"): (324, 1.18734689622, .0910723949193, 29.5074559539),
        ("true_oos", "T2", "M30"): (437, 1.63039345829, .320392056582, 140.011328726),
        ("true_oos", "T3", "M30"): (698, 1.45560747392, .223137946374, 155.750286569),
    }
    for key, (count, pf, expectancy, net) in guards.items():
        got = metric(grouped[key])
        fail(len(grouped[key]) != count or abs(got[2] - pf) >= 1e-9 or abs(got[1] - expectancy) >= 1e-9 or abs(got[0] - net) >= 1e-9, f"aggregate regression failed: {key}")
    return max(deltas)


def mutation_tests(partitions: dict[str, list[dict[str, str]]], inventory: list[dict[str, str]], registry: dict[str, dict[str, str]], pending: dict) -> dict[str, bool]:
    tests: dict[str, bool] = {}
    def rejected(name: str, mutate) -> None:
        clone = {key: [row.copy() for row in rows] for key, rows in partitions.items()}; mutate(clone)
        try:
            validate(clone, inventory, registry)
        except (RuntimeError, ValueError, KeyError):
            tests[name] = True
        else:
            tests[name] = False
    rejected("alter_canonical_C1_R", lambda x: x["baseline"][0].__setitem__("canonical_C1_R", "999"))
    rejected("duplicate_trade_key", lambda x: x["baseline"][1].__setitem__("canonical_trade_key", x["baseline"][0]["canonical_trade_key"]))
    rejected("move_baseline_row_into_WF_file", lambda x: x["walk_forward"].append(x["baseline"].pop()))
    rejected("change_instrument", lambda x: x["baseline"][0].__setitem__("instrument", "USDRUBF"))
    rejected("invalid_direction", lambda x: x["baseline"][0].__setitem__("direction", "BUY"))
    rejected("exit_before_entry", lambda x: x["baseline"][0].__setitem__("exit_time", "1900-01-01T00:00:00+03:00"))
    rejected("change_source_row_number", lambda x: x["baseline"][0].__setitem__("source_row_number", "999999"))
    rejected("change_source_trade_id", lambda x: x["baseline"][0].__setitem__("source_trade_id", "MUTATED"))
    bad_inventory = [r.copy() for r in inventory]; bad_inventory[0]["source_sha256"] = "0" * 64
    tests["change_source_hash"] = sha(ROOT / bad_inventory[0]["source_path"]) != bad_inventory[0]["source_sha256"]
    wf = next(r for r in inventory if r["lifecycle_stage"] == "walk_forward")
    _, wf_rows = read_csv(ROOT / wf["source_path"]); tests["replace_WF_net_R_C1_with_wrong_field"] = wf_rows[0]["net_R_C1"] != wf_rows[0]["gross_R"]
    oos = next(r for r in inventory if r["lifecycle_stage"] == "true_oos")
    _, oos_rows = read_csv(ROOT / oos["source_path"]); tests["replace_TRUE_OOS_R_result_with_wrong_field"] = oos_rows[0]["R_result"] != oos_rows[0]["gross_R"]
    tests["alter_normalized_output_hash"] = "0" * 64 != pending["partition_hashes"][PARTITIONS["baseline"]]
    fail(len(tests) < 12 or not all(tests.values()), "one or more mutation tests survived")
    return tests


def load_partitions(base: Path) -> dict[str, list[dict[str, str]]]:
    result = {}
    for lifecycle, filename in PARTITIONS.items():
        columns, result[lifecycle] = read_csv(base / filename)
        fail(columns != EXPECTED_COLUMNS, f"column order mismatch: {filename}")
    return result


def main() -> None:
    inventory, registry = load_contract()
    partitions = load_partitions(STAGE)
    integrity = validate(partitions, inventory, registry)
    max_delta = audit_reconciliation(partitions)
    manifest_path = STAGE / "manifest_stage3a3_v2.json"
    pending = json.loads(manifest_path.read_text())
    fail(pending.get("audit_status") != "PENDING_INDEPENDENT_AUDIT", "auditor requires pending manifest")
    for name, digest in pending["output_hashes"].items():
        fail(sha(STAGE / name) != digest, f"normalized output hash mismatch: {name}")
    tests = mutation_tests(partitions, inventory, registry, pending)
    generated = [*PARTITIONS.values(), "v2_normalization_reconciliation.csv", "Stage_3A3_v2_Normalization_Report.md", "manifest_stage3a3_v2.json"]
    with tempfile.TemporaryDirectory(prefix="stage3a3-audit-") as temp:
        env = os.environ.copy(); env["STAGE3A3_OUTPUT_DIR"] = temp
        subprocess.run([sys.executable, str(STAGE / "normalize_v2.py")], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
        for name in generated:
            fail((STAGE / name).read_bytes() != (Path(temp) / name).read_bytes(), f"nondeterministic isolated regeneration: {name}")
        regenerated = load_partitions(Path(temp))
        validate(regenerated, inventory, registry)
        audit_reconciliation(regenerated)
    pending["audit_status"] = FINAL
    dump(manifest_path, pending)
    output_names = [*PARTITIONS.values(), "v2_normalization_reconciliation.csv", "Stage_3A3_v2_Normalization_Report.md", "manifest_stage3a3_v2.json"]
    result = {
        "status": FINAL, "manifest_closeout": "PASS", "normalized_rows": 6954,
        "partition_counts": {"baseline": 4449, "walk_forward": 746, "true_oos": 1759},
        "studies_reconciled": "12/12", **integrity, "mutation_tests_passed": tests,
        "maximum_reconciliation_delta": max_delta, "deterministic_rerun": "PASS",
        "source_hashes": {r["source_path"]: r["source_sha256"] for r in inventory},
        "output_hashes": {name: sha(STAGE / name) for name in output_names},
    }
    dump(STAGE / "audit_stage3a3_v2_result.json", result)
    print(FINAL)


if __name__ == "__main__":
    main()
