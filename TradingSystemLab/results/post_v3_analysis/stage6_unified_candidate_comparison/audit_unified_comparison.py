"""Independent fail-closed audit for the Stage 6.6 source preflight."""
from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    with (HERE / "variant_source_registry.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    exact = [r["variant"] for r in rows] == ["CANONICAL", "TRAIL1", "SESSION_10_21",
                                                   "LOCK1_AFTER_2R", "STRUCTURAL_STACK_V1"]
    missing = [r["variant"] for r in rows if r["source_status"] != "AUTHENTICATED"]
    result = {"status": "FAIL" if missing else "PASS", "exact_five_variants": exact,
              "source_incomplete": missing, "ranking_performed": False,
              "strategy_replay_executed": False,
              "reason": "Ranking is forbidden until every authoritative trade ledger is present." if missing else ""}
    (HERE / "independent_audit_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if not exact or missing:
        raise RuntimeError("INDEPENDENT_AUDIT_SOURCE_INCOMPLETE: " + ", ".join(missing))


if __name__ == "__main__":
    main()
