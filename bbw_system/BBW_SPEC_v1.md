# BBW CORE v1.0 specification

## Safety and architecture

`bbw_system` is isolated from existing strategies. `data` validates and sorts
OHLCV; `market` defines timezone-aware sessions/trading dates; `timeframes`
builds setup bars; `indicators` computes local indicators; `strategy` contains
pure signal/risk rules and the state machine; `engine` handles next-bar orders
and the one-position portfolio; `exits`, `metrics`, and `reports` handle their
named concerns. Input market files remain read-only. The baseline accepts arbitrary years;
research train/OOS enforcement belongs outside this non-optimizing runner.
Parameters are configuration, not searched.

An input timestamp is a candle **open**. Its OHLCV becomes observable only at
the end of that timeframe. Functions consume complete rows chronologically;
confirmation at `t` executes exclusively at the open of row `t+1`. A rolling
compression threshold at `t` slices strictly before `t`. Deterministic stable
sorting and IDs (`SETUP-%08d`, `TRADE-%08d`) make ties reproducible.

## Indicators

For period `n`, `Middle_t = mean(Close[t-n+1:t])`. Population deviation is
`Std_t = sqrt(sum((Close_i-Middle_t)^2)/n)` (`ddof=0`). `Upper/Lower = Middle ±
k*Std`; `BBW=(Upper-Lower)/Middle`. Recursive EMA uses `alpha=2/(n+1)`,
`EMA_t=alpha*Close_t+(1-alpha)*EMA_(t-1)` (`adjust=False`). True range is
`max(H-L, abs(H-prev_close), abs(L-prev_close))`. Wilder ATR seeds with the
first `n` TR mean, then `ATR_t=(ATR_(t-1)*(n-1)+TR_t)/n`.

Compression threshold uses BBW observations belonging to the last configured completed
trading dates strictly before the current trading date by default, takes the configured smallest
values, averages, and rounds upward (ceiling) to configured decimals. Its audit
record includes current BBW, threshold, minima, and trading dates. Weekends and
session-excluded observations cannot enter.

## Synthetic setup bars

Each input bar is assigned relative to `session_anchor`, never to an arbitrary
midnight resample. Bucket start is anchor plus `floor(elapsed/setup_hours)`.
OHLCV is first open, maximum high, minimum low, last close, and volume sum.
`source_bars` and `complete` are emitted. Default signal input drops any bucket
whose source count is not exactly `setup_hours`; `mark` mode exposes it only for
diagnostics. This assumes contiguous one-hour source bars; gaps are separately
reported.

## Rules and transitions

Range shadows define `high=max(high)`, `low=min(low)`, and width. Width must be
inside configured ATR and instrument percent bounds. Boundary variation must
not exceed configured ATR fraction. A breakout is **close only**, above high
for LONG or below low for SHORT; the range then freezes. Trend requires the
configured signed EMA slope and close on the correct EMA side. Retest permits a
touch/penetration limited by both configured tick/price metadata and range
fraction. Confirmation closes back beyond the level. Entry is next bar open,
plus adverse configured slippage. Structural stop is never replaced: LONG
`range_low-offset`, SHORT `range_high+offset`. Invalid ATR/range stop ratios
reject the trade. Size is `min(floor(equity*risk_pct/stop_money),
floor(equity*max_margin_pct/GO))`, where `stop_money=distance/tick_size *
tick_value * lot`.

Allowed transitions are `IDLE→COMPRESSION→RANGE→BREAKOUT→RETEST→CONFIRMATION→
POSITION→CLOSED→IDLE`; any pre-position state may use its declared
`→CANCELLED→IDLE` transition. A single portfolio reservation prevents parallel
positions.

At +1R, 50% of original size exits and stop moves to entry. At +2R, 30% exits
and stop moves to +1R. At +3R, the final 20% exits. If a bar contains both the
active stop and next target, lower-TF event ordering may be supplied externally;
without it the configured baseline is STOP FIRST. Commission and slippage are
explicit config inputs (commission is retained for monetary trade accounting).

## Cancellation/rejection codes

`NO_VALID_RANGE`, `RANGE_TOO_NARROW`, `RANGE_TOO_WIDE`,
`RANGE_NOT_HORIZONTAL`, `EMA_DIRECTION_FAIL`, `BREAKOUT_FAILED`,
`RETEST_TIMEOUT`, `RETEST_TOO_DEEP`, `ENTRY_TOO_EXTENDED`,
`CONFIRMATION_TOO_LARGE`, `STOP_TOO_SMALL`, `STOP_TOO_LARGE`,
`POSITION_SIZE_ZERO`, and `POSITION_ALREADY_OPEN`. Journals are `events.csv`,
`setups.csv`, `rejected_setups.csv`, and `trades.csv`; intermediate range and
horizontality values can be appended to events/setups.

## Known limitations and unresolved policy inputs

The passport does not define exchange holidays, daylight-saving ambiguity,
whether overnight session end is inclusive, how incomplete sessions around
holidays qualify, the exact start bar of a range after compression, competing
LONG/SHORT setup priority, gap-through-stop fill price, contract rounding of
partial exits, or lower-TF ordering protocol. These are not guessed as trading
rules. Before a real baseline run, freeze instrument/session hours, holidays and
breaks, anchor/timezone/DST treatment, tick and point economics, GO, width cap,
penetration points, stop offset and all stop bounds, extension/candle bounds,
costs/slippage, partial-contract rounding, gap fills, and setup competition.


## Frozen causal policy choices

The baseline threshold excludes all observations from the current trading date;
including same-day history requires explicit opt-in. Holidays are explicit
`excluded_dates`. Range anchoring supports `end_at_compression`,
`start_at_compression`, and `rolling_after_compression`; every decision receives
only the observable prefix, uses the longest eligible capped window, and never
uses breakout outcome as a tie-breaker.
