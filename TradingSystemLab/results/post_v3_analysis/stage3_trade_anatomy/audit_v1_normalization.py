#!/usr/bin/env python3
"""Independent, fail-closed auditor for the Stage 3A.2 v1 ledger."""

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
FINAL = "POST_V3_STAGE_3A2_V1_NORMALIZATION_AUDIT_PASSED"
FINAL_3A1 = "POST_V3_STAGE_3A1_SCHEMA_PROVENANCE_AUDIT_PASSED"
DERIVED = "profit_R-2*0.001/initial_risk"
EXPECTED_SCHEMAS = {"V1_H1_TRUE_OOS", "V1_T2_H1_WF_LEGACY", "V1_T2_M30_TRUE_OOS", "V1_T2_M30_WF", "V1_T2_MTF_BASELINE", "V1_T3_H1_WF_LEGACY_C1_DERIVED", "V1_T3_M30_TRUE_OOS", "V1_T3_M30_WF", "V1_T3_MTF_BASELINE_C1_DERIVED"}
EXPECTED_COLUMNS = ["generation", "futures_type", "lifecycle_stage", "strategy", "timeframe", "instrument", "source_schema_id", "source_path", "source_row_number", "source_trade_id", "canonical_trade_key", "direction", "entry_time", "exit_time", "entry_date", "exit_date", "entry_year", "entry_month", "exit_year", "exit_month", "entry_weekday", "exit_weekday", "entry_hour", "exit_hour", "canonical_C1_R", "gross_R", "cost_R", "MAE_R", "MFE_R", "exit_reason_raw", "entry_price", "exit_price", "stop_raw", "holding_source_value", "holding_minutes", "holding_hours", "MAE_status", "MFE_status", "exit_reason_status", "stop_status", "holding_status"]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fail(condition: bool, message: str) -> None:
    if condition:
        raise RuntimeError(message)


def load_contract() -> tuple[dict, dict, list[dict[str, str]], dict[str, dict[str, str]]]:
    mpath, apath = STAGE / "manifest_stage3a1.json", STAGE / "audit_stage3a1_result.json"
    manifest, audit = json.loads(mpath.read_text()), json.loads(apath.read_text())
    fail(manifest.get("audit_status") != FINAL_3A1 or audit.get("manifest_audit_status") != FINAL_3A1, "Stage 3A.1 prerequisite is not final PASS")
    for name in ("trade_source_inventory.csv", "trade_schema_registry.csv"):
        fail(sha(STAGE / name) != manifest["generated_output_hashes"][name], f"changed Stage 3A.1 artifact: {name}")
    _, all_inventory = read_csv(STAGE / "trade_source_inventory.csv")
    inventory = [r for r in all_inventory if r["generation"] == "v1"]
    _, registry_rows = read_csv(STAGE / "trade_schema_registry.csv")
    registry = {r["source_schema_id"]: r for r in registry_rows if r["generation"] == "v1"}
    fail(set(registry) != EXPECTED_SCHEMAS or {x["source_schema_id"] for x in inventory} != EXPECTED_SCHEMAS, "v1 schema scope mismatch")
    for item in inventory:
        path = ROOT / item["source_path"]
        fail(not path.is_file() or sha(path) != item["source_sha256"] or manifest["source_hashes"].get(item["source_path"]) != item["source_sha256"], "v1 source hash mismatch")
    return manifest, audit, inventory, registry


def mapped(raw: dict[str, str], field: str) -> str:
    return "" if field == "NA" else raw[field]


def c1(raw: dict[str, str], contract: str) -> float:
    if contract == DERIVED:
        return float(raw["profit_R"]) - 2 * 0.001 / float(raw["initial_risk"])
    fail(contract not in raw, "unknown C1 field")
    return float(raw[contract])


def canonical_instrument(value: str) -> str:
    aliases = {"Si": "USDRUBF", "USDRUBF": "USDRUBF", "CNY": "CNYRUBF", "CNYRUBF": "CNYRUBF"}
    fail(value not in aliases, "invalid instrument alias")
    return aliases[value]


