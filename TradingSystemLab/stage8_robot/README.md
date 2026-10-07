# Stage 8 robot foundation

## Stage 8.11 first physical attempt corrective record (2026-10-04)

`STAGE8_11_FIRST_PHYSICAL_ATTEMPT_FAILED_HTTP_400` is the canonical historical result. The accepted code commit was `069806355fc6931470d7f68d5ca6db20b06358fa`; the fixed request was `CNYRUBF` / `CNYRUBF@RTSX`, `LONG`, quantity `1`. Exactly one order-endpoint call returned HTTP 400. Physical evidence with SHA-256 `9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324` proves zero broker fills, `OPERATOR_INTERVENTION_REQUIRED`, and final kill switch `HALTED`. No retry and no controlled flatten occurred. The original physical evidence remains immutable and **did not PASS**.

`STAGE8_11_PRIOR_ONE_CONTRACT_AUTHORIZATION_CONSUMED`: the independently observed, structurally order-incapable `REAL_READONLY` recovery completed with schema `stage8_11_failed_attempt_recovery.v1` and `recovery_status = COMMITTED`. It terminalized only the historical `stage8.11:CNYRUBF:entry` ledger row as `REJECTED`, with `broker_order_id = NULL` and canonical unresolved intent count `0`. Fresh account-wide reconciliation passed, all positions were zero, and active broker order count was zero. This repository closeout does not retroactively change the failed physical result, constitute successful physical acceptance, or make the consumed authorization reusable.

Canonical lifecycle status:

- Stage 8.11.0 — **COMPLETE**.
- Stage 8.11.1 — **COMPLETE / PASS**.
- Stage 8.11.2 — **COMPLETE / PASS**.
- Stage 8.11.3 — prior explicit authorization **CONSUMED** by the first physical attempt; any broker-side retry requires a new explicit authorization after merge and independent audit.
- Stage 8.11.4 — **ATTEMPTED / FAILED HTTP 400 / NO ACCEPTED ENTRY PROVEN**.
- Stage 8.11.5 — **NO POSITION / BROKER CLEAN PROVED**.
- Stage 8.11.6 — **FLATTEN NOT SUBMITTED** because entry fill/position was not proved.
- Stage 8.11.7 — **COMPLETE / PASS / HISTORICAL INTENT RECOVERED**.
- Stage 8.11.8 — **COMPLETE / STAGE 8.11 CLOSEOUT**.
- Stage 8.12 — **NOT STARTED / NOT AUTHORIZED**.

Corrective code distinguishes acknowledged, definitive rejection, and uncertain submission outcomes; a definite HTTP 400 terminalizes its durable intent as `REJECTED` and can be `NOT_ACCEPTED_NO_EXECUTION` only after a fresh account-wide clean proof. POST-side 5xx and transport ambiguity remain `UNCERTAIN`, require reconciliation, and are never blindly retried. The current official PlaceOrder schema exposes `time_in_force`; the bounded market entry and flatten payloads now explicitly use the official `TIME_IN_FORCE_DAY` enum. A fresh exact-symbol FINAM schedule must prove that the timestamp is within `EARLY_TRADING`, `CORE_TRADING`, or `LATE_TRADING` immediately before every possible POST. Missing, malformed, stale/non-current, auction, clearing, closed, or outside-session evidence blocks before a new intent and with zero POSTs.

The recovery was repository-external `REAL_READONLY` evidence work only: it submitted no order, performed no cancellation, and did not retry physical acceptance. Stage 8.11 is closed while its aggregate result remains `STAGE_8_11_CONTROLLED_REAL_EXECUTION_ACCEPTANCE_NOT_YET_PASSED`. The kill switch remains `HALTED`, the Scheduled Task remains `Disabled`, and Stage 8.12 was neither started nor authorized. Any future physical retry requires a new explicit operator authorization.

`stage8.11.attempt2` was physically executed on 2026-10-05. Exactly one CNYRUBF@RTSX LONG quantity-1 entry POST was acknowledged by FINAM. Immutable `stage8_11_physical_acceptance_attempt2.json` evidence SHA-256 `0954B5C3D62444BA9AE59519386B0FC454D85C987BE1BAC04B82CA6C671B15A0` records `broker_order_present = true`, `final_position_quantity = 1`, zero active broker orders, zero proven fills at the instant of reconciliation, one unresolved `stage8.11.attempt2:CNYRUBF:entry` ACK intent, no controlled flatten, final `HALTED`, and `OPERATOR_INTERVENTION_REQUIRED`. The operator subsequently reported manually closing that one-contract broker position; that external manual close is not retroactive Stage 8.11 PASS. The observed defect is FINAM read-side eventual consistency: the immediate reconciliation required order/account/trade views to converge in one observation and stopped when the account position became visible before matching trade proof. The corrective attempt-3 code adds bounded GET-only convergence, reconciles the durable attempt-2 ACK without resubmitting entry, requires a broker-flat account, then uses fixed `stage8.11.attempt3` keys and create-only `stage8_11_physical_acceptance_attempt3.json` evidence for a clean repeat. Attempt 3 has not been physically executed by this code change. Stage 8.12 remains not started and not authorized.

The canonical Intel recovery used
`deploy/windows/run-stage8-11-failed-intent-recovery.ps1` at recovery-code commit
`da3bf756fefc4ed8dbe8c33847c6bb183fcaff30`. The external recovery evidence SHA-256 is
`4B787AD9A4986D2E3AB88CAAB1B5F2FCD88CAB299A303FA431D38A74D1CD292D`.
The wrapper loaded only the CurrentUser `REAL_READONLY` credential and exposed no
execution, cancellation, modification, or ARMED capability. The immutable original
physical evidence remained hash-bound to
`9FEFC5469F2C97F1EB36A5B5C99D323FA37BB948CF53C8A8745A27A06AB3B324`.
Neither external recovery JSON nor the runtime SQLite database is stored in Git.


**Status:** `STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE`
— `LIVE_TRADING_NOT_AUTHORIZED`.

