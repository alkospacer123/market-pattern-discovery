# BBW Core v1.0 post-merge audit

## Scope and method

The specification, README, both configurations, every `src/bbw_system` module,
and the original tests were read completely. Timestamp flow was traced from H1
open through sessions, setup bars, indicators, decisions, entry, and exits.
Existing tests were treated as evidence to challenge, not as the definition.

## CRITICAL

### Hard-coded calendar-year rejection

* **Found:** the CLI rejected every 2025 row.
* **Why:** a reusable baseline cannot encode a particular research split.
* **Causality:** no direct look-ahead, but research policy was incorrectly mixed
  into data semantics.
* **Backtest impact:** valid samples were unavailable.
* **Fixed:** removed the function and CLI call; no optimizer/OOS selector added.
* **Proof:** `test_no_hardcoded_calendar_year_restriction` covers 2022–2026.

### Threshold admitted current trading-day history

* **Found:** “strictly before this row” still included earlier same-day bars.
* **Why:** baseline requires ten previous completed trading dates.
* **Causality:** observable, but contrary to the frozen baseline information set.
* **Backtest impact:** changed intraday thresholds and compression events.
* **Fixed:** current date is excluded by default; alternative behavior is opt-in.
* **Proof:** `test_threshold_uses_previous_unique_completed_trading_dates` and
  `test_threshold_current_day_history_is_explicit_opt_in`.

## HIGH

### Short session-end setup bars were always discarded

* **Found:** completeness always meant exactly four H1 rows.
* **Why:** valid shortened endings and gaps require different treatment.
* **Causality:** permissive row-count logic could expose a live candle.
* **Backtest impact:** valid bars disappeared or invalid bars could be invented.
* **Fixed:** `strict_source_count` and `session_end_valid` policies. The latter
  accepts only a bucket containing every configured expected H1 slot.
* **Proof:** `test_session_end_completion_policy_accepts_short_bucket_but_not_gap`
  and `test_strict_completion_policy_rejects_short_session_end_bucket`.

### Range timing had no causal selector

* **Found:** only unconstrained range construction existed.
* **Why:** callers could select 6–30 bars after seeing breakout success.
* **Causality:** architectural look-ahead risk.
* **Backtest impact:** optimistic range selection and false breakouts.
* **Fixed:** three configured modes consume an explicit observable prefix, cap at
  the maximum, and deterministically choose the longest eligible window (latest
  capped window for rolling mode).
* **Proof:** `test_range_selection_cannot_see_future_breakout` mutates a future
  breakout and demonstrates unchanged decisions in every mode.

## MEDIUM

### Calendar modeled weekdays only

* **Found:** holidays were inexpressible; overnight exclusion used wall-clock
  weekday instead of trading date.
* **Why:** Monday-Friday is not an exchange calendar.
* **Causality:** incorrect membership changes the available information set.
* **Backtest impact:** changed day counts, threshold minima, and setup OHLCV.
* **Fixed:** explicit `excluded_dates`, keyed by trading date. Timezone, overnight
  anchor, breaks, date-specific session-end overrides and zoneinfo DST behavior
  remain configurable. A full MOEX calendar remains out of scope.
* **Proof:** `test_explicit_holiday_excluded_from_days_threshold_and_setup_bars`.

### Configuration mutability

* **Found:** loading popped a nested mapping and left frozen sequence fields as lists.
* **Why:** this weakened reproducible immutable configuration.
* **Causality:** none. **Backtest impact:** indirect configuration-state risk.
* **Fixed:** mappings are copied and sequence fields normalized to tuples.
* **Proof:** `test_config_and_reports`.

## LOW / verified without change

* Threshold uses upward ceiling, pinned by `test_threshold_uses_ceiling_not_rounding`
  (`0.01201 -> 0.013`), never ordinary rounding.
* EMA uses recursive `adjust=False` with 50-bar warm-up; covered by
  `test_recursive_ema_matches_manual_and_warmup`.
* ATR uses current completed OHLC, prior close, 14-TR seed and Wilder recursion;
  covered by `test_wilder_atr_manual_example`.
* Confirmation executes only at the following bar open with configured adverse
  slippage; existing end-to-end tests pin this behavior.

## Readiness conclusion

The primitives are ready for a first baseline once the caller supplies actual
sessions, holidays/short days, economics, costs, and slippage. This does not
validate profitability, select parameters, or authorize use of locked TRUE OOS
in research/optimization. No optimizer was added.
