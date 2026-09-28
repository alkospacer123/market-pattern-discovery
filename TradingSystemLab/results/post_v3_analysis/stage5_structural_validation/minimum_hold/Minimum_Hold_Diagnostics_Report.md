# Minimum-Hold Diagnostics Report

## 1. Scope
Stage 5.4 describes canonical T2/T3 holding-time outcomes only. No exit was changed and no duration was selected.

## 2. Prerequisite provenance
Authenticated Stage 3 normalized metadata and the Stage 5 canonical comparator are the only evidence inputs. Economics use `CORRECTED_SINGLE_C1`; the frozen strategy hashes and data identity are unchanged.

## 3. Canonical 9,694 reconciliation
Exactly **9,694** v2/v3 trades reconcile with zero canonical path mismatches. Six-lifecycle counts are 4,449 / 746 / 1,759 for v2 and 1,124 / 515 / 1,101 for v3.

The five trade metrics (count, Net R, expectancy, PF, and win rate) are independently rebuilt from the 24 studies authenticated by the canonical comparator trade-reconciliation contract. Portfolio DD and recovery are not claimed as comparator metrics; they carry the separate `CHRONOLOGICAL_PORTFOLIO_RECONSTRUCTION` status and are independently reconstructed by the certification auditor.

For T2, the auditor reads the authoritative single-C1 source field. For T3, it independently applies the frozen historical correction `corrected_net_R = raw_net_R_C1 + cost_R`; the comparator trade artifact authenticates row identity and execution reconciliation but is not treated as proof of this corrected representation.

## 4. Holding metadata reconciliation
All **9,694 / 9,694** records match one-to-one by authenticated source path, source row, and trade identity. Duplicate, unmatched, and unexpected counts are zero.

## 5. Six-lifecycle bucket table
`minimum_hold_lifecycle_report.csv` preserves every observed frozen bucket and lifecycle; no bucket is ranked.