Stage 8.8 operational hardening is COMPLETE. Stages 8.8.1, 8.8.2, 8.8.3,
8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE. Stage 8.9 is COMPLETE. Stage 8.10 is COMPLETE; Stage 8.11.0 is COMPLETE, Stage 8.11.1 and 8.11.2 are COMPLETE / PASS, and Stage 8.11.3 prior authorization is CONSUMED; Stage 8.11.7 historical intent recovery is COMPLETE / PASS; Stage 8.12 is NOT STARTED / NOT AUTHORIZED.

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
The account-type-consistent portfolio `available_cash.value` is the capacity
authority. UNION requires exactly one `portfolio_mc`, whose `initial_margin`
and `maintenance_margin` are account-level evidence and are not subtracted.
Supported FORTS accounts require exactly one `portfolio_forts`, whose
`money_reserved.value` is evidence and is not double-subtracted. Directional
`long_initial_margin` and `short_initial_margin` are exact RUB Money values. A
batch-local budget reserves margin before the next entry is sized, and zero is
never rounded to one.

### Real FINAM account data types

FINAM REST account values use two deliberately separate representations.
`equity`, UNION `portfolio_mc` financial fields, and FORTS `portfolio_forts`
financial fields are strict Decimal value objects such as
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
validation token was read-only and no real order was transmitted. The original physical run remains historically blocked because the old model
incorrectly required `portfolio_forts`; later funded-account evidence confirmed
the clean UNION account uses `portfolio_mc`. Stage 8.9.9 physical revalidation of the corrected model is complete; its pre-funding zero-capacity result is historical, and Stage 8.9.10 is complete after the accepted post-funding validation. LIVE trading remains unauthorized. Intel host artifacts are under `deploy/windows/` and
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
made. Stage 8.9 funding/margin validation is complete under its accepted physical
authority; Stage 8.10.1 now closes only the repository preconditions gate, and
8.11/8.12 execution remains not authorized. This acceptance does not authorize LIVE
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

The first Windows preflight exposed that SQLite's transaction context manager
does not close its file handle before publication. Backup and recovery
validation now explicitly close every short-lived SQLite connection before any
temporary database is replaced, quarantined, or cleaned up. This correction is
covered by platform-independent handle-lifecycle tests. A second Windows
preflight then exposed a Linux-only regression fixture that kept its canonical
WAL database open across restore. The fixture now creates real committed WAL
state in an abruptly terminated subprocess, so restore starts with crash-left
WAL state and no live SQLite handle. A separate Windows regression preserves
the fail-closed contract when an external process really does hold the database
open.

Status is `STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE`. Physical
Intel acceptance used audited code commit
`dc2b79e74817e71435eee20103ae617e13067d8e`; the external evidence remains
outside Git and is recorded only by SHA-256
`1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6`.
Repository tests remain synthetic and did not generate the external acceptance.

On Windows, 27 recovery tests and all 255 Stage 8 tests passed; the independent
Stage 8 audit passed 124 checks, and the Stage 7 audit passed 22 checks plus 19
mutation tests. The accepted backup
`readonly-supervisor-20261002T125325.986665Z.sqlite3` had SHA-256
`00b5e4ca2b389d55389b6b57ac73b5e557c11b72daab8d6e118311613e0aa3b0`; its
manifest had SHA-256
`3d0ef1d7cb11ee592be32550625e8badefc596108f4d0c34eff6c5e12ceba822`, the exact
production ID, schema `stage8-readonly-sqlite-backup/v1`, a matching checksum,
and a valid recovery point.

A controlled marker changed the canonical state from 9 to 10 rows and changed
its logical SHA. Restore exited 0 with
`READONLY_STATE_RECOVERY_COMMITTED_RECONCILIATION_REQUIRED`, removed the marker,
and returned to 9 rows and the exact pre-mutation logical SHA-256
`13f01f1009768ddce65dce079f70486f2cbc2508cd1ea8ec4787414a78e0d3be`, with
cycle 19, five consecutive failures, and `FAULT`. No recovery internal material
remained.

The following real FINAM `REAL_READONLY --once` cycle passed preflight with
`live_trading_authorized = false`, loaded CurrentUser DPAPI credentials without
printing the secret or account ID, and exited 0. It advanced cycle 19 to 20,
reset failures 5 to 0, and produced `HEALTHY` / `PASS`; every production
instrument had `h1 == expected_h1 == 2026-10-02T12:00:00+00:00`. The heartbeat
recorded the exact production ID, entries disabled, zero unresolved orders,
cycle 20, and zero failures. Order-capable calls were `[]`. The Scheduled Task
remained Disabled; no supervisor process or recovery-internal file remained;
credential and account-ID environment variables were absent. No live order was
transmitted and no live trading was authorized.

### Stage 8.8.7 final operational acceptance

Status: `STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`.

Stage 8.8 operational hardening is COMPLETE. Stages 8.8.1, 8.8.2, 8.8.3,
8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

Physical Intel acceptance executed against exact GitHub merge
`bda46f57f0f977e05593c46b55851c40c4ad34fe`. The external acceptance artifact
remains outside Git and is referenced only by SHA-256
`181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E`.
The accepted Windows gate passed 267 Stage 8 tests, 43 final operational checks,
132 Stage 8 checks, and 22 Stage 7 checks plus 19 mutation tests. One
`REAL_READONLY --once` cycle advanced cycle count 20 to 21 and all N4 H1
watermarks monotonically from 12:00 to 13:00 UTC with expected-H1 equality.
Final state was `HEALTHY` / `PASS`, entries disabled, zero unresolved orders,
and zero failures. The Scheduled Task remained Disabled, process and recovery
internal file counts were zero, and secret/account environment variables were
absent. No live order was transmitted and no authorization changed. Repository
tooling validates the provenance and hash; it did not generate the evidence.

