# Candidate Baseline v1

- **Status:** `RESEARCH_CANDIDATE`
- **Experiment version:** `Candidate Baseline v1`
- **Experiment date:** `2026-09-15`
- **Parameter source:** `Optimization R2` (`PARAMETERS_STABLE`, conservative representative of the three-combination stable region)
- **Configuration SHA-256:** `1be187b9dad663cb8864f4701b97343ad4c9a5923b06bfc2c319432f00ce6b0b`
- **Intended next stage:** Robustness testing only

## Research boundary

This is a separate research candidate, not a new Baseline. The Frozen Baseline,
BBW trading logic, Optimization R2, and its evaluator were not changed. This
candidate has not passed Robustness, Walk Forward, or TRUE OOS validation and
must not be used for trading.

The repository path `results/candidate_baseline/v1` is the portable equivalent
of the requested Windows artifact path `C:\BBW\results\candidate_baseline\v1`.
`CANDIDATE_CONFIG.json` is byte-for-byte identical to
`config/bbw_candidate_v1.json`, so either file supplies the same deterministic
Robustness input.

## Parameters

```json
{
  "atr_max": 3.0,
  "atr_min": 1.0,
  "bbw_period": 10,
  "bbw_std": 1.5,
  "ema_period": 20,
  "ema_slope_threshold": 0.0,
  "penetration": 0.2,
  "range_max_bars": 40,
  "range_min_bars": 3,
  "retest_max_bars": 30,
  "retest_min_bars": 3,
  "squeeze_window": 5
}
```

## Difference from Frozen Baseline

| Parameter | Frozen Baseline | Candidate v1 |
|---|---:|---:|
| `atr_max` | 2.0 | 3.0 |
| `atr_min` | 1.0 | 1.0 |
| `bbw_period` | 10 | 10 |
| `bbw_std` | 2.0 | 1.5 |
| `ema_period` | 50 | 20 |
| `ema_slope_threshold` | 0.001 | 0.0 |
| `penetration` | 0.2 | 0.2 |
| `range_max_bars` | 30 | 40 |
| `range_min_bars` | 6 | 3 |
| `retest_max_bars` | 30 | 30 |
| `retest_min_bars` | 5 | 3 |
| `squeeze_window` | 10 | 5 |

The candidate differs on seven parameters. Unchanged values do not imply a
Baseline promotion; the two configurations retain separate identities and
purposes.
