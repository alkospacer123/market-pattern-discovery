# CNYRUBF metadata evidence freeze (BBW 03B-2A)

**Freeze date:** 2026-09-14  
**Scope:** metadata and temporal regimes only. This package neither normalizes
bars nor constructs H4 bars, indicators, orders, trades, a baseline, or an
optimization result.

## Evidence method and limitations

The machine-readable passport is the normative proposal. Every scalar identity
field and every temporal regime points to an entry in its `evidence.sources`
registry. The registry records source title, official URL/reference, retrieval
date (at registry level), evidence type, and notes. Half-open intervals are used
throughout: `effective_from <= instant < effective_to`.

MOEX publications/specifications are the authority for exchange semantics.
Finam is an authority only for its export controls, not for MOEX contract
semantics. The supplied `C:\BBW\data\raw` files and the original Finam export
dialog state are not mounted in this repository environment. Consequently, the
required M1 empirical comparison and the selected export timezone/label option
cannot honestly be certified here. They are explicit 03B-2B blockers rather
than assumptions.

## Frozen identity

| Field | Frozen value | Status | Effective interval | Evidence |
|---|---|---|---|---|
| Symbol | `CNYRUBF` | VERIFIED | dataset lifetime | MOEX contract card |
| Exchange | Moscow Exchange Derivatives Market | VERIFIED | 2023-01-03 onward | MOEX contract card |
| Type | daily futures with automatic prolongation | VERIFIED | 2023-01-03 onward | MOEX perpetual-futures specification |
| Settlement | cash-settled | VERIFIED | 2023-01-03 onward | MOEX specification |
| Underlying | CNY/RUB exchange rate | VERIFIED | 2023-01-03 onward | MOEX contract card |
| Quote | RUB per 1 CNY | VERIFIED | 2023-01-03 onward | MOEX contract card |
| Lot | 1,000 CNY | VERIFIED | 2023-01-03 onward | MOEX contract card |
| Settlement currency | RUB | VERIFIED | 2023-01-03 onward | MOEX contract card |
| Series type | `exchange_perpetual_daily_autoprolong` | VERIFIED | 2023-01-03 onward | MOEX specification |
| Exchange timezone | `Europe/Moscow` | VERIFIED | 2023-01-03 onward | MOEX rules/schedules |

This type is intentionally incompatible with the meanings
`individual_contract`, `continuous_adjusted`, and
`continuous_unadjusted`. Existing rollover consumers must branch on the new
enum and treat `rollover.policy=not_applicable_exchange_autoprolong` as no
synthetic roll. Q1/Q2/Q3 filenames are storage partitions and create no event.
Automatic daily prolongation keeps the exchange instrument alive; funding is a
cash-flow mechanism; quarterly exercise is an optional exchange mechanism;
synthetic rollover is a vendor/backtester transformation. None implies another.

## Tick regime

The MOEX change notice makes the new parameters effective in the evening
session on **27 September 2023**, which belongs to trading day **28 September
2023** under the then-current assignment rule. The deterministic instant is
therefore `2023-09-27T19:05:00+03:00`.

| Half-open interval (Moscow time) | Tick | Tick value / contract | Status |
|---|---:|---:|---|
| 2023-01-03 00:00 through 2023-09-27 19:05 | 0.01 RUB per CNY | 10 RUB | EFFECTIVE_DATED_VERIFIED |
| 2023-09-27 19:05 through freeze end | 0.001 RUB per CNY | 1 RUB | EFFECTIVE_DATED_VERIFIED |

The lot identity verifies the arithmetic (`tick × 1,000 CNY`). A raw-price
grid check at the boundary remains required on the locally held files; no price
data was copied into the repository and no strategy output was consulted.

## Production sessions (Moscow local time)

Intervals are half-open; opening auctions are separate from continuous
trading. The encoded schedule is:

1. **2023-01-03–2025-01-26:** trading 09:00–14:00,
   14:05–18:50, 19:05–23:50; clearing 14:00–14:05 and 18:50–19:05.
2. **2025-01-27–2026-03-22:** opening auction 08:50–09:00; the same continuous
   intervals and two clearing intervals as above.
3. **Weekend sessions from 2025-03-01:** Saturday/Sunday 09:50–19:00 and
   attributed to the following working trading day. These bars remain metadata;
   BBW may later exclude them deliberately, never because they vanished.
4. **2026-03-23–2026-07-13 (Unified Trading Session):** auction 08:50–09:00;
   trading 09:00–14:00 and 14:05–23:50; clearing 14:00–14:05. The former
   evening/day boundary is removed.
