"""Preflight and generate Stage 6.6 without ever replaying strategy signals.

The requested comparison cannot be produced unless each variant has an
authenticated, trade-level input ledger.  In particular, summary/digest files
are deliberately not accepted as substitutes for the Stage-5 TRAIL1 ledger.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STARTING_MAIN_SHA = "27b31703054574682c38384ddf1e33a2a7097652"
VARIANTS = {
    "CANONICAL": HERE.parent / "stage6_structural_stack/full_canonical_trades.csv",
    "TRAIL1": HERE.parent / "stage5_structural_validation/trail1/trail1_trades.csv",
    "SESSION_10_21": HERE.parent / "stage6_session_10_21_causal/session_10_21_trades.csv",
    "LOCK1_AFTER_2R": HERE.parent / "stage6_lock1_after_2r/lock1_after_2r_trades.csv",
    "STRUCTURAL_STACK_V1": HERE.parent / "stage6_structural_stack/structural_stack_v1_trades.csv",
}
REQUIRED = {("baseline", "2023"), ("baseline", "2024"),
            ("walk_forward", "2024"), ("historical_true_oos", "2025"),
            ("historical_true_oos", "2026")}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {"source_sha256": "", "trade_count": "0", "instruments": "",
                "lifecycle_coverage": "", "source_status": "SOURCE_INCOMPLETE"}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    columns = set(rows[0]) if rows else set()
    net = "net_R_C1" if "net_R_C1" in columns else "strategy_R" if "strategy_R" in columns else ""
    core = {"lifecycle", "instrument", "direction", "entry_time", "exit_time", "trade_id"}
    coverage = {(r.get("lifecycle", ""), r.get("exit_time", "")[:4]) for r in rows}
    complete = bool(rows and net and core <= columns and REQUIRED <= coverage)
    return {
        "source_sha256": sha256(path), "trade_count": str(len(rows)),
        "instruments": "+".join(sorted({r["instrument"] for r in rows})),
        "lifecycle_coverage": "+".join(f"{a}:{b}" for a, b in sorted(coverage)),
        "source_status": "AUTHENTICATED" if complete else "SOURCE_INCOMPLETE",
    }


def generate(output_dir: Path = HERE) -> None:
    rows = []
    rules = {
        "CANONICAL": "frozen v3 T3/H1",
        "TRAIL1": "+1R causal gated ATR trail",
        "SESSION_10_21": "10:00 <= new entry < 21:00 Europe/Moscow",
        "LOCK1_AFTER_2R": "+2R causal trigger; +1R floor from next event",
        "STRUCTURAL_STACK_V1": "SESSION_10_21 + LOCK1_AFTER_2R",
    }
    for variant, path in VARIANTS.items():
        rows.append({"variant": variant, "authoritative_source_paths": str(path.relative_to(ROOT)),
                     **inspect(path), "strategy_identity": "T3_H1_candidate_v3",
                     "parameter_identity": "4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a",
                     "rule_identity": rules[variant]})
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = output_dir / "variant_source_registry.csv"
    with registry.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    incomplete = [r["variant"] for r in rows if r["source_status"] != "AUTHENTICATED"]
    manifest = {
        "status": "SOURCE_INCOMPLETE" if incomplete else "PREFLIGHT_PASSED",
        "actual_starting_main_sha": STARTING_MAIN_SHA,
        "artifact_only": True, "strategy_replay_executed": False,
        "incomplete_variants": incomplete,
        "source_registry_sha256": sha256(registry),
    }
    (output_dir / "audit_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    if incomplete:
        raise RuntimeError("SOURCE_INCOMPLETE: authoritative instrument-level ledger missing for " + ", ".join(incomplete))


def main() -> None:
    generate()


if __name__ == "__main__":
    main()
