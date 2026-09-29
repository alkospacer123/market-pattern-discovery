# Final Pre-Stage-7 TRAIL1 Instrument Stability and Path Audit

**Scope:** frozen `PROD_STAGE6_83C7B31BB42C`; v3 / perpetual / T3 / H1 / TRAIL1 / CORRECTED_SINGLE_C1 / tick 0.001. This is revealed historical evidence, not fresh OOS, and performs no selection or Stage 7 execution.

**Authenticated historical TRUE OOS end:** `2026-09-15 21:00:00+00:00`. The 2026 rows are partial through that timestamp, not a complete year.

## Four-instrument evidence

The complete Baseline/WF/OOS metric table (including expectancy, win rate, median and every delta) is `instrument_canonical_vs_trail1_summary.csv`. Compact OOS view:

| instrument | canonical_trades | canonical_net_R | canonical_PF | canonical_max_DD_R | canonical_recovery_factor | trail1_trades | trail1_net_R | trail1_PF | trail1_max_DD_R | trail1_recovery_factor | delta_net_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | 51 | 22.7656 | 2.6843 | -3.6386 | 6.2567 | 50 | 20.1527 | 2.0892 | -3.3095 | 6.0894 | -2.6129 |
| GLDRUBF | 41 | 36.2004 | 3.6936 | -3.2270 | 11.2180 | 40 | 31.7277 | 2.6655 | -5.0001 | 6.3454 | -4.4728 |
| IMOEXF | 58 | 3.3231 | 1.1387 | -4.0237 | 0.8259 | 50 | 13.1869 | 1.5709 | -3.8316 | 3.4416 | 9.8638 |
| USDRUBF | 49 | 23.4473 | 2.4411 | -5.4717 | 4.2852 | 44 | 22.8372 | 2.0789 | -6.5583 | 3.4822 | -0.6101 |

## Annual and monthly stability

| instrument | year | canonical_trades | canonical_net_R | trail1_trades | trail1_net_R | delta_net_R |
| --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | 2025 | 27 | 10.0147 | 26 | 11.1142 | 1.0995 |
| CNYRUBF | 2026 | 24 | 12.7508 | 24 | 9.0385 | -3.7123 |
| GLDRUBF | 2025 | 20 | 15.3777 | 20 | 12.1049 | -3.2728 |
| GLDRUBF | 2026 | 21 | 20.8228 | 20 | 19.6228 | -1.2000 |
| IMOEXF | 2025 | 28 | 3.8251 | 23 | 8.9394 | 5.1143 |
| IMOEXF | 2026 | 30 | -0.5020 | 27 | 4.2475 | 4.7496 |
| USDRUBF | 2025 | 25 | 7.1299 | 21 | 9.4590 | 2.3291 |
| USDRUBF | 2026 | 24 | 16.3174 | 23 | 13.3782 | -2.9392 |

Availability excludes `NOT_YET_AVAILABLE`; an available zero-trade month is retained as zero. All rolling windows contain exactly six available calendar months. Detailed distributions and every full rolling value are in `instrument_monthly_stability.csv`.

## Exact path reconciliation

| instrument | canonical_trades | canonical_net_R | trail1_trades | trail1_net_R | total_delta_R | matched_exit_delta_R | canonical_only_count | canonical_only_R | canonical_only_bridge_contribution_R | trail1_only_count | trail1_only_R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | 51 | 22.7656 | 50 | 20.1527 | -2.6129 | -3.5267 | 1 | -0.9138 | 0.9138 | 0 | 0.0000 |
| GLDRUBF | 41 | 36.2004 | 40 | 31.7277 | -4.4728 | -3.5811 | 1 | 0.8917 | -0.8917 | 0 | 0.0000 |
| IMOEXF | 58 | 3.3231 | 50 | 13.1869 | 9.8638 | 4.2245 | 8 | -5.6393 | 5.6393 | 0 | 0.0000 |
| USDRUBF | 49 | 23.4473 | 44 | 22.8372 | -0.6101 | 2.4467 | 5 | 3.0568 | -3.0568 | 0 | 0.0000 |

Every row satisfies `matched_exit_delta - canonical_only_R + trail1_only_R = total_delta` within 1e-9. The key is lifecycle + fold + instrument + direction + UTC entry timestamp + entry price, never ordinal position.

* **CNY OOS:** the loss is a combination quantified above: matched exits -3.526652 R, suppression/removal bridge +0.913773 R, and new TRAIL1-only trades +0.000000 R.
* **GLD OOS:** the loss is a combination quantified above: matched exits -3.581065 R, suppression/removal bridge -0.891732 R, and new TRAIL1-only trades +0.000000 R.
* **IMOEX OOS bridge verified:** matched exits +4.224545 R; 8 canonical-only trades total -5.639292 R and contribute +5.639292 R; 0 TRAIL1-only trades; total +9.863837 R.

## Mechanism stability and drawdown trade-off

