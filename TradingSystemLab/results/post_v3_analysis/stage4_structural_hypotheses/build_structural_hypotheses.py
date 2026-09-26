#!/usr/bin/env python3
"""Freeze the Stage 4 hypothesis set from authenticated, aggregate evidence only."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
POST = HERE.parent
S1 = POST / "stage1_master_evidence"
S2 = POST / "stage2_portfolio_diversification"
S3 = POST / "stage3_trade_anatomy"
CANONICAL = "244a5adac2baee3bb28d697efa25299b0a1973ef"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def authenticate() -> dict[str, str]:
    s1m = json.loads((S1 / "manifest.json").read_text())
    s2m = json.loads((S2 / "manifest.json").read_text())
    s3m = json.loads((S3 / "manifest_stage3d.json").read_text())
    s3a = json.loads((S3 / "audit_stage3d_result.json").read_text())
    assert s1m["audit_status"] == "POST_V3_STAGE_1_MASTER_EVIDENCE_AUDIT_PASSED"
    assert s2m["audit_status"] == "POST_V3_STAGE_2_PORTFOLIO_DIVERSIFICATION_AUDIT_PASSED"
    assert s3m["audit_status"] == "POST_V3_STAGE_3D_INDEPENDENT_CLOSEOUT_AUDIT_PASSED"
    assert s3m["stage3_status"] == "POST_V3_STAGE_3_TRADE_ANATOMY_FAILURE_ANALYSIS_CLOSED"
    assert s3a["status"] == "POST_V3_STAGE_3D_INDEPENDENT_CLOSEOUT_AUDIT_PASSED"
    assert s3a["stage3_status"] == "POST_V3_STAGE_3_TRADE_ANATOMY_FAILURE_ANALYSIS_CLOSED"
    for name, digest in s1m["artifacts"].items():
        assert sha(S1 / name) == digest
    for name, digest in s2m["output_sha256"].items():
        assert sha(S2 / name) == digest
    for name, digest in s3a["output_hashes"].items():
        if name != "manifest_stage3d.json":
            assert sha(S3 / name) == digest
    return {
        "stage1_manifest": sha(S1 / "manifest.json"),
        "stage1_master_study_comparison": sha(S1 / "master_study_comparison.csv"),
        "stage2_manifest": sha(S2 / "manifest.json"),
        "stage2_portfolio_stability": sha(S2 / "portfolio_stability_summary.csv"),
        "stage3d_manifest": sha(S3 / "manifest_stage3d.json"),
        "stage3d_audit": sha(S3 / "audit_stage3d_result.json"),
    }


def registry() -> list[dict[str, str]]:
    common_unchanged = "All canonical T2/T3 entry, filter, sizing, cost, slippage, and execution logic except the stated exit change"
    return [
        {
            "hypothesis_id": "H4_01_PROFIT_PROTECTION_BE1", "hypothesis_name": "Break-even after authenticated +1.0R excursion",
            "hypothesis_family": "profit_protection", "affected_layer": "exit risk management", "affected_strategy": "T2|T3",
            "affected_timeframe": "M30|H1", "affected_universe": "canonical v2 and v3 instruments",
            "structural_change": "Add one causal break-even transition after favorable excursion reaches +1.0R.",
            "fixed_trigger": "After entry, on the first completed execution bar whose causally observable high/low establishes favorable excursion >= +1.0 initial R.",
            "fixed_action": "From the next executable event, replace the active protective stop with entry price; never loosen it; keep it active until the canonical exit.",
            "unchanged_components": common_unchanged, "evidence_pattern_id": "FM_MFE1_FINAL_NONPOSITIVE",
            "evidence_summary": "5322/10993 trades reached 1R and 1135 finished nonpositive; recurrence spans generations and TRUE OOS; event order is unavailable.",
            "expected_mechanism": "Designed to test whether a single causal stop-state transition changes outcomes after an observable favorable excursion.",
            "falsification_condition": "Reject if causal re-execution does not show a stable benefit across lifecycles, destroys material expectancy/net R, worsens direction or instrument stability, is concentration-driven, or needs tuning.",
            "new_strategy_identity_required": "true", "admitted_status": "ADMITTED",
        },
        {
            "hypothesis_id": "H4_02_PROFIT_PROTECTION_TRAIL1", "hypothesis_name": "Delayed canonical ATR trail activation at +1.0R",
            "hypothesis_family": "profit_protection", "affected_layer": "exit risk management", "affected_strategy": "T2|T3",
            "affected_timeframe": "M30|H1", "affected_universe": "canonical v2 and v3 instruments",
            "structural_change": "Gate the canonical engine's existing ATR trailing stop until one fixed favorable-excursion threshold.",
            "fixed_trigger": "After entry, on the first completed execution bar whose causally observable high/low establishes favorable excursion >= +1.0 initial R.",
            "fixed_action": "Activate only that engine's frozen canonical ATR trailing-stop formula from the next executable event; preserve its distance, update cadence, and never-loosen rule exactly.",
            "unchanged_components": common_unchanged + "; canonical ATR trail parameters are unchanged",
            "evidence_pattern_id": "FM_MFE1_FINAL_NONPOSITIVE|WINNER_GIVEBACK|EXIT_RETENTION",
            "evidence_summary": "The repeated 1R/final-nonpositive pattern, 4264-winner giveback, and 10398-trade retention diagnostic motivate a causal activation test, not a saved-trade claim.",
            "expected_mechanism": "Designed to test whether delaying the already-defined trailing structure until one observable milestone changes retention without redefining trail geometry.",
            "falsification_condition": "Reject if causal re-execution lacks lifecycle recurrence, sacrifices material expectancy/net R, worsens stability, concentrates results, or requires changing activation or trail parameters.",
            "new_strategy_identity_required": "true", "admitted_status": "ADMITTED",
        },
        {
            "hypothesis_id": "H4_03_TOTAL_OPEN_RISK_CAP", "hypothesis_name": "One-unit aggregate open initial-risk cap",
            "hypothesis_family": "maximum_simultaneous_portfolio_risk", "affected_layer": "portfolio sizing gate", "affected_strategy": "T2|T3",
            "affected_timeframe": "M30|H1", "affected_universe": "each canonical v2 or v3 portfolio evaluated separately",
            "structural_change": "Cap summed remaining initial protective-stop risk across open positions at 1.0 standard R unit.",
            "fixed_trigger": "Immediately before sizing any eligible signal, aggregate the remaining protective-stop risk of all open T2/T3 positions in that generation portfolio.",
            "fixed_action": "Size the new position to min(its unchanged normal risk, max(0, 1.0R minus aggregate open risk)); skip at zero. Resolve simultaneous signals by timestamp, T2 before T3, M30 before H1, then instrument code ascending.",
            "unchanged_components": "All canonical signals, exits, filters, costs, slippage, and per-trade normal sizing; no correlation grouping or portfolio optimizer",
            "evidence_pattern_id": "PORTFOLIO_DRAWDOWN|PARENT_BOUNDED_LOSS_STREAK",
            "evidence_summary": "Stage 2 records portfolio monthly drawdowns and simultaneous negative instruments; Stage 3 records a 16-trade longest and -13.357307543122R worst parent-bounded streak.",
            "expected_mechanism": "Designed to test whether a deterministic exposure ceiling changes clustered-loss behavior while retaining the same signals.",
            "falsification_condition": "Reject if portfolio drawdown/simultaneous-loss behavior is not stably improved, if material total net R or expectancy is destroyed, if benefit is concentrated, or if tuning is required.",
            "new_strategy_identity_required": "true", "admitted_status": "ADMITTED",
        },
    ]


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    hashes = authenticate()
    reg = registry()
    reg_fields = list(reg[0])
    write_csv(HERE / "structural_hypothesis_registry.csv", reg_fields, reg)
    evidence_fields = ["hypothesis_id", "source_stage", "evidence_artifact", "evidence_metric", "generation", "lifecycle_stage", "strategy", "timeframe", "observed_value", "sample_size", "recurrence_status", "limitation", "evidence_sha256"]
    e = []
    def add(h, stage, artifact, metric, value, size, recurrence, limitation):
        path = ROOT / artifact
        e.append(dict(hypothesis_id=h, source_stage=stage, evidence_artifact=artifact, evidence_metric=metric, generation="v1|v2|v3", lifecycle_stage="baseline|walk_forward|true_oos", strategy="T2|T3", timeframe="M30|H1", observed_value=value, sample_size=size, recurrence_status=recurrence, limitation=limitation, evidence_sha256=sha(path)))
    threshold = "TradingSystemLab/results/post_v3_analysis/stage3_trade_anatomy/mfe_threshold_outcomes.csv"
    giveback = "TradingSystemLab/results/post_v3_analysis/stage3_trade_anatomy/winner_giveback.csv"
    retention = "TradingSystemLab/results/post_v3_analysis/stage3_trade_anatomy/exit_efficiency.csv"
    streak = "TradingSystemLab/results/post_v3_analysis/stage3_trade_anatomy/loss_streak_profile.csv"
    portfolio = "TradingSystemLab/results/post_v3_analysis/stage2_portfolio_diversification/portfolio_stability_summary.csv"
    master = "TradingSystemLab/results/post_v3_analysis/stage1_master_evidence/master_study_comparison.csv"
    for h in ("H4_01_PROFIT_PROTECTION_BE1", "H4_02_PROFIT_PROTECTION_TRAIL1"):
        add(h, "Stage 3C", threshold, "MFE>=1R reached / final nonpositive", "5322 / 1135", "10993", "multiple generations including TRUE OOS", "MAE_MFE_ORDER_UNAVAILABLE; occurrence is observational and cannot identify saved trades")
    add("H4_02_PROFIT_PROTECTION_TRAIL1", "Stage 3C", giveback, "winner descriptive giveback mean / median", "1.5804400716010985R / 1.442805981291279R", "4264", "all frozen studies", "Descriptive giveback is not realizable missed profit")
    add("H4_02_PROFIT_PROTECTION_TRAIL1", "Stage 3C", retention, "median uncapped final_R/MFE_R", "-0.3011787641484001", "10398", "all frozen studies", "Ratio is descriptive; causal execution is absent")
    add("H4_03_TOTAL_OPEN_RISK_CAP", "Stage 2", portfolio, "monthly portfolio drawdown and simultaneous negative instruments", "monthly equity DD observed; up to 6 instruments simultaneously negative", "24 portfolio studies", "v2 and v3; baseline, walk-forward, TRUE OOS", "Monthly co-movement does not establish trade-level overlap or an optimal cap")
    add("H4_03_TOTAL_OPEN_RISK_CAP", "Stage 3C", streak, "longest / worst parent-bounded loss streak", "16 / -13.357307543122R", "36 parent studies", "multiple generations including TRUE OOS", "Parent-bounded streaks are not a simulated portfolio risk rule")
    add("H4_03_TOTAL_OPEN_RISK_CAP", "Stage 1", master, "authenticated study universe", "36 studies; 10993 normalized trades downstream", "36 studies", "v1|v2|v3", "Stage 1 is comparator provenance, not causal support for the cap")
    write_csv(HERE / "structural_hypothesis_evidence.csv", evidence_fields, e)
    metrics = "trades|PF|expectancy R|net R|max DD|recovery|win rate|monthly stability|quarterly stability|direction stability|instrument stability|concentration|top-5 trade dependence"
    stability = "monthly stability|quarterly stability|direction stability|instrument stability|concentration|top-5 trade dependence"
    contracts = []
    for row in reg:
        hid = row["hypothesis_id"]
        portfolio_h = hid.endswith("TOTAL_OPEN_RISK_CAP")
        contracts.append({
            "hypothesis_id": hid, "new_identity_prefix": {"H4_01_PROFIT_PROTECTION_BE1":"T2_BE1_|T3_BE1_", "H4_02_PROFIT_PROTECTION_TRAIL1":"T2_TRAIL1_|T3_TRAIL1_", "H4_03_TOTAL_OPEN_RISK_CAP":"PORT_RISK1_"}[hid],
            "validation_stage": "Stage 5", "causal_reexecution_required": "true", "frozen_trigger": row["fixed_trigger"], "frozen_action": row["fixed_action"],
            "frozen_scope": row["affected_strategy"] + "; " + row["affected_timeframe"] + "; " + row["affected_universe"] + "; test individually only",
            "baseline_comparator": "Corresponding unchanged canonical T2 or T3 engine on identical instrument, timeframe, data slice, cost contract, and execution methodology",
            "primary_metrics": metrics + ("|portfolio max DD|simultaneous losses|total net R" if portfolio_h else ""),
            "stability_metrics": stability + ("|portfolio max DD|simultaneous losses|total net R" if portfolio_h else ""),
            "rejection_conditions": row["falsification_condition"], "no_parameter_search": "true", "no_posthoc_tuning": "true", "status": "FROZEN_FOR_INDIVIDUAL_STAGE5_TEST",
        })
    write_csv(HERE / "structural_hypothesis_validation_contract.csv", list(contracts[0]), contracts)
    report = (HERE / "Stage_4_Structural_Hypothesis_Set.md")
    report.write_text(REPORT, encoding="utf-8", newline="\n")
    manifest = {
        "status": "POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_COMPLETE", "audit_status": "PENDING_INDEPENDENT_AUDIT",
        "final_status": "PENDING_INDEPENDENT_AUDIT", "canonical_stage3d_commit": CANONICAL,
        "stage3d_manifest_sha256": hashes["stage3d_manifest"], "stage3d_audit_sha256": hashes["stage3d_audit"],
        "stage1_evidence_hashes_used": {"manifest.json": hashes["stage1_manifest"], "master_study_comparison.csv": hashes["stage1_master_study_comparison"]},
        "stage2_evidence_hashes_used": {"manifest.json": hashes["stage2_manifest"], "portfolio_stability_summary.csv": hashes["stage2_portfolio_stability"]},
        "admitted_hypothesis_count": len(reg), "admitted_hypothesis_ids": [r["hypothesis_id"] for r in reg],
        "registry_sha256": sha(HERE / "structural_hypothesis_registry.csv"), "evidence_sha256": sha(HERE / "structural_hypothesis_evidence.csv"),
        "validation_contract_sha256": sha(HERE / "structural_hypothesis_validation_contract.csv"),
        "controls": {k: True for k in ["no_strategy_execution", "no_backtest", "no_raw_market_data", "no_optimization", "no_ranking", "no_parameter_grid", "no_stage5", "no_production_selection", "individual_testing_only", "no_combined_variants"]},
    }
    (HERE / "manifest_stage4.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_COMPLETE")


REPORT = """# Stage 4 — Structural Hypothesis Set

