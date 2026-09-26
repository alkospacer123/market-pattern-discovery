# Stage 4 — Structural Hypothesis Set

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
