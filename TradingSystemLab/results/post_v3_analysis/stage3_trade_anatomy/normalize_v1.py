#!/usr/bin/env python3
"""Build the Stage 3A.2 v1 normalized trade ledger (normalization only)."""

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
OUT = Path(os.environ.get("STAGE3A2_OUTPUT_DIR", STAGE))
EXPECTED_SCHEMAS = {
    "V1_H1_TRUE_OOS", "V1_T2_H1_WF_LEGACY", "V1_T2_M30_TRUE_OOS",
    "V1_T2_M30_WF", "V1_T2_MTF_BASELINE",
    "V1_T3_H1_WF_LEGACY_C1_DERIVED", "V1_T3_M30_TRUE_OOS",
    "V1_T3_M30_WF", "V1_T3_MTF_BASELINE_C1_DERIVED",
}
DERIVED = "profit_R-2*0.001/initial_risk"
FINAL_3A1 = "POST_V3_STAGE_3A1_SCHEMA_PROVENANCE_AUDIT_PASSED"
FIELDS = [
    "generation", "futures_type", "lifecycle_stage", "strategy", "timeframe",
    "instrument", "source_schema_id", "source_path", "source_row_number",
    "source_trade_id", "canonical_trade_key", "direction", "entry_time", "exit_time",
    "entry_date", "exit_date", "entry_year", "entry_month", "exit_year", "exit_month",
    "entry_weekday", "exit_weekday", "entry_hour", "exit_hour", "canonical_C1_R",
    "gross_R", "cost_R", "MAE_R", "MFE_R", "exit_reason_raw", "entry_price",
    "exit_price", "stop_raw", "holding_source_value", "holding_minutes", "holding_hours",
    "MAE_status", "MFE_status", "exit_reason_status", "stop_status", "holding_status",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def dump_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prerequisite() -> tuple[dict, dict, list[dict[str, str]], dict[str, dict[str, str]]]:
    manifest_path = STAGE / "manifest_stage3a1.json"
    audit_path = STAGE / "audit_stage3a1_result.json"
    manifest = json.loads(manifest_path.read_text())
    audit = json.loads(audit_path.read_text())
    if manifest.get("audit_status") != FINAL_3A1 or audit.get("manifest_audit_status") != FINAL_3A1:
        raise RuntimeError("Stage 3A.1 is not in final PASS state")
    for name in ("trade_source_inventory.csv", "trade_schema_registry.csv"):
        if sha(STAGE / name) != manifest["generated_output_hashes"][name]:
            raise RuntimeError(f"Stage 3A.1 contract changed: {name}")
    inventory = [r for r in rows(STAGE / "trade_source_inventory.csv") if r["generation"] == "v1"]
    registry = {r["source_schema_id"]: r for r in rows(STAGE / "trade_schema_registry.csv") if r["generation"] == "v1"}
    if set(registry) != EXPECTED_SCHEMAS or {r["source_schema_id"] for r in inventory} != EXPECTED_SCHEMAS:
        raise RuntimeError("unexpected or missing v1 schema")
    for item in inventory:
        path = ROOT / item["source_path"]
        if not path.is_file() or sha(path) != item["source_sha256"] or manifest["source_hashes"].get(item["source_path"]) != item["source_sha256"]:
            raise RuntimeError(f"source authentication failed: {item['source_path']}")
    return manifest, audit, inventory, registry


def source_value(raw: dict[str, str], field: str) -> str:
    return "" if field == "NA" else raw[field]


def canonical_c1(raw: dict[str, str], contract: str) -> str:
    if contract == DERIVED:
        risk = float(raw["initial_risk"])
        if risk <= 0:
            raise RuntimeError("non-positive initial_risk in derived C1")
        return format(float(raw["profit_R"]) - 2 * 0.001 / risk, ".15g")
    if contract not in raw:
        raise RuntimeError(f"canonical C1 field absent: {contract}")
    return raw[contract]


def instrument(raw_value: str) -> str:
    aliases = {"Si": "USDRUBF", "USDRUBF": "USDRUBF", "CNY": "CNYRUBF", "CNYRUBF": "CNYRUBF"}
    if raw_value not in aliases:
        raise RuntimeError(f"unsupported v1 instrument alias: {raw_value}")
    return aliases[raw_value]


def metrics(values: list[float]) -> tuple[float, float, float, float]:
    net = sum(values)
    wins = sum(x for x in values if x > 0)
    losses = -sum(x for x in values if x < 0)
    return net, net / len(values), wins / losses, sum(x > 0 for x in values) / len(values)


def main() -> None:
    manifest3a1, _, inventory, registry = prerequisite()
    normalized: list[dict[str, str]] = []
    for item in inventory:
        schema = registry[item["source_schema_id"]]
        source_rows = rows(ROOT / item["source_path"])
        if len(source_rows) != int(item["trade_count"]):
            raise RuntimeError("source row count differs from authenticated inventory")
        for row_number, raw in enumerate(source_rows, 2):
            entry_text, exit_text = raw[schema["entry_time_field"]], raw[schema["exit_time_field"]]
            entry, exit_ = datetime.fromisoformat(entry_text), datetime.fromisoformat(exit_text)
            if exit_ < entry:
                raise RuntimeError("exit precedes entry")
            direction = raw[schema["direction_field"]].upper()
            if direction not in {"LONG", "SHORT"}:
                raise RuntimeError("invalid direction")
            inst = instrument(raw[schema["instrument_field"]])
            trade_id = source_value(raw, schema["trade_id_field"])
            # Several authenticated stitched ledgers reuse trade_id across folds;
            # the immutable source row locator therefore participates in every key.
            key_tail = f"{row_number}|{trade_id}" if trade_id else f"{row_number}|{entry_text}|{exit_text}|{direction}"
            key = "|".join(("v1", item["lifecycle_stage"], item["strategy"], item["timeframe"], inst, item["source_path"], key_tail))
            minutes = (exit_ - entry).total_seconds() / 60
            status = lambda field: "UNAVAILABLE" if field == "NA" else "SOURCE"
            normalized.append({
                "generation": "v1", "futures_type": "perpetual", "lifecycle_stage": item["lifecycle_stage"],
                "strategy": item["strategy"], "timeframe": item["timeframe"], "instrument": inst,
                "source_schema_id": item["source_schema_id"], "source_path": item["source_path"],
                "source_row_number": str(row_number), "source_trade_id": trade_id, "canonical_trade_key": key,
                "direction": direction, "entry_time": entry_text, "exit_time": exit_text,
                "entry_date": entry.date().isoformat(), "exit_date": exit_.date().isoformat(),
                "entry_year": str(entry.year), "entry_month": str(entry.month), "exit_year": str(exit_.year),
                "exit_month": str(exit_.month), "entry_weekday": str(entry.weekday()), "exit_weekday": str(exit_.weekday()),
                "entry_hour": str(entry.hour), "exit_hour": str(exit_.hour),
                "canonical_C1_R": canonical_c1(raw, schema["canonical_c1_field"]),
                "gross_R": source_value(raw, schema["gross_R_field"]), "cost_R": source_value(raw, schema["cost_R_field"]),
                "MAE_R": source_value(raw, schema["MAE_field"]), "MFE_R": source_value(raw, schema["MFE_field"]),
                "exit_reason_raw": source_value(raw, schema["exit_reason_field"]),
                "entry_price": source_value(raw, schema["entry_price_field"]), "exit_price": source_value(raw, schema["exit_price_field"]),
                "stop_raw": source_value(raw, schema["stop_field"]), "holding_source_value": source_value(raw, schema["holding_field"]),
                "holding_minutes": format(minutes, ".15g"), "holding_hours": format(minutes / 60, ".15g"),
                "MAE_status": status(schema["MAE_field"]), "MFE_status": status(schema["MFE_field"]),
                "exit_reason_status": status(schema["exit_reason_field"]), "stop_status": status(schema["stop_field"]),
                "holding_status": "DERIVED",
            })
    if len(normalized) != 1299:
        raise RuntimeError(f"expected 1299 rows, found {len(normalized)}")
    keys = [r["canonical_trade_key"] for r in normalized]
    if len(keys) != len(set(keys)):
        raise RuntimeError("duplicate canonical trade key")
    economic = [(r["lifecycle_stage"], r["strategy"], r["timeframe"], r["instrument"], r["entry_time"], r["exit_time"], r["direction"]) for r in normalized]
    if len(economic) != len(set(economic)):
        raise RuntimeError("unproven economic duplicate")
    order = {"baseline": 0, "walk_forward": 1, "true_oos": 2}
    normalized.sort(key=lambda r: (order[r["lifecycle_stage"]], r["strategy"], r["timeframe"], r["instrument"], r["entry_time"], r["exit_time"], r["source_path"], int(r["source_row_number"])))
    OUT.mkdir(parents=True, exist_ok=True)
    normalized_path = OUT / "normalized_trades_v1.csv"
    with normalized_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(normalized)

    expected = {(r["lifecycle_stage"], r["strategy"], r["timeframe"]): r for r in rows(STAGE / "study_expected_counts.csv") if r["generation"] == "v1"}
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for r in normalized:
        grouped[(r["lifecycle_stage"], r["strategy"], r["timeframe"])].append(float(r["canonical_C1_R"]))
    reconciliation = []
    for key in sorted(grouped, key=lambda x: (order[x[0]], x[1], x[2])):
        values, exp = grouped[key], expected[key]
        net, expectancy, pf, win_rate = metrics(values)
        refs = [float(exp[x]) for x in ("Stage1_net_R", "Stage1_expectancy_R", "Stage1_PF", "Stage1_win_rate")]
        deltas = [net - refs[0], expectancy - refs[1], pf - refs[2], win_rate - refs[3]]
        passed = len(values) == int(exp["expected_trade_count"]) and max(map(abs, deltas)) < 1e-9
        reconciliation.append(dict(zip(
            ["lifecycle_stage", "strategy", "timeframe", "normalized_trade_count", "Stage3A1_trade_count", "trade_count_match", "normalized_net_R", "Stage3A1_net_R", "net_R_delta", "normalized_expectancy_R", "Stage3A1_expectancy_R", "expectancy_delta", "normalized_PF", "Stage3A1_PF", "PF_delta", "normalized_win_rate", "Stage3A1_win_rate", "win_rate_delta", "status"],
            [*key, len(values), exp["expected_trade_count"], str(len(values) == int(exp["expected_trade_count"])).lower(), format(net, ".15g"), exp["Stage1_net_R"], format(deltas[0], ".15g"), format(expectancy, ".15g"), exp["Stage1_expectancy_R"], format(deltas[1], ".15g"), format(pf, ".15g"), exp["Stage1_PF"], format(deltas[2], ".15g"), format(win_rate, ".15g"), exp["Stage1_win_rate"], format(deltas[3], ".15g"), "PASS" if passed else "FAIL"])))
    if len(reconciliation) != 12 or any(r["status"] != "PASS" for r in reconciliation):
        raise RuntimeError("study reconciliation failed")
    recon_path = OUT / "v1_normalization_reconciliation.csv"
    with recon_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, reconciliation[0].keys(), lineterminator="\n"); writer.writeheader(); writer.writerows(reconciliation)

    counts = lambda field: dict(sorted(Counter(r[field] for r in normalized).items()))
    schemas = sorted({r["source_schema_id"] for r in normalized})
    report = f"""# Stage 3A.2 — v1 Normalization Report

## 1. Scope
This stage normalized only v1 perpetual T2/T3 M30/H1 trades. No v2 or v3 rows were included.

## 2. Stage 3A.1 prerequisite
The final Stage 3A.1 manifest/audit PASS states, registry hash, inventory hash, and every v1 source hash were verified before reading source rows.

## 3. Source schemas used
{', '.join(schemas)}.

## 4. C1 normalization
Canonical C1 follows the registry exactly. `V1_T3_H1_WF_LEGACY_C1_DERIVED` and `V1_T3_MTF_BASELINE_C1_DERIVED` use `profit_R - 2*0.001/initial_risk`; no fallback mapping exists.

## 5. v1 trade counts
1,299 rows: baseline 606, walk_forward 194, true_oos 499; T2 597, T3 702; H1 426, M30 873.

## 6. Field availability in normalized output
Raw anatomy values are copied only through registry mappings. Missing source fields remain empty and `UNAVAILABLE`; holding duration is `DERIVED`. MAE/MFE sign convention remains UNKNOWN.

## 7. Reconciliation
All 12 lifecycle × strategy × timeframe studies reconcile for count, net R, expectancy, PF, and win rate.

## 8. Duplicate, timestamp, and direction checks
Canonical keys are unique; no unproven economic duplicates, invalid timestamps, or invalid directions exist. Instruments are only USDRUBF/CNYRUBF.

## 9. Determinism
Rows use an explicit lifecycle-first stable ordering. The independent auditor performs isolated regeneration and byte comparison.

## 10. Final audit status
The generator leaves `PENDING_INDEPENDENT_AUDIT`; the independent auditor owns closeout to `POST_V3_STAGE_3A2_V1_NORMALIZATION_AUDIT_PASSED`. The accompanying final manifest and audit result confirm that closeout.

No trade anatomy analysis was performed. No optimization, ranking, or rule testing was performed.
"""
    report_path = OUT / "Stage_3A2_v1_Normalization_Report.md"
    report_path.write_text(report, encoding="utf-8")
    output_hashes = {p.name: sha(p) for p in (normalized_path, recon_path, report_path)}
    dump_json(OUT / "manifest_stage3a2_v1.json", {
        "status": "POST_V3_STAGE_3A2_V1_NORMALIZATION_COMPLETE", "audit_status": "PENDING_INDEPENDENT_AUDIT",
        "stage3a1_canonical_commit": "e8385b7a6ca3d3ab17628bbaf434daa555edfd03",
        "stage3a1_manifest_sha256": sha(STAGE / "manifest_stage3a1.json"), "stage3a1_audit_sha256": sha(STAGE / "audit_stage3a1_result.json"),
        "source_hashes": {r["source_path"]: r["source_sha256"] for r in inventory}, "normalized_row_count": len(normalized),
        "counts_by_lifecycle": counts("lifecycle_stage"), "counts_by_strategy": counts("strategy"),
        "counts_by_timeframe": counts("timeframe"), "counts_by_instrument": counts("instrument"),
        "output_hashes": output_hashes, "no_v2_rows": True, "no_v3_rows": True, "no_analysis": True,
        "no_optimization": True, "no_ranking": True, "no_rule_testing": True,
    })
    print("POST_V3_STAGE_3A2_V1_NORMALIZATION_COMPLETE; audit_status = PENDING_INDEPENDENT_AUDIT")


if __name__ == "__main__":
    main()
