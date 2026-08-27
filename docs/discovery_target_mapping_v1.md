# Discovery Target Mapping v1.0 — Inventory

**Signature:** `158da282d2972016ee07de22982e7de289df2c4e3f390b76ccbe0a0fd36272dd`

This preregistered inventory was selected from frozen contract metadata using elapsed-time and semantic coverage only. No feature→outcome relationship or target-result distribution was inspected. H1 path descriptors removed by Phase 3C are excluded; therefore M5 short-scale volatility uses future range alone and path geometry starts at the medium scale. Upper/lower hit binaries and known-hypothesis labels are not mapped.

| TIMEFRAME | FAMILY | ROLE | COLUMN | HORIZON | ELAPSED MINUTES | TYPE | PRIMARY CONTRASTS | HYPOTHESIS UNITS | VALIDITY RULE |
|---|---|---|---|---:|---:|---|---|---:|---|
| M1 | DIRECTIONAL | SHORT_SIGNED_DISPLACEMENT | `behavior_signed_displacement_atr_5` | 5 | 5 | continuous | median_difference | 1 | `target_future_valid_5_and_atr_20_finite_positive` |
| M1 | DIRECTIONAL | MEDIUM_SIGNED_DISPLACEMENT | `behavior_signed_displacement_atr_15` | 15 | 15 | continuous | median_difference | 1 | `target_future_valid_15_and_atr_20_finite_positive` |
| M1 | DIRECTIONAL | LONG_SIGNED_DISPLACEMENT | `behavior_signed_displacement_atr_60` | 60 | 60 | continuous | median_difference | 1 | `target_future_valid_60_and_atr_20_finite_positive` |
| M1 | DIRECTIONAL | SHORT_DIRECTION_CLASS | `label_direction_5` | 5 | 5 | multiclass | P(+1 \| feature_state) - P(+1 \| baseline)<br>P(-1 \| feature_state) - P(-1 \| baseline) | 2 | `target_future_valid_5_and_atr_20_finite_positive` |
| M1 | DIRECTIONAL | MEDIUM_DIRECTION_CLASS | `label_direction_15` | 15 | 15 | multiclass | P(+1 \| feature_state) - P(+1 \| baseline)<br>P(-1 \| feature_state) - P(-1 \| baseline) | 2 | `target_future_valid_15_and_atr_20_finite_positive` |
| M1 | DIRECTIONAL | LONG_DIRECTION_CLASS | `label_direction_60` | 60 | 60 | multiclass | P(+1 \| feature_state) - P(+1 \| baseline)<br>P(-1 \| feature_state) - P(-1 \| baseline) | 2 | `target_future_valid_60_and_atr_20_finite_positive` |
| M1 | VOLATILITY | SHORT_FUTURE_RANGE | `behavior_future_range_atr_5` | 5 | 5 | continuous | median_difference | 1 | `target_future_valid_5_and_atr_20_finite_positive` |
| M1 | VOLATILITY | MEDIUM_FUTURE_RANGE | `behavior_future_range_atr_15` | 15 | 15 | continuous | median_difference | 1 | `target_future_valid_15_and_atr_20_finite_positive` |
| M1 | VOLATILITY | LONG_FUTURE_RANGE | `behavior_future_range_atr_60` | 60 | 60 | continuous | median_difference | 1 | `target_future_valid_60_and_atr_20_finite_positive` |
| M1 | VOLATILITY | MEDIUM_PATH_LENGTH | `behavior_path_length_atr_15` | 15 | 15 | continuous | median_difference | 1 | `target_future_valid_15_and_atr_20_finite_positive` |
| M1 | VOLATILITY | LONG_PATH_LENGTH | `behavior_path_length_atr_60` | 60 | 60 | continuous | median_difference | 1 | `target_future_valid_60_and_atr_20_finite_positive` |
| M1 | PATH | MEDIUM_PATH_EFFICIENCY | `behavior_path_efficiency_15` | 15 | 15 | continuous | median_difference | 1 | `target_future_valid_15_and_atr_20_finite_positive` |
| M1 | PATH | LONG_PATH_EFFICIENCY | `behavior_path_efficiency_60` | 60 | 60 | continuous | median_difference | 1 | `target_future_valid_60_and_atr_20_finite_positive` |
| M1 | PATH | LONG_DIRECTION_PERSISTENCE | `behavior_direction_persistence_60` | 60 | 60 | continuous | median_difference | 1 | `target_future_valid_60_and_atr_20_finite_positive` |
| M1 | PATH | LONG_DIRECTION_CHANGES | `behavior_direction_changes_60` | 60 | 60 | continuous | median_difference | 1 | `target_future_valid_60_and_atr_20_finite_positive` |
| M1 | PATH | LONG_EXTREME_ORDER | `label_extreme_order_60` | 60 | 60 | binary | P(+1 high-before-low \| feature_state) - P(+1 high-before-low \| baseline) | 1 | `target_future_valid_60_and_atr_20_finite_positive` |
| M1 | FIRST_PASSAGE | SHORT_FIRST_PASSAGE_0p5_ATR | `label_first_passage_0p5_5` | 5 | 5 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_5_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M1 | FIRST_PASSAGE | SHORT_FIRST_PASSAGE_1p0_ATR | `label_first_passage_1p0_5` | 5 | 5 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_5_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M1 | FIRST_PASSAGE | MEDIUM_FIRST_PASSAGE_0p5_ATR | `label_first_passage_0p5_15` | 15 | 15 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_15_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M1 | FIRST_PASSAGE | MEDIUM_FIRST_PASSAGE_1p0_ATR | `label_first_passage_1p0_15` | 15 | 15 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_15_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M1 | FIRST_PASSAGE | LONG_FIRST_PASSAGE_0p5_ATR | `label_first_passage_0p5_60` | 60 | 60 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_60_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M1 | FIRST_PASSAGE | LONG_FIRST_PASSAGE_1p0_ATR | `label_first_passage_1p0_60` | 60 | 60 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_60_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M1 | MULTI_HORIZON | EARLY_TO_MID_INCREMENT | `behavior_early_to_mid_increment_atr` | — | — | continuous | median_difference | 1 | `multi_horizon_anchor_validity_and_atr_20_finite_positive` |
| M1 | MULTI_HORIZON | MID_TO_LATE_INCREMENT | `behavior_mid_to_late_increment_atr` | — | — | continuous | median_difference | 1 | `multi_horizon_anchor_validity_and_atr_20_finite_positive` |
| M1 | MULTI_HORIZON | PEAK_ABSOLUTE_DISPLACEMENT_HORIZON_INDEX | `behavior_peak_abs_displacement_hindex` | — | — | continuous | median_difference | 1 | `multi_horizon_anchor_validity_and_atr_20_finite_positive` |
| M1 | MULTI_HORIZON | FINAL_VS_PEAK_ABSOLUTE_RATIO | `behavior_final_vs_peak_abs_ratio` | — | — | continuous | median_difference | 1 | `multi_horizon_anchor_validity_and_atr_20_finite_positive` |
| M1 | MULTI_HORIZON | HORIZON_SIGN_CHANGES | `behavior_horizon_sign_changes` | — | — | continuous | median_difference | 1 | `multi_horizon_anchor_validity_and_atr_20_finite_positive` |
| M5 | DIRECTIONAL | SHORT_SIGNED_DISPLACEMENT | `behavior_signed_displacement_atr_1` | 1 | 5 | continuous | median_difference | 1 | `target_future_valid_1_and_atr_20_finite_positive` |
| M5 | DIRECTIONAL | MEDIUM_SIGNED_DISPLACEMENT | `behavior_signed_displacement_atr_3` | 3 | 15 | continuous | median_difference | 1 | `target_future_valid_3_and_atr_20_finite_positive` |
| M5 | DIRECTIONAL | LONG_SIGNED_DISPLACEMENT | `behavior_signed_displacement_atr_12` | 12 | 60 | continuous | median_difference | 1 | `target_future_valid_12_and_atr_20_finite_positive` |
| M5 | DIRECTIONAL | SHORT_DIRECTION_CLASS | `label_direction_1` | 1 | 5 | multiclass | P(+1 \| feature_state) - P(+1 \| baseline)<br>P(-1 \| feature_state) - P(-1 \| baseline) | 2 | `target_future_valid_1_and_atr_20_finite_positive` |
| M5 | DIRECTIONAL | MEDIUM_DIRECTION_CLASS | `label_direction_3` | 3 | 15 | multiclass | P(+1 \| feature_state) - P(+1 \| baseline)<br>P(-1 \| feature_state) - P(-1 \| baseline) | 2 | `target_future_valid_3_and_atr_20_finite_positive` |
| M5 | DIRECTIONAL | LONG_DIRECTION_CLASS | `label_direction_12` | 12 | 60 | multiclass | P(+1 \| feature_state) - P(+1 \| baseline)<br>P(-1 \| feature_state) - P(-1 \| baseline) | 2 | `target_future_valid_12_and_atr_20_finite_positive` |
| M5 | VOLATILITY | SHORT_FUTURE_RANGE | `behavior_future_range_atr_1` | 1 | 5 | continuous | median_difference | 1 | `target_future_valid_1_and_atr_20_finite_positive` |
| M5 | VOLATILITY | MEDIUM_FUTURE_RANGE | `behavior_future_range_atr_3` | 3 | 15 | continuous | median_difference | 1 | `target_future_valid_3_and_atr_20_finite_positive` |
| M5 | VOLATILITY | LONG_FUTURE_RANGE | `behavior_future_range_atr_12` | 12 | 60 | continuous | median_difference | 1 | `target_future_valid_12_and_atr_20_finite_positive` |
| M5 | VOLATILITY | MEDIUM_PATH_LENGTH | `behavior_path_length_atr_3` | 3 | 15 | continuous | median_difference | 1 | `target_future_valid_3_and_atr_20_finite_positive` |
| M5 | VOLATILITY | LONG_PATH_LENGTH | `behavior_path_length_atr_12` | 12 | 60 | continuous | median_difference | 1 | `target_future_valid_12_and_atr_20_finite_positive` |
| M5 | PATH | MEDIUM_PATH_EFFICIENCY | `behavior_path_efficiency_3` | 3 | 15 | continuous | median_difference | 1 | `target_future_valid_3_and_atr_20_finite_positive` |
| M5 | PATH | LONG_PATH_EFFICIENCY | `behavior_path_efficiency_12` | 12 | 60 | continuous | median_difference | 1 | `target_future_valid_12_and_atr_20_finite_positive` |
| M5 | PATH | LONG_DIRECTION_PERSISTENCE | `behavior_direction_persistence_12` | 12 | 60 | continuous | median_difference | 1 | `target_future_valid_12_and_atr_20_finite_positive` |
| M5 | PATH | LONG_DIRECTION_CHANGES | `behavior_direction_changes_12` | 12 | 60 | continuous | median_difference | 1 | `target_future_valid_12_and_atr_20_finite_positive` |
| M5 | PATH | LONG_EXTREME_ORDER | `label_extreme_order_12` | 12 | 60 | binary | P(+1 high-before-low \| feature_state) - P(+1 high-before-low \| baseline) | 1 | `target_future_valid_12_and_atr_20_finite_positive` |
| M5 | FIRST_PASSAGE | SHORT_FIRST_PASSAGE_0p5_ATR | `label_first_passage_0p5_1` | 1 | 5 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_1_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M5 | FIRST_PASSAGE | SHORT_FIRST_PASSAGE_1p0_ATR | `label_first_passage_1p0_1` | 1 | 5 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_1_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M5 | FIRST_PASSAGE | MEDIUM_FIRST_PASSAGE_0p5_ATR | `label_first_passage_0p5_3` | 3 | 15 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_3_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M5 | FIRST_PASSAGE | MEDIUM_FIRST_PASSAGE_1p0_ATR | `label_first_passage_1p0_3` | 3 | 15 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_3_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M5 | FIRST_PASSAGE | LONG_FIRST_PASSAGE_0p5_ATR | `label_first_passage_0p5_12` | 12 | 60 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_12_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M5 | FIRST_PASSAGE | LONG_FIRST_PASSAGE_1p0_ATR | `label_first_passage_1p0_12` | 12 | 60 | multiclass | P(+1 upper-first \| feature_state) - P(+1 upper-first \| baseline)<br>P(-1 lower-first \| feature_state) - P(-1 lower-first \| baseline) | 2 | `target_future_valid_12_and_atr_20_finite_positive_and_no_same_candle_first_passage_ambiguity` |
| M5 | MULTI_HORIZON | EARLY_TO_MID_INCREMENT | `behavior_early_to_mid_increment_atr` | — | — | continuous | median_difference | 1 | `multi_horizon_anchor_validity_and_atr_20_finite_positive` |
| M5 | MULTI_HORIZON | MID_TO_LATE_INCREMENT | `behavior_mid_to_late_increment_atr` | — | — | continuous | median_difference | 1 | `multi_horizon_anchor_validity_and_atr_20_finite_positive` |
| M5 | MULTI_HORIZON | PEAK_ABSOLUTE_DISPLACEMENT_HORIZON_INDEX | `behavior_peak_abs_displacement_hindex` | — | — | continuous | median_difference | 1 | `multi_horizon_anchor_validity_and_atr_20_finite_positive` |
| M5 | MULTI_HORIZON | FINAL_VS_PEAK_ABSOLUTE_RATIO | `behavior_final_vs_peak_abs_ratio` | — | — | continuous | median_difference | 1 | `multi_horizon_anchor_validity_and_atr_20_finite_positive` |
| M5 | MULTI_HORIZON | HORIZON_SIGN_CHANGES | `behavior_horizon_sign_changes` | — | — | continuous | median_difference | 1 | `multi_horizon_anchor_validity_and_atr_20_finite_positive` |

## Frozen policies

* **Multiclass:** fixed one-vs-baseline probability contrasts. Direction tests +1/up and -1/down; first passage tests +1/upper-first and -1/lower-first. Class 0 is reported but not independently screened. NaN is excluded, never converted to zero.
* **Continuous:** median difference is primary; mean difference and probability of superiority are descriptive only.
* **Binary:** absolute probability difference is primary; relative risk and odds ratio are descriptive only.
* **Baseline:** all target-valid rows from the same instrument, timeframe, and DISCOVERY period; candidate rows are a subset.
* **FDR family key:** `instrument|timeframe|discovery_method|target_family|target_role_or_horizon`.

## Safety attestations

* FEATURE→OUTCOME RELATIONSHIPS ANALYZED: NO
* REAL DISCOVERY RUN: NO
* INTERNAL CONFIRMATION ACCESSED: NO
* 2025 DATA ACCESSED: NO
* PROFITABILITY USED: NO