## 1. Scope
This stage freezes three small, evidence-linked hypotheses. It performs no strategy execution, backtest, raw-data read, counterfactual P&L rewrite, optimization, ranking, or production selection.

## 2. Canonical Stage 3 closeout
Canonical `main` is `244a5adac2baee3bb28d697efa25299b0a1973ef`. The authenticated prerequisite statuses are `POST_V3_STAGE_3D_INDEPENDENT_CLOSEOUT_AUDIT_PASSED` and `POST_V3_STAGE_3_TRADE_ANATOMY_FAILURE_ANALYSIS_CLOSED`. The manifest records the authenticated Stage 1, Stage 2, and Stage 3D hashes.

## 3. Evidence principles
The required chain is frozen evidence → observed mechanism → structural hypothesis → exact future validation contract. All evidence is committed aggregate post-v3 evidence. Calendar 2025 TRUE OOS has been revealed, so every modification is a new post-OOS research identity, never a revision of historical evidence.

## 4. Confirmed diagnostic problems
The normalized population is v1 1,299, v2 6,954, v3 2,740: 10,993 trades in 36 studies. MFE thresholds 0.5R/1.0R/2.0R were reached by 7,337/5,322/2,954 trades; 3,077/1,135/54 respectively finished nonpositive. Among 4,264 positive trades, mean/median descriptive giveback was 1.5804400716010985R/1.442805981291279R. INITIAL_STOP count/share was 1,255/0.11416355862821796, mean final R/MAE/MFE was -1.041555793884741/0.5899240178217228/0.29387693883368216, and its MFE>=1R share was 0.050199203187251. For 10,398 MFE-positive trades, median uncapped final_R/MFE_R was -0.3011787641484001. The longest/worst parent-bounded loss streak was 16/-13.357307543122R. `FM_MFE1_FINAL_NONPOSITIVE` recurs across generations including TRUE OOS.

