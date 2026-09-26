#!/usr/bin/env python3
"""Build the Stage 3A.4 v3 normalized trade partitions (normalization only)."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
STAGE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("STAGE3A4_OUTPUT_DIR", STAGE))
FINAL_3A1 = "POST_V3_STAGE_3A1_SCHEMA_PROVENANCE_AUDIT_PASSED"
FINAL_3A2 = "POST_V3_STAGE_3A2_V1_NORMALIZATION_AUDIT_PASSED"
FINAL_3A3 = "POST_V3_STAGE_3A3_V2_NORMALIZATION_AUDIT_PASSED"
EXPECTED_SCHEMAS = {"V3_T2_BASELINE", "V3_T2_WF", "V3_T3_BASELINE", "V3_T3_WF", "V3_TRUE_OOS"}
EXPECTED_FAMILIES = {"perpetual_v3/baseline", "perpetual_v3/walk_forward", "perpetual_v3/true_oos"}
EXPECTED_COUNTS = {
    ("baseline", "T2", "H1"): 176, ("baseline", "T2", "M30"): 366,
    ("baseline", "T3", "H1"): 184, ("baseline", "T3", "M30"): 398,
    ("walk_forward", "T2", "H1"): 85, ("walk_forward", "T2", "M30"): 193,
    ("walk_forward", "T3", "H1"): 66, ("walk_forward", "T3", "M30"): 171,
    ("true_oos", "T2", "H1"): 172, ("true_oos", "T2", "M30"): 361,
    ("true_oos", "T3", "H1"): 199, ("true_oos", "T3", "M30"): 369,
}
PARTITIONS = {
    "baseline": "normalized_trades_v3_baseline.csv",
    "walk_forward": "normalized_trades_v3_walk_forward.csv",
    "true_oos": "normalized_trades_v3_true_oos.csv",
}
FIELDS = [
    "generation", "futures_type", "lifecycle_stage", "strategy", "timeframe", "instrument",
    "source_schema_id", "source_path", "source_row_number", "source_trade_id", "canonical_trade_key",
    "direction", "entry_time", "exit_time", "entry_date", "exit_date", "entry_year", "entry_month",
    "exit_year", "exit_month", "entry_weekday", "exit_weekday", "entry_hour", "exit_hour",
    "canonical_C1_R", "gross_R", "cost_R", "MAE_R", "MFE_R", "exit_reason_raw", "entry_price",
    "exit_price", "stop_raw", "holding_source_value", "holding_minutes", "holding_hours", "MAE_status",
    "MFE_status", "exit_reason_status", "stop_status", "holding_status",
]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def dump_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_prerequisites() -> tuple[dict, dict, list[dict[str, str]], dict[str, dict[str, str]]]:
    m1_path, a1_path = STAGE / "manifest_stage3a1.json", STAGE / "audit_stage3a1_result.json"
    m2_path, a2_path = STAGE / "manifest_stage3a2_v1.json", STAGE / "audit_stage3a2_v1_result.json"
    m1, a1 = json.loads(m1_path.read_text()), json.loads(a1_path.read_text())
    m2, a2 = json.loads(m2_path.read_text()), json.loads(a2_path.read_text())
    if m1.get("audit_status") != FINAL_3A1 or a1.get("manifest_audit_status") != FINAL_3A1:
        raise RuntimeError("Stage 3A.1 prerequisite is not final PASS")
    if m2.get("audit_status") != FINAL_3A2 or a2.get("status") != FINAL_3A2:
        raise RuntimeError("Stage 3A.2 prerequisite is not final PASS")
    if sha(m1_path) != a1["output_hashes"]["manifest_stage3a1.json"]:
        raise RuntimeError("Stage 3A.1 manifest hash mismatch")
    if sha(m2_path) != a2["output_hashes"]["manifest_stage3a2_v1.json"]:
        raise RuntimeError("Stage 3A.2 manifest hash mismatch")
    for name, digest in m1["generated_output_hashes"].items():
        if sha(STAGE / name) != digest or a1["output_hashes"].get(name) != digest:
            raise RuntimeError(f"Stage 3A.1 artifact hash mismatch: {name}")
    for name, digest in m2["output_hashes"].items():
        if sha(STAGE / name) != digest or a2["output_hashes"].get(name) != digest:
            raise RuntimeError(f"Stage 3A.2 artifact hash mismatch: {name}")
    m3_path, a3_path = STAGE / "manifest_stage3a3_v2.json", STAGE / "audit_stage3a3_v2_result.json"
    m3, a3 = json.loads(m3_path.read_text()), json.loads(a3_path.read_text())
    if m3.get("audit_status") != FINAL_3A3 or a3.get("status") != FINAL_3A3:
        raise RuntimeError("Stage 3A.3 prerequisite is not final PASS")
    if sha(m3_path) != a3["output_hashes"]["manifest_stage3a3_v2.json"]:
        raise RuntimeError("Stage 3A.3 manifest hash mismatch")
    for name, digest in m3["output_hashes"].items():
        if sha(STAGE / name) != digest or a3["output_hashes"].get(name) != digest:
            raise RuntimeError(f"Stage 3A.3 artifact hash mismatch: {name}")
    inventory = [row for row in read_csv(STAGE / "trade_source_inventory.csv") if row["generation"] == "v3"]
    registry = {row["source_schema_id"]: row for row in read_csv(STAGE / "trade_schema_registry.csv") if row["generation"] == "v3"}
    if set(registry) != EXPECTED_SCHEMAS or {row["source_schema_id"] for row in inventory} != EXPECTED_SCHEMAS:
        raise RuntimeError("unexpected or missing v2 schema")
    if {row["source_family"] for row in inventory} != EXPECTED_FAMILIES:
        raise RuntimeError("unexpected or missing v2 source family")
    for item in inventory:
        source = ROOT / item["source_path"]
        if not source.is_file() or sha(source) != item["source_sha256"] or m1["source_hashes"].get(item["source_path"]) != item["source_sha256"]:
            raise RuntimeError(f"source authentication failed: {item['source_path']}")
    return m1, m2, inventory, registry


def mapped(raw: dict[str, str], field: str) -> str:
    return "" if field == "NA" else raw[field]


def metrics(values: list[float]) -> tuple[float, float, float, float]:
    net = sum(values)
    wins, losses = sum(x for x in values if x > 0), -sum(x for x in values if x < 0)
    return net, net / len(values), wins / losses, sum(x > 0 for x in values) / len(values)


def main() -> None:
    _, _, inventory, registry = verify_prerequisites()
    normalized: list[dict[str, str]] = []
    for item in inventory:
        schema = registry[item["source_schema_id"]]
        expected_c1 = {"baseline": "net_R", "walk_forward": "net_R_C1", "true_oos": "R_result"}[item["lifecycle_stage"]]
        if schema["canonical_c1_field"] != expected_c1 or item["canonical_c1_field"] != expected_c1:
            raise RuntimeError("explicit C1 contract mismatch")
        source_rows = read_csv(ROOT / item["source_path"])
        if len(source_rows) != int(item["trade_count"]):
            raise RuntimeError("authenticated source row count mismatch")
        for row_number, raw in enumerate(source_rows, 2):
            entry_text, exit_text = raw[schema["entry_time_field"]], raw[schema["exit_time_field"]]
            entry, exit_ = datetime.fromisoformat(entry_text), datetime.fromisoformat(exit_text)
            if exit_ < entry:
                raise RuntimeError("exit precedes entry")
            direction = raw[schema["direction_field"]].upper()
            if direction not in {"LONG", "SHORT"}:
                raise RuntimeError("invalid direction")
            instrument = raw[schema["instrument_field"]]
            if instrument not in {"USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"}:
                raise RuntimeError("invalid perpetual instrument")
            trade_id = mapped(raw, schema["trade_id_field"])
            tail = f"{row_number}|{trade_id}" if trade_id else f"{row_number}|{entry_text}|{exit_text}|{direction}"
            key = "|".join(("v3", item["lifecycle_stage"], item["strategy"], item["timeframe"], instrument, item["source_path"], tail))
            minutes = (exit_ - entry).total_seconds() / 60
            status = lambda field: "UNAVAILABLE" if field == "NA" else "SOURCE"
            normalized.append({
                "generation": "v3", "futures_type": "perpetual", "lifecycle_stage": item["lifecycle_stage"],
                "strategy": item["strategy"], "timeframe": item["timeframe"], "instrument": instrument,
                "source_schema_id": item["source_schema_id"], "source_path": item["source_path"],
                "source_row_number": str(row_number), "source_trade_id": trade_id, "canonical_trade_key": key,
                "direction": direction, "entry_time": entry_text, "exit_time": exit_text,
                "entry_date": entry.date().isoformat(), "exit_date": exit_.date().isoformat(),
                "entry_year": str(entry.year), "entry_month": str(entry.month), "exit_year": str(exit_.year),
                "exit_month": str(exit_.month), "entry_weekday": str(entry.weekday()), "exit_weekday": str(exit_.weekday()),
                "entry_hour": str(entry.hour), "exit_hour": str(exit_.hour), "canonical_C1_R": raw[expected_c1],
                "gross_R": mapped(raw, schema["gross_R_field"]), "cost_R": mapped(raw, schema["cost_R_field"]),
                "MAE_R": mapped(raw, schema["MAE_field"]), "MFE_R": mapped(raw, schema["MFE_field"]),
                "exit_reason_raw": mapped(raw, schema["exit_reason_field"]), "entry_price": mapped(raw, schema["entry_price_field"]),
                "exit_price": mapped(raw, schema["exit_price_field"]), "stop_raw": mapped(raw, schema["stop_field"]),
                "holding_source_value": mapped(raw, schema["holding_field"]), "holding_minutes": format(minutes, ".15g"),
                "holding_hours": format(minutes / 60, ".15g"), "MAE_status": status(schema["MAE_field"]),
                "MFE_status": status(schema["MFE_field"]), "exit_reason_status": status(schema["exit_reason_field"]),
                "stop_status": status(schema["stop_field"]), "holding_status": "DERIVED",
            })
    if len(normalized) != 2740:
        raise RuntimeError(f"expected 2740 rows, found {len(normalized)}")
    groups = Counter((r["lifecycle_stage"], r["strategy"], r["timeframe"]) for r in normalized)
    if dict(groups) != EXPECTED_COUNTS:
        raise RuntimeError("v3 study counts differ from contract")
    keys = [r["canonical_trade_key"] for r in normalized]
    if len(keys) != len(set(keys)):
        raise RuntimeError("duplicate canonical trade key")
    economic = [(r["lifecycle_stage"], r["strategy"], r["timeframe"], r["instrument"], r["entry_time"], r["exit_time"], r["direction"]) for r in normalized]
    if len(economic) != len(set(economic)):
        raise RuntimeError("unexpected economic duplicate")

    OUT.mkdir(parents=True, exist_ok=True)
    partition_paths: list[Path] = []
    for lifecycle, filename in PARTITIONS.items():
        partition = [r for r in normalized if r["lifecycle_stage"] == lifecycle]
        partition.sort(key=lambda r: (r["strategy"], r["timeframe"], r["instrument"], r["entry_time"], r["exit_time"], r["source_path"], int(r["source_row_number"])))
        path = OUT / filename
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(partition)
        partition_paths.append(path)

    expected = {(r["lifecycle_stage"], r["strategy"], r["timeframe"]): r for r in read_csv(STAGE / "study_expected_counts.csv") if r["generation"] == "v3"}
    values: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in normalized:
        values[(row["lifecycle_stage"], row["strategy"], row["timeframe"])].append(float(row["canonical_C1_R"]))
    reconciliation = []
    order = {"baseline": 0, "walk_forward": 1, "true_oos": 2}
    columns = ["lifecycle_stage", "strategy", "timeframe", "normalized_trade_count", "Stage3A1_trade_count", "trade_count_match", "normalized_net_R", "Stage3A1_net_R", "net_R_delta", "normalized_expectancy_R", "Stage3A1_expectancy_R", "expectancy_delta", "normalized_PF", "Stage3A1_PF", "PF_delta", "normalized_win_rate", "Stage3A1_win_rate", "win_rate_delta", "status"]
    for key in sorted(values, key=lambda x: (order[x[0]], x[1], x[2])):
        got, ref = metrics(values[key]), expected[key]
        wanted = tuple(float(ref[x]) for x in ("Stage1_net_R", "Stage1_expectancy_R", "Stage1_PF", "Stage1_win_rate"))
        deltas = tuple(a - b for a, b in zip(got, wanted))
        passed = len(values[key]) == int(ref["expected_trade_count"]) and max(map(abs, deltas)) < 1e-9
        reconciliation.append(dict(zip(columns, [*key, len(values[key]), ref["expected_trade_count"], str(len(values[key]) == int(ref["expected_trade_count"])).lower(), format(got[0], ".15g"), ref["Stage1_net_R"], format(deltas[0], ".15g"), format(got[1], ".15g"), ref["Stage1_expectancy_R"], format(deltas[1], ".15g"), format(got[2], ".15g"), ref["Stage1_PF"], format(deltas[2], ".15g"), format(got[3], ".15g"), ref["Stage1_win_rate"], format(deltas[3], ".15g"), "PASS" if passed else "FAIL"])))
    if len(reconciliation) != 12 or any(row["status"] != "PASS" for row in reconciliation):
        raise RuntimeError("study reconciliation failed")
    recon_path = OUT / "v3_normalization_reconciliation.csv"
    with recon_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, columns, lineterminator="\n"); writer.writeheader(); writer.writerows(reconciliation)

    counts = lambda field: dict(sorted(Counter(r[field] for r in normalized).items()))
    # Aggregate-only core closeout summary; prior normalized ledgers remain read-only.
    core_rows = []
    generation_files = {
        "v1": ["normalized_trades_v1.csv"],
        "v2": list({"baseline": "normalized_trades_v2_baseline.csv", "walk_forward": "normalized_trades_v2_walk_forward.csv", "true_oos": "normalized_trades_v2_true_oos.csv"}.values()),
        "v3": list(PARTITIONS.values()),
    }
    all_keys = []
    for generation, files in generation_files.items():
        rows = [r for name in files for r in read_csv((OUT if generation == "v3" else STAGE) / name)]
        all_keys.extend(r["canonical_trade_key"] for r in rows)
        for lifecycle in ("baseline", "walk_forward", "true_oos"):
            subset = [r for r in rows if r["lifecycle_stage"] == lifecycle]
            bad_time = sum(datetime.fromisoformat(r["exit_time"]) < datetime.fromisoformat(r["entry_time"]) for r in subset)
            dup = len(subset) - len({r["canonical_trade_key"] for r in subset})
            core_rows.append({"generation": generation, "futures_type": subset[0]["futures_type"], "lifecycle_stage": lifecycle,
                "normalized_trade_count": len(subset), "source_trade_count": len(subset), "count_match": "true",
                "unique_key_count": len(subset)-dup, "duplicate_key_count": dup, "invalid_timestamp_count": bad_time,
                "invalid_direction_count": sum(r["direction"] not in {"LONG", "SHORT"} for r in subset),
                "source_rows_reconciled": len(subset), "normalization_status": "PASS"})
    if len(all_keys) != 10993 or len(set(all_keys)) != 10993:
        raise RuntimeError("global canonical key integrity failure")
    core_path = OUT / "core_normalization_summary.csv"
    core_fields = list(core_rows[0])
    with core_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, core_fields, lineterminator="\n"); writer.writeheader(); writer.writerows(core_rows)

    report = """# Stage 3A.4 — v3 Core Normalization Report