| Generation | Lifecycle | Bucket | Trades | Share | Net R | Expectancy | PF | Win rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| v2 | baseline | 12–24h | 1304 | 0.293099572938 | 60.637095928 | 0.0465008404356 | 1.12561195732 | 0.388803680982 |
| v2 | baseline | 1–3h | 633 | 0.142279163857 | -548.602103805 | -0.866669990213 | 0.0311409977299 | 0.0284360189573 |
| v2 | baseline | 24–48h | 575 | 0.12924252641 | 649.44643325 | 1.12947205783 | 12.0166407909 | 0.739130434783 |
| v2 | baseline | 3–6h | 577 | 0.129692065633 | -387.303452482 | -0.671236486103 | 0.095876457457 | 0.0953206239168 |
| v2 | baseline | 48–96h | 706 | 0.158687345471 | 727.921110662 | 1.03104973182 | 5.23148392527 | 0.616147308782 |
| v2 | baseline | 6–12h | 381 | 0.0856372218476 | -126.967483452 | -0.333247988063 | 0.385099679028 | 0.228346456693 |
| v2 | baseline | <1h | 96 | 0.0215778826703 | -89.3295730155 | -0.930516385578 | 0 | 0 |
| v2 | baseline | >96h | 177 | 0.0397842211733 | 511.306622927 | 2.88873798264 | 151.530051755 | 0.966101694915 |
| v2 | true_oos | 12–24h | 558 | 0.317225696418 | 43.8265784388 | 0.0785422552667 | 1.20402238624 | 0.412186379928 |
| v2 | true_oos | 1–3h | 242 | 0.137578169414 | -220.951329595 | -0.913022023118 | 0.0201211381735 | 0.0247933884298 |
| v2 | true_oos | 24–48h | 265 | 0.150653780557 | 319.422947983 | 1.20536961503 | 9.51040993239 | 0.732075471698 |
| v2 | true_oos | 3–6h | 239 | 0.135872654918 | -160.367984885 | -0.670995752656 | 0.129131321735 | 0.0627615062762 |
| v2 | true_oos | 48–96h | 214 | 0.12166003411 | 398.610930372 | 1.86266789893 | 10.1788158967 | 0.682242990654 |
| v2 | true_oos | 6–12h | 171 | 0.0972143263218 | -79.9909296407 | -0.467783214273 | 0.282227874094 | 0.187134502924 |
| v2 | true_oos | <1h | 39 | 0.0221716884594 | -38.4751681208 | -0.986542772329 | 0 | 0 |
| v2 | true_oos | >96h | 31 | 0.017623649801 | 148.833164692 | 4.80106982877 | 54.7435421358 | 0.935483870968 |
| v2 | walk_forward | 12–24h | 259 | 0.347184986595 | 19.0749132461 | 0.0736483136914 | 1.20442141118 | 0.432432432432 |
| v2 | walk_forward | 1–3h | 108 | 0.144772117962 | -97.1448795685 | -0.899489625634 | 0.00309694320088 | 0.0185185185185 |
| v2 | walk_forward | 24–48h | 82 | 0.109919571046 | 107.471172635 | 1.31062405652 | 14.4316711837 | 0.768292682927 |
| v2 | walk_forward | 3–6h | 94 | 0.12600536193 | -59.1872192958 | -0.629651269105 | 0.125148295413 | 0.13829787234 |
| v2 | walk_forward | 48–96h | 115 | 0.154155495979 | 92.7097320695 | 0.806171583213 | 3.12749331665 | 0.573913043478 |
| v2 | walk_forward | 6–12h | 46 | 0.0616621983914 | -23.2011558811 | -0.504372953937 | 0.201464544625 | 0.195652173913 |
| v2 | walk_forward | <1h | 17 | 0.0227882037534 | -16.319561984 | -0.959974234353 | 0 | 0 |
| v2 | walk_forward | >96h | 25 | 0.0335120643432 | 88.0277914786 | 3.52111165915 | INF | 1 |
| v3 | baseline | 12–24h | 327 | 0.290925266904 | 71.8006310405 | 0.219573795231 | 1.65425676766 | 0.428134556575 |
| v3 | baseline | 1–3h | 159 | 0.141459074733 | -142.683507396 | -0.897380549662 | 0.00297426770483 | 0.0062893081761 |
| v3 | baseline | 24–48h | 169 | 0.150355871886 | 262.195972395 | 1.55145545796 | 16.0854512623 | 0.757396449704 |
| v3 | baseline | 3–6h | 156 | 0.138790035587 | -85.3664880838 | -0.547221077461 | 0.179794346127 | 0.153846153846 |
| v3 | baseline | 48–96h | 147 | 0.130782918149 | 194.523383024 | 1.32328831989 | 9.60457499354 | 0.714285714286 |
| v3 | baseline | 6–12h | 105 | 0.0934163701068 | -7.45585061474 | -0.0710081010927 | 0.832282131506 | 0.314285714286 |
| v3 | baseline | <1h | 26 | 0.0231316725979 | -23.6553052981 | -0.909819434542 | 0 | 0 |
| v3 | baseline | >96h | 35 | 0.0311387900356 | 127.832260642 | 3.65235030406 | 470.697424581 | 0.971428571429 |
| v3 | true_oos | 12–24h | 324 | 0.294277929155 | 25.5927379903 | 0.0789899320689 | 1.23085118584 | 0.41975308642 |
| v3 | true_oos | 1–3h | 151 | 0.13714804723 | -130.82464917 | -0.866388405102 | 0.0427987201847 | 0.0397350993377 |
| v3 | true_oos | 24–48h | 179 | 0.162579473206 | 263.663924888 | 1.4729828206 | 12.5680588796 | 0.703910614525 |
| v3 | true_oos | 3–6h | 140 | 0.127157129882 | -81.4294240865 | -0.581638743475 | 0.226004242229 | 0.114285714286 |
| v3 | true_oos | 48–96h | 145 | 0.131698455949 | 237.024850806 | 1.63465414349 | 9.49609444348 | 0.703448275862 |
| v3 | true_oos | 6–12h | 112 | 0.101725703906 | -46.9319651564 | -0.419035403182 | 0.299632740591 | 0.205357142857 |
| v3 | true_oos | <1h | 31 | 0.0281562216167 | -28.3534008384 | -0.914625833497 | 0 | 0 |
| v3 | true_oos | >96h | 19 | 0.0172570390554 | 106.286000021 | 5.5940000011 | INF | 1 |
| v3 | walk_forward | 12–24h | 166 | 0.322330097087 | 50.5567759786 | 0.304558891437 | 1.92220514675 | 0.427710843373 |
| v3 | walk_forward | 1–3h | 78 | 0.15145631068 | -71.3314083285 | -0.914505234981 | 0 | 0 |
| v3 | walk_forward | 24–48h | 64 | 0.12427184466 | 126.344425687 | 1.97413165135 | 26.8481821939 | 0.8125 |
| v3 | walk_forward | 3–6h | 61 | 0.118446601942 | -42.4245358425 | -0.695484194139 | 0.0406860477661 | 0.0983606557377 |
| v3 | walk_forward | 48–96h | 76 | 0.147572815534 | 88.9195364461 | 1.16999390061 | 9.80355158973 | 0.736842105263 |
| v3 | walk_forward | 6–12h | 43 | 0.0834951456311 | 3.68103137087 | 0.0856053807179 | 1.21482623951 | 0.395348837209 |
| v3 | walk_forward | <1h | 13 | 0.0252427184466 | -11.1105782661 | -0.854659866622 | 0 | 0 |
| v3 | walk_forward | >96h | 14 | 0.0271844660194 | 52.5180250043 | 3.75128750031 | INF | 1 |