| instrument | classification | positive_views | negative_views | zero_views | PF_improving_lifecycles | DD_improving_lifecycles | recovery_improving_lifecycles | rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CNYRUBF | DEVELOPMENT_WF_BENEFIT_OOS_DEGRADATION | 2 | 3 | 0 | 1 | 2 | 1 | five descriptive views: Baseline, WF, revealed OOS, 2025, 2026 partial; no score |
| GLDRUBF | DEVELOPMENT_WF_BENEFIT_OOS_DEGRADATION | 2 | 3 | 0 | 1 | 0 | 1 | five descriptive views: Baseline, WF, revealed OOS, 2025, 2026 partial; no score |
| IMOEXF | OOS_SPECIFIC_BENEFIT | 3 | 2 | 0 | 1 | 1 | 1 | five descriptive views: Baseline, WF, revealed OOS, 2025, 2026 partial; no score |
| USDRUBF | DEVELOPMENT_WF_BENEFIT_OOS_DEGRADATION | 3 | 2 | 0 | 2 | 0 | 1 | five descriptive views: Baseline, WF, revealed OOS, 2025, 2026 partial; no score |

TRAIL1 is **not** a universal improvement or universally protective. The full table records whether each slice has improved Net R, DD (less-negative is improvement), and recovery. Effects rotate by lifecycle and instrument; several improved-return slices have worse DD and several lower-return slices have better DD.

## CNY/USD redundancy

| canonical correlation | canonical Jaccard | canonical overlap pairs | canonical co-loss pairs | TRAIL1 correlation | TRAIL1 Jaccard | TRAIL1 overlap pairs | TRAIL1 co-loss pairs | conclusion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.8992 | 0.5418 | 41 | 17 | 0.8295 | 0.4234 | 42 | 11 | REDUNDANCY_SUPPORTED_CNY_REMAINS_FROZEN_REPRESENTATIVE |

1. Redundancy remains supported by high monthly co-movement and material trade overlap/co-loss.
2. TRAIL1 does not provide sufficiently consistent evidence to overturn CNY as the frozen currency representative.
3. No evidence is strong enough to invalidate the existing Stage 6 CNY-over-USD decision; this audit does not re-select.

## Frozen selected assembly

| lifecycle | path | trades | net_R | PF | expectancy_R | max_DD_R | recovery_factor | win_rate | positive_month_share | median_monthly_R | monthly_std_R | worst_month_R | monthly_equity_max_DD_R | longest_negative_month_streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | canonical | 120 | 55.9607 | 2.2444 | 0.4663 | -8.8261 | 6.3404 | 0.4500 | 0.5417 | 0.0971 | 5.2640 | -2.7914 | -8.8261 | 4 |
| baseline | trail1 | 117 | 57.6710 | 2.1270 | 0.4929 | -13.8253 | 4.1714 | 0.4957 | 0.5000 | 0.0358 | 5.4289 | -3.9396 | -13.8253 | 6 |
| walk_forward | canonical | 52 | 26.6434 | 2.8472 | 0.5124 | -2.2817 | 11.6767 | 0.5000 | 0.4167 | 0.0000 | 4.6001 | -0.7581 | -0.7581 | 1 |
| walk_forward | trail1 | 49 | 32.9683 | 3.1102 | 0.6728 | -3.0768 | 10.7152 | 0.6531 | 0.4167 | 0.0000 | 4.6220 | -1.0710 | -1.0710 | 1 |
| historical_true_oos | canonical | 150 | 62.2891 | 2.2234 | 0.4153 | -7.1532 | 8.7079 | 0.4467 | 0.5714 | 0.0890 | 6.3657 | -3.6437 | -5.4347 | 2 |
| historical_true_oos | trail1 | 140 | 65.0673 | 2.0728 | 0.4648 | -8.5754 | 7.5877 | 0.5357 | 0.6667 | 0.8051 | 6.2571 | -3.7571 | -5.0209 | 2 |

The OOS TRAIL1 advantage is entirely dependent on IMOEXF: CNY and GLD deltas are negative while IMOEX is positive, summing exactly to the basket delta. That concentration is a production concern, but not by itself evidence against the frozen common overlay: Baseline/WF show benefits rotating to CNY/GLD while IMOEX is weaker. The conclusion therefore uses recurrence, drawdown/recovery and diversification rather than OOS Net R alone.

## Production-readiness questions

1. **Strongest raw profitability: GLDRUBF.** It combines the strongest canonical/OOS return, PF and expectancy evidence with positive Baseline evidence, though its WF and TRAIL1 OOS degradation prevent a claim of universal dominance.
2. **Strongest stability: CNYRUBF.** Its evidence is more balanced across lifecycle/year/month views and recovery/DD than the more concentrated IMOEX effect; the matrix preserves the raw values.
3. **Mainly diversification value: IMOEXF.** Its standalone development evidence is weaker and its key frozen role is non-currency diversification plus the verified OOS path benefit.
4. **Universal TRAIL1 improvement? NO.** Effects are explicitly heterogeneous.
5. **Common production overlay supported? YES, conservatively.** Aggregate benefit recurs across development views through rotating components and remains positive OOS, although OOS benefit concentration and non-universal DD protection require Stage 7 monitoring.
6. **CNY versus USD? YES.** Existing redundancy and CNY choice remain supported; no revealed result is used to re-select.
7. **IMOEX justified? YES.** Exact reconciliation confirms its benefit rather than an aggregate arithmetic artifact, and it retains diversification value; the dependence is disclosed.
8. **Ready to enter Stage 7? YES, after independent review, unchanged.** This audit itself does not execute Stage 7.

## Final audited recommendation

`CURRENT_STAGE6_ASSEMBLY_SUPPORTED_FOR_STAGE7`

Proceed only with `PROD_STAGE6_83C7B31BB42C` unchanged: T3 / H1 / CNYRUBF + GLDRUBF + IMOEXF / TRAIL1. No retrospective winner, new basket, parameter, or identity was created.