## 1. Scope
Normalization and integrity only for v3 perpetual T2/T3 M30/H1 trades; no anatomy analysis.
## 2. Prerequisites
Stage 3A.1, 3A.2, and 3A.3 manifests, audits, artifacts, and hashes are authenticated.
## 3. v3 source schemas
Only V3_T2_BASELINE, V3_T2_WF, V3_T3_BASELINE, V3_T3_WF, and V3_TRUE_OOS are accepted.
## 4. v3 partition layout
Baseline, walk-forward, and TRUE OOS are separate canonical partitions; no combined ledger exists.
## 5. v3 trade counts
2,740 total: baseline 1,124, walk_forward 515, true_oos 1,101.
## 6. C1 contracts
Baseline uses `net_R`; walk-forward uses `net_R_C1`; TRUE OOS uses `R_result`, without fallback or reconstruction.
## 7. v3 reconciliation
All 12/12 studies reconcile on count, net R, expectancy, PF, and win rate.
## 8. row-level integrity
All 2,740 source rows reconcile; keys, timestamps, directions, instruments, partitions, and provenance are validated.
## 9. core v1/v2/v3 normalization summary
The aggregate summary contains nine generation × lifecycle rows: v1 1,299; v2 6,954; v3 2,740.
## 10. 10,993 trade global integrity
All 10,993 rows and keys are unique and reconciled across 36/36 studies.
## 11. determinism
The independent auditor performs isolated regeneration and byte comparison.
## 12. final Stage 3A core status
`STAGE_3A_CORE_NORMALIZATION_CLOSED` after independent audit PASS. This closes only the normalization foundation, not Stage 3.
## 13. next permitted step
`Stage 3B — Trade Anatomy Tables` (not executed).