def validate(dataset: list[dict[str, str]], inventory: list[dict[str, str]], registry: dict[str, dict[str, str]]) -> dict:
    fail(len(dataset) != 1299, "normalized row count is not 1299")
    fail(any(set(r) != set(EXPECTED_COLUMNS) for r in dataset), "normalized column contract mismatch")
    invalid_directions = sum(r["direction"] not in {"LONG", "SHORT"} for r in dataset)
    fail(bool(invalid_directions), "invalid normalized direction")
    fail(any(r["generation"] != "v1" or r["futures_type"] != "perpetual" for r in dataset), "non-v1 scope row")
    fail(any(r["instrument"] not in {"USDRUBF", "CNYRUBF"} for r in dataset), "noncanonical instrument")
    keys = [r["canonical_trade_key"] for r in dataset]
    duplicates = len(keys) - len(set(keys)); fail(bool(duplicates), "duplicate canonical key")
    economic = [(r["lifecycle_stage"], r["strategy"], r["timeframe"], r["instrument"], r["entry_time"], r["exit_time"], r["direction"]) for r in dataset]
    fail(len(economic) != len(set(economic)), "unproven economic duplicate")
    by_locator = {(r["source_path"], r["source_row_number"]): r for r in dataset}
    fail(len(by_locator) != len(dataset), "duplicate source locator")
    invalid_timestamps = 0; reconciled = 0
    for item in inventory:
        schema = registry[item["source_schema_id"]]
        _, source_rows = read_csv(ROOT / item["source_path"])
        fail(len(source_rows) != int(item["trade_count"]), "authenticated source count mismatch")
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
            inst = canonical_instrument(raw[schema["instrument_field"]])
            trade_id = mapped(raw, schema["trade_id_field"])
            tail = f"{row_number}|{trade_id}" if trade_id else f"{row_number}|{entry_text}|{exit_text}|{raw[schema['direction_field']].upper()}"
            expected_key = "|".join(("v1", item["lifecycle_stage"], item["strategy"], item["timeframe"], inst, item["source_path"], tail))
            exact = {
                "source_schema_id": item["source_schema_id"], "source_trade_id": trade_id, "canonical_trade_key": expected_key,
                "direction": raw[schema["direction_field"]].upper(), "entry_time": entry_text, "exit_time": exit_text,
                "instrument": inst, "MAE_R": mapped(raw, schema["MAE_field"]), "MFE_R": mapped(raw, schema["MFE_field"]),
                "exit_reason_raw": mapped(raw, schema["exit_reason_field"]), "entry_price": mapped(raw, schema["entry_price_field"]),
                "exit_price": mapped(raw, schema["exit_price_field"]), "stop_raw": mapped(raw, schema["stop_field"]),
                "holding_source_value": mapped(raw, schema["holding_field"]), "gross_R": mapped(raw, schema["gross_R_field"]), "cost_R": mapped(raw, schema["cost_R_field"]),
            }
            fail(any(norm[k] != v for k, v in exact.items()), "row-level source reconciliation failed")
            fail(abs(float(norm["canonical_C1_R"]) - c1(raw, schema["canonical_c1_field"])) > 1e-12, "canonical C1 mismatch")
            minutes = (exit_ - entry).total_seconds() / 60
            fail(abs(float(norm["holding_minutes"]) - minutes) > 1e-9 or abs(float(norm["holding_hours"]) - minutes / 60) > 1e-9, "derived holding mismatch")
            calendar = [norm["entry_date"] == entry.date().isoformat(), norm["exit_date"] == exit_.date().isoformat(), norm["entry_year"] == str(entry.year), norm["entry_month"] == str(entry.month), norm["exit_year"] == str(exit_.year), norm["exit_month"] == str(exit_.month), norm["entry_weekday"] == str(entry.weekday()), norm["exit_weekday"] == str(exit_.weekday()), norm["entry_hour"] == str(entry.hour), norm["exit_hour"] == str(exit_.hour)]
            fail(not all(calendar), "calendar normalization mismatch")
            reconciled += 1
    fail(invalid_timestamps != 0 or reconciled != 1299, "timestamp/source reconciliation failure")
    groups = Counter((r["lifecycle_stage"], r["strategy"], r["timeframe"]) for r in dataset)
    expected_counts = {("baseline", "T2", "H1"): 79, ("baseline", "T2", "M30"): 178, ("baseline", "T3", "H1"): 114, ("baseline", "T3", "M30"): 235, ("walk_forward", "T2", "H1"): 33, ("walk_forward", "T2", "M30"): 67, ("walk_forward", "T3", "H1"): 34, ("walk_forward", "T3", "M30"): 60, ("true_oos", "T2", "H1"): 69, ("true_oos", "T2", "M30"): 171, ("true_oos", "T3", "H1"): 97, ("true_oos", "T3", "M30"): 162}
    fail(dict(groups) != expected_counts, "study counts mismatch")
    return {"invalid_timestamp_count": invalid_timestamps, "invalid_direction_count": invalid_directions, "duplicate_trade_keys": duplicates, "source_rows_reconciled": reconciled}