**Stage 8.9 is COMPLETE.** Stage 8.10 is **COMPLETE**; Stages 8.10.1 through 8.10.5 are complete; Stage 8.10.6 is complete; Stage 8.10.7 is complete; Stage 8.10.8 is complete.
LIVE trading and real-order transmission remain unauthorized.

## Current handoff

Stage 8.9 is **COMPLETE**. Stage 8.10 is **COMPLETE**. Stage 8.11 — Controlled Real Execution Acceptance — is now **COMPLETE / PASS**.

Canonical Stage 8.11 physical acceptance authority:

- accepted code commit: `72a910e49b876cda99484a810e6f8a1b16ac0209`;
- immutable attempt: `stage8.11.attempt7`;
- external evidence: `runtime/diagnostics/stage8_11_physical_acceptance_attempt7.json`;
- evidence SHA-256: `704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F`;
- fixed physical case: `CNYRUBF@RTSX`, LONG, quantity `1`;
- exactly two real order-endpoint calls: one entry POST and one controlled flatten POST;
- broker fills proven: `2`;
- entry fill proven: `true`;
- one-contract position observed: `true`;
- controlled flatten proven: `true`;
- final position quantity: `0`;
- final active broker orders: `0`;
- unresolved Stage 8.11 intents: `0`;
- reconciliation result: `PASS`;
- physical result classification: `PASS`;
- final production kill switch: `HALTED`;
- Scheduled Task: `Disabled`.

The accepted normal reconciliation model is position-authoritative: after each physical POST, synchronous fill/risk authority is the exact `/account` position. Normal fill detection does not depend on `/trades`, exact `/orders/{id}`, `executed_quantity`, `remaining_quantity`, or the former order-status state machine. The physical authorization used for attempt7 is consumed. Current `execution_authorized = false`; real-order transmission remains unauthorized after the Stage 8.11 PASS.

Attempts 1–6, their failures/OIR classifications, manual closes, and recovery evidence remain immutable historical provenance and are not reclassified by the attempt7 PASS.

Stage 8.12 — **STARTED / STAGES 8.12.1–8.12.3 COMPLETE / STAGE 8.12.4 IMPLEMENTATION IN PROGRESS / NOT AUTHORIZED**. Stage 8.12.1 — Production runtime assembly — is **COMPLETE / PASS**. Stage 8.12.2 — Production path conformance and failure audit — is **COMPLETE / PASS**. Stage 8.12.3 — Intel production preflight — is **COMPLETE / PASS**.

Canonical Stage 8.12.1 authority:

- accepted merged code commit: `3f2d68ca0c327271fb543a0b63c0e8f842c855bd`;
- external test-only verifier evidence SHA-256: `F11FD6620A21F48499600392F49D3FC8A2340765B2B7B1C3C190822D8316513C`;
- structural zero-order boundary: `PASS`;
- Stage 8.12.1 runtime + N4 capacity tests: `25/25 PASS`;
- frozen Stage 7 / risk / margin regression: `166/166 PASS`;
- Stage 8.11 position-authority regression: `113/113 PASS`;
- independent Stage 8 audit: `PASS`;
- final operational audit: `PASS`;
- test-only real-order count: `0`;
- current `execution_authorized = false`;
- production kill switch: `HALTED`;
- production Scheduled Task: `Disabled`.

Canonical Stage 8.12.2 authority:

- accepted tested main commit: `2a15f4331afc1433dfbfd0464108e39e59d236f8`;
- external test-only verifier evidence SHA-256: `4F58595E2F62F2A377E5525972B9E88A136B2F9BC51760268D012AF94A70AE9F`;
- Stage 8.12.2 end-to-end + protective-stop conformance: `19/19 PASS`;
- Stage 8.12.1 runtime regression: `25/25 PASS`;
- R15 / margin / same-batch financial regressions: `144/144 PASS`;
- readonly account / H1 freshness / kill-switch regressions: `48/48 PASS`;
- Stage 8.11 bounded position-authority / timeout regressions: `113/113 PASS`;
- frozen research-to-robot / Stage 7 core conformance: `111/111 PASS`;
- independent Stage 8 audit: `PASS` (`262` checks);
- final operational audit: `PASS` (`149` checks);
- test-only real-order count: `0`;
- real order endpoint called: `false`;
- current `execution_authorized = false`;
- production kill switch: `HALTED`;
- production Scheduled Task: `Disabled`.

Stage 8.12.2 is closed as TEST/AUDIT ONLY with zero real orders.
Canonical Stage 8.12.3 authority:

- accepted Intel preflight commit: `0a40e3bf7a97f0c011d3a6f5216d9f61dd52ef30`;
- external sanitized evidence: `runtime/diagnostics/stage8_12_3_intel_preflight.json`;
- evidence SHA-256: `9584F45186DE38ABAE9209E1F326255C783AF762CD736EA45718D19C93BC61B1`;
- focused Stage 8.12 zero-order regression: `205/205 PASS`;
- independent Stage 8 audit: `PASS` (`262` checks);
- final operational audit: `PASS` (`149` checks);
- physical result: `STAGE_8_12_3_INTEL_PRODUCTION_PREFLIGHT_PASS`;
- exact Stage 7 production ID / active identity / real-account binding / trading-capable DPAPI credential: `PASS`;
- frozen N4 registry, tradability, current H1/reconciliation, clean broker account, and production-state continuity: `PASS`;
- external evidence contains the required N4 simultaneous-capacity report, strategy-consistent loss-per-contract, and 0/10/20/30% reserve scenarios; account financial values remain external and are not reproduced in the public repository;
- real order endpoint calls: `0`;
- real order count: `0`;
- `execution_authorized = false`;
- production kill switch: `HALTED`;
- production Scheduled Task: `DisabledOrAbsent`;
- Stage 8.12.4: `NOT_STARTED_NOT_AUTHORIZED`.

Stage 8.12.3 is **COMPLETE / PASS / REAL ACCOUNT / ZERO ORDERS / STILL NOT AUTHORIZED**. Stage 8.12.4 — Explicit FULL/R15 production authorization and activation — is the **CURRENT GATE** and remains the only gate that may authorize continuous real production trading.