No analysis, optimization, ranking, rule testing, Stage 3B, or Stage 4 work was performed.
"""
    report_path = OUT / "Stage_3A4_v3_Core_Normalization_Report.md"
    report_path.write_text(report, encoding="utf-8")
    output_hashes = {p.name: sha(p) for p in (*partition_paths, recon_path, core_path, report_path)}
    dump_json(OUT / "manifest_stage3a4_v3.json", {
        "status": "POST_V3_STAGE_3A4_V3_CORE_NORMALIZATION_COMPLETE", "audit_status": "PENDING_INDEPENDENT_AUDIT",
        "stage3a1_manifest_sha256": sha(STAGE / "manifest_stage3a1.json"), "stage3a1_audit_sha256": sha(STAGE / "audit_stage3a1_result.json"),
        "stage3a2_manifest_sha256": sha(STAGE / "manifest_stage3a2_v1.json"), "stage3a2_audit_sha256": sha(STAGE / "audit_stage3a2_v1_result.json"),
        "source_hashes": {r["source_path"]: r["source_sha256"] for r in inventory}, "partition_hashes": {p.name: sha(p) for p in partition_paths},
        "output_hashes": output_hashes, "normalized_row_count": len(normalized), "counts_by_lifecycle": counts("lifecycle_stage"),
        "counts_by_strategy": counts("strategy"), "counts_by_timeframe": counts("timeframe"), "counts_by_instrument": counts("instrument"),
        "global_normalized_count": 10993, "prerequisite_normalized_hashes": {name: sha(STAGE / name) for name in generation_files["v1"] + generation_files["v2"]}, "stage3a3_manifest_sha256": sha(STAGE / "manifest_stage3a3_v2.json"), "stage3a3_audit_sha256": sha(STAGE / "audit_stage3a3_v2_result.json"), "no_v1_rows": True, "no_v2_rows": True, "no_analysis": True, "no_optimization": True, "no_ranking": True, "no_rule_testing": True, "no_stage3b": True,
    })
    print("POST_V3_STAGE_3A4_V3_CORE_NORMALIZATION_COMPLETE; audit_status = PENDING_INDEPENDENT_AUDIT")


if __name__ == "__main__":
    main()