## 5. Admitted hypotheses
1. `H4_01_PROFIT_PROTECTION_BE1`: one break-even transition after causally authenticated +1.0R.
2. `H4_02_PROFIT_PROTECTION_TRAIL1`: activation of the unchanged canonical ATR trail only after causally authenticated +1.0R.
3. `H4_03_TOTAL_OPEN_RISK_CAP`: deterministic 1.0R-equivalent aggregate open-risk ceiling.

No hypothesis predicts performance; each is designed to test a mechanism and can be rejected.

## 6. Evidence per hypothesis
BE1 is motivated by the repeated 5,322-reached/1,135-final-nonpositive diagnostic. TRAIL1 adds the winner-giveback and exit-retention diagnostics. TOTAL_OPEN_RISK_CAP joins Stage 2 portfolio drawdown/simultaneous-negative evidence with Stage 3 parent-bounded loss streaks. Exact artifact hashes and limitations are frozen in `structural_hypothesis_evidence.csv`.

## 7. Exact frozen structural mechanics
BE1: after entry, the first completed execution bar establishing favorable excursion >=+1.0 initial R triggers replacement of the active stop by entry price from the next executable event; it is never loosened. TRAIL1 uses the same completed-bar threshold and then activates only the canonical engine's existing frozen ATR trail formula from the next executable event, without changing distance or cadence. RISK_CAP measures remaining protective-stop risk before each eligible signal, limits the portfolio to 1.0 standard R, resizes to the nonnegative residual, and skips at zero; simultaneous ordering is timestamp, T2 before T3, M30 before H1, instrument ascending.

