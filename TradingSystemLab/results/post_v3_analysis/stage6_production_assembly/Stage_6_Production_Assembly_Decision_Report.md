# Stage 6 Production Assembly Decision Report

## Scope
Artifact-only certification of the existing decision; no strategy execution, new backtest, search, or new hypothesis occurred. Stage 7 is not performed.

## Parent and instrument decision
v3/T3/H1 remains the only parent with WF PASS and TRUE OOS PASS. CNYRUBF, GLDRUBF, and IMOEXF remain selected. USDRUBF remains economically positive, but its authenticated TRUE OOS relationship with CNYRUBF is redundant: historical Pearson 0.897371915725, corrected Pearson 0.89922329434, Jaccard 0.541809290954, 41 overlapping pairs, and 17 both-negative pairs.

## Selected instrument basket — canonical base-exit monthly verification
**CANONICAL_BASE_EXIT_BASKET_VERIFICATION**
These monthly basket metrics come from the authenticated Stage 2 canonical base-exit instrument matrix and do not represent a TRAIL1-modified basket backtest.
- baseline: net 54.3951944185R; positive share 0.565217391304; std 4.64911410378R; worst -2.83525573256R; monthly DD -9.25311915619R.
- walk_forward: net 26.249612948R; positive share 0.625; std 4.20810330239R; worst -0.793919150874R; monthly DD -0.793919150874R.
- true_oos: net 61.1433647238R; positive share 0.6; std 6.30565547361R; worst -3.6581668307R; monthly DD -5.58524823295R.

The parent comparison is selected instrument subset versus the full parent universe under canonical base exits; it is not TRAIL1 versus base.

## Selected-pair evidence
- CNYRUBF/GLDRUBF: Pearson 0.663314146409; both-negative months 4; opposite-sign months 5; Jaccard 0.123235800344; overlapping pairs 18; both-final-negative pairs 3; ADEQUATE.
- CNYRUBF/IMOEXF: Pearson -0.0433979696475; both-negative months 4; opposite-sign months 9; Jaccard 0.0734162226169; overlapping pairs 18; both-final-negative pairs 4; ADEQUATE.
- GLDRUBF/IMOEXF: Pearson -0.104726378338; both-negative months 4; opposite-sign months 5; Jaccard 0.123978201635; overlapping pairs 20; both-final-negative pairs 3; ADEQUATE.

## TRAIL1 selected-parent evidence
Overlay evidence is parent-level Stage 5 **RETROSPECTIVE_CAUSAL_VALIDATION**, not a newly constructed three-instrument overlay portfolio.

| lifecycle | canonical net R | TRAIL1 net R | canonical expectancy | TRAIL1 expectancy | canonical DD | TRAIL1 DD | canonical recovery | TRAIL1 recovery |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 83.9981135635 | 90.1461238163 | 0.456511486758 | 0.509300134555 | -6.58269159678 | -11.124529862 | 12.7604509992 | 8.10336481046 |
| walk_forward | 38.7298662832 | 46.8252275571 | 0.586816155806 | 0.743257580272 | -2.3003880261 | -2.43841556495 | 16.8362319069 | 19.2031367541 |
| historical_true_oos | 85.7364212456 | 87.9044651108 | 0.430836287666 | 0.477741658211 | -11.7191182979 | -14.4514696452 | 7.31594468684 | 6.08273533897 |

TRAIL1 is selected as the structural overlay because Stage 5 classified it **SUPPORTED_RETROSPECTIVELY** under retrospective causal validation. For the selected v3/T3/H1 parent, TRAIL1 improves some return/expectancy measures but does not dominate the canonical exit on every risk metric; historical OOS max drawdown and recovery show counter-evidence. Selection therefore preserves this documented trade-off.

TRAIL1 is not fresh untouched TRUE OOS, is not uniformly superior on all metrics, and is selected despite the documented DD/recovery tradeoff. BE1 remains **MIXED_RETROSPECTIVE_EVIDENCE**; no BE1+TRAIL1 combination is admitted. Risk Cap remains **FORMAL_RESEARCH_VERDICT_NOT_ASSIGNED**, **FINAL_ECONOMIC_CERTIFICATION_INCOMPLETE_TERMINAL_OPEN_POSITIONS**, and **DEFERRED_UNRESOLVED**. Minimum Hold, Session, and Correlated-risk grouping remain NOT_ADMITTED and NOT_ELIGIBLE_NOT_ADMITTED.

## Direction, concentration, and limitations
LONG and SHORT remain included; there is no direction filter. Selected-parent TRUE OOS net R without top five remains positive. The finite samples, imperfect currency diversification, concurrency, and overlay risk counter-evidence remain explicit.

Perpetual research data are not executable contracts. Exact live-contract mapping, roll convention, allocation, sizing, costs, broker semantics, data-feed conventions, and operational safeguards remain for Stage 7.

## Final decision
**PROD_STAGE6_83C7B31BB42C**: v3 perpetual / T3 / H1 / CNYRUBF, GLDRUBF, IMOEXF / TRAIL1 / CORRECTED_SINGLE_C1 / tick 0.001.

**POST_V3_STAGE_6_PRODUCTION_ASSEMBLY_DECISION_COMPLETE**. Stage 6 is **CLOSED**; the production specification is **NOT YET FROZEN**. Stage 7 — Production Specification Freeze is **NEXT**.