## 6. T2/T3 and M30/H1 comparison
`minimum_hold_strategy_timeframe_report.csv` retains generation, lifecycle, strategy, timeframe, and bucket.

## 7. Walk-forward fold diagnostics
`minimum_hold_wf_fold_report.csv` keeps real folds separate. `minimum_hold_recurrence_report.csv` counts positive, negative, zero, and small-sample folds without a score.

## 8. Exit-reason diagnostics
`minimum_hold_exit_reason_report.csv` preserves source exit reasons verbatim and uses `UNAVAILABLE` only for missing values.

## 9. Direction diagnostics
`minimum_hold_direction_report.csv` is descriptive and makes no direction selection.

## 10. Instrument diagnostics
`minimum_hold_instrument_report.csv` is descriptive and makes no instrument selection.

## 11. Cumulative descriptive cohorts
`minimum_hold_cumulative_report.csv` combines frozen buckets only. For `<3h`, 1593 trades are represented across the 24 parent study cells; this view reports realized canonical R, not a system with those trades removed.

## 12. Recurrence across v2/v3 and lifecycle
**Observed fact:** `<3h` trades have negative expectancy in **14 of 14** sufficiently populated (at least 30 trades) generation/lifecycle/strategy/timeframe parent cells. The detailed tables show heterogeneous bucket economics across generation, lifecycle, engine, and timeframe. This is observable evidence only and remains insufficient to define one structural duration.

## 13. Small-sample limitations
Every cell with fewer than 30 trades remains visible and is flagged. Such cells are not pooled with larger samples.

## 14. No-counterfactual statement
It is unknown how a canonical trade closed early would have ended had its exit been forbidden. A minimum-hold rule would require a predeclared duration, separate research identity, and causal re-execution; none is performed here.

## 15. Stage 4 preservation
`Stage4 minimum-hold status = NOT_ADMITTED`. `Stage4 registry unchanged = true`.

## 16. Technical audit status
`STAGE5_5_4_MINIMUM_HOLD_DIAGNOSTICS_COMPLETE` / `DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION`. The independent audit is the authority for manifest status.

## 17. Conclusion and next roadmap step
Stage 5.4 finds a strong recurring descriptive association between very short realized holding times and poor canonical outcomes. This does not establish that preventing early exits would improve results.

**NO CAUSAL MINIMUM-HOLD CONCLUSION**

`Stage4 minimum-hold status = NOT_ADMITTED`

`Stage4 registry unchanged = true`

`Research status = DIAGNOSTIC_ONLY_NO_HYPOTHESIS_ADMISSION`

`Stage5 status = OPEN`

Next roadmap step: 5.5 Session/time-of-day diagnostics.
