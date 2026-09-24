# TradingSystemLab v2 Phase 3 Candidate Freeze Report

**Status:** `PHASE_3_CANDIDATE_FREEZE_COMPLETE`

This artifact-only freeze applies the original H1 Phase 3.3 predeclared-candidate
contract to committed Phase 2 Development evidence. The four identities were
declared before validation. No metric ranking, parameter search, market-data
read, strategy execution, Robustness, Walk Forward, or TRUE OOS access occurred.

## T2 / M30 — `T2_M30_candidate_v2`

- Phase 2 configuration: `T2-M30-7c89b4a215cd`
- Change from Baseline: `adx_threshold: 20 → 25`
- Phase 2 membership: `ROBUST_PLATEAU`
- Evidence: 982 trades; PF_C1 1.38439307062; expectancy_C1 0.179005404674;
  net_R_C1 175.783307389; max_DD_C1 -33.5282069751; recovery_factor_C1
  5.24284843266.
- Balance: all six instruments and all Development years 2020–2024 have
  positive C1 expectancy; LONG and SHORT expectancy are positive.
- Parameter hash: `7c89b4a215cd8b68f96de2fc0938c2b99e755158b919a1284dfc07c6c2547ac6`
- Predeclared reason: cross-instrument/year balance within an independently
  verified stable region, not maximum-PF selection. Its drawdown is somewhat
  larger than T2/M30 Baseline drawdown; it does not dominate every metric, and
  no plateau member combines all-six-instrument positivity with lower drawdown.

## T2 / H1 — `T2_H1_candidate_v2`

- Phase 2 configuration: `T2-H1-a98459cab4f2`
- Change from Baseline: `ema_fast: 20 → 25`
- Phase 2 membership: `ROBUST_PLATEAU`
- Evidence: 649 trades; PF_C1 1.49070753729; expectancy_C1 0.224423840621;
  net_R_C1 145.651072563; max_DD_C1 -14.9346837251; recovery_factor_C1
  9.75253813499.
- Balance: every Development year is positive; five of six instruments are
  positive, with the sole weak negative near zero; LONG and SHORT are positive.
- Parameter hash: `a98459cab4f22e598fbfd705fb60cfb8a65f1771fa7d903bafa581544faa35ea`
- Predeclared reason: balanced plateau evidence and lower absolute drawdown
  than Baseline, not maximum-PF selection and without future/validation data.

## T3 / M30 — `T3_M30_candidate_v2`

- Phase 2 configuration: `T3-M30-0050d828c1a8`
- Change from Baseline: `ema_period: 100 → 75`
- Phase 2 membership: `ROBUST_PLATEAU`
- Evidence: 1581 trades; PF_C1 1.36261268342; expectancy_C1 0.162875006507;
  net_R_C1 257.505385288; max_DD_C1 -22.5343558886; recovery_factor_C1
  11.4272352208.
- Balance: all six instruments and all Development years are positive; LONG
  and SHORT expectancy are positive.
- Parameter hash: `0050d828c1a8628621f63de1c88fc7bb67fa686d72767732998f6767b1eed8bc`
- Predeclared reason: balanced plateau evidence and lower absolute drawdown
  than Baseline, not maximum-PF selection and without future/validation data.

## T3 / H1 — `T3_H1_candidate_v2`

- Phase 2 configuration: `T3-H1-aeeb96942cf3`
- Change from Baseline: `atr_average_period: 20 → 30`
- Phase 2 membership: `ROBUST_PLATEAU`
- Evidence: 714 trades; PF_C1 1.46328578667; expectancy_C1 0.203160457152;
  net_R_C1 145.056566406; max_DD_C1 -16.2129477802; recovery_factor_C1
  8.9469582196.
- Balance: all six instruments and all Development years are positive; LONG
  and SHORT expectancy are positive.
- Parameter hash: `aeeb96942cf33d9551b5635f33d2f2745aefad572f57f7ea92b9791c2d992a39`
- Predeclared reason: balanced plateau evidence and lower absolute drawdown
  than Baseline, not maximum-PF selection and without future/validation data.

## Historical H1 comparison (provenance only)

The historical T2 candidate `T2-0007-608dc87d09f1` changed
`max_initial_stop_atr` to 2.5. Both selected v2 T2 changes differ. The
historical T3 candidate `T3-0014-0050d828c1a8` changed `ema_period` to 75:
T3/M30 uses that same value but was independently frozen from current v2
plateau/balance evidence; T3/H1 differs. This comparison did not affect any
selection.

## Lifecycle lock

Parameters are immutable for Phase 3. Robustness must consume exactly the
registry in this directory. A weak result cannot authorize replacement or a
second plateau member; any parameter change requires a new identity and return
to an earlier research stage. TRUE OOS 2025+ remains sealed.