Stage 8.12.4 — Explicit FULL/R15 production authorization and activation — is now **STARTED / IMPLEMENTATION IN PROGRESS / NOT AUTHORIZED**.

Current Stage 8.12.4 implementation boundary:

- durable production authorization is repository-external, create-only, and bound to the exact production commit, sanitized real-account hash, frozen production ID/identity, Stage 8.12.2 evidence SHA, and Stage 8.12.3 evidence SHA;
- creating authorization requires a separate exact operator authorization phrase; importing code or possessing the trading credential never authorizes execution;
- a production-aware heartbeat/reconciliation gate is separate from the historical REAL_READONLY flat-account gate, so reconciled frozen N4 positions do not silently disable FULL portfolio semantics;
- the FINAM transport now has a dedicated SL/TP POST primitive and preserves no-retry / uncertain-submission behavior;
- market entry requires durable authorization + `ARMED` + a fresh healthy production gate;
- protective-stop installation/replacement and emergency exit remain risk-reducing operations after authorization and are not disabled merely because the kill switch subsequently HALTs new entries;
- no authorization record has been created, the kill switch remains `HALTED`, the production Scheduled Task remains disabled, and no Stage 8.12.4 real order has been transmitted.

Stage 8.12.4 activation remains pending exact-commit zero-order validation and a new explicit operator authorization bound to that exact accepted commit.

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

## Stage 8.9 funding and margin validation closeout

Canonical repository status: `STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.
Stage 8.9.8 is **COMPLETE**, Stage 8.9.9 is **PHYSICAL REVALIDATION COMPLETE**,
Stage 8.9.10 is **COMPLETE**, and Stage 8.9 is **COMPLETE**.

The accepted post-funding physical REAL_READONLY run used exact code commit
`1013a5a2324e015ab3bc047a7b9af9064552cd10` and returned
`STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1`, classification
`STAGE_8_9_FUNDING_MARGIN_VALIDATED`, reason `ALL_AUTHORITIES_VALID`.
Its external diagnostic report SHA-256 is
`C87400F845B73A666B95C83DA2E3B6B710F36F3210AD4AD175BFDABB453864D5`, and its
external physical summary SHA-256 is
`099F85A0DCCF94D404411CFFAC2F5D8C80D606C5C1B5AA2F5B650E8BF5FEB636`.
The raw external JSON, account identity, financial values, broker responses,
DPAPI material, runtime database, and runtime audit JSON remain outside Git.

The accepted authorities were a clean, active UNION account with a READ_ONLY
token, exactly one `portfolio_mc` and no `portfolio_forts`, valid financial
schema, MC initial and maintenance margins, equity, directional margins, exact
frozen N4 binding, funding/margin feasibility, and batch budget. No
order-capable operation occurred. Across eight N4-direction sizing cases,
`sizing_case_count = 8`, `positive_capacity_case_count = 4`,
`zero_capacity_case_count = 4`, and
`positive_batch_reservation_count = 1`. The positive cases were
`CNYRUBF:LONG:QTY=2`, `CNYRUBF:SHORT:QTY=2`, `GLDRUBF:LONG:QTY=1`, and
`GLDRUBF:SHORT:QTY=1`.

This proves account funding authority, FINAM margin authority, at least one
executable contract-capacity case, and 4/8 positive N4-direction cases in the
accepted run. It does **not** prove that every N4 instrument has positive
capacity, simultaneous FULL N4 portfolio capacity, FULL/R15 production funding
sufficiency, permission to trade, trading-token readiness, or one-contract real
execution acceptance. USDRUBF and IMOEXF may remain zero-capacity at the current
account balance; those limitations remain later gates.

The immediately previous pre-funding result is retained as **historical Stage
8.9.9 evidence only**: `BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY` /
`ZERO_CONTRACT_CAPACITY`, accepted code
`c461911fdceddf54a2a6fe6768574dd93f4844d1`, diagnostic SHA-256
`F307D3F5ADC4525FF304B9582F683B89A097FC9BCFB502E8150FC98D2625860F`, summary
SHA-256 `F36B16565F9E08C38B3264831DCA94A65390275F7A2B78A3C6C90302E4A7C09B`, and
`positive_capacity_case_count = 0`. It is not a current blocker.

The earlier FORTS-only implementation result is also retained as **historical
evidence only**: `BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE` /
`FORTS_PORTFOLIO_MISSING`, accepted code
`5deedb49f16d9f2525c430383a029017cd9a53ce`, diagnostic SHA-256
`2911D7857B9404E5178FF1A754A9168845E457A9349CEF7B1AFD0E088E06BF46`, and
summary SHA-256
`59A9ADD4BD229C7A7BF3E20337E494F90CF90082208469AD5A694A4B075D852B`. It is
not a current blocker.

Stage 8.10 is **COMPLETE** because Stage 8.10.1 and Stage 8.10.2 are complete.
Stage 8.10.3 is **COMPLETE**. Stage 8.10.4 is **COMPLETE**. Stage 8.10.5 is **COMPLETE** after accepted physical offline validation. Stage 8.11.0 is **COMPLETE**, Stage 8.11.1 and 8.11.2 are **COMPLETE / PASS**, and Stage 8.11.3 prior authorization is **CONSUMED**; Stage 8.11.4 failed HTTP 400 and Stage 8.11.7 historical intent recovery is COMPLETE / PASS; Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**.
`LIVE_TRADING_NOT_AUTHORIZED`, `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`, and
`NEW_ENTRIES_DISABLED` remain unchanged. No live order was transmitted and no
live trading was authorized.

## Stage 8.10 — trading-token lifecycle

Stage 8.9 is **COMPLETE** under
`STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`. Its accepted code,
diagnostic SHA-256, physical-summary SHA-256, capacity counts, classification,
and reason recorded above remain unchanged.

Stage 8.10 is **COMPLETE**. The current lifecycle records completion of all
eight Stage 8.10 gates under `STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE`.
This completion does not authorize Stage 8.11, permission to execute, or LIVE
trading.

Canonical Stage 8.10 sequence and status:

1. Stage 8.10.1 is **COMPLETE** — Trading Token Preconditions Gate.
   Canonical status: `STAGE_8_10_1_TRADING_TOKEN_PRECONDITIONS_COMPLETE`.
2. Stage 8.10.2 is **COMPLETE** — Secure Provisioning.
3. Stage 8.10.3 is **COMPLETE** — Identity / Account Binding.
4. Stage 8.10.4 is **COMPLETE** — Permission Boundary Validation.
5. Stage 8.10.5 is **COMPLETE** — Order Path Dry Validation.
6. Stage 8.10.6 is **COMPLETE** — Kill Switch / Safety Gates.
7. Stage 8.10.7 is **COMPLETE** — Intel Trading-Token Acceptance.
8. Stage 8.10.8 is **COMPLETE** — Stage 8.10 Closeout.

Stage 8.11.0 is **COMPLETE**, Stage 8.11.1 and 8.11.2 are **COMPLETE / PASS**, and Stage 8.11.3 prior authorization is **CONSUMED**; Stage 8.11.4 failed HTTP 400 and Stage 8.11.7 historical intent recovery is COMPLETE / PASS — Controlled Real Execution
Acceptance, exactly one-contract test. Stage 8.12 is **NOT STARTED / NOT AUTHORIZED** — FULL/R15 Production Authorization. Stage 8.11 remains the first
possible real-order gate and requires separate explicit authorization.

### Stage 8.10.1 security boundary

The READ_ONLY credential remains the only operational credential. Existing
REAL_READONLY credential handling remains bound to Windows CurrentUser DPAPI,
and the REAL_READONLY broker cannot submit real orders. Trading Token 1 is now provisioned locally in the separate Windows CurrentUser
DPAPI store. Its plaintext, account ID, DPAPI bytes, and runtime metadata remain
outside Git. Possession or storage of Token 1 does not authorize trading.

Plaintext tokens must never be written to Git, logs, command-line arguments,
committed JSON, runtime audit output, or repository metadata. Trading and
read-only credentials must be distinguishable by schema/mode, must never
silently substitute for each other, and token/account/production-ID binding
must fail closed. Acquiring or storing a token cannot authorize order
transmission.

Physical provisioning was performed and Trading Token 1 is provisioned locally
in Windows CurrentUser DPAPI. Token 1 has now been used, and FINAM authentication
has now been performed solely for Stage 8.10.3 identity/session validation.
Stage 8.10 order_count remains exactly 0;
no order-capable operation occurred, no live order was transmitted, and the
Scheduled Task remains Disabled. Possession or storage does not authorize
trading, and real-order capability is not authorized.

`LIVE_TRADING_NOT_AUTHORIZED`, `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`, and
`NEW_ENTRIES_DISABLED` remain enforced. The frozen production contract remains
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`
/ `TRAIL1__N4_01__FULL__R15`: T3, H1, exact N4 (`USDRUBF`, `CNYRUBF`,
`GLDRUBF`, `IMOEXF`), TRAIL1, FULL, R15, 1.5% of current realized equity per
new instrument position, 6% maximum nominal simultaneous initial risk, no
pyramiding, no session filter, and no runtime canonical fallback.


