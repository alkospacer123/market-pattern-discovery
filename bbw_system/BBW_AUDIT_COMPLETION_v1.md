# BBW Task 02B audit completion checklist

This is a code-and-test audit, not a function-name inventory. No market data,
2025 TRUE OOS data, optimizer, or performance experiment was used.

| Requirement | Before 02B | After 02B / evidence |
|---|---|---|
| Task 02 threshold/session/range hardening | IMPLEMENTED | Retained in `test_bbw_core.py`. |
| Dedicated causal prefix suite | MISSING | **IMPLEMENTED** — `test_bbw_causality.py`. |
| H4 availability before H1 retest | MISSING (CRITICAL) | **IMPLEMENTED** — open/close/known/first-retest metadata and overlap tests. |
| Confirmation at next real open | PARTIAL | **IMPLEMENTED** — timestamp ordering and actual-open tests. |
| Gap-after-confirmation extension | PARTIAL | **IMPLEMENTED** — slipped actual open is filtered. |
| Retest-window meaning | MISSING | **IMPLEMENTED** — ordinal after known breakout, inclusive bounds. |
| Penetration tick **AND** range cap | PARTIAL | **IMPLEMENTED** — both active; equality accepted. |
| Immutable LONG/SHORT structural stop | PARTIAL | **IMPLEMENTED** — grid-aligned; filters only reject. |
| Four stop dimensions / boundaries | PARTIAL | **IMPLEMENTED** — price, ticks, ATR, range ratio. |
| Dimensional sizing | MISSING (HIGH) | **IMPLEMENTED** — tick value and GO per contract; lot not multiplied. |
| Central tick alignment | MISSING | **IMPLEMENTED** — Decimal helpers and three decimal tick tests. |
| Integer partial allocation | MISSING | **IMPLEMENTED** — floor/floor/remainder. |
| LONG and SHORT management | PARTIAL / MISSING | **IMPLEMENTED** — separate +1R/+2R/+3R tests. |
| Same-bar ambiguity | PARTIAL | **IMPLEMENTED** — pre-existing active stop first. |
| Lower-TF interface | PARTIAL | **IMPLEMENTED** — missing data fails unless explicit fallback. |
| Gap through initial/BE/moved stop | MISSING (CRITICAL) | **IMPLEMENTED** — actual adverse open fill basis. |
| Adverse slippage | PARTIAL | **IMPLEMENTED** — BUY up, SELL down on entries/exits. |
| Commission on every fill | MISSING (HIGH) | **IMPLEMENTED** — entry and each integer exit fill. |
| Gross R / net R | MISSING | **IMPLEMENTED** — named metrics against initial risk cash. |
| Current equity feeds next size | PARTIAL | **IMPLEMENTED** — net PnL updates equity before release. |
| Global one-position tie-break | PARTIAL | **IMPLEMENTED** — time, configured priority, symbol. |
| Research diagnostics | PARTIAL | **IMPLEMENTED** — required schema on accepted/rejected rows. |
| Reconstructable event journal | PARTIAL | **IMPLEMENTED** — timestamp/setup/from/to/reason helper. |
| End-to-end prefix/future mutation | MISSING | **IMPLEMENTED** — extreme future mutation test. |
| Optimizer / real baseline / live trading | NOT APPLICABLE / prohibited | Not created or run. |

## Defects and severity

* **CRITICAL:** H4 open timestamps did not encode when aggregates became known,
  allowing constituent H1 rows. Availability metadata now requires entry opens
  at or after `breakout_known_at`.
* **CRITICAL:** crossed stops filled at the stop without gap-open input. They now
  fill from the adverse actual open.
* **CRITICAL:** OHLC handling could invent favorable sequencing after moving a
  stop. The bar-start stop is checked first; newly moved stops wait one bar.
* **HIGH:** ambiguous `tick_value * lot` could double-count economics. Tick value
  and GO are per contract; lot is legacy metadata.
* **HIGH:** fractional exits and missing costs misstated equity. Integer fills and
  entry/every-exit commissions now drive net equity.
* **MEDIUM:** retest age, equality, grids, diagnostics and ordering were not
  explicit. Code, documentation and boundary tests now freeze them.

## Frozen examples

Allocations are `floor(.50*N)`, `floor(.30*N)`, remainder: `1 → (0,0,1)`, `2 →
(1,0,1)`, `3 → (1,0,2)`, `5 → (2,1,2)`, `10 → (5,3,2)`. Zero legs emit no
fill. Exact stop-bound and penetration-cap equality passes. `retest_min_bars=5`
means the fifth entry-TF candle after breakout availability is first eligible,
not setup age or touch duration.
