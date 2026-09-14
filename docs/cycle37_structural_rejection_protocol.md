# Cycle37 structural rejection family — frozen protocol

This document freezes Cycle37 before engine implementation. Its sole question is:
**does rejection from independent structural levels produce repeatable high-R
edge?** It is a family-mining experiment, not an optimization of Cycle29 or
Cycle36. `ROUND`, `ROLL30`, `ROLL60`, and `PREVIOUS_DAY_HIGH_LOW` are separate
families; results may never be combined with `OR` logic.

## Causal level and signal contract

All timestamps are Europe/Moscow. A setup bar labelled by its M5 open becomes
observable only at `open + 5 minutes`. Levels used by that bar are frozen from
strictly earlier information:

* `ROUND`: every integer multiple of the instrument's configured round step.
* `ROLL30` / `ROLL60`: the high and low of the preceding 30 / 60 completed M5
  bars in the same Moscow trading day. The setup bar is excluded and an
  incomplete window produces no level.
* `PREVIOUS_DAY_HIGH_LOW`: high and low of the immediately preceding trading
  day present in the data. The current day's observations are excluded.

For each level, LONG tests support (the low side) and SHORT tests resistance
(the high side). Exact comparisons are used (no tunable proximity threshold).
The four frozen rejection predicates are:

* **wick rejection:** the wick touches/crosses the level, the body remains on
  the expected side, and the close is on that side;
* **close rejection:** the bar opens beyond/on the adverse side and closes on
  the expected side;
* **sweep reclaim:** the bar trades strictly beyond the level and closes
  strictly back on the expected side;
* **failed breakout:** the prior completed M5 close is strictly beyond the
  level and the setup close returns strictly to the expected side.

LONG reverses each SHORT inequality. A zero-body candle satisfies neither the
body-side wick predicate nor a directional open/close crossing. When several
eligible levels exist, choose minimum distance from setup close, then LOW
before HIGH, then numeric level. Candidate identity includes exactly one
structure, one direction, one rejection type, one session, one stop, and one
target.

## Execution and scoring

Selection is January–February 2026 only. Forward validation is March 1 through
May 15 inclusive. Calendar 2025 is locked TRUE OOS and must never be loaded.
Signals are accepted from 09:00 through the session end inclusive; entry is the
first M1 open at or after M5 completion and never the setup close. Positions
are forced out at the last M1 close no later than the configured session end.
There is one position at a time per candidate. Stops are fixed configured ticks
from entry and targets are fixed R multiples. If stop and target occur in one
M1 bar, stop wins. Gaps fill adversely at the M1 open. Costs and slippage are
charged per side using the frozen manifest defaults and are doubled in stress.

All configurations are enumerated once; discovery does not adapt the grid.
Shortlisting requires selection BASE PF >= 2.0 and N >= 30. A survivor must
also pass forward BASE PF/N, forward STRESS PF >= 1.5 and N >= 20, a strictly
positive 2.5% trade-bootstrap bound (2,000 samples, seed 370037), and positive
net R independently in March, April, and May 1–15. It must have a positive-net-R
forward neighbor in the same structural family differing by one adjacent grid
value (stop, target, or session); direction and rejection type stay fixed.
Profit factor with no losses is serialized as `null` plus an explicit infinity
flag. Empty samples fail every gate.

Artifacts are written below `results/cycle37_structural_rejection_family/`.
Each instrument receives `run_manifest.json`, `generated_candidates.json`,
`shortlist.json`, `survivors.json`, and `report.md`; `cycle37_summary.json` is
global. Source files remain read-only and only their paths, hashes, and row
ranges are recorded.
