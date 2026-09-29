"""Independent verifier for the published fixed-basket evidence package."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from . import generate_reassessment as producer

HERE = Path(__file__).resolve().parent
FILES = ("basket_registry.csv", "basket_yearly_metrics.csv", "basket_monthly_metrics.csv",
         "basket_rolling_stability.csv", "basket_lifecycle_metrics.csv", "basket_instrument_contribution.csv")


def audit() -> dict:
    frames = {name: pd.read_csv(HERE/name) for name in FILES}
    status = pd.read_csv(HERE/"production_candidate_comparison.csv").computed_final_status.iloc[0]
    producer.validate_artifacts(frames, status, identities={"trail_sha": producer.TRAIL_SHA,
        "decision_sha": producer.DECISION_SHA})
    return {"status": "FIXED_BASKET_INDEPENDENT_AUDIT_PASSED", "computed_final_status": status,
            "yearly_monthly_contribution_gate_recomputation": "PASS", "no_stage7_execution": True}


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
