# Optimization Level Rejection M5 — bounded frozen 2023 search

Current user authorization: this study only, one Draft PR, then STOP. Actual main
verified via git fetch and GitHub REST is e8312745c22539be3eeacd53bcc9e63aae30170f,
merge of #482. A/B/C completed with no qualifying candidate. Existing Roadmap,
PROJECT_CONTEXT, Master Strategy Registry, Queue, Level Rejection original
strategy/config/specification and frozen Baseline artifacts were inspected.
No earlier file is changed, including Roadmap and Registry historical snapshots.

## Complete grid and budget

Baseline values: Close reentry 1 historical tick; structural Stop buffer 1 tick;
maximum hold 120 calendar minutes; Take 3 FULL_NET_C1_R. Fixed six immediately
preceding completed valid positive-volume M5 bars within same day/session form
high/low levels. Test bar does not enter level until after its evaluation. Breach
at least one dated tick, completed Close back inside; lower rejection LONG,
upper rejection SHORT; both sides qualifying means ambiguous and no signal.
Directional confirmed-test START cooldown 30 minutes is consumed even if later
busy, time-limited, nonfill or data gap. Missing/invalid/nonconsecutive callbacks,
day/session boundaries reset range and dedup.

Enumerated before P&L: Close reentry [1,2] ticks, Stop buffer [1,2] ticks, hold
[120,60] minutes (half is exactly 12 M5 boundaries), Take [2,3,4,5,6,7,8,9,10].
Exactly 72 unique parameter tuples, stable IDs
LR_OPT2023_REENTRY{r}_SB{s}_HOLD{h}_TP{q}; GRID.csv and EVALUATION_MATRIX.csv
contain the full 72×3=216 evaluations. No incompatibility or duplicate detected;
no replacement values, adaptive trials, early abandonment or P&L-based changes.
Original min_close_reentry_ticks also governs future scalar Open reentry. This
parameter coupling remains explicit and preserved; it is not a new filter.

Instruments USDRUBF (Baseline 614 CLOSED/243 entry days/12 months), CNYRUBF
(213/99/11), GLDRUBF (128/70/6). These are Baseline observations, not expected
optimization counts. IMOEXF 22 CLOSED is excluded; its raw candles are excluded from Optimization and its independent audit.

## Fixed execution and R

Unchanged common Backtester, ENTRY_WAIT_ONE_BAR: test START T closes T+5, full
waiting M5 [T+5,T+10), conditional entry at observed Open T+10. Future Open alone
must persist inside by frozen reentry ticks; structural Stop is frozen completed
test Low minus buffer ticks for LONG, High plus buffer ticks for SHORT. Initial
adverse price risk must be positive and at least four entry-date ticks; Stop is
never shifted. One instrument/one position; no entry-bar Take; Stop-first and
adverse Open Stop gaps; no Take gap improvement. Hold is frozen 60/120 calendar
minutes or earlier exact 17:00 Open / one M5 before session end. Entry+35 minutes
must not exceed min(session end,17:00), equality allowed. Accepted holidays,
March extended lunch, daily/session resets retained. No indicator, MTF, trailing,
partial close, new filter or strategy replacement.

C1: one actual dated tick at entry and one at exit. Let s be initial gross
price risk; c=2*entry_tick is planned round-trip C1 (all fills/flat before CNY
19:00 tick change, hence planned same-tick cost justified). Target multiplier q
uses FULL_NET_C1_R: gross Take distance d=q*(s+c)+c, rounded outward on entry
historical grid (LONG ceiling, SHORT floor). Planned net/net R=(d-c)/(s+c).
An ordinary Stop at specified price loses s+c after C1, net/net Stop=-1; adverse
gaps can lose more. Actual cost=entry_tick+exit_tick. As in A/B/C, reporting
net_R_c1=(gross-actual_cost)/s and PF_R/DD/expectancy use this immutable initial
gross-risk denominator. Realized net/net R=(gross-actual_cost)/(s+actual_cost)
is separately recorded. No gross/net denominator is substituted by outcome.

DATA_GAP_SKIP_V2: missing/invalid execution Open => SKIP without fill or economics,
no day block. Missing/invalid filled exposure or forced-exit observation =>
EXCLUDED without fabricated exit/P&L, blocks remaining day. Later days explicitly
assume conditional FLAT. CLOSED, SKIP, EXCLUDED separate; accepted fills exactly
CLOSED+EXCLUDED. Missing waiting bar retains original NO_WAITING_BAR rejection.
Only conditional CLOSED economics; no complete annual return/equity claim.

