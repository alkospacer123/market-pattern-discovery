# Current state — read first

## Active handoff

TradingSystemLab is in **Stage 8 Robot / FINAM integration**.

Stage 7 Production Specification Freeze is complete and immutable. Stage 8.8
operational hardening is complete. Stage 8.9 funding/margin validation has been
physically revalidated against the corrected UNION account authority, but Stage
8.9 is **NOT COMPLETE** because the current production account has zero contract
capacity under the frozen Stage 7 risk/sizing contract.

Current repository anchor before this memory sync:
`1013a5a2324e015ab3bc047a7b9af9064552cd10`.

## Frozen Stage 7 production specification

Production specification:
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.

Sole active identity:
`TRAIL1__N4_01__FULL__R15`.

Frozen semantics:

- v3 perpetual / T3 / H1;
- N4 basket: `USDRUBF + CNYRUBF + GLDRUBF + IMOEXF`;
- TRAIL1 only;
- FULL load;
- R15 = 1.5% current realized equity risk per new instrument position;
- maximum nominal simultaneous initial risk = 6%;
- one active position per instrument;
- no pyramiding;
- no session filter;
- no automatic canonical fallback;
- unrealized PnL excluded from sizing.

`CANONICAL__N4_01__FULL__R15` remains
`STABLE_REFERENCE_NOT_ACTIVE_PRODUCTION` only.

## Historical research / decision provenance