### Stage 8.10.2 secure provisioning completed gate

Canonical status: `STAGE_8_10_2_SECURE_PROVISIONING_COMPLETE`. Accepted physical code commit:
`f0c271e428c05ee0ff67b7941e342c06b48a42a0`. External physical evidence SHA-256:
`E5FEA93CE28006BC5ADA19F1AA1C1C365FF7CF4BE48A5A1B8BC8C5589DFD754D`. Physical
result: `STAGE_8_10_2_PHYSICAL_SECURE_PROVISIONING_LOCAL_PASS`. Physical
provisioning was performed and Trading Token 1 is provisioned locally in Windows
CurrentUser DPAPI. Possession/storage of Token 1 does not authorize trading.
`trading_token_used=false`; `finam_authentication_performed=false`; no
order-capable operation occurred; `order_count=0`; and the Scheduled Task remains
Disabled. In this historical Stage 8.10.2 snapshot, Stage 8.10.3 through Stage
8.10.8 had not yet completed. Current authority is recorded by the later Stage
8.10.8 closeout: Stage 8.10 is **COMPLETE**. Current authority is Stage 8.11
**IN PROGRESS / CODE READY PENDING PHYSICAL ACCEPTANCE**, while Stage 8.12 is
**NOT STARTED / NOT AUTHORIZED**. `LIVE_TRADING_NOT_AUTHORIZED`,
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`, and `NEW_ENTRIES_DISABLED` remain in
force.


## Stage 8.10.3 identity/account binding completed gate

Stage 8.10 is **COMPLETE**. Stage 8.10.1 is **COMPLETE** under
`STAGE_8_10_1_TRADING_TOKEN_PRECONDITIONS_COMPLETE`. Stage 8.10.2 is **COMPLETE**
under `STAGE_8_10_2_SECURE_PROVISIONING_COMPLETE`; its historical facts remain
scoped to that earlier gate. Stage 8.10.3 is **COMPLETE** under
`STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_COMPLETE`.

Accepted physical code commit: `428d285336380726a3ce00487e2c85eb755e2dd9`. External physical evidence SHA-256:
`0DA102E61AB06FFA6A508CC64203FEA3F56BBA3016891A887688A4E300E11BB6`. Physical result: `STAGE_8_10_3_IDENTITY_ACCOUNT_BINDING_PASS`. The external
`stage8_10_3_identity_account_binding.json` remains outside Git; only its digest
and sanitized facts are repository authority.

Before remote authentication, the trading and READ_ONLY credentials resolved
locally to the same production account. Token 1 successfully created a FINAM
session and the expected production account was enumerated exactly once. Token
1 has now been used and FINAM authentication has now been performed, solely for
Stage 8.10.3 session identity/account-binding validation. No permission
validation or order-path validation occurred. No order endpoint was called and
`order_count` remains exactly 0. LIVE trading and real-order transmission remain
unauthorized. The Scheduled Task remains Disabled.

In this historical Stage 8.10.3 snapshot, Stage 8.10.5 was
**NOT STARTED**. In the current lifecycle, Stage 8.10.4 and Stage 8.10.5 are **COMPLETE**. Stage 8.10.6 is **COMPLETE**, Stage 8.10.7 is **COMPLETE**, and Stage 8.10.8 is **COMPLETE**. Stage 8.11.0 is **COMPLETE**, Stage 8.11.1 and 8.11.2 are **COMPLETE / PASS**, and Stage 8.11.3 prior authorization is **CONSUMED**; Stage 8.11.4 failed HTTP 400 and Stage 8.11.7 historical intent recovery is COMPLETE / PASS. Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**. That Stage 8.10.5 code-ready statement is historical; Stage 8.10.5 is now **COMPLETE**.


## Stage 8.10.4 permission boundary complete

Canonical status: `STAGE_8_10_4_PERMISSION_BOUNDARY_COMPLETE`.
Stage 8.10.4 is **COMPLETE**. Accepted physical code:
`44858bacc2902591e11adc85cfa5f79e2b62dd5b`. External evidence SHA-256:
`E4AEDC153F89E000EC034E5F33A6EF7BECB5DA29BA253BC0B28B2AC3D0C26C5D`. Physical
result: `STAGE_8_10_4_TOKEN_PERMISSION_BOUNDARY_PASS`. The external
`stage8_10_4_permission_boundary.json` remains outside Git.

Before authentication, the READ_ONLY and trading credentials still resolved
locally to the same frozen production account. The READ_ONLY session and trading
Token 1 session were created successfully. The expected production account
appeared exactly once in each session. Session-details returned exact boolean
`readonly=true` for READ_ONLY and exact boolean `readonly=false` for trading
Token 1; the token-level permission boundary therefore passed.

This proves only the FINAM session-details token-level boundary. No order-path
validation occurred, no order endpoint was called, and `order_count=0`. LIVE
trading remains unauthorized, real-order transmission remains unauthorized, and
the Scheduled Task remains Disabled. At the time Stage 8.10.4 completed, Stage
8.10.5 through Stage 8.10.8 had not yet completed. Current authority is recorded
by the later Stage 8.10.8 closeout: Stage 8.10 is now **COMPLETE**. Stage 8.11
and Stage 8.12 remain **NOT STARTED / NOT AUTHORIZED**.


## Stage 8.10.5 physical offline order-path dry-validation complete

Canonical status: `STAGE_8_10_5_ORDER_PATH_DRY_VALIDATION_COMPLETE`.
Stage 8.10.5 is **COMPLETE**.

Accepted code commit: `ba284e95954c8473c0e77a95172117bc5cefaf65`.
External evidence SHA-256: `D878309E22FA49BFFA9EE9B37200C3FE207BF77DB5C29D6DE97010F1FFCE904A`.
Physical result: `STAGE_8_10_5_OFFLINE_ORDER_PATH_DRY_VALIDATION_PASS`.
The external `stage8_10_5_order_path_dry_validation.json` remains outside Git;
only its digest and sanitized facts are repository authority.

The physical validation used `OFFLINE_SYNTHETIC_NO_TRANSMISSION` and was fully
offline. No FINAM credential was used, no FINAM authentication occurred, no
external network call occurred, and no real account ID was used. All 16 frozen
N4 broker payload cases passed, including client-order-ID and market-order
serialization validation. One synthetic order POST was intercepted in the
success path and one synthetic order POST was intercepted in the uncertainty
path. The automatic order retry count was zero. The real order endpoint remained
uncalled (`real_order_endpoint_called = false`) and `real_order_count = 0`.
This validates only deterministic local construction and serialization through
an in-process synthetic transport; it does not establish broker acceptance,
execution permission, exchange acceptance, fills, cancellation, margin
sufficiency, LIVE readiness, or production trading authorization.

- Stage 8.10.1 is **COMPLETE**.
- Stage 8.10.2 is **COMPLETE**.
- Stage 8.10.3 is **COMPLETE**.
- Stage 8.10.4 is **COMPLETE**; its historical authority is unchanged.
- Stage 8.10.5 is **COMPLETE**.
- Stage 8.10.6 is **COMPLETE**. Stage 8.10.7 is **COMPLETE**. Stage 8.10.8 is **COMPLETE**.
- Stage 8.10 is **COMPLETE**.
- Stage 8.11.0 is **COMPLETE**, Stage 8.11.1 and 8.11.2 are **COMPLETE / PASS**, and Stage 8.11.3 prior authorization is **CONSUMED**; Stage 8.11.4 failed HTTP 400 and Stage 8.11.7 historical intent recovery is COMPLETE / PASS. Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**.

Stage 8.10.6 — Kill Switch / Safety Gates is **COMPLETE** after accepted physical Intel validation. LIVE trading and
real-order transmission remain unauthorized, and the Scheduled Task remains
Disabled. `LIVE_TRADING_NOT_AUTHORIZED` and
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remain in force.

## Stage 8.10.6 kill switch / safety gates complete

Canonical status: `STAGE_8_10_6_KILL_SWITCH_SAFETY_GATES_COMPLETE`. Physical validation is complete on accepted code `35ec9007e6302d66e35e1a42a34fc2e77be8a467`; the external evidence SHA-256 is `CF34E54212B3385F154804F440361FE5E213B0AFA63D8DD8AE56E1EBB49D6B30`, and the physical result is `STAGE_8_10_6_PHYSICAL_SAFETY_GATE_VALIDATION_PASS`.

On Intel, pandas 3.0.6 was present and the full Stage 8 suite passed 518 tests with 0 failures. The production kill switch was initialized and remained `HALTED`. The isolated synthetic matrix passed all 25 cases: 1 `OPEN` and 24 `BLOCKED`; emergency HALT passed. `execution_authorized=false`. No credential was used, no FINAM authentication or external network request occurred, no real order endpoint was called, and the real order count was 0. The Scheduled Task remained Disabled. At the time of this historical Stage 8.10.6 snapshot, Stage 8.10.7 had not started; it completed subsequently.

The durable external kill switch defaults fail closed. Its canonical safe production state is `HALTED`; a missing, malformed, mismatched, or unknown state blocks new entries. `ARMED` alone never authorizes trading: a separate exact `execution_authorized=true` input is required, and the current/operator value is `false`. The Stage 8.10.6 wrapper exposes HALT only and cannot arm production. This is only a new-entry inhibit; it neither implements nor authorizes exits, cancels, broker calls, LIVE trading, or order transmission. Existing LIVE and real-order-transmission blocks remain unchanged.

Stage 8.10.7 is **COMPLETE** and Stage 8.10.8 is **COMPLETE**. Stage 8.10 is **COMPLETE**. Stage 8.11.0 is **COMPLETE**, Stage 8.11.1 and 8.11.2 are **COMPLETE / PASS**, and Stage 8.11.3 prior authorization is **CONSUMED**; Stage 8.11.4 failed HTTP 400 and Stage 8.11.7 historical intent recovery is COMPLETE / PASS; Stage 8.12 remains **NOT STARTED / NOT AUTHORIZED**.


## Stage 8.10.7 Intel Trading-Token acceptance complete

Stage 8.10.7 is **COMPLETE** (`STAGE_8_10_7_INTEL_TRADING_TOKEN_ACCEPTANCE_COMPLETE`). Physical Intel validation was accepted against code commit `df4bba6be4f98ba4659e13a01c90bec8e4162ff3`; the external evidence SHA-256 is `A2A6B330A5DC1F15D67A84860223D80786022B634BB8B6CD73E01C815EE7D1B6`, and the physical result is `STAGE_8_10_7_PHYSICAL_INTEL_TRADING_TOKEN_ACCEPTANCE_PASS`. The external report remains outside Git.

The accepted Intel host used pandas 3.0.6. Focused Stage 8.10.7 validation passed 97 tests (91 deselected), and the full Stage 8 suite passed 615 tests with 0 failures. The DPAPI CurrentUser Trading credential was validated, and its production/account identity matched the locally loaded READ_ONLY credential. Trading Token 1 alone was used for remote authentication; the READ_ONLY credential was not used for remote authentication. FINAM authentication created one session, and the expected production account occurred exactly once. Session details returned the exact boolean `readonly=false`, confirming only the token/session write-permission boundary.

The remote method scope was strictly `SESSION_CREATE_AND_DETAILS_ONLY` (`FinamAPI.create_session()` and `FinamAPI.session_details()`). No order permission was tested: `order_endpoint_called=false`, `order_count=0`, `execution_authorized=false`, `live_trading_authorized=false`, and `real_order_transmission_authorized=false`. The valid production kill switch was observed `HALTED` both before and after authentication, remained unmodified, and the Scheduled Task remained Disabled.

At the time Stage 8.10.7 physical acceptance completed, Stage 8.10.7 was
**COMPLETE**, Stage 8.10.8 was **NOT STARTED**, and Stage 8.10 remained **IN
PROGRESS**. Subsequently, the repository-only Stage 8.10.8 closeout completed;
current authority records Stage 8.10.8 and Stage 8.10 as **COMPLETE**. The next
separate lifecycle gate is Stage 8.11 — Controlled Real Execution Acceptance,
which remains **NOT STARTED / NOT AUTHORIZED**. Stage 8.12 also remains **NOT
STARTED / NOT AUTHORIZED**. `LIVE_TRADING_NOT_AUTHORIZED` and
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remain in force.


## Stage 8.10.8 repository-only lifecycle closeout

Stage 8.10.8 is **COMPLETE**. Stage 8.10 is **COMPLETE** under the canonical overall status `STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE`. This repository-only closeout created no new physical evidence, accepted-code commit, external evidence SHA, or physical result. All seven predecessor gates retain their exact accepted historical authority and are **COMPLETE**.

The accepted lifecycle establishes these aggregate safety facts: Trading Token 1 is provisioned in a separate Windows CurrentUser DPAPI store; local READ_ONLY/trading production-account identity and the token-level readonly boundary were validated; the order serialization/path was validated only through offline synthetic cases; kill-switch/safety gates and the Intel Trading Token session acceptance were physically validated. `readonly=false` confirms only the token write-permission boundary and is not order acceptance or system authorization. A synthetic POST is not a real FINAM order request.

The production kill switch final accepted state is `HALTED`; `execution_authorized` remains `false`; no real order endpoint was called during Stage 8.10; and the aggregate real order count is exactly 0. The Scheduled Task remains Disabled. `LIVE_TRADING_NOT_AUTHORIZED`, `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`, and `NEW_ENTRIES_DISABLED` for existing `REAL_READONLY` paths remain in force.

Stage 8.11.1 and Stage 8.11.2 are **COMPLETE / PASS**. Stage 8.11.3 prior authorization is **CONSUMED**; Stage 8.11 closeout is complete and a new explicit authorization remains the gate for any physical retry. Stage 8.12 is **NOT STARTED / NOT AUTHORIZED**.

## Stage 8.11.0–8.11.2 canonical lifecycle closeout (2026-10-04)

The accepted physical PRECHECK authority is commit
`9be31f1723877a9c542f89027052570425f7e976`, production specification
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`,
`schema_id = stage8_11_intel_precheck.v1`, and
`mode = STAGE8_11_PRECHECK_ONLY`. The external report remains outside Git at
`runtime/diagnostics/stage8_11_intel_precheck.json`; its SHA-256 is
`7171B7CD0098FF51159DC05C46C0326BF7F412A2D9EA0CBB3F9BDAFBE7745455`.
The external canonical acceptance ledger remains outside Git at
`runtime/state/stage8-11-acceptance.sqlite3`; its physically observed SHA-256 is
`A83C93733321C696225F606A5DBE584413915DA3C46C2B4A261091EC85B7C354`.