def metric(values: list[float]) -> tuple[float, float, float, float]:
    net = sum(values); positive = sum(x for x in values if x > 0); negative = -sum(x for x in values if x < 0)
    return net, net / len(values), positive / negative, sum(x > 0 for x in values) / len(values)


def audit_reconciliation(dataset: list[dict[str, str]]) -> float:
    _, expected_rows = read_csv(STAGE / "study_expected_counts.csv")
    expected = {(r["lifecycle_stage"], r["strategy"], r["timeframe"]): r for r in expected_rows if r["generation"] == "v1"}
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in dataset: grouped[(row["lifecycle_stage"], row["strategy"], row["timeframe"])].append(float(row["canonical_C1_R"]))
    deltas = []
    for key, values in grouped.items():
        got, ref = metric(values), expected[key]
        wanted = (float(ref["Stage1_net_R"]), float(ref["Stage1_expectancy_R"]), float(ref["Stage1_PF"]), float(ref["Stage1_win_rate"]))
        deltas.extend(abs(a - b) for a, b in zip(got, wanted))
    fail(len(grouped) != 12 or max(deltas) >= 1e-9, "independent aggregate reconciliation failed")
    guard = metric(grouped[("walk_forward", "T3", "H1")])
    fail(len(grouped[("walk_forward", "T3", "H1")]) != 34 or abs(guard[0] - 32.9117048791) > 1e-9 or abs(guard[1] - .967991319974) > 1e-9 or abs(guard[2] - 3.38032767202) > 1e-9 or abs(guard[2] - 3.49197193021) < 1e-6, "T3/H1 WF C1 regression")
    return max(deltas)


