# Stage 6 IMOEXF Decision Tests — Monthly Semantics Correction

**Audit status:** `POST_V3_STAGE6_IMOEXF_DECISION_TESTS_CORRECTION_AUDIT_PASSED`

**Decision status:** AUDIT ONLY — `PROD_STAGE6_83C7B31BB42C` remains unchanged.

## Calendar and monthly semantics

Month attribution uses the UTC calendar of the exit timestamp, exactly as the Stage 5 TRAIL1 lifecycle authority (`pd.to_datetime(..., utc=True).dt.strftime('%Y-%m')`). `NOT_YET_AVAILABLE` is excluded; authenticated available months with no trades remain zero-return rows. Monthly PF is blank for fewer than two trades and for a zero gross-loss denominator. Six-month rolling values require six complete available calendar months.

## Frozen TRAIL1 evidence

### Historical TRUE OOS metrics

| basket_or_symbol | lifecycle | trades | net_R | PF | expectancy_R | max_DD_R | recovery | win_rate | median_R | positive_month_share | monthly_median_R | monthly_std_R | worst_month_R | monthly_equity_max_DD_R | longest_negative_month_streak | co_loss_months |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF+GLDRUBF | historical_true_oos | 90 | 51.8804 | 2.38156 | 0.576448 | -7.2968 | 7.11002 | 0.544444 | 0.134889 | 0.571429 | 0.8051 | 6.02001 | -2.75702 | -4.08512 | 2 | 3 |
| CNYRUBF+GLDRUBF+IMOEXF | historical_true_oos | 140 | 65.0673 | 2.07283 | 0.464766 | -8.57535 | 7.58771 | 0.535714 | 0.183053 | 0.666667 | 0.8051 | 6.25711 | -3.75706 | -5.02091 | 2 | 4 |
| IMOEXF | historical_true_oos | 50 | 13.1869 | 1.5709 | 0.263739 | -3.83159 | 3.44164 | 0.52 | 0.319696 | 0.52381 | 0.0642367 | 1.63005 | -2.22641 | -3.03164 | 2 | 0 |

### All lifecycle marginal results

| lifecycle | three_instrument_net_R | two_instrument_net_R | IMOEXF_marginal_net_R |
| --- | --- | --- | --- |
| baseline | 57.671 | 44.6405 | 13.0305 |
| walk_forward | 32.9683 | 25.6052 | 7.36307 |
| historical_true_oos | 65.0673 | 51.8804 | 13.1869 |

## Corrected standalone IMOEXF monitoring

* Frozen TRAIL1 2025 Net R: **8.939418 R**.
* Frozen TRAIL1 2026 through September Net R: **4.247524 R**.
* Full six-month rolling Net R ending 2026-09: **3.678414 R**.
* Availability-aware positive-month share: **0.523810**.

These are frozen TRAIL1 monitoring results. They are distinct from canonical/base-exit evidence and are revealed historical evidence, not fresh OOS.

## Canonical/base-exit versus frozen TRAIL1 bridge

Canonical IMOEXF historical TRUE OOS is **3.323105 R**; frozen TRAIL1 is **13.186942 R**; difference **9.863837 R**. Matched exit delta is **4.224545 R**; canonical-only trades total **-5.639292 R** (8 trades); TRAIL1-only trades total **0.000000 R** (0 trades).

## Predeclared cost sensitivity

| lifecycle | cost_multiplier | three_instrument_net_R | two_instrument_net_R | IMOEXF_marginal_net_R |
| --- | --- | --- | --- | --- |
| historical_true_oos | 1 | 65.0673 | 51.8804 | 13.1869 |
| historical_true_oos | 1.5 | 64.5045 | 51.3193 | 13.1853 |
| historical_true_oos | 2 | 63.9418 | 50.7582 | 13.1836 |

The only multipliers are 1.0x, 1.5x, and 2.0x, applied as `TRAIL1_net_R - (multiplier - 1) * round_trip_C1_cost_R` without changing trade paths.

## Identity implication

`CURRENT_STAGE6_ASSEMBLY_REMAINS_FROZEN`

No optimization, ranking, basket selection, strategy change, or Stage 7 execution occurred.
