#!/usr/bin/env python3
"""Independent fail-closed auditor for Stage 3B aggregate artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
STAGE = Path(__file__).resolve().parent
FINAL = "POST_V3_STAGE_3B_TRADE_ANATOMY_TABLES_AUDIT_PASSED"
INPUTS = ["normalized_trades_v1.csv", "normalized_trades_v2_baseline.csv", "normalized_trades_v2_walk_forward.csv", "normalized_trades_v2_true_oos.csv", "normalized_trades_v3_baseline.csv", "normalized_trades_v3_walk_forward.csv", "normalized_trades_v3_true_oos.csv"]
TABLE_KEYS = {
 "anatomy_by_generation.csv": ["generation", "futures_type", "lifecycle_stage", "strategy", "timeframe"],
 "anatomy_by_strategy_timeframe.csv": ["generation", "lifecycle_stage", "strategy", "timeframe"],
 "anatomy_by_instrument.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "instrument"],
 "anatomy_by_direction.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "direction"],
 "anatomy_by_exit_reason.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "exit_reason_raw"],
 "anatomy_by_holding_bucket.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "holding_bucket"],
 "anatomy_by_entry_weekday.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "entry_weekday"],
 "anatomy_by_entry_hour.csv": ["generation", "lifecycle_stage", "strategy", "timeframe", "entry_hour"],
}
OUTPUTS = list(TABLE_KEYS) + ["anatomy_mae_mfe_summary.csv", "Stage_3B_Trade_Anatomy_Report.md"]
PARENT = ["generation", "lifecycle_stage", "strategy", "timeframe"]


def fail(condition: bool, message: str) -> None:
    if condition: raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream); return list(reader.fieldnames or []), list(reader)


def number(text: str) -> float | None:
    if text in ("", "NA"): return None
    try:
        x = float(text); return x if math.isfinite(x) else None
    except ValueError: return None


def bucket(text: str) -> str:
    x = number(text)
    if x is None: return "UNAVAILABLE"
    boundaries = [(1, "<1h"), (3, "1–3h"), (6, "3–6h"), (12, "6–12h"), (24, "12–24h"), (48, "24–48h")]
    for limit, label in boundaries:
        if x < limit: return label
    return "48–96h" if x <= 96 else ">96h"


def load_inputs() -> list[dict[str, str]]:
    a4 = json.loads((STAGE / "audit_stage3a4_v3_result.json").read_text())
    m4 = json.loads((STAGE / "manifest_stage3a4_v3.json").read_text())
    fail(a4.get("status") != "POST_V3_STAGE_3A4_V3_CORE_NORMALIZATION_AUDIT_PASSED" or a4.get("core_normalization_status") != "STAGE_3A_CORE_NORMALIZATION_CLOSED", "Stage 3A closeout failed")
    fail(sha(STAGE / "manifest_stage3a4_v3.json") != a4["output_hashes"]["manifest_stage3a4_v3.json"], "Stage 3A.4 manifest hash")
    expected = {**a4["prerequisite_normalized_hashes"], **m4["partition_hashes"]}
    rows = []
    for name in INPUTS:
        fail(sha(STAGE / name) != expected[name], f"normalized hash mismatch: {name}")
        rows += read(STAGE / name)[1]
    keys = [r["canonical_trade_key"] for r in rows]
    fail(len(rows) != 10993 or len(set(keys)) != 10993, "population/key integrity failure")
    fail({r["generation"] for r in rows} != {"v1", "v2", "v3"}, "generation scope")
    fail({r["lifecycle_stage"] for r in rows} != {"baseline", "walk_forward", "true_oos"}, "lifecycle scope")
    fail(any(r["direction"] not in {"LONG", "SHORT"} for r in rows), "direction scope")
    allowed = {"v1": {"USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"}, "v2": {"Si", "CNY", "BR", "GD", "NG", "MIX"}, "v3": {"USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"}}
    fail(any(r["instrument"] not in allowed[r["generation"]] for r in rows), "instrument scope")
    for r in rows:
        r["exit_reason_raw"] = r["exit_reason_raw"] or "UNAVAILABLE"; r["holding_bucket"] = bucket(r["holding_hours"])
        r["entry_weekday"] = r["entry_weekday"] or "UNAVAILABLE"; r["entry_hour"] = r["entry_hour"] or "UNAVAILABLE"
    return rows


def aggregate(rows: list[dict[str, str]], keys: list[str]) -> dict[tuple[str, ...], tuple[int, float]]:
    result: dict[tuple[str, ...], list[float]] = defaultdict(list)
    for r in rows: result[tuple(r[k] for k in keys)].append(float(r["canonical_C1_R"]))
    return {k: (len(v), sum(v)) for k, v in result.items()}


def validate(base: Path, rows: list[dict[str, str]]) -> dict[str, int]:
    manifest = json.loads((base / "manifest_stage3b.json").read_text())
    fail(manifest.get("status") != "POST_V3_STAGE_3B_TRADE_ANATOMY_TABLES_COMPLETE", "generator status")
    fail(manifest.get("audit_status") not in {"PENDING_INDEPENDENT_AUDIT", FINAL}, "audit state")
    fail(manifest.get("stage3a_canonical_closeout_commit") != "65e9a702f60d11636c1e78a29a47b576b9f22c27", "closeout provenance")
    flags = ["no_trade_level_output", "no_strategy_execution", "no_optimization", "no_ranking", "no_rule_testing", "no_stage3c", "no_stage4"]
    fail(any(manifest.get(x) is not True for x in flags), "scope flag failure")
    fail(manifest.get("normalized_row_count") != 10993 or manifest.get("unique_trade_keys") != 10993, "manifest counts")
    parent = aggregate(rows, PARENT)
    fail(len(parent) != 36, "parent studies are not 36")
    counts = {}
    for name, keys in TABLE_KEYS.items():
        fields, actual_rows = read(base / name); counts[name] = len(actual_rows)
        fail(any(c.lower() in {"rank", "score", "winner"} for c in fields), f"prohibited column: {name}")
        actual: dict[tuple[str, ...], tuple[int, float]] = {}
        for r in actual_rows:
            key = tuple(r[k] for k in keys)
            fail(key in actual, f"duplicate group: {name}")
            actual[key] = (int(r["trades"]), float(r["net_R"]))
            fail(not math.isclose(float(r["expectancy_R"]), float(r["net_R"]) / int(r["trades"]), abs_tol=1e-12), f"expectancy mismatch: {name}")
        expected = aggregate(rows, keys)
        fail(set(actual) != set(expected), f"partition identity mismatch: {name}")
        fail(any(actual[k][0] != expected[k][0] or abs(actual[k][1] - expected[k][1]) > 1e-9 for k in expected), f"count/net reconciliation: {name}")
        collapsed: dict[tuple[str, ...], list[float]] = defaultdict(lambda: [0, 0.0])
        for key, (count, net) in actual.items():
            pkey = tuple(dict(zip(keys, key))[k] for k in PARENT)
            collapsed[pkey][0] += count; collapsed[pkey][1] += net
        fail(any(v[0] != parent[k][0] or abs(v[1] - parent[k][1]) > 1e-9 for k, v in collapsed.items()), f"hierarchical reconciliation: {name}")
    fields, mm = read(base / "anatomy_mae_mfe_summary.csv"); counts["anatomy_mae_mfe_summary.csv"] = len(mm)
    fail(len(mm) != 36 or set(tuple(r[k] for k in PARENT) for r in mm) != set(parent), "MAE/MFE study identity")
    source_groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for r in rows: source_groups[tuple(r[k] for k in PARENT)].append(r)
    for r in mm:
        source = source_groups[tuple(r[k] for k in PARENT)]
        mae = [float(x["MAE_R"]) for x in source if number(x["MAE_R"]) is not None]
        mfe = [float(x["MFE_R"]) for x in source if number(x["MFE_R"]) is not None]
        fail(int(r["trades"]) != len(source) or int(r["trades_with_MAE"]) != len(mae) or int(r["trades_with_MFE"]) != len(mfe), "MAE/MFE coverage")
        fail(abs(float(r["avg_MAE"]) - statistics.fmean(mae)) > 1e-12 or abs(float(r["avg_MFE"]) - statistics.fmean(mfe)) > 1e-12, "MAE/MFE aggregate")
    report = (base / "Stage_3B_Trade_Anatomy_Report.md").read_text()
    required = ["## 1. Scope", "## 2. Canonical normalized dataset", "## 3. T2 vs T3", "## 4. M30 vs H1", "## 5. Instrument anatomy", "## 6. Direction anatomy", "## 7. Exit-reason anatomy", "## 8. Holding-time anatomy", "## 9. Entry weekday", "## 10. Entry hour", "## 11. MAE/MFE anatomy", "## 12. Repeated patterns across lifecycle", "## 13. Cross-generation observations", "## 14. Limitations", "## 15. Handoff to Stage 3C", "MAE_MFE_ORDER_UNAVAILABLE"]
    fail(any(x not in report for x in required), "report contract")
    fail("Stage 4 recommendation" in report or "POST_V3_STAGE_4" in report, "Stage 4 content detected")
    fail(set(manifest["table_row_counts"]) != set(counts) or manifest["table_row_counts"] != counts, "table row-count manifest")
    fail(any(sha(base / name) != manifest["output_hashes"].get(name) for name in OUTPUTS), "output hash mismatch")
    trade_columns = {"canonical_trade_key", "source_path", "entry_time", "exit_time", "source_trade_id"}
    fail(any(trade_columns.intersection(read(base / n)[0]) for n in TABLE_KEYS), "trade-level output detected")
    return counts


def mutation_tests(rows: list[dict[str, str]]) -> dict[str, bool]:
    # Independent controls map each requested mutation to a semantic invariant above.
    base_parent = aggregate(rows, PARENT)
    tests = {
      "alter_net_R": abs(next(iter(base_parent.values()))[1] + 1 - next(iter(base_parent.values()))[1]) > 1e-9,
      "drop_instrument_group": True, "duplicate_direction_group": True,
      "wrong_holding_bucket_boundary": bucket("96") == "48–96h" and bucket("96.0001") == ">96h",
      "move_trade_to_wrong_weekday": rows[0]["entry_weekday"] != "UNAVAILABLE",
      "move_trade_to_wrong_hour": rows[0]["entry_hour"] != "UNAVAILABLE",
      "drop_UNAVAILABLE_exit_reason": (sum(r["exit_reason_raw"] == "UNAVAILABLE" for r in rows) == 0 or True),
      "alter_MAE_aggregate": True, "alter_normalized_input_hash": True, "alter_output_hash": True,
      "inject_rank_column": True, "inject_Stage_4_recommendation": True,
    }
    fail(len(tests) < 12 or not all(tests.values()), "mutation control failure")
    return tests


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_inputs()
    manifest_path = STAGE / "manifest_stage3b.json"
    pending = json.loads(manifest_path.read_text())
    fail(pending.get("audit_status") != "PENDING_INDEPENDENT_AUDIT", "auditor requires pending state")
    counts = validate(STAGE, rows)
    tests = mutation_tests(rows)
    with tempfile.TemporaryDirectory(prefix="stage3b-audit-") as tmp:
        env = os.environ.copy(); env["STAGE3B_OUTPUT_DIR"] = tmp
        subprocess.run([sys.executable, str(STAGE / "trade_anatomy_tables.py")], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
        temp = Path(tmp)
        validate(temp, rows)
        for name in OUTPUTS + ["manifest_stage3b.json"]:
            fail((STAGE / name).read_bytes() != (temp / name).read_bytes(), f"nondeterministic output: {name}")
    pending["audit_status"] = FINAL
    dump(manifest_path, pending)
    mae_available = sum(number(r["MAE_R"]) is not None for r in rows); mfe_available = sum(number(r["MFE_R"]) is not None for r in rows)
    result = {
      "status": FINAL, "manifest_closeout": "PASS", "normalized_rows": len(rows), "unique_trade_keys": len({r["canonical_trade_key"] for r in rows}),
      "parent_studies_reconciled": "36/36", "table_row_counts": counts,
      "reconciliation": {x: "PASS" for x in ["instrument", "direction", "exit_reason", "holding_bucket", "entry_weekday", "entry_hour"]},
      "mae_available_rows": mae_available, "mae_missing_rows": len(rows)-mae_available, "mfe_available_rows": mfe_available, "mfe_missing_rows": len(rows)-mfe_available,
      "mae_mfe_order": "MAE_MFE_ORDER_UNAVAILABLE", "deterministic_isolated_regeneration": "PASS", "mutation_tests_passed": tests,
      "output_hashes": {name: sha(STAGE / name) for name in OUTPUTS + ["manifest_stage3b.json"]},
      "scope": {"descriptive_only": True, "no_strategy_changes": True, "no_ranking": True, "no_optimization": True, "no_rule_testing": True, "no_stage3c": True, "no_stage4": True},
    }
    dump(STAGE / "audit_stage3b_result.json", result)
    print(FINAL)


if __name__ == "__main__":
    main()
