# Optimization work queue

Registry preparation only. Every Optimization requires separate explicit authorization after registry review and merge. Working order follows the user’s A → B → C instruction, then existing family chronology; PF does not choose the order.

**Common gate per instrument: 100 verified CLOSED / 40 distinct CLOSED entry dates / 6 active CLOSED entry months; credible signal/execution and reproducible source/config. Any initial PF. ELIGIBLE is not economic PASS. Only 2023 development history may be used.**

| Order | Family | Qualified instruments/configurations | Excluded instruments / scope |
| --- | --- | --- | --- |
| 1 | A Equal High/Low | USD, CNY / A_v1 | GLD 9 CLOSED; IMOEX 13 |
| 2 | B High/Low Cluster | CNY B4/B7/B10; USD B4/B7 | USD B10: 34 CLOSED / 30 days; all GLD/IMOEX cohorts sparse |
| 3 | C Return/Retest/Rejection | USD C_v1 | CNY 61; GLD 2; IMOEX 3 CLOSED |
| 4 | Level Rejection | USD, CNY, GLD | IMOEX 22 CLOSED; opportunity-only and unpublished #460/#462 excluded |
| 5 | R16 Compression Breakout | USD, CNY | GLD 51; IMOEX 9 CLOSED |
| 6 | R17 ORB Breakout/Retest | USD, CNY | GLD 20; IMOEX 7 CLOSED |
| 7 | R18 / ORB False Break Fade | USD canonical A BASE | CNY 59; GLD 40; IMOEX 10 CLOSED; branch-only variants require verification |
| 8 | VWAP Mean Reversion | USD, CNY, GLD; qualifying rows in candidate CSV | IMOEX none; restrictive/context variants often sparse |
| 9 | Momentum Breakout | USD, CNY, GLD; qualifying rows in candidate CSV | IMOEX none; restrictive/context variants often sparse |

USD/CNY/GLD/IMOEX abbreviate USDRUBF/CNYRUBF/GLDRUBF/IMOEXF. Qualification belongs to a configuration and instrument, never every member of a family. For VWAP/Momentum, use the documented corrective v2 primary cohort as the planning reference; later FROZEN/NONE records can repeat the same sample. ENTRY/MANAGEMENT/context/T15 variants remain explicit alternatives, not additional independent trades. No variant is selected by its highest PF.

Before each family study freeze its bounded grid, search budget, exact entry/Stop/Take/execution conventions and candidate IDs. Potential directions are in the Master CSV; no grid or optimal parameter is fixed here. Take range 2R–10R must declare its R denominator. Trailing/filters/context apply only where justified for that family.

All qualifying configuration/instrument rows follow, ordered by family and configuration ID. Their counts must never be summed into an independent family sample.

## A

| Configuration | Instrument | CLOSED | Days | Months | C1 PF R / price |
| --- | --- | --- | --- | --- | --- |
| equal_high_low_m5_2023_a_v1 | CNYRUBF | 234 | 131 | 12 | 0.458 / 0.295 |
| equal_high_low_m5_2023_a_v1 | USDRUBF | 235 | 149 | 12 | 0.699 / 0.708 |

## B

| Configuration | Instrument | CLOSED | Days | Months | C1 PF R / price |
| --- | --- | --- | --- | --- | --- |
| high_low_cluster_m5_2023_b10_v1 | CNYRUBF | 164 | 92 | 12 | 0.396 / 0.361 |
| high_low_cluster_m5_2023_b4_v1 | CNYRUBF | 319 | 162 | 12 | 0.420 / 0.355 |
| high_low_cluster_m5_2023_b4_v1 | USDRUBF | 549 | 217 | 12 | 0.558 / 0.559 |
| high_low_cluster_m5_2023_b7_v1 | CNYRUBF | 217 | 115 | 12 | 0.465 / 0.462 |
| high_low_cluster_m5_2023_b7_v1 | USDRUBF | 123 | 86 | 12 | 0.487 / 0.462 |

## C

| Configuration | Instrument | CLOSED | Days | Months | C1 PF R / price |
| --- | --- | --- | --- | --- | --- |
| return_retest_rejection_m5_2023_c_v1 | USDRUBF | 102 | 82 | 12 | 0.626 / 0.642 |

## LEVEL_REJECTION

