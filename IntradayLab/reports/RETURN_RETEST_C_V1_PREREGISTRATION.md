# RETURN_RETEST_REJECTION_M5 — C_v1 preregistration, 2026-10-11

One fixed Baseline, approved by the current user task. Base main is
f0e56f5df557ac4eae19af333b6d438524f5f6ff, merged #477. This task supersedes
historical STOP-before-C and positive-Baseline-only Optimization gates;
it authorizes no Optimization or subsequent stage.

## Causal construction fixed before historical P&L

Only completed valid M5 from one research window, day and historical tick.
SHORT first High is strictly greater than all five immediately preceding Highs;
LONG first Low strictly smaller than those five Lows. Equal extrema do not
establish a new local level. The five are consecutive, valid, same-window,
same-day and same-tick. Strictness resolves the otherwise unspecified local
extremum convention before any returns. No retrospective pivot confirmation.

One greedy active construction per side. An already active level takes priority
over newer local extrema. The first observed level never moves. Repeated touches
use the candle High (SHORT) / Low (LONG), within inclusive +/-2 ticks. Between
approaches the first completed bar with High <= level-3 ticks (SHORT), or
Low >= level+3 ticks (LONG), arms the next approach. Record that witness and its
whole-bar depth; repeated retreat bars do not arm multiple approaches. A zone
bar can count only after this retreat. Adjacent zone bars cannot count as
independent approaches. Retreat and touch conditions are disjoint.

The first zone bar of approach three is the only candidate signal candle:
Close <= first level-1 tick for SHORT; Close >= first level+1 tick for LONG.
Failure gives THIRD_CLOSE_NOT_REJECTED and consumes the construction. Both
qualified directions on the same close give AMBIGUOUS_BOTH_SIDES; consume both.
There is at most one candidate per construction, irrespective of fill/refusal.
A consumed construction continues to occupy its side until structural reset;
no fourth-approach retry and no re-entry after an execution refusal.

Valid lifetime is first bar through bar 24 inclusive; before processing bar 25
expire. A strict outward break (High > level+2 ticks SHORT; Low < level-2 ticks
LONG) resets before evaluating that bar as a possible new first. Expiry also
allows a new first on the current bar using only its preceding five. Gaps,
invalid bars, session/day changes and tick changes clear active levels and
five-bar history. Session change is observed at the close of the first bar of
the next window; day end clears after the last callback. Construction event
receipts contain FIRST / RETREAT / SECOND / THIRD / RESET, including unfinished
and consumed constructions. FIRST/SECOND/THIRD are directional counts.

## Execution, unchanged common Backtester

ENTRY_NEXT_OPEN and DATA_GAP_SKIP_V2. Signal Close and immediate next M5 Open
share the same boundary. Only that scalar Open is used for entry admission.
SHORT Stop is maximum observed High of every bar first through third +1 tick;
LONG Stop is minimum observed Low -1 tick. Reference for displacement is that
observed outward construction boundary, not the abstract tolerance edge.
Open must be on the rejection side; risk 3..12 ticks; displacement 0..4 ticks.
No Stop movement, delayed entry, indicators, MTF, filters, trailing or Oracle.
These unchanged bounds jointly imply effective same-grid risk 3..5 ticks.
The redundant 12-tick upper cap is retained for comparison, not tuned.

FULL_NET_C1_R=3: gross Take distance is 3*(risk+2*tick)+2*tick = 3*risk+8*tick,
rounded outward on the entry grid. Net R in the ledger uses gross initial
price risk; planned net-win/net-Stop-loss is separately 3. Realized C1 uses
one dated tick at each side. Maximum hold 120 calendar minutes; earlier
session-flat Open one M5 before window end. Stop-first including conflicts,
adverse Stop gap at actual Open, no Take on entry bar, one position/instrument.
An invalid/missing entry Open is a counted SKIP. After an observed fill,
unverifiable exposure/exit is EXCLUDED with no exit or P&L, same-day block;
subsequent independent days disclose conditional, unproven FLAT. trades.csv
contains only CLOSED. Accepted entries must reconcile by ID with CLOSED plus
EXCLUDED. No excluded outcome counts as zero or as a known loss/profit.

## Data and freeze

Read-only market-pattern-data pinned f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8.
Only four exact previously authenticated M5 byte prefixes of 2023; unbuffered
bounded readers guard both runner and independent auditor. Never read 2024+
OHLC even for metadata or auxiliary computations. USDRUBF/CNYRUBF start Jan 3,
GLDRUBF Jul 11, IMOEXF Nov 14. CNY tick changes 0.01 -> 0.001 on Sep 27 19:00
MSK; preserve the common calendar/windows and dated lunch exception.

Before first historical P&L: strategy/config/runner/auditor/tests/guards and
this preregistration committed together, with SHA-256 dependencies and source
receipts. Technical preflight scans signals and actual next Opens only; no
historical position paths, exit metrics or P&L. Synthetic P&L fixtures are
allowed for technical validation. After freeze one complete 2023 Baseline,
plus two full identical verification repeats, never a parameter search.
Trading dependencies and audit/report code must equal the pre-P&L commit.
Any defect after historical P&L requires explicit disclosure and new version;
no silent repairs to improve PF.

## Reporting and decision

All 12 months per instrument and pooled normalized R only; price PF per
instrument, no mixed price PF or account-return/continuous-equity claim.
Report first/second/third counts, direction signals, refusals, fills,
CLOSED/SKIP/EXCLUDED, gross/cost/net R, conditional PF R/price, mean win/loss,
WR/expectancy, exit attribution, trade days/active months, source inception
and coverage, pullback/separation/width/Stop geometry, observed DD of known
closures, concentration and exclusion shares. Months before inception are
NO_COVERAGE, not observed zero-return months. Incomplete outcomes may bias PF.

Technical PASS, resolved sample breadth, conditional economics, data
sufficiency and prospective Optimization suitability are separate findings.
Initial PF <2 or negative expectancy does not itself disqualify family C
under the latest Roadmap. Common minimum sample/month eligibility for future
Optimization is not chosen here. Archived A_v1/B4/B7/B10 are different signal
constructions with historical UNKNOWN; compare their immutable reports and
signal overlaps without stacking overlapping signals as independent trades.

Independent auditor reconstructs raw constructions, resets, paths, next Open,
Stop/Take/C1, CLOSED/SKIP/EXCLUDED, fill identity, arithmetic, calendar and
coverage without importing production strategy/Backtester/loader/metrics.
This is an independent implementation by the task author, not external
human signoff or a second agent. Synthetic corruption fixtures test it.

Only new IntradayLab files and current-status additions to the three project
documents. Common core, frozen A/B, all previous results, TradingSystemLab,
source checkout, live robot/accounts/capital and separate Draft #472 immutable.
Separate Draft PR; no merge/auto-merge. STOP after Baseline C.