The sanitized PRECHECK facts are: Stage 8.10 authority `PASS`; DPAPI authority
`PASS`; trading-session write-capable boundary `PASS`; account binding `PASS`;
reconciliation `PASS`; active orders `0`; canonical unresolved acceptance intents
`0`; unresolved broker intents/orders `0`; instrument binding `PASS`; tradable
`PASS`; recovery readiness `PASS`; R15 permits at least one contract `true`; margin
permits at least one contract `true`; acceptance quantity `1`; execution authorization
observed `false`; order endpoint call count `0`; real order count `0`; and kill switch
observed `HALTED`. The exact and only safety-gate reasons were
`KILL_SWITCH_HALTED` and `EXECUTION_NOT_AUTHORIZED`. Stage 8.12 was
`NOT_STARTED_NOT_AUTHORIZED`.

Immediately before PRECHECK, one structurally order-incapable REAL_READONLY supervisor
cycle completed with: `cycle_count = 23`, `health_status = HEALTHY`,
`reconciliation_status = PASS`, `consecutive_failures = 0`, `entries_enabled = false`,
`unresolved_order_count = 0`, last completed H1
`2026-10-04T10:00:00+00:00`, last successful FINAM contact
`2026-10-04T11:58:57.828648+00:00`, and heartbeat
`2026-10-04T11:59:01.549910+00:00`. Only the sanitized account SHA is retained:
`a113cd66fb2aff5583ddebb480bacf71876cf4f7c10e7209ac6330ccec456826`.