| Configuration | Instrument | CLOSED | Days | Months | C1 PF R / price |
| --- | --- | --- | --- | --- | --- |
| level_rejection_2023_m5_v1 | CNYRUBF | 213 | 99 | 11 | 0.789 / 0.715 |
| level_rejection_2023_m5_v1 | GLDRUBF | 128 | 70 | 6 | 0.645 / 0.656 |
| level_rejection_2023_m5_v1 | USDRUBF | 614 | 243 | 12 | 0.574 / 0.607 |

## R16

| Configuration | Instrument | CLOSED | Days | Months | C1 PF R / price |
| --- | --- | --- | --- | --- | --- |
| r16_compression_breakout_2023_m5_v1 | CNYRUBF | 124 | 104 | 12 | 0.596 / 0.666 |
| r16_compression_breakout_2023_m5_v1 | USDRUBF | 246 | 178 | 12 | 0.689 / 0.834 |

## R17

| Configuration | Instrument | CLOSED | Days | Months | C1 PF R / price |
| --- | --- | --- | --- | --- | --- |
| r17_orb_breakout_retest_2023_m5_v1 | CNYRUBF | 144 | 131 | 12 | 0.323 / 0.392 |
| r17_orb_breakout_retest_2023_m5_v1 | USDRUBF | 126 | 110 | 12 | 0.735 / 1.037 |

## R18

| Configuration | Instrument | CLOSED | Days | Months | C1 PF R / price |
| --- | --- | --- | --- | --- | --- |
| orb_a_base_2023_canonical_v1 | USDRUBF | 137 | 119 | 12 | 0.582 / 0.964 |

## VWAP_MR

