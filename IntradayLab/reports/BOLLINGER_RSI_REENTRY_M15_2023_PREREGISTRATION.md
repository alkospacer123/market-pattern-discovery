# BOLLINGER_RSI_REENTRY_M15 — fixed 2023 Baseline contract

Registered before the first market P&L on the exact main
`a63581a6942974ff7d636387d2ceb23893303096` (Merge #471). PR #467–471 merged:
`b6baeed4c98967f8b7ccb61cb695952a8a8fbcd9`,
`c18ec04a450bb973c4d19b5ce93c4e56448419ab`,
`69fdcfa0b79c6eac5739306f7b6cf7fefe09dae2`,
`0663fac5389ecfd65b6c7d21686856eb3e59fb87`,
`a63581a6942974ff7d636387d2ceb23893303096`.
The local checkout initially lagged at #468; fetched main was the expected HEAD.
The task branch starts at fetched main and preserves all existing files.

## One fixed hypothesis

Standalone M15 Bollinger/RSI re-entry, both LONG and SHORT, no MTF or additional
filter. Bollinger20 includes the current completed Close: SMA20 ± 2 population
standard deviations (ddof=0). Wilder RSI14 seeds the average gains and losses
from the first 14 real close changes, then updates `(13 × previous + change)/14`.
If both averages are zero RSI=50; if only losses are zero RSI=100; if only gains
are zero RSI=0. Bollinger is not ready before 20 real completed Close observations;
RSI is not ready before 14 real changes. Both must be ready on B and C.

Only existing `aggregate_m15` parents made of three real valid consecutive M5
are observations. Parents align to MSK calendar quarter hours, start/close labels
are explicit, and partial session-edge parents are excluded. Indicator history
explicitly crosses approved calendar sessions and days; scheduled breaks add no
synthetic observations. Every missing/invalid expected full M15 slot clears all
indicator warm-up, requiring 20 new valid Close observations. Only real 2023
parents within the existing research windows warm indicators; no before-2023,
future, native-M15 or outside-window substitute is introduced.

B and C are adjacent calendar M15, same research day and same approved window:

- LONG B: `Close_B < Lower_B` and `RSI_B ≤ 35`. C: its Close is inclusively
  inside its own current bands and `RSI_C > RSI_B`.
- SHORT B: `Close_B > Upper_B` and `RSI_B ≥ 65`. C: its Close is inclusively
  inside its own current bands and `RSI_C < RSI_B`.

No B/C carry across lunch, day, source gap or incomplete observation. Each
snapshot is computed at its own Close; the later C never recalculates B. At C
Close, Stop is fixed to `min(Low_B, Low_C) − tick_C` for LONG, or
`max(High_B, High_C) + tick_C` for SHORT. A candidate expires after its immediately
next observation. Every expected decision, warm-up refusal, B rejection,
C rejection and engine admission/refusal is logged in signals.csv.

## Unchanged common execution

Existing core Backtester receives timeframe_minutes=15. C Close → one complete
waiting D → next E Open. Example B 15:00–15:15, C 15:15–15:30,
D 15:30–15:45, E entry at observed Open 15:45. Entry Open checks the historical
price grid, adverse Stop side and minimum risk of four entry-date historical
ticks. No entry dependence on future E High/Low/Close/Volume.

FULL_NET_C1_R=1.5. With gross initial price risk s and historical entry tick t,
unrounded target distance is `1.5 × (s + 2t) + 2t = 1.5s + 5t`. Shared outward
rounding uses LONG ceiling / SHORT floor. C1 charges one actual dated tick per
entry and exit; the unchanged gross-risk R metric and separate full net/net R
are retained. No entry-bar Take; Stop-first, adverse Open Stop gap and scheduled
Open exits are the unchanged shared model.

One pending/open position per instrument. Hold ≤120 calendar minutes. Mandatory
flat is the earlier of the shared last full session M15 Open (13:45 AM or 18:30
PM) and 17:00. Planned entry needs ≥35 minutes to that actual flat, preserving
the existing March calendar exception. No holding through a break/day.
Calendar-only admissible slots are frozen in config/*_reachability.json before P&L.

Missing/invalid waiting rejects before order. Missing entry Open is UNKNOWN
possible fill; observed first Open with incomplete parent may fill and then have
UNKNOWN path. Missing exposed/exit prices do not become a closure or zero P&L.
UNKNOWN blocks its research day; subsequent days only conditionally assume FLAT,
with the existing persistent prior-UNKNOWN flag. No continuous annual equity claim.

## Source, freeze and acceptance

Read-only `alkospacer123/market-pattern-data` commit
`f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; only the four
`forever/{instrument}/{instrument}_M5.csv` original exact SHA-256-verified
2023 byte prefixes. Existing verified loader and an independent LF-budget reader
consume zero price bytes 2024+. Repeat validation also records actual read offsets
and rejects any request beyond each approved prefix. Historical ticks/calendar
are copied unchanged; CNY 0.01→0.001 at 27 September 2023 19:00 MSK.
GLD starts 11 July, IMOEX 14 November: no fabricated full-year coverage.

All new strategy, config, runner, oracle, validator, tests and documentation are
committed before first market P&L. Config SHA-256 and executable research hashes
are sealed beforehand; the creation commit SHA is resolved from Git and recorded
in result provenance. They remain unchanged after P&L.

The classification_policy is copied verbatim from PR #471: complete coverage and
outcomes required; ≥30 CLOSED, ≥15 unique trade days, ≥3 active/positive months,
≥60% positive active months, positive C1 expectancy, price and R PF ≥1.6,
largest winner share ≤25% and largest positive month share ≤50%. Incomplete
coverage/outcomes gives INCONCLUSIVE, with separate conditional known-close
economic diagnosis. Negative known expectancy is NO ECONOMIC BASELINE PASS.
No positive subset can silently replace the declared four-instrument/both-side
hypothesis. Months without quotes are NO_COVERAGE; zero-trade months are not positive.

Independent oracle imports no production strategy, indicators, loader, engine
or metrics. Population variance uses 80-digit E[x²]−E[x]²; RSI uses the weighted
expansion of real changes. Indicator comparison alone permits absolute 1e-22
Decimal rounding error; discrete decisions, prices, clocks and trade accounting
must match exactly. Corruption tests must detect falsified indicator/Stop/Take/
entry/exit/C1/P&L facts. All CLOSED/UNKNOWN and all 12 monthly/direction/instrument
cohorts are checked. Two full identical repeats are deterministic verification
of this same Baseline, not additional parameter trials. Old Baselines are replayed
and their stored bytes remain immutable.

All additions remain inside IntradayLab; common core and every existing file
remain byte unchanged. No market-pattern-data mutation or production/broker
change. Stop after one Draft PR without merge. Optimization, Robustness,
Walk Forward, TRUE OOS and LIVE are not performed.
