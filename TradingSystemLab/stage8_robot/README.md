# Stage 8 robot foundation

**Status:** `STAGE_8_RESEARCH_ROBOT_CONFORMANCE_FAIL` — never production-live.

This package implements the sole frozen identity `TRAIL1__N4_01__FULL__R15` under production specification `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`. It does not expose strategy parameters as runtime configuration and does not use the canonical reference as a fallback.

## Boundaries and startup

`strategy_core` and `trail1_state` contain no broker imports. `broker` owns all FINAM-specific concerns; `risk`, `instrument_resolver`, `state`, `reconciliation`, `market_data`, `audit_logging`, and `runner` are separate. Startup authenticates Stage 7, opens the transactional SQLite store, connects the selected broker, and reconciles positions/orders. Anything except `RECONCILED`, stale/invalid data, an unresolved contract, or `NEW_ENTRIES_DISABLED=true` blocks entries. Open-position roll is operator-action-required because Stage 7 freezes no roll policy.

The state store uses SQLite transactions, WAL, a unique idempotency-key primary key, explicit partial-fill-compatible order states, fills, realized equity and reconciliation markers. An intent is committed before submission. Sizing uses realized equity only; exits and actual fees are booked before later same-timestamp entries. Live commissions/exchange fees/slippage are separate from historical C1.

## FINAM schema record (2026-09-30 UTC)

The corrective schema authority fixes session creation (`POST /v1/sessions`),
session enumeration (`POST /v1/sessions/details`), H1 bars
(`GET /v1/instruments/{symbol}/bars`, `timeframe=TIME_FRAME_H1`), account-bound
asset parameters, and the object quantity/order enums/client ID fields.  Schema
authentication is deliberately distinct from credential-backed account and
instrument binding.  No credentials were available, so all registry rows stay
`BLOCKED_UNAUTHENTICATED` and no FINAM symbol is fabricated.

Before live authorization, an operator must authenticate and record the current official API version, token method and credentials reference; candle/security, account/portfolio, order/cancel/status and execution endpoints; documented limits; account tariff and MOEX fees; and current FINAM/MOEX contract security ID, code, expiry, step, tick value, multiplier, lot granularity, currency and trading status for every registry row. Tests must then be extended against the authenticated schema.

## Runbook

1. Keep credentials outside Git and set `STARTING_REALIZED_EQUITY`; leave `LIVE_TRADING_ENABLED=false` and normally `NEW_ENTRIES_DISABLED=true`.
2. Run `python -m pytest TradingSystemLab/stage8_robot/tests -q` and `python TradingSystemLab/stage8_robot/audit_stage8.py`.
3. Instantiate `RobotRunner(RuntimeConfig.from_environment())`; without an explicitly injected live broker it always uses `DryRunBroker`, which records `transmitted: false`.
4. Reconcile realized equity to broker cash flows (completed exits minus actual commission/exchange fees). Any unexplained mismatch outside an operator-defined monetary tolerance blocks entries; no tolerance is silently defaulted.
5. Live trading requires separate authorization, authenticated registry rows, an explicitly supplied FINAM broker, and the exact literal `LIVE_TRADING_ENABLED=true`. Missing/malformed values remain off. The kill switch only blocks new entries and does not invent emergency liquidation.

Audit records are JSON Lines and support the full schema (instrument/contract, bar/signal/direction, equity/risk/quantity, entry/stops/TRAIL1, orders/fills/responses, reconciliation, exit/PnL/fees and failure reason). Callers must provide the applicable fields for each lifecycle event.

## FINAM v1 demo/perpetual integration (in progress)

The low-level dependency-free client implements bearer JWT recreation after 401,
explicit account enumeration, asset discovery/parameters/schedules, and causal
H1 bar normalization. A centralized limiter uses 180 requests/minute (below the
documented 200/minute maximum); GET retries are bounded, 429 is explicit, and an
uncertain order POST is reconciled by compact client ID rather than retransmitted.
`FINAM_MODE` is either `DRY_RUN` (default) or `DEMO`; `LIVE` always raises
`LIVE_TRADING_NOT_AUTHORIZED`.

The N4 registry now models all four names directly as non-expiring `PERPETUAL_FUTURE` instruments with daily automatic prolongation and operator-only quarterly exercise. Exchange reference economics are recorded, but every binding remains `BLOCKED_UNAUTHENTICATED` until an operator runs the read-only smoke against official FINAM responses and independently retrieves the official MOEX pages. This environment received HTTP CONNECT 403 for both authorities; it therefore did not assert an authenticated binding.

Run `python -m TradingSystemLab.stage8_robot.demo_smoke` with external credentials
for a sanitized read-only diagnostic, then use `update_demo_registry` for an
all-four atomic registry update. The separate order smoke demands DEMO mode,
explicit consent, four authenticated records, Stage 7 authentication, a full
conformance PASS, and reconciliation. Frozen data authentication passed, but the
real replay currently reports 418 expected versus 424 reproduced trades and 177
unexplained mismatches. It therefore fails closed as
`STAGE_8_RESEARCH_ROBOT_CONFORMANCE_FAIL`; no demo order was transmitted.
