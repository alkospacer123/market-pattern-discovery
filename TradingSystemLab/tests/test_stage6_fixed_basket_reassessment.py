import copy
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parents[1] / "results/post_v3_analysis/stage6_fixed_basket_reassessment"
SPEC = importlib.util.spec_from_file_location("fixed_baskets", HERE / "generate_reassessment.py")
mod = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)
NAMES = ("basket_registry.csv", "basket_yearly_metrics.csv", "basket_monthly_metrics.csv",
         "basket_rolling_stability.csv", "basket_lifecycle_metrics.csv", "basket_instrument_contribution.csv")


@pytest.fixture
def evidence():
    frames = {name: pd.read_csv(HERE/name) for name in NAMES}
    identities = {"trail_sha": mod.TRAIL_SHA, "decision_sha": mod.DECISION_SHA,
                  "frame_hashes": {name: mod.event_sha(frame) for name, frame in frames.items()}}
    status = pd.read_csv(HERE/"production_candidate_comparison.csv").computed_final_status.iloc[0]
    return frames, identities, status


def test_published_evidence_recomputes(evidence):
    frames, identities, status = evidence
    mod.validate_artifacts(frames, status, identities=identities)


@pytest.mark.parametrize("mutation", [
    "annual_negative", "delete_month", "preavailability_zero", "contribution", "dd", "recovery",
    "rolling_6m", "rolling_12m", "membership", "seventh_basket", "candidate_hash",
    "trail_hash", "decision_sha", "hardcoded_verdict",
])
def test_required_mutations_are_detected(evidence, mutation):
    original, identity, status = evidence
    frames = {k: v.copy(deep=True) for k, v in original.items()}; ids = copy.deepcopy(identity); verdict = status
    if mutation == "annual_negative": frames["basket_yearly_metrics.csv"].loc[0, "net_R"] = -999
    elif mutation == "delete_month": frames["basket_monthly_metrics.csv"] = frames["basket_monthly_metrics.csv"].drop(index=0)
    elif mutation == "preavailability_zero": frames["basket_monthly_metrics.csv"].loc[0, "available_instruments"] = ""
    elif mutation == "contribution": frames["basket_instrument_contribution.csv"].loc[0, "instrument_net_R"] += 1
    elif mutation == "dd": frames["basket_lifecycle_metrics.csv"].loc[0, "trade_level_max_DD_R"] += 1
    elif mutation == "recovery": frames["basket_lifecycle_metrics.csv"].loc[0, "recovery_factor"] += 1
    elif mutation == "rolling_6m": frames["basket_rolling_stability.csv"].loc[0, "worst_6M_R"] += 1
    elif mutation == "rolling_12m": frames["basket_rolling_stability.csv"].loc[0, "worst_12M_R"] += 1
    elif mutation == "membership": frames["basket_registry.csv"].loc[0, "members"] = "USDRUBF"
    elif mutation == "seventh_basket": frames["basket_registry.csv"] = pd.concat([frames["basket_registry.csv"], frames["basket_registry.csv"].iloc[[0]].assign(basket="G")])
    elif mutation == "candidate_hash": frames["basket_registry.csv"].loc[0, "parameter_hash"] = "bad"
    elif mutation == "trail_hash": ids["trail_sha"] = "bad"
    elif mutation == "decision_sha": ids["decision_sha"] = "bad"
    elif mutation == "hardcoded_verdict": verdict = "CURRENT_STAGE6_ASSEMBLY_RECONFIRMED_UNDER_ANNUAL_HARD_GATE"
    with pytest.raises(RuntimeError): mod.validate_artifacts(frames, verdict, identities=ids)


def test_gate_is_strictly_positive_and_final_status_is_computed():
    gate = pd.read_csv(HERE/"annual_hard_gate.csv")
    assert gate.loc[gate.basket == "B", "baseline_2023_positive"].item() is False or not gate.loc[gate.basket == "B", "baseline_2023_positive"].item()
    assert set(pd.read_csv(HERE/"production_candidate_comparison.csv").computed_final_status) == {"NEW_PRODUCTION_IDENTITY_REQUIRED_BEFORE_STAGE7"}
