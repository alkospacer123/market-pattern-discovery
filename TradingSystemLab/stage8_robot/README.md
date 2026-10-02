# Stage 8 robot foundation

**Status:** `STAGE_8_8_6_SQLITE_RECOVERY_CODE_READY_PENDING_INTEL_ACCEPTANCE` / `STAGE_8_MARGIN_AWARE_FULL_R15_CODE_READY` — `LIVE_TRADING_NOT_AUTHORIZED`.

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

The credential-backed real smoke records sanitized binding, schedule,
contract-economics, account-cleanliness, and directional-margin evidence. If
account funding structures required for sizing are unavailable, the smoke stops
fail-closed and does not fabricate equity, cash, margin capacity, or hypothetical
position sizing. On 2026-10-01 an operator-executed `REAL_READONLY` diagnostic
authenticated all four N4 perpetual futures against FINAM. The
committed production registry is now 4/4 `AUTHENTICATED_REAL_READONLY`; the
validation token was read-only and no real order was transmitted. Funding
readiness remains separate and fail-closed because the clean UNION account did
not expose the required `portfolio_forts` financial structure. LIVE trading
remains unauthorized. Intel host artifacts are under `deploy/windows/` and
cover external state paths, instance locking, online SQLite backup, bounded logs,
heartbeat, secrets, and reboot reconciliation.

This package implements the sole frozen identity `TRAIL1__N4_01__FULL__R15` under production specification `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`. It does not expose strategy parameters as runtime configuration and does not use the canonical reference as a fallback.

## Stage 8.8.1 operational supervisor

`python -m TradingSystemLab.stage8_robot.readonly_supervisor --runtime-root
<PATH>` is the persistent Windows production observer. It is separate from the
trading runner and funding initialization, fixes REAL_READONLY with entries
disabled, holds an external lifetime instance lock, observes account cleanliness
and completed N4 H1 data, and persists only sanitized operational continuity.
`--once` executes exactly the same single operational cycle without sleeping.

Completion state is `STAGE_8_8_1_REAL_READONLY_SUPERVISOR_CODE_READY`. Real Intel
operational acceptance is complete: supervisor startup and `--once`, continuous
operation, restart, second-instance exclusion, reboot, and network/API failure
through `UNHEALTHY` / `FAULT` and recovery to `HEALTHY` / `PASS` were validated.
Recovery reset the consecutive-failure counter, and no order-capable call was
made. Stage 8.9 funding readiness remains separately blocked by unavailable
account financials; 8.10 trading-token integration is pending, and 8.11/8.12
execution remains not authorized. This acceptance does not authorize LIVE
production operation.

### Stage 8.8.5 stale-market-data rule

Real READ_ONLY timing evidence was validated externally. The production model
now treats FINAM H1 timestamps as whole-hour UTC bar opens, merges touching
EARLY_TRADING, CORE_TRADING and LATE_TRADING intervals, and completes each bar
at `min(open + 1 hour, contiguous trading-window end)`. Auction, clearing and
closed intervals never create an expectation. Freshness requires exact presence
of the expected completed raw open, not merely a newer timestamp.

The order-incapable collector is run with `FINAM_MODE=REAL_READONLY` and
`NEW_ENTRIES_DISABLED=true`:

`python -m TradingSystemLab.stage8_robot.h1_timing_diagnostic --output C:\TradingSystemLab\runtime\diagnostics\finam-h1-market-time-evidence.json`

It calls only session creation, `/v1/assets/{symbol}/schedule`, and H1 `/bars`
for all N4 names. Its output projection contains only symbol, session
type/start/end, H1 timestamps, local observation timestamps, and the HTTP server
date when FINAM supplies one. It discards tokens, account identifiers, prices,
and all other fields. This real capture is external operational evidence: it
must remain outside the repository checkout and must not be committed to Git.
It may be used for independent analysis, but neither its raw nor sanitized
captured market timestamps may be copied into the repository. After evidence
review, deterministic tests may encode only the proven semantic rules using
synthetic fixtures; they must not reproduce the real FINAM market-data capture.

The validated expected raw-open watermark is stored per instrument as
`expected_h1:<instrument>` in the existing transactional operational SQLite
state. A closed-period cold start without that trusted watermark fails with
`H1_EXPECTED_COMPLETED_WATERMARK_UNAVAILABLE`.

Stage 8.8.5 is
`STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE`. The real Intel stale-data
acceptance was executed against audited source Git head
`1c1c2bb5458827f200bc753e7e64db0272b33a8f`. PR #302 subsequently performed
the Stage 8.8.5 repository closeout; its GitHub-visible head was
`635bea24710cc41f0cb65eef9c6ed576494f5396`, and its merge commit was
`b19a3625698f4701b7c531cade5a27a497269b73`. PR #302 did not modify
`readonly_supervisor.py`, `finam_api.py`, or `tests/test_readonly_supervisor.py`,
so the accepted H1 implementation remained byte-identical. The external
artifact SHA-256 is
`C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC`.
The clean cycle was `HEALTHY` / `PASS`; the controlled
`STALE_COMPLETED_H1_DATA` fault was `UNHEALTHY` / `FAULT` without advancement
of successful cycle, H1, or expected-H1 state. Recovery returned `HEALTHY` /
`PASS` and reset consecutive failures to 0. Order-capable calls were 0, entries
remained disabled, and the Scheduled Task remained Disabled. The runtime JSON
and real FINAM market responses remain outside Git.