| Configuration | Instrument | CLOSED | Days | Months | C1 PF R / price |
| --- | --- | --- | --- | --- | --- |
| stage2_causal_mtf_v1_VWAP_MR_FROZEN_V2__M30_C1_T10 | CNYRUBF | 232 | 149 | 12 | 0.142 / 0.088 |
| stage2_causal_mtf_v1_VWAP_MR_FROZEN_V2__M30_C1_T10 | USDRUBF | 347 | 200 | 12 | 0.332 / 0.465 |
| stage2_causal_mtf_v1_VWAP_MR_FROZEN_V2__M30_C1_T15_DELAY | CNYRUBF | 202 | 140 | 12 | 0.101 / 0.091 |
| stage2_causal_mtf_v1_VWAP_MR_FROZEN_V2__M30_C1_T15_DELAY | USDRUBF | 290 | 185 | 12 | 0.371 / 0.504 |
| stage2_causal_mtf_v1_VWAP_MR_FROZEN_V2__NONE_C1_T10 | CNYRUBF | 345 | 174 | 12 | 0.108 / 0.083 |
| stage2_causal_mtf_v1_VWAP_MR_FROZEN_V2__NONE_C1_T10 | GLDRUBF | 114 | 77 | 6 | 0.870 / 0.784 |
| stage2_causal_mtf_v1_VWAP_MR_FROZEN_V2__NONE_C1_T10 | USDRUBF | 545 | 230 | 12 | 0.346 / 0.436 |
| stage2_causal_mtf_v1_VWAP_MR_FROZEN_V2__NONE_C1_T15_DELAY | CNYRUBF | 285 | 172 | 12 | 0.141 / 0.104 |
| stage2_causal_mtf_v1_VWAP_MR_FROZEN_V2__NONE_C1_T15_DELAY | GLDRUBF | 106 | 65 | 6 | 0.729 / 0.842 |
| stage2_causal_mtf_v1_VWAP_MR_FROZEN_V2__NONE_C1_T15_DELAY | USDRUBF | 454 | 224 | 12 | 0.337 / 0.454 |
| stage2_causal_mtf_v1_VWAP_MR_PAYABLE_CAP_ENTRY__NONE_C1_T10 | USDRUBF | 105 | 82 | 12 | 0.713 / 0.708 |
| stage2_causal_mtf_v1_VWAP_MR_PAYABLE_CAP_ENTRY__NONE_C1_T15_DELAY | USDRUBF | 100 | 87 | 12 | 0.530 / 0.564 |
| stage2_complete_architectures_v1_VWAP_MR_FROZEN_V2_C1_T10 | CNYRUBF | 345 | 174 | 12 | 0.108 / 0.083 |
| stage2_complete_architectures_v1_VWAP_MR_FROZEN_V2_C1_T10 | GLDRUBF | 114 | 77 | 6 | 0.870 / 0.784 |
| stage2_complete_architectures_v1_VWAP_MR_FROZEN_V2_C1_T10 | USDRUBF | 545 | 230 | 12 | 0.346 / 0.436 |
| stage2_complete_architectures_v1_VWAP_MR_FROZEN_V2_C1_T15_DELAY | CNYRUBF | 285 | 172 | 12 | 0.141 / 0.104 |
| stage2_complete_architectures_v1_VWAP_MR_FROZEN_V2_C1_T15_DELAY | GLDRUBF | 106 | 65 | 6 | 0.729 / 0.842 |
| stage2_complete_architectures_v1_VWAP_MR_FROZEN_V2_C1_T15_DELAY | USDRUBF | 454 | 224 | 12 | 0.337 / 0.454 |
| stage2_complete_architectures_v1_VWAP_MR_MANAGEMENT_C1_T10 | CNYRUBF | 363 | 186 | 12 | 0.147 / 0.107 |
| stage2_complete_architectures_v1_VWAP_MR_MANAGEMENT_C1_T10 | GLDRUBF | 113 | 73 | 6 | 0.802 / 0.914 |
| stage2_complete_architectures_v1_VWAP_MR_MANAGEMENT_C1_T10 | USDRUBF | 524 | 234 | 12 | 0.441 / 0.473 |
| stage2_complete_architectures_v1_VWAP_MR_MANAGEMENT_C1_T15_DELAY | CNYRUBF | 323 | 185 | 12 | 0.156 / 0.121 |
| stage2_complete_architectures_v1_VWAP_MR_MANAGEMENT_C1_T15_DELAY | USDRUBF | 447 | 227 | 12 | 0.328 / 0.469 |
| stage2_m5_conditional_v2_VWAP_MR | CNYRUBF | 345 | 174 | 12 | 0.108 / 0.083 |
| stage2_m5_conditional_v2_VWAP_MR | GLDRUBF | 114 | 77 | 6 | 0.870 / 0.784 |
| stage2_m5_conditional_v2_VWAP_MR | USDRUBF | 545 | 230 | 12 | 0.346 / 0.436 |
| stage2_vwap_payable_cap_v1_VWAP_MR_PAYABLE_CAP_ENTRY_C1_T10 | USDRUBF | 105 | 82 | 12 | 0.713 / 0.708 |
| stage2_vwap_payable_cap_v1_VWAP_MR_PAYABLE_CAP_ENTRY_C1_T15_DELAY | USDRUBF | 100 | 87 | 12 | 0.530 / 0.564 |

## MOMENTUM

