# Autonomous Profitable Candidate Registry

This directory is the persistent research registry requested for the autonomous strategy-discovery project. Positive candidates are retained even when they fail the strict research-survivor gate; they are never silently discarded or relabeled as confirmed systems.

## Safety fences

- 2025 TRUE OOS remains **SEALED** and is not part of this registry's discovery evidence.
- The retired interval `2026-05-16` through `2026-07-01` must not be reused for discovery, ranking, filtering, or confirmation.
- New Cycles 14–18 used only the permitted research prefix `2026-01-05 <= t < 2026-05-16`.
- A strict research survivor still requires genuinely fresh untouched data before any promotion beyond research status.

## Retention rule

For Cycles 15 onward, retain every frozen candidate with:

- at least 10 executed trades;
- BASE profit factor > 1.0;
- positive BASE expectancy.

The strict research-survivor gate is separate and much stronger: BASE PF >= 2.00, STRESS PF >= 1.50, positive BASE/STRESS expectancy, N>=30, >=15 trading days, >=3 positive BASE months, >=2 positive STRESS months, largest BASE winner share <=0.25, and monotonic GROSS >= BASE >= STRESS total PnL.

## Current inventory

| Source | Retained profitable candidates | Strict research survivors | Notes |
|---|---:|---:|---|
| Legacy V4 DEV-positive registry | 17 | 0 | Historical research candidates; previously selected V4 systems retain their historical validation/rejection status. |
| Cycle 15 — prior-day sweep/reclaim | 16 | 0 | Weak friction-sensitive cluster. |
| Cycle 16 — compression breakout | 27 | 0 | Stronger positive cluster; best BASE PF about 1.50. |
| Cycle 17 — opening-range breakout retest | 43 | 0 | High-priority near-survivor; best BASE/STRESS PF about 1.75/1.41. |
| Cycle 18 — opening-range false-break fade | 38 | **1** | First candidate to pass every preregistered strict research gate. |
| **Total** | **141** | **1** | |

## Current strict research survivor

`C18-d67edca2d39566f5`

Frozen parameters:

- `buffer_atr=0.30`
- `reclaim_bars=1`
- `inside_ticks=2`
- `target_r=1.5`
- `max_hold=60`

Research-prefix result:

- N=36, 33 unique trading days;
- BASE PF=2.331313, expectancy=+5.295450 bps;
- STRESS PF=1.778669, expectancy=+3.518578 bps;
- four positive BASE months and four positive STRESS months;
- largest BASE winner share=0.124938;
- LONG=18 / SHORT=18;
- independent trade-by-trade integrity recheck passed.

This status is **RESEARCH_SURVIVOR**, not production-ready and not confirmed out-of-sample. The frozen-grid neighborhood is positive but the strict pass is not a broad plateau, so parameter-selection risk remains material.

## Files

- `legacy_v4_dev_positive.csv` — historical V4 DEV-positive candidates retained without rewriting their later validation status.
- `cycle15_profitable.csv`
- `cycle16_profitable.csv`
- `cycle17_profitable.csv`
- `cycle18_profitable.csv`

Cycle-level protocols and result reports live one directory above. The current scientifically valid stopping point is Cycle 18: freeze the survivor and obtain genuinely fresh untouched data rather than consuming 2025 TRUE OOS or the retired May16–Jul1 interval.