"""Fail-closed entry point for frozen Stage 5 BE1 causal validation.

The command authenticates every prerequisite before market data is opened.
It never falls back to committed trade ledgers when the read-only data checkout
is unavailable: that would turn causal validation into forbidden post-hoc
arithmetic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CANONICAL_BASE = "2c39c681f51294d62c2622ad360e7aa1b2867b6a"
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
T2_HASH = "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774"
T3_HASH = "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c"
AUDIT = HERE / "canonical_comparator_audit_result.json"
STAGE4 = HERE.parent / "stage4_structural_hypotheses"
STAGE4_FILES = (
    "audit_stage4_result.json", "manifest_stage4.json",
    "structural_hypothesis_evidence.csv", "structural_hypothesis_registry.csv",
    "structural_hypothesis_validation_contract.csv",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), *args], check=True,
                          text=True, capture_output=True).stdout.strip()


def resolve_data_root() -> tuple[Path, str]:
    """Resolve the read-only data checkout using the frozen precedence.

    An explicitly configured path is authoritative and therefore fails closed
    when missing rather than silently selecting a different checkout.
    """
    configured = os.environ.get("MARKET_PATTERN_DATA_ROOT")
    candidates = ([(Path(configured), "env")] if configured else []) + [
        (ROOT.parent / "market-pattern-data", "sibling"),
        (Path("/workspace/market-pattern-data"), "workspace"),
    ]
    seen: set[Path] = set()
    for candidate, source in candidates:
        candidate = candidate.expanduser().resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_dir() and all((candidate / x).is_dir() for x in ("futures_quarterly", "forever")):
            return candidate, source
        if source == "env":
            raise RuntimeError(f"BE1_CONFIGURED_MARKET_DATA_ROOT_INVALID: {candidate}")
    raise RuntimeError("BE1_MARKET_DATA_ROOT_NOT_FOUND: checked env, sibling, workspace")


def authenticate(data_root: Path) -> dict[str, Any]:
    """Authenticate lineage and immutable evidence, returning frozen identities."""
    # Descendants of the specified base are allowed so the command remains
    # runnable from its implementation commit; histories not containing it fail.
    subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor",
                    CANONICAL_BASE, "HEAD"], check=True, capture_output=True)
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    required = {
        "status": "STAGE5_CANONICAL_COMPARATOR_INDEPENDENT_AUDIT_PASSED",
        "Stage5_status": "OPEN", "studies_reconciled": "24/24",
        "folds_reconciled": "32/32", "trade_rows_reconciled": 9694,
        "trade_level_mismatches": 0, "maximum_metric_delta": 0.0,
        "clean_control_before": "PASS", "clean_control_after": "PASS",
        "deterministic_audit_rerun": "PASS",
    }
    if any(audit.get(k) != v for k, v in required.items()):
        raise RuntimeError("BE1_COMPARATOR_PREREQUISITE_INVALID")
    mutations = audit.get("mutation_tests", {})
    if (mutations.get("mode"), mutations.get("passed"), mutations.get("total")) != (
            "EXECUTABLE_ADVERSARIAL", 30, 30):
        raise RuntimeError("BE1_COMPARATOR_MUTATION_PREREQUISITE_INVALID")
    expected_stage4 = audit["stage4_authentication"]["hashes"]
    actual_stage4 = {name: sha(STAGE4 / name) for name in STAGE4_FILES}
    if actual_stage4 != expected_stage4:
        raise RuntimeError("BE1_STAGE4_HASH_INVALID")
    if not data_root.is_dir() or _git(data_root, "rev-parse", "HEAD") != DATA_COMMIT:
        raise RuntimeError("BE1_MARKET_DATA_COMMIT_INVALID")
    source_hashes = audit["source_data_hashes"]
    actual_sources = {name: sha(data_root / name) for name in source_hashes}
    if actual_sources != source_hashes:
        raise RuntimeError("BE1_SOURCE_DATA_IDENTITY_INVALID")
    strategy_dir = ROOT / "TradingSystemLab/strategies/trend"
    if sha(strategy_dir / "T2_Trend_Pullback.py") != T2_HASH or sha(
            strategy_dir / "T3_MTF_Trend.py") != T3_HASH:
        raise RuntimeError("BE1_STRATEGY_HASH_INVALID")
    return {
        "canonical_base": CANONICAL_BASE,
        "comparator_artifact_hashes": {p.name: sha(p) for p in sorted(HERE.glob("canonical_comparator*"))},
        "stage4_artifact_hashes": actual_stage4,
        "source_hashes": source_hashes,
    }


def run(data_root: Path, output: Path) -> dict[str, Any]:
    """Authenticate before dispatching the causal study implementation.

    Publishing partial or synthetic evidence is intentionally impossible.  The
    full data checkout is mandatory and output is untouched until authentication
    succeeds.
    """
    identities = authenticate(data_root)
    from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_be1_lifecycle import execute
    return execute(data_root, output, identities)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--output", type=Path, default=HERE / "be1")
    args = parser.parse_args()
    if args.data_root is None:
        data_root, _ = resolve_data_root()
    else:
        data_root = args.data_root
    print(json.dumps(run(data_root, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
