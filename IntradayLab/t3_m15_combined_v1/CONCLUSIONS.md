# Combined v1 — conclusions without further fitting

**Gross PF ≥2 is not reached on ALL_FOUR full 2023–2024 by any C1/C2 configuration. GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.**

| Configuration | Gross PF | Gross R | CLOSED | Positive months / 24 | Closed DD R |
|---|---:|---:|---:|---:|---:|
| C1 BASELINE, trail 3.0 | 1.637310 | 151.064548 | 512 | 19 | 11.336507 |
| C1 OPTIMIZED, trail 3.5 | 1.737704 | 176.339662 | 497 | 17 | 15.809092 |
| C2 BASELINE, trail 3.0 | 1.525938 | 161.227410 | 647 | 18 | 20.940353 |
| C2 OPTIMIZED, trail 3.5 | 1.645215 | 195.913672 | 619 | 18 | 22.027767 |

Each row has one terminal OPEN, excluded from CLOSED metrics. An isolated C1 OPTIMIZED 2023 PF 2.005764 or USDRUBF C1 PF above 2 does not meet the frozen ALL_FOUR full-period objective and cannot be promoted to independent validation.

## C1 — A6 + S1

Compared with standalone A6, full Gross R increases +15.097877R / +11.486148R and PF increases only +0.014357 / +0.012906 (BASELINE / OPTIMIZED). The gain is concentrated in improved 2024: 63.941675→80.448015R / 86.124534→97.650690R. 2023 changes 72.024996→70.616533R / 78.728980→78.688972R. Full drawdown improves 15.871960→11.336507R in BASELINE but worsens 14.249525→15.809092R in OPTIMIZED. Positive months change 18→19 / 18→17; the optimized 2024 calendar falls from nine to eight positive months. Adding S1 is therefore not uniformly better in risk/calendar behavior.

The entry filter's cost remains substantial against CONTROL: 2023 loses −23.588370R / −19.928831R, while 2024 gains +30.241681R / +17.548670R. Full Gross R changes +6.653311R / −2.380161R. C1 retains 60/81 and 63/90 original CONTROL winners >=2R, with 21 / 27 missing entries. Relative to A6 itself, 68/69 and 74/74 large winners are fully preserved; no matched large winner is shortened or turned nonpositive. S1's occupancy removes one extra A6 large-winner entry in BASELINE.

Accepted entries fall 523→513 / 502→498 against A6, while observed-bar occupancy rises 9.2522%→10.6642% / 10.7445%→11.9399%. This difference demonstrates why entry filtering plus delayed trailing cannot be represented by combining ready-made trades. The worst full-period month is August 2023, −5.609535R / −7.143983R.

## C2 — A7 + S1

Against standalone A7, full Gross R increases +18.967483R / +13.441270R and PF +0.028599 / +0.020412. 2024 changes 46.838488→68.802438R / 81.452976→94.993363R. 2023 changes 95.421439→92.424972R / 101.019426→100.920310R. BASELINE drawdown improves 24.357942→20.940353R; OPTIMIZED worsens 21.621623→22.027767R. Positive months rise 16→18 / 17→18.

Against CONTROL, 2023 changes −1.779930R / +2.302507R and 2024 +18.596104R / +14.891343R. Full Gross R is +16.816173R / +17.193849R. C2 retains 68/81 and 76/90 CONTROL large winners; 13 / 14 original large-winner entries are missing. Against A7, 70/73 and 80/82 are fully preserved with three / two missing entries. There are no reduced matched >=2R outcomes or matched large winners turned nonpositive.

Accepted entries fall 670→648 / 632→620 against A7; occupancy rises 11.6428%→13.2104% / 13.3081%→14.6733%. The worst month is August 2023 −6.356205R for BASELINE and May 2023 −7.486652R for OPTIMIZED.

## Concentration and November 2024

C1 top5/top10 concentration is 9.3864%/16.4860% and 10.2818%/17.4077% of positive R. C2 is 8.5621%/15.2215% and 9.9031%/16.8894%. Removing top10 leaves full Gross PF 1.367384 / 1.435209 for C1 and 1.293668 / 1.367349 for C2. None of these fixed removal diagnostics changes a replay or permits selecting a modified strategy.

November 2024 contributes C1 46.231081R / 52.397239R (57.4670% / 53.6578% of 2024 net gross R) and C2 38.971172R / 44.855947R (56.6421% / 47.2201%). Dependence is still material. However, 2024 without November remains positive: C1 +34.216934R / +45.253451R, PF 1.226879 / 1.294603; C2 +29.831265R / +50.137416R, PF 1.158251 / 1.269044. This is retrospective bookkeeping sensitivity on development-exposed data, not Robustness, WF or TRUE OOS.

Every instrument's full-period gross R is positive for both combinations/versions; differences by year and LONG/SHORT remain visible in the complete tables and are not replaced by the pooled figures. The primary report and CSVs preserve all losers, missing winners, terminal positions, month signs, drawdowns, attribution and new-entry outcomes.

No thresholds, trailing multipliers, component mechanics or hypotheses were changed after viewing results. No extra combination, Optimization, Robustness, Walk Forward, TRUE OOS or LIVE was run. The separate implementation audit passes; external independent human review remains pending. **One Draft PR, STOP for external review, no Merge or Auto-Merge.**