### Stage 8.8.6 SQLite recovery boundary

The canonical supervisor database is only
`<runtime>/state/readonly-supervisor.sqlite3`. Create a recovery unit without
choosing a database path:

`python -m TradingSystemLab.stage8_robot.backup_state --runtime-root <runtime>`

The command uses SQLite online backup (never a live filesystem copy), verifies
source and destination integrity, and atomically publishes a sanitized manifest
containing the schema ID, frozen production specification ID, UTC timestamp,
backup filename and SHA-256. Retention prunes database/manifest pairs together.

With the supervisor stopped, restore a listed recovery point using:

`python -m TradingSystemLab.stage8_robot.restore_state --runtime-root <runtime> --backup-filename <filename>`

Recovery rejects absent, tampered, malformed, wrong-production and wrong-schema
inputs; acquires `state/stage8-readonly.lock`; builds a validated temporary
database in `state`; removes stale WAL/SHM sidecars; and atomically replaces the
canonical database. Before that commit it quarantines the complete old
database/WAL/SHM set in internal-only rollback paths. A failed replacement or
final validation restores that set; only a validated commit discards it, so an
old WAL cannot replay over the selected recovery point. It preserves the
selected recovery point exactly and does not invent newer H1 or reconciliation
state. After validation, rollback files move to an explicit committed-cleanup
namespace before best-effort deletion. A deletion failure reports
`READONLY_STATE_RECOVERY_COMMITTED_CLEANUP_PENDING_RECONCILIATION_REQUIRED`
rather than an uncommitted recovery failure; a later invocation recognizes and
safely cleans or distinctly reports that obsolete material.

Status is
`STAGE_8_8_6_SQLITE_RECOVERY_CODE_READY_PENDING_INTEL_ACCEPTANCE`. Repository
tests use synthetic SQLite data only. **NEXT: after merge and independent audit,
perform physical Intel backup/restore and start the unchanged REAL_READONLY
supervisor for normal safety reconciliation.** Restore alone is not acceptance
and does not authorize LIVE trading or real order transmission.

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
instrument binding. The authenticated public instrument identities are recorded
in the production registry without account identity or credential material.

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
`FINAM_MODE` supports `DRY_RUN` (default), `DEMO`, and `REAL_READONLY`; `LIVE` always raises
`LIVE_TRADING_NOT_AUTHORIZED`.

The N4 registry models all four names directly as non-expiring `PERPETUAL_FUTURE`
instruments with daily automatic prolongation and operator-only quarterly
exercise. Exchange reference economics are recorded and every committed binding is
`AUTHENTICATED_REAL_READONLY` based on the operator-executed read-only diagnostic.
Official documentation was reviewed at
`https://api.finam.ru/docs/rest/` and `https://api.finam.ru/docs/grpc/`; direct
retrieval from this build environment was blocked by HTTP CONNECT 403.

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

For `REAL_READONLY` operations on the documented Windows Intel deployment:

1. Set `FINAM_MODE=REAL_READONLY` while keeping credentials outside Git.
2. Set `NEW_ENTRIES_DISABLED=true`.
3. Run `python -m TradingSystemLab.stage8_robot.real_account_smoke` to produce the
   sanitized diagnostic.
4. Inspect the sanitized diagnostic.
5. Independently verify the binding evidence for all four instruments.
6. From the repository root, explicitly call the function-based registry updater
   with the diagnostic and registry paths:

   ```powershell
   & $py -c "from pathlib import Path;from TradingSystemLab.stage8_robot.update_real_registry import update;update(Path(r'c:\tradingsystemlab\runtime\diagnostics\finam-real-readonly-diagnostic.json'),Path(r'TradingSystemLab\stage8_robot\production_instrument_registry.csv'));print('REGISTRY_UPDATE_PASS')"
   ```

   This command reads the sanitized `REAL_READONLY` diagnostic, validates all
   activation gates, atomically updates the four-row production registry, and
   prints `REGISTRY_UPDATE_PASS` only after successful completion. Registry
   activation is not automatic and does not authorize trading.
7. Verify the production registry.
8. Run the Stage 7 and Stage 8 audits and the server preflight.

The separate order smoke demands DEMO mode,
explicit consent, four authenticated records, Stage 7 authentication, a full
conformance PASS, and reconciliation. Both the isolated research-authority replay
and the independent Stage 8 production replay reproduce all 418 authoritative
trades exactly and deterministically. No FINAM connection was attempted and no
demo order was transmitted.
