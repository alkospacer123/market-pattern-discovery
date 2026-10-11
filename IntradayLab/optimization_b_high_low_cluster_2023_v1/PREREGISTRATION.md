# Optimization B High/Low Cluster — pre-P&L contract

Only the explicitly authorized Optimization B / HIGH_LOW_CLUSTER_M5 / 2023.
Verified base main `0aa3851b754705145b3c64af9781e93f553e4a09` (Merge #480).
Original B4/B7/B10 and all preexisting files remain byte immutable.

Primary grid: N4–10 × width2/3 × boundary touches2/3 × buffer1 × Take2–10:
252 distinct configurations. Preregistered Stop check: N4–10 × width3 ×
touches2 × buffer2 × Take2–10: 63 configurations. Total315. GRID.csv carries
all parameters and both instrument flags; EVALUATION_MATRIX.csv has all585
included pairs: USD N4–9 /270, CNY N4–10 /315. USD N10 excluded before any
P&L because old B10 has34 CLOSED /30 dates. GLD/IMOEX excluded. N5/6/8/9
are new parameter variants; their volume is assessed from new CLOSED only.
IDs contain N, width, touches, buffer and Take. No extra variants, early stop,
random/Bayesian/ML search, new approaches or post-results expansion.

Each direction builds a sequential greedy episode from completed M5 High for
SHORT /Low for LONG. **maximum_width_ticks governs continuation/termination
of the entire episode envelope, as well as the last-N slice.** A candle breaking
the envelope starts a new episode on itself, with no recycled preceding bars.
Slice width is at least1 tick (zero belongs to A); touches count exact external
boundary extrema in the last N consecutive candles. The first formed slice
consumes the whole episode even when Close/admission/busy/ambiguity fails.
CLOSE_AT_BOUNDARY records no entry and forbids a later retry. Two valid sides
are both AMBIGUOUS_BOTH_SIDES. Reset on missing/invalid candle, nonadjacency,
day/session/tick change. Episode endings are descriptive only and unavailable
for admission. The independent auditor uses batch envelope partitions and
prefix/slice calculations rather than importing the streaming strategy.

Fixed minimum_width1, risk3–12 ticks, favorable Open rebound≤4 ticks,
hold120 calendar minutes, tolerance0; no ATR/MTF/trailing/dynamic management,
round filter or additional confirmation. Original daytime windows, March
13–20 lunch regime, holidays, session-flat and Stop-first retained.
Structural Stop: SHORT boundary +buffer dated ticks; LONG boundary −buffer
at signal tick. Actual next Open determines risk; never move Stop to admit.
Unchanged common Backtester: ENTRY_NEXT_OPEN, DATA_GAP_SKIP_V2,
allow_entry_bar_take=false, cost_ticks_per_side=1.

FULL_NET_C1_R Take distance = R×(gross initial risk +planned round-trip C1)
+planned round-trip C1; outward entry-date grid rounding. Planned C1=2 entry
ticks. Actual C1=dated entry tick +dated exit tick. Gross/C1/net price and R
are separate; Net R denominator=initial gross risk, planned net/net denominator
=risk+planned C1, realized net/net denominator=risk+actual C1. CNY tick .01
before2023-09-27 19:00 MSK, .001 thereafter. Round diagnostics use USD .10,
CNY .05, nearest node ties upward; ROUND_NEAR≤1 dated tick, otherwise ORDINARY_FAR.
No diagnostics enter selection or subsequent admission.

Per included pair: ≥100 CLOSED, ≥40 MSK entry dates, ≥6 CLOSED entry months;
PF R≥2 and PF price≥2, net expectancy>0, ≥9 positive calendar exit months
(out of12;12/12 explicit), conditional CLOSED-only DD≤20R, largest winner
≤25% positive R profits, largest positive month≤50% positive months R.
At least2 actual included immediate grid neighbors, changing only one adjacent
step in N/width/touches/buffer/Take, need100 CLOSED, expectancy>0 and PF R≥1.5.
Excluded USD N10 never supplies a neighbor. Rank only all-criteria passes by
positive months descending; min(PFs) descending; conditional DD ascending;
CLOSED descending; ID ascending. No pass => NO QUALIFYING OPTIMIZATION CANDIDATE.
Pass status remains PROVISIONAL_2023_OPTIMIZATION_CANDIDATE_PENDING_INDEPENDENT_AUDIT
pending the user's external audit, regardless of internal algorithm PASS.

Study metrics use Decimal50 aggregation of saved Decimal28 trade R; trade/path
fields and study metrics must agree exactly. Independently reconstruct common
Decimal28 reports at their published precision; no epsilon, tolerance, zero-sign
repair or exclusion of discrepancies. This distinction preserves the unchanged
Backtester/reporting and avoids masking a discrepancy with rounding.

Source: read-only alkospacer123/market-pattern-data commit
f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8; exact pinned blobs and SHA-256 prefixes
in policy. USD42576 rows /2342431 bytes; CNY39362 /2212189. One load81938 candle
rows /4554620 bytes. Development [2023-01-01,2024-01-01) MSK. Zero2024+ candle
bytes. Bounded unbuffered Python reader plus independent actual syscall receipts.
Missing mandatory entry Open => SKIP without entry/P&L. Missing exposed data
=> EXCLUDED with known entry and no invented exit/P&L, block the rest of day.
Later days assume conditional FLAT. Accepted IDs exactly disjoint CLOSED∪EXCLUDED.
Ordinary trades.csv CLOSED only. Incomplete CNY and exclusions disclose possible
selection bias; conditional PF/Net/DD are not full annual/broker account evidence.
No price pooling; nearby configurations and baseline B durations overlap.

Freeze includes every study module, original common dependencies, policy, both
CSVs, source commitments, protected inventory, preflight and synthetic receipts.
Guard checks necessary dependency membership, freeze Git bytes and current bytes,
and published branch ancestry before historic load. GRID is explicitly force-added
through existing global *.csv ignore. Freeze is pushed and GitHub verified before
historic P&L. Missing dependency stops before source; correction requires explicit
new complete pre-P&L commit. No hidden changes after first historic P&L.

Canonical585 plus two full separate process repeats, each with independent raw-M5
audit585. All deterministic runner **and audit** artifacts are compared bytewise.
Six full source loads (three runner, three auditor)=491628 candle rows /27327720
bytes, repeated exact2023 prefixes. Syscall hashes/read receipts and logs published.
Baseline comparator W3/T2/SB1/TP3 replays only the five included historic pairs
inside independent audit. Per-ID V2 differences published; all common CLOSED
entry/Stop/Take/risk/exit/Net R exact. USD B10 is existing ledger reference only,
no new USD N10 evaluation or raw replay. Synthetic full585 integration adapts
source and archival comparator metadata in memory only, with no historical candles.

Additions only inside IntradayLab. Every original repository file, Master Registry,
Optimization A, TradingSystemLab/live/broker/production and separate Draft#472
(head82ec9ffe61e18a43cd7510e398f6913b25f045e1) protected. No source mutation,
Robustness, WF2024, TRUE OOS2025+, Optimization C, other families or LIVE.
Exactly one Draft PR with full Summary; no merge/auto-merge. STOP after publication.
