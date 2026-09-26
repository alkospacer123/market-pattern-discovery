"""Independent fail-closed audit gate for post-v3 Stage 5.

The audit refuses to issue a PASS or CLOSED status until a complete runner has
written all mandatory evidence.  It exists now so an incomplete implementation
cannot accidentally be represented as completed research.
"""
from __future__ import annotations

from pathlib import Path
import json

from run_stage5_validation import HERE, HYPOTHESES, preflight


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


def audit() -> None:
    preflight()
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
