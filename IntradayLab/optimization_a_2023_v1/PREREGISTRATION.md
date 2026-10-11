# Optimization A — frozen bounded 2023 search, version 1

User authorization is the CODEX TASK for one Draft PR titled
`IntradayLab: Optimization A Equal High/Low 2023 — bounded frozen grid`.
Actual GitHub main was fetched and verified as
`ce89458b063f3af2451f8c4c162107207973c53b`. PR #474–479 are MERGED.
The newest Roadmap section and PR #479 allow separately authorized Optimization
after a negative fixed Baseline with sufficient audited closures. Older
positive-PF-only gates are superseded. No existing file is changed.

The policy JSON contains all parameters, exact grid, 144-evaluation budget,
selection limits, ranking and denominator definitions. GRID.csv contains all
72 deterministic IDs with every parameter. Both instruments receive the same
grid. Only touches 2/3/4/5, Stop buffers 1/2 and FULL_NET_C1_R targets 2–10 vary.
No adaptive step, new variant, additional filter or directional selection.

The new strategy parameterizes the A_v1 streaming equal-extreme grammar. It
retains first qualifying completed-bar consumption for the maximal run,
ambiguous-side rejection and gap/session/day/tick resets. New runner uses the
unchanged Backtester and opt-in DATA_GAP_SKIP_V2. Actual Open admission never
uses that candle's High/Low/Close or moves a structural Stop. Allowed historical
day windows, March lunch exception, holidays, session flat, conservative Stop
precedence, no entry-bar Take and 120-minute limit remain unchanged.

USDRUBF tick is .01. CNYRUBF tick is .01 until 2023-09-27 19:00 MSK, then .001.
Gross Take distance is `R*(initial gross risk + 2*entry tick)+2*entry tick`,
rounded outward. Realized costs are dated entry plus exit ticks. Gross-risk
Net R, planned net/net R and realized net/net R have separate ledger columns.

Source commit, two original Git blobs, byte prefixes, rows and SHA-256 are
copied from the approved A_v1 manifest without opening source candles.
Research is 2023-01-01 inclusive through 2024-01-01 exclusive, MSK. The original
loader reads exactly the approved prefix with unbuffered FileIO. A Python guard
checks actual reads; independent LF-budget reading reconstructs input separately.
Validation also observes Linux source-file read syscalls, including descendants,
and verifies each reader's exact byte ceiling. No raw OHLC is copied into Git.

Missing entry Open is SKIP, without entry/cost/P&L/later fill. Missing evidence
after fill is EXCLUDED with preserved entry and unknown exit. Remaining same-day
entries are blocked; subsequent days have conditional FLAT only. CLOSED trades,
SKIP, EXCLUDED, REJECTED/NONFILL and coverage are separate. Accepted IDs must
equal the disjoint union of CLOSED and EXCLUDED IDs. No skip/exclusion economics.

Per configuration/instrument sample gate: ≥100 CLOSED, ≥40 distinct MSK entry
dates, ≥6 CLOSED entry months. All subsequent criteria are study-specific:
both after-C1 PF R/price ≥2, Net expectancy >0, ≥9 positive exit months, conditional
CLOSED-only DD ≤20R, largest positive trade ≤25% of positive R and largest
positive month ≤50% of positive monthly R. Ideal 12/12 is shown separately.
At least two immediate adjacent neighbors require ≥100 CLOSED, positive
expectancy and PF R ≥1.5. This is local 2023 diagnosis, not Robustness.
Only fully passing candidates are ranked, separately by instrument, by positive
months descending, minimum of two PF descending, conditional DD ascending,
CLOSED descending, deterministic ID ascending. All failures remain published.
No-loss PF is NOT_AVAILABLE, never infinity. Registry Decimal reporting
tolerance 1e-20 handles arithmetic remnants in zero monthly sign only.

The auditor is a separate standard-library-only implementation. It scans raw
backward maximal-run slices and forward execution paths; no strategy,
Backtester, execution, loader, metrics or optimizer selection imports. It
rebuilds all 144 signal and economic evaluations, coverage, every 12-month and
direction table, neighbors, candidate checks and ranks. Mutation tests detect
forged paths and economics. Legacy comparator replay independently reconciles
saved A_v1 T3/SB1/TP3 signals/trades; V2-only differences are explicitly paired.

Before P&L: synthetic tests, source metadata/admission reconciliation, all code,
grid, policy, reporting, runner, auditor, validation orchestrator, test logs and
dependency SHA-256 are committed in a separate freeze. No historical candles
are opened during this preparation. After freeze: canonical complete 144,
two complete 144 repeats with byte comparison, then independent full audit.
Any computation correction requires an explicitly documented new freeze and
complete reruns; no silent or selected correction.

Incomplete data prevent claims of complete annual PF/return, continuous equity,
broker Max DD or pooled price P&L. Internal algorithm audit is not external
human review. A passed configuration remains PROVISIONAL, pending independent
review. No qualifying settings means NO QUALIFYING OPTIMIZATION CANDIDATE.

Every preexisting repository file, including all Baselines, registry and
TradingSystemLab, is protected by byte hashes. Draft #472 stays at
`82ec9ffe61e18a43cd7510e398f6913b25f045e1`. No source mutation, 2024+ candle
read, other family, new stage, Robustness, WF, TRUE OOS, LIVE, merge or auto-merge.
STOP immediately after creating the one Draft PR.
