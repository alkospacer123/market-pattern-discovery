# Current state — read first

## Active handoff

TradingSystemLab has completed Stage 7 Production Specification Freeze and is
actively in **Stage 8 Robot / FINAM integration**, currently through
**Stage 8.8.7 Final Operational Audit — Intel acceptance complete**.

Repository status is
`BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE`.
Stage 8.8 operational hardening is COMPLETE. Stages 8.8.1, 8.8.2, 8.8.3,
8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE. Stage 8.9 is CURRENT; repository diagnostic readiness is retained and physical validation was performed with a fail-closed blocked result;
Stage 8.10/8.11/8.12 remain pending and not authorized.

Resolve the current Git `main` SHA directly from GitHub during every independent
audit; this versioned file is not authoritative for a moving branch SHA.

Current Stage 8 repository audit state:

- `stage8_status`: `STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE`;
- `stage8_8_7_status`: `STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`;
- Stage 8 independent repository audit: PASS, 142 checks, zero recorded errors;
- LIVE trading: **NOT AUTHORIZED**;
- real order transmission: **NOT AUTHORIZED**.

## Frozen Stage 7 production specification

Stage 7 is COMPLETE.

Sole active production specification:

**`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`**

Identity:

- `TRAIL1__N4_01__FULL__R15`;
- generation: v3 perpetual;
- strategy: T3;
- timeframe: H1;
- basket `N4_01`: `USDRUBF + CNYRUBF + GLDRUBF + IMOEXF`;
- overlay: TRAIL1;
- load: FULL;
- risk mode: R15;
- risk per new instrument position: **1.5% of current realized equity**;
- maximum nominal simultaneous initial risk: **6%**;
- realized equity only; unrealized PnL excluded from sizing;
- one active position per instrument; no pyramiding;
- no session entry filter;
- forbidden overlays: BE1, LOCK1_AFTER_2R, SESSION_10_21, ONE_BAR,
  EXIT_ON_OPPOSITE_REGIME, STRUCTURAL_STACK.

`CANONICAL__N4_01__FULL__R15` is
`STABLE_REFERENCE_NOT_ACTIVE_PRODUCTION` only and is never a runtime fallback.

Stage 7 independent audit: PASS, 22 checks and 19 mutation tests.

## Final pre-Stage-7 evidence

Stage 6.7 broad FULL/NORMALIZED evidence remains historical:

- 55 configurations / 110 R cases / 220 equity cases;
- broad frozen production-eligibility gate produced only N2 eligible cases;
- no broadly eligible case met the 70–80% target.

After that checkpoint, a separately authorized focused N4 FULL four-case analysis
was completed and independently audited:

- CANONICAL R15;
- TRAIL1 R15;
- CANONICAL R20;
- TRAIL1 R20.

Headline 2024+ historical evidence:

- CANONICAL R15: CAGR 109.13%, Max DD -16.34%;
- TRAIL1 R15: CAGR 122.44%, Max DD -19.96%;
- CANONICAL R20: CAGR 160.44%, Max DD -21.27%;
- TRAIL1 R20: CAGR 182.14%, Max DD -25.88%.

The four-case analysis did **not** automatically select production. The user
explicitly selected `TRAIL1__N4_01__FULL__R15`, and Stage 7 froze that exact
identity. R20 remains historical comparative evidence only.

## Stage 8 foundation and conformance

Stage 8 began after Stage 7 and now contains a fail-closed production robot
foundation under `TradingSystemLab/stage8_robot/`.

Key accepted properties:

- runtime parameters cannot alter the frozen Stage 7 strategy identity;
- no canonical-reference runtime fallback;
- LIVE mode always raises `LIVE_TRADING_NOT_AUTHORIZED`;
- REAL_READONLY broker `submit_order` raises
  `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED`;
- intent/state persistence is transactional SQLite with WAL and idempotency;
- exits and actual fees are applied before later same-timestamp entry sizing;
- C1 remains historical research evidence; live commissions/fees/slippage are
  separate operational inputs.

Historical research-to-robot conformance is exact:

- authority replay: **418 / 418 exact trades**, zero mismatches;
- independent production replay: **418 / 418 exact trades**, zero mismatches;
- repeated replay hashes are deterministic.

## FINAM production binding

The production registry contains all four N4 perpetual futures as
`AUTHENTICATED_REAL_READONLY`:

- USDRUBF → `USDRUBF@RTSX`, security ID `3447194`, step `0.01`, tick value 10 RUB,
  contract size 1000, quantity granularity 1;
- CNYRUBF → `CNYRUBF@RTSX`, security ID `3447192`, step `0.001`, tick value 1 RUB,
  contract size 1000, quantity granularity 1;
- GLDRUBF → `GLDRUBF@RTSX`, security ID `4454911`, step `0.1`, tick value 0.1 RUB,
  contract size 1, quantity granularity 1;
- IMOEXF → `IMOEXF@RTSX`, security ID `4631091`, step `0.5`, tick value 5 RUB,
  contract size 10, quantity granularity 1.

All four are modeled as `PERPETUAL_FUTURE`, automatic prolongation enabled,
quarterly exercise operator-only.