| Configuration | Instrument | CLOSED | Days | Months | C1 PF R / price |
| --- | --- | --- | --- | --- | --- |
| stage2_causal_mtf_v1_MOMENTUM_ENTRY_MANAGEMENT__NONE_C1_T10 | USDRUBF | 197 | 148 | 12 | 0.600 / 0.730 |
| stage2_causal_mtf_v1_MOMENTUM_ENTRY_MANAGEMENT__NONE_C1_T15_DELAY | USDRUBF | 136 | 114 | 12 | 0.975 / 1.199 |
| stage2_causal_mtf_v1_MOMENTUM_FROZEN_V2__M30_C1_T10 | CNYRUBF | 120 | 83 | 11 | 0.451 / 0.609 |
| stage2_causal_mtf_v1_MOMENTUM_FROZEN_V2__M30_C1_T10 | USDRUBF | 262 | 168 | 12 | 0.796 / 0.932 |
| stage2_causal_mtf_v1_MOMENTUM_FROZEN_V2__M30_C1_T15_DELAY | USDRUBF | 215 | 153 | 12 | 0.706 / 0.964 |
| stage2_causal_mtf_v1_MOMENTUM_FROZEN_V2__NONE_C1_T10 | CNYRUBF | 300 | 154 | 12 | 0.337 / 0.371 |
| stage2_causal_mtf_v1_MOMENTUM_FROZEN_V2__NONE_C1_T10 | GLDRUBF | 126 | 76 | 6 | 0.991 / 1.138 |
| stage2_causal_mtf_v1_MOMENTUM_FROZEN_V2__NONE_C1_T10 | USDRUBF | 594 | 238 | 12 | 0.662 / 0.759 |
| stage2_causal_mtf_v1_MOMENTUM_FROZEN_V2__NONE_C1_T15_DELAY | CNYRUBF | 250 | 143 | 12 | 0.374 / 0.411 |
| stage2_causal_mtf_v1_MOMENTUM_FROZEN_V2__NONE_C1_T15_DELAY | GLDRUBF | 104 | 72 | 6 | 0.392 / 0.598 |
| stage2_causal_mtf_v1_MOMENTUM_FROZEN_V2__NONE_C1_T15_DELAY | USDRUBF | 459 | 226 | 12 | 0.517 / 0.752 |
| stage2_complete_architectures_v1_MOMENTUM_ENTRY_C1_T10 | USDRUBF | 202 | 150 | 12 | 0.755 / 0.836 |
| stage2_complete_architectures_v1_MOMENTUM_ENTRY_C1_T15_DELAY | USDRUBF | 142 | 119 | 12 | 1.156 / 1.224 |
| stage2_complete_architectures_v1_MOMENTUM_ENTRY_MANAGEMENT_C1_T10 | USDRUBF | 197 | 148 | 12 | 0.600 / 0.730 |
| stage2_complete_architectures_v1_MOMENTUM_ENTRY_MANAGEMENT_C1_T15_DELAY | USDRUBF | 136 | 114 | 12 | 0.975 / 1.199 |
| stage2_complete_architectures_v1_MOMENTUM_FROZEN_V2_C1_T10 | CNYRUBF | 300 | 154 | 12 | 0.337 / 0.371 |
| stage2_complete_architectures_v1_MOMENTUM_FROZEN_V2_C1_T10 | GLDRUBF | 126 | 76 | 6 | 0.991 / 1.138 |
| stage2_complete_architectures_v1_MOMENTUM_FROZEN_V2_C1_T10 | USDRUBF | 594 | 238 | 12 | 0.662 / 0.759 |
| stage2_complete_architectures_v1_MOMENTUM_FROZEN_V2_C1_T15_DELAY | CNYRUBF | 250 | 143 | 12 | 0.374 / 0.411 |
| stage2_complete_architectures_v1_MOMENTUM_FROZEN_V2_C1_T15_DELAY | GLDRUBF | 104 | 72 | 6 | 0.392 / 0.598 |
| stage2_complete_architectures_v1_MOMENTUM_FROZEN_V2_C1_T15_DELAY | USDRUBF | 459 | 226 | 12 | 0.517 / 0.752 |
| stage2_complete_architectures_v1_MOMENTUM_MANAGEMENT_C1_T10 | CNYRUBF | 312 | 157 | 12 | 0.364 / 0.377 |
| stage2_complete_architectures_v1_MOMENTUM_MANAGEMENT_C1_T10 | GLDRUBF | 136 | 78 | 6 | 0.696 / 1.006 |
| stage2_complete_architectures_v1_MOMENTUM_MANAGEMENT_C1_T10 | USDRUBF | 605 | 241 | 12 | 0.621 / 0.698 |
| stage2_complete_architectures_v1_MOMENTUM_MANAGEMENT_C1_T15_DELAY | CNYRUBF | 252 | 145 | 12 | 0.293 / 0.354 |
| stage2_complete_architectures_v1_MOMENTUM_MANAGEMENT_C1_T15_DELAY | GLDRUBF | 114 | 80 | 6 | 1.240 / 0.975 |
| stage2_complete_architectures_v1_MOMENTUM_MANAGEMENT_C1_T15_DELAY | USDRUBF | 486 | 232 | 12 | 0.491 / 0.643 |
| stage2_m5_conditional_v2_MOMENTUM | CNYRUBF | 300 | 154 | 12 | 0.337 / 0.371 |
| stage2_m5_conditional_v2_MOMENTUM | GLDRUBF | 126 | 76 | 6 | 0.991 / 1.138 |
| stage2_m5_conditional_v2_MOMENTUM | USDRUBF | 594 | 238 | 12 | 0.662 / 0.759 |

STOP. This queue initiates no Optimization, Baseline, Robustness, WF or TRUE OOS.