5. **2026-07-14–2026-08-30:** auction 06:50–07:00; trading 07:00–14:00 and
   14:05–23:50; clearing 14:00–14:05.

Annual holidays, exceptional openings, cancellations, and shortened days must
come from a versioned official MOEX calendar snapshot. They are deliberately
not synthesized from missing bars. Until that artifact is acquired, calendar
status is `REQUIRES_CONFIRMATION` and normalization must fail closed.

## Trading-date assignment

* Before `2026-03-23T00:00:00+03:00`, a weekday timestamp at or after 19:05 is
  assigned to the **next working trading day**.
* From that instant, weekday session timestamps use the **current calendar
  date**.
* An admitted Saturday/Sunday session is assigned to the **following working
  trading day** in both eras.
* “Working” is resolved from the versioned MOEX calendar, not merely weekday
  arithmetic. The lookup API therefore requires the nonworking-date set and
  rejects a missing calendar. A bar on a holiday is rejected unless special
  session evidence admits it.

This model forbids a global `timestamp.date()` shortcut and is suitable for
later calculation of “previous 10 completed trading days,” without calculating
that feature in this task.

## Finam timestamps and H1 alignment

Finam's export UI permits timestamp-related choices, while the CSV payload does
not preserve the checkbox state. The evidence supports neither silently
declaring Moscow time nor start/end labels. Thus:

* source timezone: `REQUIRES_CONFIRMATION`;
* M1/M5/M15/M30/H1 label convention: `REQUIRES_CONFIRMATION` (observed H1
  wall-clock labels are consistent with, but do not prove, START labels);
* D1 is treated as a trading-date label only after confirmation.

**The exact single user fact required:** provide the saved Finam export setting
(or screenshot/preset) stating the timezone and whether intraday candle time is
the interval beginning or interval ending time for these files.

03B-2B must then compare raw M1 first/last trades against the official 08:50
auction/09:00 continuous open and, after 14 July 2026, the 06:50 auction/07:00
open. It must verify all six timeframes agree. H1 labels such as 08:00 strongly
suggest wall-clock-aligned buckets whose first bucket contains only 08:50–09:00;
after expansion, a 06:00 bucket may contain only 06:50–07:00. This remains a
testable hypothesis, not a frozen fact. Synthetic H4 validation must explicitly
handle partial first H1 buckets, prove bucket membership from M1, and never
shift/complete a candle with future observations.

## Funding, margin, and costs

### Funding

The contract specification establishes funding as a distinct daily cash-flow
component of the auto-prolonging contract. A complete official historical
series, its exact application timestamp, and audited long/short sign were not
acquired. The ingestion contract is: immutable official rows keyed by MOEX
trading date and application timestamp; rate and/or RUB amount per contract;
calculation base; positive-sign meaning for the long account; publication time;
source URL; retrieval time; and revision identifier. Duplicates or gaps fail
closed.

`FUNDING_MODEL_READY_FOR_IMPLEMENTATION = NO`

No later baseline may hold across funding settlement until this is resolved.

### Initial margin / GO

The current ISS risk parameter is not historical evidence. No current GO is
backfilled. Preferred remediation is an official effective-dated archive of GO
values. If unavailable, a separately approved conservative proxy may be used
and must be labelled a modeling simplification; a fixed current value is last
priority and non-historical. Historical sizing under the 75% cap is currently
**not reproducible**.

### Transaction costs

Exchange registration/trading fee, clearing/exercise fee, broker commission,
and slippage are four separate inputs. Current contract-card fees cannot be
projected backward without archived schedules. Broker commission is
`REQUIRES_USER_INPUT` in RUB/contract/side (or a complete effective-dated
formula including minimums); slippage is also required in ticks/side. No
broker tariff is inferred from an exchange fee. This package is not a baseline
cost authorization.

## Authoritative source register

The exact machine references and retrieval metadata live in the passport.
Primary sources used are the MOEX CNYRUBF contract card, perpetual-futures
specification, 2023 parameter-change notice, Derivatives Market rules and
schedule notices (12 September 2022, 27 January 2025, 1 March 2025, 23 March
2026, and 14 July 2026), MOEX trading calendars, tariff materials, and ISS risk
parameters. Finam export help/UI is used only for export semantics.

## Gate

`READY_FOR_03B2B = NO`

Deterministic metadata APIs and schedule/tick regimes are ready, but the source
timezone/label setting, empirical M1 alignment, official special-day calendar
snapshot, and archival recheck of the 2026 notices must be completed before
normalization or technical H4 validation. Funding, historical margin, archived
fees, broker commission, and slippage additionally block any later baseline.
