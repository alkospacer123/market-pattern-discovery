# Execution Units Audit Verdict

## Verdict: **COST_MODEL_FIXED**

The extreme C1 degradation was a unit-configuration artifact, not a property of the frozen strategies. The old Si tick size was `1.0` source price point; the corrected value is `0.001`. CNY remains `0.001`. The dimensionally explicit tick → points → R formula is now tested, including quantity cancellation and no double counting.

## Transparent history

| Strategy | Previous C0 / C1 | Corrected C0 / C1 | Consequence |
| --- | --- | --- | --- |
| T1 | expectancy -0.088324 / -2.348289 R; C1 NO_EDGE | expectancy -0.088324 / -0.109932 R; C1 NO_EDGE | Previous robustness verdict invalidated by unit bug; corrected verdict remains **NO_EDGE** because C0 itself is negative. |
| T3 | expectancy +0.478023 / -1.624125 R; C1 NO_EDGE | expectancy +0.478023 / +0.463443 R; C1 ROBUST_CANDIDATE | Previous robustness verdict invalidated by unit bug; corrected verdict is **ROBUST_CANDIDATE**. |

C0 trade identities and frozen economic fields are unchanged. Generated robust artifacts were regenerated rather than silently retained. Full scenarios are in `corrected_cost_comparison.csv`.

## Break-even round-trip costs

The direct aggregate equation is:

`break_even_round_trip_ticks = sum(gross_R) / sum(1 / initial_risk_ticks)`.

* T1: `-8.175478` ticks. Since gross aggregate R is already negative, there is no non-negative break-even transaction cost.
* T3: `65.571899` ticks.
