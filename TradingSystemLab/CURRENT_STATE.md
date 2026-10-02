# Current state — read first

## Active handoff

TradingSystemLab has completed Stage 7 Production Specification Freeze and is
actively in **Stage 8 Robot / FINAM integration**, currently through
**Stage 8.8.5 stale-data protection code readiness**.

Resolve the current Git `main` SHA directly from GitHub during every independent
audit; this versioned file is not authoritative for a moving branch SHA.

Current Stage 8 repository audit state:

- `stage8_status`: `STAGE_8_8_5_STALE_DATA_PROTECTION_CODE_READY_PENDING_INTEL_FAULT_INJECTION`;
- Stage 8 independent repository audit: PASS, 111 checks, zero recorded errors;
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

Real Intel 24/7 restart/network-failure/recovery acceptance is still pending.

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
no-order semantics. The code is ready for Intel fault-injection validation.

**Operational gate remains open:** real Intel fault-injection validation of the
supervisor/stale-data behavior is still pending. Repository tests do not count
as completed 24/7 operational acceptance.

## Current next action

Do **not** start LIVE trading.

The next permitted work is operational validation on the Intel host under
REAL_READONLY with entries disabled, including restart/network/stale-data fault
injection and recovery verification.

Separately:

- Stage 8.9 funding readiness remains blocked by unavailable account financials;
- Stage 8.10 trading-token integration is pending;
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
