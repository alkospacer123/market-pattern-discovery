# Optimization C — bounded frozen USDRUBF 2023 search

Authorized by the current user task. Base is actual GitHub main
297137fe17f0de851976ea26180fac441f2ada6e (Merge #481).
All preexisting repository files are immutable. No TradingSystemLab, production,
market-pattern-data, A/B, Master Registry or Draft #472 mutation.

Exactly 288 unique configurations, enumerated in GRID.csv and EVALUATION_MATRIX.csv.
IDs are C_OPT2023_APP{2,3}_LOOKBACK{3,5}_TOL{1,2}_MAXBARS{24,36}_SB{1,2}_TP{2..10}.
No additional values, strategies, filters, algorithms or adaptive trials.
OPTIMIZATION_C_POLICY.json publishes all fixed/variable parameters, execution,
source bytes, sample/economic gates, adjacent-list-index neighbors and deterministic
ranking before any historical P&L. One canonical search, two full repeats and
three complete implementation-independent audits; repeats add no parameter trials.

New strategy preserves the C_v1 state machine: completed M5; strict causal local
extreme from contiguous prior lookback bars within day/window/tick; first level
immutable and one active construction per side. The first retreat witness must
precede a new zone-touch bar. Retreat 3 ticks; inclusive tolerance; adjacent touches
without retreat do not increment. First approach is the original extreme.
SECOND is final for APP2, THIRD for APP3. Final first touch Close must reject at
least one tick; failed Close consumes without retry. Both qualified sides reject
as AMBIGUOUS_BOTH_SIDES. Consumed state remains until structural reset. Lifetime
includes first; bar limit+1 expires before processing and may start causally anew.
Strict outer break may restart from current completed local extreme. Reset on
missing/invalid/gap/session/day/tick. Full FIRST/RETREAT/SECOND/THIRD/RESET receipts.

Stop is observed construction max High/min Low through final approach plus/minus
buffer. Actual immediate next Open must satisfy wrong-side/risk 3..12/displacement
0..4 admission. Never shift Stop or delay fill. Unchanged Backtester,
ENTRY_NEXT_OPEN, DATA_GAP_SKIP_V2, one dated tick per side C1, no entry-bar Take,
Stop-first and adverse Open gaps, one position, 120 calendar minutes and earlier
one-M5-before-window-end flat boundary. FULL_NET_C1_R target uses
R*(gross risk + planned round-trip C1)+planned round-trip C1, rounded outward.
Raw initial-risk Net R, planned net/net R and realized net/net R remain separate.

Only read-only pinned f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8 source
forever/USDRUBF/USDRUBF_M5.csv. Unbuffered exact 2,342,431-byte prefix, 42,576
candles, SHA256 047de8fbc74fbe98028cd236b67bf11823b4e6b9f79a6488113a1d0f43947e1d.
Tick .01; 2023-01-01 <= MSK candle_time < 2024-01-01.
No other raw instrument or 2024+ candle read. Preflight uses synthetic candles
and Git/source metadata only: zero historical candles and zero historical P&L.
Guard verifies complete dependencies, SHA256 and Git bytes, published freeze
ancestry and all dependency blob IDs via actual GitHub API before raw source load.
Content-hidden strace verifies exact physical source prefix reads for all six
runner/auditor processes; deterministic receipts and logs are published.

Sample 100 CLOSED /40 MSK entry dates /6 CLOSED entry months. Economics both
PF R and PF price >=2, expectancy >0, >=9 positive exit months of 12,
CLOSED-only conditional DD <=20R, largest winner <=25% positive trade R,
largest positive month <=50% positive month R. At least two one-parameter
one-published-index-step neighbors: 100 CLOSED, PF R >=1.5, expectancy >0.
LOOKBACK3/5 and MAXBARS24/36 are direct neighbors. Rank only all-gate passes:
positive months DESC, min(PF R,price) DESC, DD ASC, CLOSED DESC, ID ASC.
Missing/no-trade months cannot supply positive evidence. Aggregation Decimal50
from immutable Decimal28 trade fields; exact audit with no numerical sign repair.

Missing next Open is SKIP with no fill/P&L. Unresolvable filled exposure is
EXCLUDED with no exit/P&L/zero substitution, blocks remaining day; later days
are explicitly conditional FLAT. Accepted IDs = CLOSED + EXCLUDED IDs.
Ordinary trades.csv contains only CLOSED. Report exclusions and conditional
coverage apart from economics; no full-year account-profit claim.

Historical control APP3/LOOKBACK5/TOL2/MAXBARS24/SB1/TP3 must compare every saved
column and row order of signals, constructions, CLOSED, SKIP, EXCLUDED, days and
coverage to original C_v1 USDRUBF. Expected 102 CLOSED /2 SKIP /2 EXCLUDED.
Any discrepancy prevents PASS; original Baseline is never altered.

Independent auditor is a separate standard-library-only batch span/local-level
walk plus raw chronological replay. It imports no production strategy, engine,
calendar, loader, execution, metrics or selector; reconstructs every configuration,
all construction records/resets and execution fields, monthly/directional metrics,
coverage, selection and neighbors. Internal computational independence does not
constitute external human/user signoff. Corruption tests demonstrate checks.

New detailed ledgers are sharded in evaluations/<ID>/USDRUBF/ and indexed by
configuration, with exact global candidate/month/direction/funnel/neighborhood
reports. Every evaluation publishes full signals.csv, construction_events.csv,
trades.csv, data_gap_skips.csv, data_quality_exclusions.csv, rejected_nonfill.csv,
coverage_report.csv and diagnostics. Nothing is copied from raw source into Git.

Complete technical PASS with a full qualifying candidate yields
PROVISIONAL_2023_OPTIMIZATION_CANDIDATE_PENDING_INDEPENDENT_AUDIT;
otherwise NO QUALIFYING OPTIMIZATION CANDIDATE. Only 2023 development fitting.
No Robustness, WF, TRUE OOS, other families, merge or auto-merge.
Create one Draft PR and STOP for independent user audit.