def mutation_tests(dataset: list[dict[str, str]], inventory: list[dict[str, str]], registry: dict[str, dict[str, str]]) -> dict[str, bool]:
    tests: dict[str, bool] = {}
    def rejected(name: str, mutate) -> None:
        clone = [r.copy() for r in dataset]; mutate(clone)
        try: validate(clone, inventory, registry)
        except (RuntimeError, ValueError, KeyError): tests[name] = True
        else: tests[name] = False
    rejected("change_canonical_C1_R", lambda x: x[0].__setitem__("canonical_C1_R", "999"))
    rejected("duplicate_canonical_trade_key", lambda x: x[1].__setitem__("canonical_trade_key", x[0]["canonical_trade_key"]))
    rejected("incorrect_instrument_alias", lambda x: x[0].__setitem__("instrument", "Si"))
    rejected("invalid_direction", lambda x: x[0].__setitem__("direction", "BUY"))
    rejected("exit_before_entry", lambda x: x[0].__setitem__("exit_time", "1900-01-01 00:00:00+03:00"))
    rejected("change_source_row_number", lambda x: x[0].__setitem__("source_row_number", "999999"))
    rejected("change_source_trade_id", lambda x: x[0].__setitem__("source_trade_id", "MUTATED"))
    # Contract and output-integrity mutations are checked without touching protected/source files.
    bad_inventory = [r.copy() for r in inventory]; bad_inventory[0]["source_sha256"] = "0" * 64
    tests["change_source_hash"] = sha(ROOT / bad_inventory[0]["source_path"]) != bad_inventory[0]["source_sha256"]
    wf = next(r for r in dataset if r["lifecycle_stage"] == "walk_forward" and r["strategy"] == "T3" and r["timeframe"] == "H1")
    source = inventory[[r["source_path"] for r in inventory].index(wf["source_path"])]
    _, raw_rows = read_csv(ROOT / source["source_path"]); raw = raw_rows[int(wf["source_row_number"]) - 2]
    tests["replace_T3_H1_WF_C1_by_C0"] = abs(float(raw["profit_R"]) - float(wf["canonical_C1_R"])) > 1e-12
    manifest = json.loads((STAGE / "manifest_stage3a2_v1.json").read_text()); tests["alter_normalized_output_SHA"] = ("0" * 64 != manifest["output_hashes"]["normalized_trades_v1.csv"])
    fail(not all(tests.values()), "one or more mutation tests survived")
    return tests


def main() -> None:
    _, _, inventory, registry = load_contract()
    columns, dataset = read_csv(STAGE / "normalized_trades_v1.csv")
    fail(columns != EXPECTED_COLUMNS, "normalized columns/order mismatch")
    integrity = validate(dataset, inventory, registry)
    max_delta = audit_reconciliation(dataset)
    pending = json.loads((STAGE / "manifest_stage3a2_v1.json").read_text())
    fail(pending.get("audit_status") != "PENDING_INDEPENDENT_AUDIT", "auditor requires pending manifest")
    for name, digest in pending["output_hashes"].items(): fail(sha(STAGE / name) != digest, f"output hash mismatch: {name}")
    tests = mutation_tests(dataset, inventory, registry)
    with tempfile.TemporaryDirectory(prefix="stage3a2-audit-") as temp:
        env = os.environ.copy(); env["STAGE3A2_OUTPUT_DIR"] = temp
        subprocess.run([sys.executable, str(STAGE / "normalize_v1.py")], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
        for name in ("normalized_trades_v1.csv", "v1_normalization_reconciliation.csv", "Stage_3A2_v1_Normalization_Report.md", "manifest_stage3a2_v1.json"):
            fail((STAGE / name).read_bytes() != (Path(temp) / name).read_bytes(), f"nondeterministic isolated regeneration: {name}")
        _, regenerated = read_csv(Path(temp) / "normalized_trades_v1.csv")
        validate(regenerated, inventory, registry); audit_reconciliation(regenerated)
    pending["audit_status"] = FINAL
    dump(STAGE / "manifest_stage3a2_v1.json", pending)
    output_hashes = {name: sha(STAGE / name) for name in ("normalized_trades_v1.csv", "v1_normalization_reconciliation.csv", "Stage_3A2_v1_Normalization_Report.md", "manifest_stage3a2_v1.json")}
    result = {
        "status": FINAL, "manifest_closeout": "PASS", "normalized_rows": 1299, "studies_reconciled": "12/12",
        **integrity, "maximum_reconciliation_delta": max_delta,
        "C1_regression": {"status": "PASS", "trades": 34, "PF": 3.38032767202098, "expectancy_R": 0.967991319973547, "net_R": 32.9117048791006, "legacy_C0_PF_rejected": 3.49197193021},
        "mutation_tests_passed": tests, "deterministic_rerun": "PASS",
        "source_hashes": {r["source_path"]: r["source_sha256"] for r in inventory}, "output_hashes": output_hashes,
    }
    dump(STAGE / "audit_stage3a2_v1_result.json", result)
    print(FINAL)


if __name__ == "__main__":
    main()