The operational physical-acceptance candidate was research symbol `CNYRUBF`, FINAM
symbol `CNYRUBF@RTSX`, prospective direction `LONG`, quantity `1`. This was **not a
trading signal and not performance selection**. The PRECHECK applies frozen N4
feasibility order `USDRUBF → CNYRUBF → GLDRUBF → IMOEXF` and selects the first member
for which frozen R15 capacity and current directional FINAM margin permit one contract.
It is not a T3 entry signal, PF ranking, optimizer result, portfolio preference, or
production allocation change.

The independent audit result is
`STAGE_8_11_2_INDEPENDENT_PRECHECK_EVIDENCE_AUDIT_PASS`. It confirmed accepted-code
HEAD, fresh healthy heartbeat, account and reconciliation authority, separate
acceptance-ledger and supervisor authorities, zero unresolved acceptance intents,
zero active broker orders, exact frozen registry binding, feasibility-order selection,
`execution_authorized = false`, `HALTED`, zero endpoint calls, zero real orders, and
Scheduled Task `Disabled`. It independently reconstructed the report SHA from the
displayed canonical JSON serialization. The ledger SHA was physically observed; the
external SQLite binary was **not** claimed to have been independently byte-for-byte
rehashed outside the Intel host.

Historical provenance is retained. The first result, `STAGE8_11_SAFETY_GATE_BLOCKED`,
was caused by stale heartbeat/contact after the supervisor was intentionally stopped;
a fresh order-incapable REAL_READONLY cycle removed those transient blockers. The
second, `STAGE8_11_CANONICAL_INTENTS_INVALID`, is classified
`BLOCKED_CANONICAL_INTENT_LEDGER_AUTHORITY_MISMATCH`: PR #356 incorrectly treated
`readonly-supervisor.sqlite3` (production `OperationalState`) as a `StateStore` intent
ledger. The dedicated `stage8-11-acceptance.sqlite3` authority corrected that defect.
The successful PRECHECK supersedes both as the current result without erasing them.

