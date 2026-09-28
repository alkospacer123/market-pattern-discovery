# Stage 6 Production Assembly Decision Report

## Scope
Artifact-only correction and certification; no strategy execution, backtest, optimization, subset search, parameter search, or new hypothesis occurred. Stage 7 is not performed.

## Corrected economic authority
Earlier Stage 6 artifacts inherited some T3 economic fields from the historical Stage 1/2 representation. Final Stage 6 certification now uses the Stage 5 corrected single-C1 authority for all R-derived production-decision economics.
Economic contract: **CORRECTED_SINGLE_C1**. Parent and instrument authority: **STAGE5_CORRECTED_CURRENT_AUTHORITY**. Monthly authority: **STAGE5_5_6_CORRECTED_MONTHLY_INSTRUMENT_MATRIX**. Pairwise authority: **STAGE5_5_6_CORRECTED_PAIRWISE_MONTHLY_CORRELATION**. Frozen lifecycle classifications are preserved; this is not retrospective reclassification.

## Corrected parent economics
v3/T3/H1 remains eligible and is the unique parent with WF PASS and TRUE OOS PASS. Corrected TRUE OOS net R is 85.7364212428 and net R without top five is 46.9115227003.

## Corrected instrument economics
All four v3/T3/H1 instruments remain economically eligible under corrected trade and monthly authority. The existing three-instrument selection is verified rather than re-optimized.

## Corrected selected basket monthly verification
**CORRECTED_SINGLE_C1_CANONICAL_BASE_EXIT_BASKET_VERIFICATION**
Selected basket monthly economics are reconstructed from the Stage 5.6 corrected single-C1 monthly authority. They represent canonical base exits with corrected C1 accounting and are not a TRAIL1-modified three-instrument basket backtest.
- baseline: net 55.96068251R; positive share 0.608695652174; std 4.67386596283R; worst -2.79141996539R; monthly DD -8.82607308622R; negative streak 4.
- walk_forward: net 26.6433960363R; positive share 0.625; std 4.23490060989R; worst -0.75813179484R; monthly DD -0.75813179484R; negative streak 1.
- true_oos: net 62.2891375018R; positive share 0.6; std 6.32935198832R; worst -3.64371676141R; monthly DD -5.4347232371R; negative streak 2.

Both the selected subset and full-parent comparison use the same corrected monthly authority.

## Corrected pairwise evidence
- CNYRUBF/GLDRUBF: historical Pearson 0.663314146409; corrected Pearson 0.664316245754; corrected both-negative months 4; corrected opposite-sign months 5; Jaccard 0.123235800344; overlapping pairs 18; both-final-negative pairs 3.
- CNYRUBF/IMOEXF: historical Pearson -0.0433979696475; corrected Pearson -0.0364197885132; corrected both-negative months 4; corrected opposite-sign months 9; Jaccard 0.0734162226169; overlapping pairs 18; both-final-negative pairs 4.
- GLDRUBF/IMOEXF: historical Pearson -0.104726378338; corrected Pearson -0.104682282157; corrected both-negative months 4; corrected opposite-sign months 5; Jaccard 0.123978201635; overlapping pairs 20; both-final-negative pairs 3.
- CNYRUBF/USDRUBF redundancy: historical Pearson 0.897371915725; corrected Pearson 0.89922329434; Jaccard 0.541809290954; overlapping pairs 41; both-final-negative pairs 17.
No correlation threshold or correlated-risk production group is introduced.

## TRAIL1 parent-level evidence
Overlay evidence = Stage 5 parent-level retrospective causal TRAIL1 validation. Basket monthly verification = corrected single-C1 canonical base exits. No exact three-instrument TRAIL1 basket backtest exists.
| lifecycle | canonical net R | TRAIL1 net R | canonical expectancy | TRAIL1 expectancy | canonical DD | TRAIL1 DD | canonical recovery | TRAIL1 recovery |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 83.9981135635 | 90.1461238163 | 0.456511486758 | 0.509300134555 | -6.58269159678 | -11.124529862 | 12.7604509992 | 8.10336481046 |
| walk_forward | 38.7298662832 | 46.8252275571 | 0.586816155806 | 0.743257580272 | -2.3003880261 | -2.43841556495 | 16.8362319069 | 19.2031367541 |
| historical_true_oos | 85.7364212456 | 87.9044651108 | 0.430836287666 | 0.477741658211 | -11.7191182979 | -14.4514696452 | 7.31594468684 | 6.08273533897 |

TRAIL1 does not dominate the canonical exit on every risk metric. TRAIL1 DOES NOT DOMINATE CANONICAL ON EVERY RISK METRIC. Historical OOS drawdown and recovery remain explicit counter-evidence.

## Decision consistency after correction
Corrected authority independently confirms the unchanged **PROD_STAGE6_83C7B31BB42C** decision: v3 perpetual / T3 / H1 / CNYRUBF, GLDRUBF, IMOEXF / TRAIL1. Historical Stage 1/2 T3 economics are not current authority.
Stage 6 is **CLOSED**. Production specification is **NOT YET FROZEN**. Stage 7 — Production Specification Freeze is **NEXT** and was not executed.

**POST_V3_STAGE_6_PRODUCTION_ASSEMBLY_DECISION_COMPLETE**
