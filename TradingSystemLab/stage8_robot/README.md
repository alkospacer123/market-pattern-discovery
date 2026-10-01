# Stage 8 robot foundation

**Status:** `STAGE_8_REAL_ACCOUNT_READONLY_CODE_READY` / `STAGE_8_MARGIN_AWARE_FULL_R15_CODE_READY` / `STAGE_8_INTEL_SERVER_DEPLOYMENT_PREPARED` — `LIVE_TRADING_NOT_AUTHORIZED`.

## Real account read-only and margin feasibility

`FINAM_MODE=REAL_READONLY` is separate from demo operation, requires the exact
`FINAM_REAL_ACCOUNT_ID` enumerated by a read-only token, and uses an adapter whose
`submit_order` unconditionally raises `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`.
The SQLite identity contains the frozen production ID, FINAM, REAL environment,
and only a SHA-256 account identity. First activation requires no positions,
active orders, or unresolved intents and persists authenticated starting equity
exactly once. Later raw broker equity and unrealized PnL never replace it.

Frozen FULL/R15 sizing is capped by
`floor_to_trade_lot(min(r15_quantity, floor(available_cash / directional_initial_margin)))`.
FORTS `portfolio_forts.available_cash.value` is the free-cash authority;
`money_reserved.value` is evidence and is not double-subtracted. Directional
`long_initial_margin` and `short_initial_margin` are exact RUB Money values. A
batch-local budget reserves margin before the next entry is sized, and zero is
never rounded to one.

### Real FINAM account data types

FINAM REST account values use two deliberately separate representations.
`equity`, `unrealized_profit`, `portfolio_forts.available_cash`, and
`portfolio_forts.money_reserved` are strict Decimal value objects such as
`{"value":"250000.50"}`. Directional `long_initial_margin` and
`short_initial_margin` remain Money objects containing exactly
`currency_code`, string `units`, and integer `nanos`. Numeric JSON values,
protobuf `{num,scale}` objects, cross-shape substitutions, and extra keys fail
closed.

The credential-backed real smoke performs atomic 4/4 binding and emits sanitized,
hypothetical sizing only. With no operator credentials, the registry remains
`BLOCKED_UNAUTHENTICATED`. Intel host artifacts are under `deploy/windows/` and
cover external state paths, instance locking, online SQLite backup, bounded logs,
heartbeat, secrets, and reboot reconciliation.

This package implements the sole frozen identity `TRAIL1__N4_01__FULL__R15` under production specification `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`. It does not expose strategy parameters as runtime configuration and does not use the canonical reference as a fallback.

## Boundaries and startup

`strategy_core` and `trail1_state` contain no broker imports. `broker` owns all FINAM-specific concerns; `risk`, `instrument_resolver`, `state`, `reconciliation`, `market_data`, `audit_logging`, and `runner` are separate. Startup authenticates Stage 7, opens the transactional SQLite store, connects the selected broker, and reconciles positions/orders. Anything except `RECONCILED`, stale/invalid data, an unresolved contract, or `NEW_ENTRIES_DISABLED=true` blocks entries. Open-position roll is operator-action-required because Stage 7 freezes no roll policy.

The state store uses SQLite transactions, WAL, a unique idempotency-key primary key, explicit partial-fill-compatible order states, fills, realized equity and reconciliation markers. An intent is committed before submission. Sizing uses realized equity only; exits and actual fees are booked before later same-timestamp entries. Live commissions/exchange fees/slippage are separate from historical C1.

## FINAM schema record (2026-09-30 UTC)

The corrective schema authority fixes session creation (`POST /v1/sessions`),
session enumeration (`POST /v1/sessions/details` with JWT `token`, returning
`account_ids`), H1 bars (`GET /v1/instruments/{symbol}/bars`,
`timeframe=TIME_FRAME_H1`, `interval.start_time`/`interval.end_time`), account-bound
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
5. LIVE is not implemented and always fails with `LIVE_TRADING_NOT_AUTHORIZED`.
   A later separately authorized change would be required; this Stage 8 package
   offers no environment-variable override. The kill switch only blocks new
   DEMO entries and does not invent emergency liquidation.

Audit records are JSON Lines and support the full schema (instrument/contract, bar/signal/direction, equity/risk/quantity, entry/stops/TRAIL1, orders/fills/responses, reconciliation, exit/PnL/fees and failure reason). Callers must provide the applicable fields for each lifecycle event.

## FINAM v1 demo/perpetual integration (in progress)

The low-level dependency-free client implements bearer JWT recreation after 401,
explicit account enumeration, asset discovery/parameters/schedules, and causal
H1 bar normalization. A centralized limiter uses 180 requests/minute (below the
documented 200/minute maximum); GET retries are bounded, 429 is explicit, and an
uncertain order POST is reconciled by compact client ID rather than retransmitted.
`FINAM_MODE` is either `DRY_RUN` (default) or `DEMO`; `LIVE` always raises
`LIVE_TRADING_NOT_AUTHORIZED`.

The N4 registry models all four names directly as non-expiring `PERPETUAL_FUTURE`
instruments with daily automatic prolongation and operator-only quarterly
exercise. Exchange reference economics are recorded, but every committed
binding remains `BLOCKED_UNAUTHENTICATED` until an operator runs the read-only
smoke against official FINAM responses. Official documentation was reviewed at
`https://api.finam.ru/docs/rest/` and `https://api.finam.ru/docs/grpc/`; direct
retrieval from this build environment was blocked by HTTP CONNECT 403, and no
credential-backed claim is made.

The production client uses **REST representation** only. `quote_currency` is a
string; `min_step` and `trade_lot_size` are decimal strings;
`lot_size` and `future_details.contract_size` are exact
`{"value": "decimal"}` objects; and account `is_tradable` is a primitive JSON
boolean. `min_step` is a mantissa in price precision and the actual step is
exactly `Decimal(min_step) / 10 ** decimals`, without binary floating point.
Unexpected types, aliases, extra object keys, and floats fail closed.

The **gRPC/protobuf semantic representation** may describe the same economic
concepts with `{num, scale}` Decimal or wrapped boolean messages. Those are not
REST wire evidence and the runtime REST binding deliberately rejects them.
For these futures, `OrderRequest.quantity.value` is a number of contracts;
`trade_lot_size` is its required increment, whereas
`future_details.contract_size` is underlying per contract. MOEX supplies the
frozen tick value used by R15 sizing. The schedule is operational evidence and
never a strategy-session filter.

Internal futures quantity is mapped to FINAM `quantity: {"value": "..."}` only
after all instrument-binding semantics have been authenticated.

Run `python -m TradingSystemLab.stage8_robot.demo_smoke` with external credentials
for a sanitized read-only diagnostic, then use `update_demo_registry` for an
all-four atomic registry update. The separate order smoke demands DEMO mode,
explicit consent, four authenticated records, Stage 7 authentication, a full
conformance PASS, and reconciliation. Both the isolated research-authority replay
and the independent Stage 8 production replay reproduce all 418 authoritative
trades exactly and deterministically. No FINAM connection was attempted and no
demo order was transmitted.