- v1, v2 and v3 research identities and TRUE OOS verdicts are immutable.
- v3 final TRUE OOS: T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`,
  T3/M30 `PASS`, T3/H1 `PASS`.
- Stage 5 retrospective authority remains `CORRECTED_SINGLE_C1`.
- Stage 6.x structural/basket work remains revealed retrospective evidence.
- The focused N4 FULL four-case analysis did not auto-select production; the user
  explicitly selected `TRAIL1__N4_01__FULL__R15`, which Stage 7 froze.

## Stage 8 research-to-robot conformance

Historical conformance remains exact and deterministic:

- research-authority replay: 418 / 418 exact trades;
- production-robot replay: 418 / 418 exact trades;
- zero timestamp, direction, price, state or R mismatches;
- repeated replay hashes match.

This validates implementation conformance only. It does not authorize live
trading.

## FINAM read-only binding

All four production instruments are committed as `AUTHENTICATED_REAL_READONLY`:

- USDRUBF → `USDRUBF@RTSX`, security ID 3447194;
- CNYRUBF → `CNYRUBF@RTSX`, security ID 3447192;
- GLDRUBF → `GLDRUBF@RTSX`, security ID 4454911;
- IMOEXF → `IMOEXF@RTSX`, security ID 4631091.

No real order has been transmitted. REAL_READONLY remains order-incapable.

## Stage 8.8 operational hardening

Stage 8.8 operational hardening is COMPLETE.
Stages 8.8.1, 8.8.2, 8.8.3, 8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

### Stage 8.8.5 — H1 freshness / stale-data acceptance

Status: `STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE`.

Accepted audited source commit:
`1c1c2bb5458827f200bc753e7e64db0272b33a8f`.

External Intel acceptance evidence SHA-256:
`C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC`.

Schedule-aware freshness is fail-closed. A missing completed expected H1 candle
raises `STALE_COMPLETED_H1_DATA`, produces `UNHEALTHY` / `FAULT`, leaves entries
disabled, and does not advance successful cycle/H1 state. Physical Intel
fault-injection and deterministic recovery passed.

### Stage 8.8.6 — SQLite backup/recovery

Status: `STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE`.

Accepted code commit:
`dc2b79e74817e71435eee20103ae617e13067d8e`.

External Intel evidence SHA-256:
`1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6`.

Accepted recovery hashes:

- backup: `00b5e4ca2b389d55389b6b57ac73b5e557c11b72daab8d6e118311613e0aa3b0`;
- manifest: `3d0ef1d7cb11ee592be32550625e8badefc596108f4d0c34eff6c5e12ceba822`;
- baseline logical state:
  `13f01f1009768ddce65dce079f70486f2cbc2508cd1ea8ec4787414a78e0d3be`.

Backup/recovery is fail-closed, Windows-safe, non-destructive on restore failure,
and preserves exact production identity/state authority.

### Stage 8.8.7 — Final Operational Audit

Status: `STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`.

Accepted code commit:
`bda46f57f0f977e05593c46b55851c40c4ad34fe`.

External Intel acceptance evidence SHA-256:
`181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E`.

Physical Intel acceptance completed with entries disabled and zero order-capable
activity. Final state was `HEALTHY` / `PASS`; instance locking, restart/recovery,
DPAPI credentials, heartbeat, H1 watermark continuity and recovery state passed.

## Stage 8.9 funding / margin authority

Stage 8.9 is **CURRENT** and **NOT COMPLETE**.

### Historical old implementation

Earlier Stage 8.9 physical evidence used an incorrect FORTS-only assumption for
a UNION production account. That earlier blocked result is historical provenance
only and is not the current blocker.

### Stage 8.9.8 — UNION / portfolio_mc authority resolution

Status: `STAGE_8_9_8_COMPLETE`.

Physical evidence established that the production account is `UNION` and
contains exactly one `portfolio_mc`. The previous FORTS-only funding authority
was corrected.

Post-funding portfolio-variant evidence SHA-256:
`60A529DB021B39E1C6117D01CCF3AB5B8B331073D407782E90383E4D124BADC5`.

Post-funding account financial-shape evidence SHA-256:
`EED27193E35F46FFCF13CFB4A2F2EAA4AB87A35F967D78139E97BFA885009371`.

### Stage 8.9.9 — physical revalidation

Stage 8.9.9 is **PHYSICAL REVALIDATION COMPLETE**.

Accepted physical REAL_READONLY code commit:
`c461911fdceddf54a2a6fe6768574dd93f4844d1`.

External diagnostic report SHA-256:
`F307D3F5ADC4525FF304B9582F683B89A097FC9BCFB502E8150FC98D2625860F`.

External physical summary SHA-256:
`F36B16565F9E08C38B3264831DCA94A65390275F7A2B78A3C6C90302E4A7C09B`.

The run confirmed the corrected UNION/`portfolio_mc` financial schema, equity,
directional margins, exact N4 binding, arithmetic and batch-budget mechanics.

However, `positive_capacity_case_count = 0` across the eight tested sizing cases,
with zero positive batch reservations.

### Stage 8.9.10 — current capacity gate

**CURRENT / BLOCKED**.

Current status:
`BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY`.

Current reason:
`ZERO_CONTRACT_CAPACITY`.

This is the **only active Stage 8.9 blocker**. It is distinct from financial
schema/binding/arithmetic validation, which passed. Zero capacity must never be
misclassified as funding-ready.

Stage 8.9 is NOT COMPLETE.

## Authorization boundary

- `LIVE_TRADING_NOT_AUTHORIZED` remains in force.
- `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remains in force.
- `NEW_ENTRIES_DISABLED` remains in force for the accepted REAL_READONLY path.
- Stage 8.10 trading-token integration is NOT STARTED / NOT AUTHORIZED.
- Stage 8.11/8.12 execution is NOT AUTHORIZED.

Do not bypass Stage 8.9.10, fabricate capacity, weaken frozen Stage 7 risk, or
reinterpret read-only acceptance as live authorization.

## Current next action

Stop at Stage 8.9.10 while contract capacity is zero.

Any work to resolve `ZERO_CONTRACT_CAPACITY` requires a new explicit
user-authorized task and must preserve the frozen Stage 7 production identity
and fail-closed sizing semantics. Do not start Stage 8.10 automatically.

## Domain boundary

Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch or other
projects.

## Update rule

Update this file after every accepted operational milestone/audit. The first
section must always reflect the latest actual blocker and authorization state.