## Frozen selection and neighbor topology

Per configuration/instrument: ≥100 CLOSED, ≥40 distinct CLOSED entry dates,
≥6 active CLOSED entry months. After C1 PF_R≥2 and PF_price≥2; positive Net
expectancy; ≥9 positive calendar EXIT months of all 12; conditional CLOSED DD≤20R;
largest winner≤25% of total positive trade R; largest profitable month≤50% of
sum of profitable monthly R. Missing/no-trade months cannot be profitable.
Metrics Decimal50 reductions from unchanged Decimal28 trade R. No tolerance,
rounding-to-zero or sign repair. No price pooling across instruments.

Immediate neighbor: exactly one grid coordinate differs by one published-list
index, all others equal, same instrument. Thus 120/60 and 1/2 are adjacent;
Take adjacent integers only. Each needs ≥100 CLOSED, PF_R≥1.5, positive Net
expectancy. At least two such neighbors mandatory. All criteria are conjunctions;
none may be relaxed. Rank full passes by positive months DESC, min(PF_R,PF_price)
DESC, DD ASC, CLOSED DESC, stable ID ASC. Diagnostic nonqualifying rows may be
shown under the same order, never nominated from PF alone.

## Source and pre-P&L controls

Only pinned read-only market-pattern-data f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8
2023 M5 prefixes, exact original blobs and byte/row budgets in policy. USDRUBF
2,342,431 bytes/42,576 rows; CNYRUBF 2,212,189/39,362; GLDRUBF 1,044,351/18,428.
All dates MSK, start-label M5. USDRUBF tick .01; GLDRUBF .1; CNY .01 before
2023-09-27 19:00 MSK then .001. No raw 2024+ bytes, no copying candles to Git.
Technical stage uses Git metadata, stored Baseline ledgers and synthetic bars.
The existing ActualMissingBars regression test reads the bounded 2023 prefixes
of all four instruments twice (stock and metadata-adapted suites) for timestamp
absence checks only: 209,590 candles /11,667,408 bytes; zero 2024+ bytes.
Optimization calculations read zero historical candles and calculate zero real
P&L before freeze. The earlier studies and their results are never rerun or changed.

Complete source/config/grid/criteria, independent audit code, tests and renderers
committed in a separate pre-P&L freeze commit. SHA256 dependency verification
checks working files AND actual commit bytes; remote GitHub recursive tree checks
all blobs before the real source opens. Every preexisting repository file has
protected SHA256 inventory. Published freeze must be ancestor of branch head.
Freeze includes all executable files and synthetic/regression evidence.

## Full results, replay and independent audit

One canonical 216-evaluation run and two full deterministic repeats with exact
artifact identity; no additional parameter trials. Three complete independent
audits. Journals sharded evaluations/<ID>/<instrument>/: signals, CLOSED trades,
SKIP, EXCLUDED, rejected/nonfill, days, coverage, metrics and parameters. Global
all_candidates.csv, 12-month and LONG/SHORT reports, funnel, all neighbor checks,
every failed gate, detail index and selection_report.json. Source provenance,
freeze_manifest.json, content-hidden syscall reads, validation and protected
scope receipts saved. No fabricated zero outcome for excluded trades.

Separate original strategy legacy replay with original parameters and execution;
compare every saved original signal/trade/day field, not just counts. Then V2
control REENTRY1/SB1/HOLD120/TP3: common credible CLOSED must match entry/Stop/
Take/exit/C1/P&L exactly; cohort differences from changed data-gap policy get
separate ID-level report and explicit cause. Old Baseline artifacts never change.

A separate auditor agent writes a standard-library batch prior-six-bar oracle,
independent chronological raw execution, metrics, coverage, neighbor and selection
checks. It imports no production strategy, execution, engine, loader, metrics or
study selector as computational reference. Synthetic corruptions must be caught
before P&L. Computational independent audit does not imply external human signoff.

Any all-gate candidate status is
PROVISIONAL_2023_OPTIMIZATION_LEVEL_REJECTION_CANDIDATE_PENDING_INDEPENDENT_AUDIT;
no passes yields NO QUALIFYING OPTIMIZATION LEVEL_REJECTION CANDIDATE. No economic
PASS from inadequate samples/unclosed trades. No R16/R17/R18/VWAP/Momentum,
Robustness, Walk Forward, TRUE OOS, LIVE/broker changes, merge or auto-merge.
