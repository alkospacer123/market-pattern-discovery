"""Independent fail-closed audit gate for post-v3 Stage 5.

The audit refuses to issue a PASS or CLOSED status until a complete runner has
written all mandatory evidence.  It exists now so an incomplete implementation
cannot accidentally be represented as completed research.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import json
import os
import subprocess


# These constants are intentionally duplicated.  Importing the runner (or an
# execution/metrics adapter used by it) would make this certification circular.
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGE4 = HERE.parent / "stage4_structural_hypotheses"
BASE_COMMIT = "1378cc2868095823655bab9eebbb8a2d01db9376"
DATA_COMMIT = "50f1fd2178c18b7ab3bd969be82ad01f47a34745"
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


REQUIRED = {
    "canonical_comparator_reconciliation.csv",
    "hypothesis_validation_summary.csv",
    "hypothesis_lifecycle_metrics.csv",
    "hypothesis_instrument_metrics.csv",
    "hypothesis_direction_metrics.csv",
    "hypothesis_monthly_metrics.csv",
    "hypothesis_quarterly_metrics.csv",
    "hypothesis_concentration.csv",
    "portfolio_risk_cap_metrics.csv",
    "manifest_stage5.json",
    "audit_stage5_result.json",
    "Stage_5_Structural_Validation_Report.md",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def _data_root() -> Path:
    candidates = []
    if os.environ.get("MARKET_PATTERN_DATA_ROOT"):
        candidates.append(Path(os.environ["MARKET_PATTERN_DATA_ROOT"]).expanduser())
    candidates.extend((ROOT.parent / "market-pattern-data", Path("/workspace/market-pattern-data")))
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_dir():
            return resolved
    raise RuntimeError("FROZEN_MARKET_DATA_REPOSITORY_UNAVAILABLE")


def authenticate_prerequisites() -> None:
    """Authenticate frozen inputs using audit-owned code only."""
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"],
        cwd=ROOT,
        check=False,
    ).returncode == 0
    if _git("rev-parse", "HEAD") != BASE_COMMIT and not ancestor:
        raise RuntimeError("CANONICAL_BASE_NOT_ANCESTOR")
    stage4 = json.loads((STAGE4 / "manifest_stage4.json").read_text(encoding="utf-8"))
    if stage4.get("audit_status") != "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_AUDIT_PASSED":
        raise RuntimeError("STAGE4_AUDIT_STATUS_MISMATCH")
    if stage4.get("final_status") != "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_CLOSED":
        raise RuntimeError("STAGE4_FINAL_STATUS_MISMATCH")
    if stage4.get("admitted_hypothesis_ids") != HYPOTHESES:
        raise RuntimeError("STAGE4_HYPOTHESIS_SET_MISMATCH")
    for name, expected in STAGE4_HASHES.items():
        if _sha(STAGE4 / name) != expected:
            raise RuntimeError(f"STAGE4_FROZEN_HASH_MISMATCH:{name}")
    for name, expected in STRATEGY_HASHES.items():
        if _sha(ROOT / name) != expected:
            raise RuntimeError(f"CANONICAL_STRATEGY_HASH_MISMATCH:{name}")
    data = _data_root()
    if _git("rev-parse", "HEAD", cwd=data) != DATA_COMMIT:
        raise RuntimeError("FROZEN_MARKET_DATA_REPOSITORY_UNAVAILABLE")
    if not all((data / name).is_dir() for name in ("futures_quarterly", "forever")):
        raise RuntimeError("FROZEN_MARKET_DATA_UNIVERSE_UNAVAILABLE")


def audit() -> None:
    authenticate_prerequisites()
    missing = sorted(name for name in REQUIRED if not (HERE / name).is_file())
    if missing:
        raise RuntimeError("STAGE5_INCOMPLETE_MISSING_ARTIFACTS:" + ",".join(missing))
    manifest = json.loads((HERE / "manifest_stage5.json").read_text())
    if manifest.get("executed_hypothesis_ids") != HYPOTHESES:
        raise RuntimeError("EXECUTED_HYPOTHESIS_SET_MISMATCH")
    if manifest.get("evidence_role") != "RETROSPECTIVE_CAUSAL_VALIDATION":
        raise RuntimeError("EVIDENCE_ROLE_MISMATCH")
    if manifest.get("audit_status") != "POST_V3_STAGE_5_STRUCTURAL_VALIDATION_AUDIT_PASSED":
        raise RuntimeError("STAGE5_NOT_INDEPENDENTLY_FINALIZED")
    if manifest.get("final_status") != "POST_V3_STAGE_5_SEPARATE_STRUCTURAL_VALIDATION_CLOSED":
        raise RuntimeError("STAGE5_NOT_CLOSED")
    print("POST_V3_STAGE_5_STRUCTURAL_VALIDATION_AUDIT_PASSED")
    print("POST_V3_STAGE_5_SEPARATE_STRUCTURAL_VALIDATION_CLOSED")


if __name__ == "__main__":
    audit()
