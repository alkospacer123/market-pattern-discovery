# Stage 8 robot foundation

**Status:** `STAGE_8_IMPLEMENTATION_IN_PROGRESS` — never production-live.

This package implements the sole frozen identity `TRAIL1__N4_01__FULL__R15` under production specification `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`. It does not expose strategy parameters as runtime configuration and does not use the canonical reference as a fallback.

## Boundaries and startup

`strategy_core` and `trail1_state` contain no broker imports. `broker` owns all FINAM-specific concerns; `risk`, `instrument_resolver`, `state`, `reconciliation`, `market_data`, `audit_logging`, and `runner` are separate. Startup authenticates Stage 7, opens the transactional SQLite store, connects the selected broker, and reconciles positions/orders. Anything except `RECONCILED`, stale/invalid data, an unresolved contract, or `NEW_ENTRIES_DISABLED=true` blocks entries. Open-position roll is operator-action-required because Stage 7 freezes no roll policy.

The state store uses SQLite transactions, WAL, a unique idempotency-key primary key, explicit partial-fill-compatible order states, fills, realized equity and reconciliation markers. An intent is committed before submission. Sizing uses realized equity only; exits and actual fees are booked before later same-timestamp entries. Live commissions/exchange fees/slippage are separate from historical C1.

## FINAM documentation authentication record (2026-09-30 UTC)

Candidate official publication locations were `https://tradeapi.finam.ru/` and FINAM's published Trade API documentation at `https://finamweb.github.io/trade-api-docs/`. Both were inaccessible from the controlled environment (HTTP CONNECT 403), so a current API version, authentication header/schema, endpoint paths, rate limits, fee schedule and live futures identifiers could **not** be authenticated. Old examples were not substituted. Consequently `FinamBroker` is an inert fail-closed foundation and all four registry rows are `BLOCKED_UNAUTHENTICATED`; no endpoint or instrument value is invented. This is an explicit operational blocker, not a fallback.

Before live authorization, an operator must authenticate and record the current official API version, token method and credentials reference; candle/security, account/portfolio, order/cancel/status and execution endpoints; documented limits; account tariff and MOEX fees; and current FINAM/MOEX contract security ID, code, expiry, step, tick value, multiplier, lot granularity, currency and trading status for every registry row. Tests must then be extended against the authenticated schema.

## Runbook

1. Keep credentials outside Git and set `STARTING_REALIZED_EQUITY`; leave `LIVE_TRADING_ENABLED=false` and normally `NEW_ENTRIES_DISABLED=true`.
2. Run `python -m pytest TradingSystemLab/stage8_robot/tests -q` and `python TradingSystemLab/stage8_robot/audit_stage8.py`.
3. Instantiate `RobotRunner(RuntimeConfig.from_environment())`; without an explicitly injected live broker it always uses `DryRunBroker`, which records `transmitted: false`.
4. Reconcile realized equity to broker cash flows (completed exits minus actual commission/exchange fees). Any unexplained mismatch outside an operator-defined monetary tolerance blocks entries; no tolerance is silently defaulted.
5. Live trading requires separate authorization, authenticated registry rows, an explicitly supplied FINAM broker, and the exact literal `LIVE_TRADING_ENABLED=true`. Missing/malformed values remain off. The kill switch only blocks new entries and does not invent emergency liquidation.

Audit records are JSON Lines and support the full schema (instrument/contract, bar/signal/direction, equity/risk/quantity, entry/stops/TRAIL1, orders/fills/responses, reconciliation, exit/PnL/fees and failure reason). Callers must provide the applicable fields for each lifecycle event.

## FINAM v1 demo/perpetual integration (in progress)

The low-level dependency-free client implements session creation (`POST /v1/sessions`), bearer JWT recreation after 401, accounts/orders, asset discovery/parameters/schedules and H1 candle retrieval. A centralized limiter uses 180 requests/minute (below the documented 200/minute maximum); GET retries are bounded, 429 is explicit, and an uncertain order POST is never retried. `FINAM_MODE` is either `DRY_RUN` (default) or `DEMO`; `LIVE` always raises `LIVE_TRADING_NOT_AUTHORIZED`.

The N4 registry now models all four names directly as non-expiring `PERPETUAL_FUTURE` instruments with daily automatic prolongation and operator-only quarterly exercise. Exchange reference economics are recorded, but every binding remains `BLOCKED_UNAUTHENTICATED` until an operator runs the read-only smoke against official FINAM responses and independently retrieves the official MOEX pages. This environment received HTTP CONNECT 403 for both authorities; it therefore did not assert an authenticated binding.

Run `python -m TradingSystemLab.stage8_robot.demo_smoke` with external credentials for a sanitized read-only diagnostic. The separate `demo_order_smoke` command additionally demands DEMO mode, explicit transmission consent, four authenticated registry records, Stage 7 authentication, a full conformance PASS and reconciliation. Current `conformance_report.json` deliberately fails closed with `AUTHENTICATED_HISTORICAL_FIXTURE_SOURCE_REQUIRED`: frozen-v3 H1 source bars are absent from this checkout. No replacement history was downloaded, no demo order was transmitted, and Stage 8 remains in progress.