## 8. New-strategy identity rules
Prefixes are `T2_BE1_`/`T3_BE1_`, `T2_TRAIL1_`/`T3_TRAIL1_`, and `PORT_RISK1_`. They are new post-OOS branches. They cannot overwrite or reuse the identities `T2_Trend_Pullback`, `T3_MTF_Trend`, or any v1/v2/v3 result.

## 9. Future Stage 5 validation contracts
Every hypothesis is tested individually, never initially as BE + risk cap, trail + BE, or any other combination. There is no parameter search or post-hoc tuning. Causal re-execution is mandatory. Each variant is compared only with its corresponding unchanged canonical T2/T3 engine using the same instrument, timeframe, data slice, transaction-cost/slippage contract, and execution methodology. Metrics are trades, PF, expectancy R, net R, max DD, recovery, win rate, monthly/quarterly/direction/instrument stability, concentration, and top-5 dependence; the portfolio hypothesis additionally uses portfolio max DD, simultaneous losses, and total net R.

## 10. Falsification conditions
Reject a hypothesis if a causal effect is absent or isolated to one lifecycle/generation, drawdown changes only by materially destroying expectancy/net R, results are concentration-driven, direction/instrument stability materially worsens, causal execution invalidates the diagnostic premise, or any benefit requires parameter tuning. No weighted optimizer score is permitted.

