"""Independent, fail-closed verifier for the fixed six-basket evidence package."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from . import generate_reassessment as producer

HERE = Path(__file__).resolve().parent
FILES = ("basket_registry.csv", "basket_yearly_metrics.csv", "basket_monthly_metrics.csv",
         "basket_rolling_stability.csv", "basket_lifecycle_metrics.csv", "basket_instrument_contribution.csv",
         "basket_monthly_concentration.csv", "v1_v3_currency_pnl_bridge.csv",
         "production_candidate_comparison.csv")


def _independent_selection(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, str, str | None]:
    """Rebuild the declared hierarchy without trusting producer decision columns."""
    year, life, roll, mon = (frames[n] for n in ("basket_yearly_metrics.csv", "basket_lifecycle_metrics.csv",
                                                  "basket_rolling_stability.csv", "basket_monthly_metrics.csv"))
    rows = []
    periods = (("baseline", 2023), ("baseline", 2024), ("walk_forward", 2024),
               ("historical_true_oos", 2025), ("historical_true_oos", 2026))
    for basket in "ABCDEF":
        y = year[year.basket == basket]
        flags = [float(y[(y.lifecycle == life_name) & (y.year == yr)].net_R.iloc[0]) > 0 for life_name, yr in periods]
        calendar = y[y.lifecycle != "walk_forward"]
        lf, rr, mm = life[life.basket == basket], roll[roll.basket == basket], mon[mon.basket == basket]
        streak = 0
        for _, group in mm.sort_values(["lifecycle", "year", "month"]).groupby("lifecycle"):
            run = best = 0
            for value in group.net_R:
                run = run + 1 if value < 0 else 0; best = max(best, run)
            streak = max(streak, best)
        rows.append({"basket": basket, "eligible": all(flags), "annual_floor": float(calendar.net_R.min()),
                     "worst_dd": float(lf.trade_level_max_DD_R.min()), "minimum_recovery": float(lf.recovery_factor.min()),
                     "chronological": float(calendar.net_R.sum()), "positive_share": float((mm.net_R > 0).mean()),
                     "median_month": float(mm.net_R.median()), "worst_6m": float(rr.worst_6M_R.min()),
                     "worst_12m": float(rr.worst_12M_R.min()), "negative_streak": streak})
    result = pd.DataFrame(rows); eligible = result[result.eligible].sort_values(
        ["annual_floor", "worst_dd", "minimum_recovery", "chronological", "positive_share", "median_month",
         "worst_6m", "worst_12m", "negative_streak", "basket"],
        ascending=[False, False, False, False, False, False, False, False, True, True], kind="mergesort")
    preferred = str(eligible.iloc[0].basket) if len(eligible) else None
    status = ("NO_TESTED_ASSEMBLY_ELIGIBLE_FOR_STAGE7" if preferred is None else
              "CURRENT_STAGE6_ASSEMBLY_RECONFIRMED_UNDER_ANNUAL_HARD_GATE" if preferred == "B" else
              "NEW_PRODUCTION_IDENTITY_REQUIRED_BEFORE_STAGE7")
    result["selection_rank"] = np.nan
    for rank, idx in enumerate(eligible.index, 1): result.loc[idx, "selection_rank"] = rank
    return result, status, preferred


def audit() -> dict:
    frames = {name: pd.read_csv(HERE/name) for name in FILES}
    producer_frame = frames["production_candidate_comparison.csv"]
    producer_status = str(producer_frame.computed_final_status.iloc[0])
    producer.validate_artifacts(frames, producer_status, identities={"trail_sha": producer.TRAIL_SHA,
        "decision_sha": producer.DECISION_SHA})
    rebuilt, auditor_status, auditor_preferred = _independent_selection(frames)
    producer_preferred = producer_frame.loc[producer_frame.production_preferred.astype(bool), "basket"]
    if list(producer_preferred) != ([auditor_preferred] if auditor_preferred else []):
        raise RuntimeError("PRODUCER_PREFERRED_AUDITOR_PREFERRED_MISMATCH")
    if producer_status != auditor_status:
        raise RuntimeError("PRODUCER_STATUS_AUDITOR_STATUS_MISMATCH")
    ranks = producer_frame.set_index("basket").selection_rank.reindex(rebuilt.basket).to_numpy()
    if not np.allclose(ranks, rebuilt.selection_rank, equal_nan=True):
        raise RuntimeError("SELECTION_RANK_INVALID")
    # Regenerate the report from verified frames, then require byte-for-byte
    # equality. This makes every embedded table value auditable, not copied text.
    bars = pd.read_csv(HERE/"v1_v3_bar_reconciliation.csv")
    compare = pd.read_csv(HERE/"canonical_vs_trail1_comparison.csv")
    expected_report = producer.report(frames["basket_yearly_metrics.csv"], pd.read_csv(HERE/"annual_hard_gate.csv"),
        auditor_status, auditor_preferred, bars, frames["v1_v3_currency_pnl_bridge.csv"], compare,
        frames["basket_monthly_metrics.csv"], frames["basket_lifecycle_metrics.csv"],
        frames["basket_rolling_stability.csv"], frames["basket_monthly_concentration.csv"],
        frames["basket_instrument_contribution.csv"], frames["basket_registry.csv"])
    if (HERE/"FINAL_FIXED_BASKET_REASSESSMENT_REPORT.md").read_text() != expected_report:
        raise RuntimeError("REPORT_VALUES_INVALID")
    return {"status": "FIXED_BASKET_INDEPENDENT_AUDIT_PASSED", "computed_final_status": auditor_status,
            "preferred_basket": auditor_preferred, "exact_registry_semantics": "PASS",
            "v1_v3_pnl_bridge": "PASS", "independent_selection_recomputation": "PASS",
            "report_exact_values": "PASS", "no_stage7_execution": True}


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