The 2026-10-01 operator REAL_READONLY diagnostic authenticated 4/4 instruments.
No real order was transmitted.

## Funding / margin gate

FULL/R15 production sizing code is margin-aware and fail-closed:

`floor_to_trade_lot(min(r15_quantity, floor(available_cash / directional_initial_margin)))`.

However, the clean UNION account used for REAL_READONLY validation did not
expose the required `portfolio_forts` funding structure. Therefore funding
readiness is currently:

**`BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE`**.

Do not fabricate equity, free cash, margin capacity, or hypothetical live sizing.

## Windows / Intel deployment state

Intel Windows deployment preparation is present under
`TradingSystemLab/stage8_robot/deploy/windows/`.

Implemented safeguards include:

- external runtime paths and single-instance lock;
- bounded logging and heartbeat;
- online SQLite backup;
- startup/reboot reconciliation;
- CurrentUser-only Windows DPAPI credential store;
- credential payload bound to the frozen production specification;
- explicit non-SYSTEM scheduled-task principal;
- ACL hardening;
- real Windows DPAPI round-trip / tamper / wrong-production-ID execution tests;
- fixes for explicit `System.Security` loading and Windows SID ACL handling.

Credentials are never committed to Git and must not be placed in command-line
arguments or logs.

## Stage 8.8.1 operational supervisor

REAL_READONLY operational supervisor code is ready.

It:

- forces REAL_READONLY;
- keeps new entries disabled;
- holds a lifetime instance lock;
- monitors account cleanliness, reconciliation, H1 data and heartbeat;
- persists only sanitized operational continuity;
- cannot transmit real orders.

Real Intel operational acceptance is complete. It covered supervisor startup and
`--once`, continuous-operation validation, restart, second-instance exclusion,
and reboot. It also covered network/API failure producing the expected
`UNHEALTHY` / `FAULT` state, recovery to `HEALTHY` / `PASS`, and reset of the
consecutive-failure counter. No order-capable call was made.

## Stage 8.8.5 stale H1 data protection

Externally validated real timing evidence established whole-hour UTC raw opens.
The implementation merges touching trading sessions into instrument-specific
windows and uses `min(open + 1 hour, window end)`, including a partial final bar.
The evidence itself remains outside Git.

Rules:

- only EARLY_TRADING, CORE_TRADING and LATE_TRADING generate expectations;
- auction, clearing and closed periods preserve `expected_h1:<instrument>`;
- cold start without schedule evidence or a persisted watermark fails closed;
- exact expected raw-open membership is required;
- malformed schedule evidence fails closed;
- if the newest completed H1 candle is stale, raise
  `STALE_COMPLETED_H1_DATA`;
- the failed cycle remains `FAULT` / `UNHEALTHY`;
- successful cycle count/watermark is not advanced;
- entries remain disabled;
- no order-capable call is introduced.

Repository synthetic tests/audit cover the validated grid, partial final bar,
stale/fresh recovery, persistence, per-instrument schedules, heartbeat and
no-order semantics.

Stage 8.8.5 status is
`STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE`. The real Intel stale-data
acceptance was executed against audited source Git head
`1c1c2bb5458827f200bc753e7e64db0272b33a8f`. PR #302 subsequently performed
the Stage 8.8.5 repository closeout; its GitHub-visible head was
`635bea24710cc41f0cb65eef9c6ed576494f5396`, and its merge commit was
`b19a3625698f4701b7c531cade5a27a497269b73`. PR #302 did not modify
`stage8_robot/readonly_supervisor.py`, `stage8_robot/finam_api.py`, or
`stage8_robot/tests/test_readonly_supervisor.py`, so the accepted H1
implementation remained byte-identical. The external acceptance artifact,
which remains outside Git, has SHA-256
`C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC`.

Sanitized acceptance facts: the clean cycle was `HEALTHY` / `PASS`; the
controlled missing-completed-H1 fault produced `STALE_COMPLETED_H1_DATA` and
`UNHEALTHY` / `FAULT`; successful cycle count, H1 state, and expected-H1 state
did not advance during the fault. Recovery returned `HEALTHY` / `PASS` and
reset consecutive failures to 0. Order-capable calls were 0, entries remained
disabled, and the production Scheduled Task remained Disabled throughout the
acceptance. No runtime JSON or raw FINAM response is stored in this repository.

## Stage 8.8.6 SQLite recovery acceptance

Do **not** start LIVE trading.

Stage 8.8.6 repository tooling backs up only
`state/readonly-supervisor.sqlite3` with SQLite's online API, binds each backup
to a strict checksum/production-ID manifest, retains database/manifest pairs,
and restores only a validated operational schema under the existing lifetime
lock via an atomic state-directory replacement. Stale WAL/SHM sidecars are
removed at commit. Offline recovery preserves the selected continuity values;
it does not fabricate a watermark or bypass the next normal supervisor cycle.

Status: `STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE`.

The physical Intel acceptance audited code commit
`dc2b79e74817e71435eee20103ae617e13067d8e`. Its external acceptance evidence
remains outside Git; its SHA-256 is
`1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6`.
Repository tests did not generate or substitute for that external evidence.