## 11. Considered but not admitted
* Minimum hold — `NOT_ADMITTED`: holding buckets do not provide a defensible, structurally predeclared single duration across generations/lifecycles.
* Session restriction — `NOT_ADMITTED`: hour aggregates do not provide stable evidence for a predeclared interval without retrospective hour selection; 10:00–17:00 is not adopted.
* Correlated-risk grouping — `NOT_ADMITTED`: Stage 2 monthly relationships do not justify one static group definition without choosing a correlation rule retrospectively.

## 12. Methodological limitations
`MAE_MFE_ORDER_UNAVAILABLE`: Stage 3 records maxima, not whether MFE occurred before MAE or an exit. A threshold occurrence and known final outcome do not prove BE or trailing would have saved any trade. Giveback is descriptive, not realizable missed profit. Profit-protection hypotheses therefore require causal re-execution and may not be evaluated by editing old outcomes. Monthly portfolio co-loss does not prove position overlap. TRUE OOS is revealed and cannot be optimized upon.

## 13. Protected historical identities
Stage 1, Stage 2, Stage 3A–D, v1/v2/v3 results, canonical T2/T3 code, frozen candidates, roadmap, and raw data remain unchanged and historical hashes remain references.

## 14. Final Stage 4 status
After independent audit: `POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_AUDIT_PASSED` and `POST_V3_STAGE_4_STRUCTURAL_HYPOTHESIS_SET_CLOSED`. Only registry hypotheses may proceed; additions require an explicit research decision and separate identity.

## 15. Next permitted roadmap step
`Stage 5 — Separate Validation of Structural Changes`
"""


if __name__ == "__main__":
    main()
