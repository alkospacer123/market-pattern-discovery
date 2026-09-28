# Stage 6 Production Assembly Decision Report

## 1. Scope
Artifact-only production decision; no strategy execution, backtest, parameter search, or new hypothesis occurred.

## 2. Governing roadmap
Stages 1–5 are closed; Stage 6 is this decision; Stage 7 remains next and is not performed here.

## 3. Authenticated evidence set
Stage 1–5 audit authorities were authenticated. v1 is historical corroborative evidence only; v2/v3 remain PARTIALLY_COMPARABLE.

## 4. Candidate universe
Exactly eight v2/v3 × T2/T3 × M30/H1 parents were considered without subset enumeration.

## 5. Parent eligibility
All hard lifecycle/economic gates are recorded in `production_parent_evidence.csv`; selection additionally requires OOS net R without top five > 0.

## 6. Parent decision
v3/T3/H1 is selected because it alone combines TRUE OOS PASS with WF PASS, while retaining positive recovery and a comparatively controlled calendar profile. It is not claimed universally superior.

## 7. Instrument eligibility
All four parent instruments pass the exact WF and TRUE OOS gates.

## 8. Instrument decision
CNYRUBF, GLDRUBF, and IMOEXF are selected. GLDRUBF supplies the strongest OOS contribution, CNYRUBF strong WF/OOS persistence, and IMOEXF a distinct equity diversification role. USDRUBF remains profitable but is not selected because its monthly behavior is comparatively redundant with CNYRUBF.

## 9. Selected basket monthly behavior
- baseline: net 54.3951944185R; positive share 0.565217391304; std 4.64911410378R; worst -2.83525573256R; equity DD -9.25311915619R.
- walk_forward: net 26.249612948R; positive share 0.625; std 4.20810330239R; worst -0.793919150874R; equity DD -0.793919150874R.
- true_oos: net 61.1433647238R; positive share 0.6; std 6.30565547361R; worst -3.6581668307R; equity DD -5.58524823295R.

## 10. Diversification evidence
- CNYRUBF/GLDRUBF: Pearson 0.663314146409, both-negative 4, opposite-sign 5, sample ADEQUATE; overlap Jaccard 0.123235800344, overlapping pairs 18.
- CNYRUBF/IMOEXF: Pearson -0.0433979696475, both-negative 4, opposite-sign 9, sample ADEQUATE; overlap Jaccard 0.0734162226169, overlapping pairs 18.
- GLDRUBF/IMOEXF: Pearson -0.104726378338, both-negative 4, opposite-sign 5, sample ADEQUATE; overlap Jaccard 0.123978201635, overlapping pairs 20.

## 11. Direction stability
LONG and SHORT evidence is retained in the direction artifact. Neither direction is removed.

## 12. Concentration
Selected-parent TRUE OOS net R without top five is 45.6543983541R and top-five positive-R share is 0.254735851464; the hard guard passes. Top-one/top-three/top-five fields remain in Stage 1 authority.

## 13. Trade-anatomy risk
Historically, 1,135 trades reached MFE >= 1R but finished nonpositive; mean winner giveback was 1.5804400716R; initial-stop share was 0.1141635586; longest loss streak was 16. These observations create no trade deletion rule.

## 14. Structural overlay decision
TRAIL1 is selected on **RETROSPECTIVE_CAUSAL_VALIDATION** and retains status **SUPPORTED_RETROSPECTIVELY**; it is not untouched TRUE OOS. BE1 remains MIXED_RETROSPECTIVE_EVIDENCE. Risk Cap remains FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED because of terminal right-censoring. Minimum Hold, Session, and Correlated-risk grouping remain NOT_ADMITTED and ineligible.

## 15. Portfolio-risk evidence
Stage 5.6 entry concurrency, same-instrument overlap, and pairwise temporal overlap are descriptive risk evidence only. No position suppression, grouping rule, or new cap is created.

## 16. Execution practicality
H1 limits signal-handling frequency, but perpetual research data are not executable contracts. Instrument availability and continuity are evidence properties; Stage 7 must define live mapping, roll convention, and the signal-data/execution-contract relation.

## 17. Counter-evidence / limitations
- TRAIL1 evidence is retrospective rather than fresh untouched OOS.
- The selected parent's WF sample is 66 trades and its TRUE OOS history is finite.
- CNYRUBF/GLDRUBF have positive monthly correlation; diversification is imperfect.
- IMOEXF has weak TRUE OOS expectancy and the worst selected-instrument OOS month.
- Simultaneous exposure and live perpetual-to-contract mapping remain unresolved production-design risks.

## 18. Final production assembly
**PROD_STAGE6_83C7B31BB42C**: v3 perpetual / T3 / H1 / CNYRUBF, GLDRUBF, IMOEXF / TRAIL1 / CORRECTED_SINGLE_C1 / tick 0.001.

## 19. Items deferred to Stage 7
Implementation source freeze, executable contract mapping and roll, allocation, sizing, safeguards, cost model, schedule, broker semantics, feed conventions, and operations are not yet frozen.

## 20. Stage 6 final status
**POST_V3_STAGE_6_PRODUCTION_ASSEMBLY_DECISION_COMPLETE**. Stage 6: **CLOSED**. This is **NOT YET A FROZEN PRODUCTION SPECIFICATION**.

## 21. Next roadmap step
Stage 7 — Production Specification Freeze: **NEXT**.