The Windows gate passed 27 SQLite recovery tests and the complete 255-test
Stage 8 suite. The Stage 8 independent audit passed 124 checks, while the Stage
7 production specification audit passed 22 checks and 19 mutation tests. The
Scheduled Task remained Disabled, supervisor process count was 0, and recovery
internal material count was 0.

The accepted real backup was
`readonly-supervisor-20261002T125325.986665Z.sqlite3`, with SHA-256
`00b5e4ca2b389d55389b6b57ac73b5e557c11b72daab8d6e118311613e0aa3b0` and
manifest SHA-256
`3d0ef1d7cb11ee592be32550625e8badefc596108f4d0c34eff6c5e12ceba822`.
The manifest used schema `stage8-readonly-sqlite-backup/v1`, contained the exact
production specification ID, matched the backup checksum, and passed
recovery-point validation.

Before controlled mutation, the operational logical SHA-256 was
`13f01f1009768ddce65dce079f70486f2cbc2508cd1ea8ec4787414a78e0d3be` with 9
rows. The observable `CONTROLLED_MUTATION` marker changed the row count to 10
and changed the logical SHA. Restore exited 0 with
`READONLY_STATE_RECOVERY_COMMITTED_RECONCILIATION_REQUIRED`; afterward the
logical SHA and row count returned exactly to their pre-mutation values, the
marker was absent, `cycle_count = 19`, `consecutive_failures = 5`, and
`last_reconciliation = FAULT`. Recovery internal material count was 0. This
established exact operational-state continuity through backup and restore.

One real FINAM `REAL_READONLY --once` reconciliation then used the existing
CurrentUser DPAPI credential path. Preflight passed with
`live_trading_authorized = false`; credential loading printed neither secret nor
account ID. The supervisor exited 0. Cycle count advanced 19 to 20,
consecutive failures reset 5 to 0, and reconciliation became `PASS`. For all
four production instruments, `h1 == expected_h1 ==
2026-10-02T12:00:00+00:00`. The resulting heartbeat was `REAL_READONLY`, exact
production specification ID, `HEALTHY` / `PASS`, entries disabled, zero
unresolved orders, cycle count 20, and zero consecutive failures. Supervisor
order-capable calls were `[]`.

After completion the Scheduled Task remained Disabled, supervisor process count
and recovery internal file count were 0, and `FINAM_API_SECRET` and
`FINAM_REAL_ACCOUNT_ID` were absent from the process environment. No live order
was transmitted and no live trading was authorized.

## Stage 8.8.7 final operational acceptance

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

## Current next action

**CURRENT: Stage 8.9 — Real Account Funding & Margin Validation.** Physical
validation was performed and is blocked by `BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE`
because the validated clean UNION account did not expose `portfolio_forts`.

Separately:

- Stage 8.9 physical funding readiness was determined by the accepted physical validation as `BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE`, reason `FORTS_PORTFOLIO_MISSING`; Stage 8.9 remains **CURRENT / BLOCKED / NOT COMPLETE**;
- Stage 8.10 trading-token integration is **NOT STARTED / NOT AUTHORIZED**;
- Stage 8.11/8.12 execution remains unauthorized.

Any change that enables live orders requires a separate explicit authorization
and its own audit.

## Historical research constraints

- v1/v2/v3 research identities and OOS verdicts remain immutable.
- 2025–2026 evidence used in Stage 6.x is retrospective/revealed, not fresh OOS.
- Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch, or
  other projects.

## Update rule

Update this file after every accepted Stage 8 operational milestone or audit.
Keep the first sections synchronized with the actual production/authorization
state in `main`.

## Stage 8.9 physical validation closeout

Repository diagnostic readiness is retained. Physical REAL_READONLY validation was performed on accepted Intel code commit `5deedb49f16d9f2525c430383a029017cd9a53ce`. `stage8_9_physical_validation_performed = true`. The result is `BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE`, reason `FORTS_PORTFOLIO_MISSING`. Diagnostic report SHA-256: `2911D7857B9404E5178FF1A754A9168845E457A9349CEF7B1AFD0E088E06BF46`. Physical validation summary SHA-256: `59A9ADD4BD229C7A7BF3E20337E494F90CF90082208469AD5A694A4B075D852B`. The external JSON evidence remains outside Git. The authenticated account was a clean, active `UNION` account using a read-only token, and its exact frozen N4 binding was valid. `portfolio_forts` was absent, so funding/margin feasibility remained `BLOCKED`; absence is not zero and no other field is a fallback. The no-order-call assertion was true. The Scheduled Task stayed Disabled; supervisor process and recovery internal file counts stayed zero; FINAM secret and account ID were removed from the process environment. The accepted physical run recorded Stage 8 repository audit PASS / 141 checks, Final Operational Audit PASS / 45 checks, Stage 7 production audit PASS / 22 checks / 19 mutation tests, and server preflight PASS. No physical order-capable operation occurred. Stage 8.9 is **CURRENT / BLOCKED / NOT COMPLETE**. Stage 8.10 is **NOT STARTED / NOT AUTHORIZED**. LIVE trading and real-order transmission remain unauthorized.