Persistence correction PR #357 has base
`ea090d99266d5dae808c03024f327c41fb8b9170`, head
`60e3f72dae3a08eeb3ba8c756861efbb4c4f28e7`, and merge
`f29053e2c4b5f687115f0a5b12f582e822b60ea1`. Later exact-ledger-schema hardening PR
#358 has base `f29053e2c4b5f687115f0a5b12f582e822b60ea1`, head
`40fcf6f5c165e8bd64b128949358aa7475521f1b`, and merge
`9be31f1723877a9c542f89027052570425f7e976`. PR #358 does not replace PR #357's
historical persistence authority.

Stage 8.11.3 prior authorization is `CONSUMED`. After historical recovery and closeout, and until a new separate explicit operator authorization
after merge and independent audit: kill switch stays `HALTED`;
`execution_authorized = false`; normal LIVE and real-order transmission remain
unauthorized; existing REAL_READONLY paths remain order-incapable; Scheduled Task
stays `Disabled`; and no physical acceptance broker is invoked. There is no automatic
transition from 8.11.2 to 8.11.3. Stage 8.12 remains FULL/R15 Production Authorization,
`NOT STARTED / NOT AUTHORIZED`. Frozen identity `TRAIL1__N4_01__FULL__R15` and all
T3/H1/TRAIL1, N4, R15, 6% cap, realized-equity sizing, margin cap, no-pyramiding,
no-session-filter, and no-canonical-fallback semantics remain unchanged.

### Stage 8.11.3 corrective production-readiness record

PR #360 is the operator-boundary predecessor authority: base
`cc1508e87c0cfc1994352761aa800da58751c132`, head
`a233ebd9c1d56d85e6878389b3e4fb86a0054683`, and merge
`a54465d84b4eddabff38519011e8a26eafbfdd6d`. The corrective findings are
`STAGE8_11_PHYSICAL_EVIDENCE_UNPROVEN_STATE_DEFAULTED_SAFE` and
`STAGE8_11_NO_FILL_FLAT_STATE_NOT_PROVEN`. This is a code-readiness finding:
the physical wrapper has never been run, execution remains unauthorized, the
real-order count remains zero, and the kill switch remains `HALTED`.
