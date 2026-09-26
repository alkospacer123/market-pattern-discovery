"""Stage 5 structural-validation entry point.

This module deliberately implements the *pre-execution gate* first.  Stage 5
cannot be reconstructed from the Stage 3 normalized trade tables: those tables
contain per-trade extrema, but not the ordered, completed execution bars needed
to establish when a 1R trigger became observable.  Rewriting a final trade R
from MFE would therefore be look-ahead.  The runner fails closed unless the
canonical market-data repositories are present at their frozen commit.

The executable variant engine is intentionally not approximated here.  In
particular, this file must never turn a missing input into a synthetic ledger.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGE4 = HERE.parent / "stage4_structural_hypotheses"
DATA = Path("/workspace/market-pattern-data")
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
BASE_COMMIT = "1378cc2868095823655bab9eebbb8a2d01db9376"
HYPOTHESES = [
    "H4_01_PROFIT_PROTECTION_BE1",
    "H4_02_PROFIT_PROTECTION_TRAIL1",
    "H4_03_TOTAL_OPEN_RISK_CAP",
]
STAGE4_HASHES = {
    "structural_hypothesis_registry.csv": "584a7c89dcb9e8985b4a0a9c5e432264b2c549675e2d45df9402cc12fb699fc8",
    "structural_hypothesis_validation_contract.csv": "5d5da406fdbd34aaaee005f4a9736ef7b8b4c56873919dfe2e7ac21f03bc00ac",
    "structural_hypothesis_evidence.csv": "c25f9d7f8fe551a8ebdf6e7d044f3468c0f6cae7a2b067af64dc9f22f90ce30f",
}
STRATEGY_HASHES = {
    "TradingSystemLab/strategies/trend/T2_Trend_Pullback.py": "376df085cfda85eefccb31343aad40ed4fbb1078f1314496472a3a4ac9507774",
    "TradingSystemLab/strategies/trend/T3_MTF_Trend.py": "840dd3b2cda43fa00259445cd0a22ace6d82e677f4c793028ccc8126f9ad9a8c",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def preflight() -> dict:
    """Authenticate all inputs before any market-data byte is opened."""
    if git("rev-parse", "HEAD") != BASE_COMMIT:
        # A Stage 5 working commit is allowed only when its first parent is the
        # canonical base.  This also makes reruns work after committing Stage 5.
        if not git("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD") == "":
            raise RuntimeError("CANONICAL_BASE_NOT_ANCESTOR")
    s4 = json.loads((STAGE4 / "manifest_stage4.json").read_text())
    if s4.get("audit_status") != "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_AUDIT_PASSED":
        raise RuntimeError("STAGE4_AUDIT_STATUS_MISMATCH")
    if s4.get("final_status") != "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_CLOSED":
        raise RuntimeError("STAGE4_FINAL_STATUS_MISMATCH")
    if s4.get("admitted_hypothesis_ids") != HYPOTHESES:
        raise RuntimeError("STAGE4_HYPOTHESIS_SET_MISMATCH")
    for name, expected in STAGE4_HASHES.items():
        if sha(STAGE4 / name) != expected:
            raise RuntimeError(f"STAGE4_FROZEN_HASH_MISMATCH:{name}")
    for name, expected in STRATEGY_HASHES.items():
        if sha(ROOT / name) != expected:
            raise RuntimeError(f"CANONICAL_STRATEGY_HASH_MISMATCH:{name}")
    if not DATA.is_dir() or git("rev-parse", "HEAD", cwd=DATA) != DATA_COMMIT:
        raise RuntimeError("FROZEN_MARKET_DATA_REPOSITORY_UNAVAILABLE")
    required = [DATA / "futures_quarterly", DATA / "forever"]
    if not all(p.is_dir() for p in required):
        raise RuntimeError("FROZEN_MARKET_DATA_UNIVERSE_UNAVAILABLE")
    return {"base": BASE_COMMIT, "data_commit": DATA_COMMIT,
            "stage4_hashes": STAGE4_HASHES, "strategy_hashes": STRATEGY_HASHES}


def run() -> None:
    preflight()
    raise RuntimeError(
        "STAGE5_FAIL_CLOSED: exact lifecycle re-execution adapters are not yet "
        "implemented; normalized MFE/MAE must not be used to fabricate causal "
        "completed-bar trigger timing"
    )


if __name__ == "__main__":
    run()
