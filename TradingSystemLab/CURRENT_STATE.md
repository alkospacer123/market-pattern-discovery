# Current state — read first

## Active handoff

TradingSystemLab is in **Stage 8 Robot / FINAM integration**.

Stage 7 Production Specification Freeze is complete and immutable. Stage 8.8
operational hardening is complete. Stage 8.9 funding/margin validation is
**COMPLETE** under `STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.
Stage 8.10, Stage 8.11, and Stage 8.12 are **NOT STARTED / NOT AUTHORIZED**.

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

Stage 8.9 is **COMPLETE**.
Canonical status: `STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.

### Historical old implementation

The earlier FORTS-only implementation result is retained strictly as historical
provenance: `BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE` /
`FORTS_PORTFOLIO_MISSING`, accepted code
`5deedb49f16d9f2525c430383a029017cd9a53ce`, diagnostic SHA-256
`2911D7857B9404E5178FF1A754A9168845E457A9349CEF7B1AFD0E088E06BF46`, and
physical-summary SHA-256
`59A9ADD4BD229C7A7BF3E20337E494F90CF90082208469AD5A694A4B075D852B`.
It is not a current blocker.

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

Its pre-funding zero-capacity result is retained strictly as historical
provenance: `BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY` /
`ZERO_CONTRACT_CAPACITY`, accepted code
`c461911fdceddf54a2a6fe6768574dd93f4844d1`, diagnostic SHA-256
`F307D3F5ADC4525FF304B9582F683B89A097FC9BCFB502E8150FC98D2625860F`, physical
summary SHA-256
`F36B16565F9E08C38B3264831DCA94A65390275F7A2B78A3C6C90302E4A7C09B`, and
`positive_capacity_case_count = 0`. It is not a current blocker.

### Stage 8.9.10 — post-funding closeout

Stage 8.9.10 is **COMPLETE**.

The accepted physical REAL_READONLY run used exact code commit
`1013a5a2324e015ab3bc047a7b9af9064552cd10` and returned
`STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1`, classification
`STAGE_8_9_FUNDING_MARGIN_VALIDATED`, reason `ALL_AUTHORITIES_VALID`.

External diagnostic report SHA-256:
`C87400F845B73A666B95C83DA2E3B6B710F36F3210AD4AD175BFDABB453864D5`.

External physical summary SHA-256:
`099F85A0DCCF94D404411CFFAC2F5D8C80D606C5C1B5AA2F5B650E8BF5FEB636`.

The accepted result has `sizing_case_count = 8`,
`positive_capacity_case_count = 4`, `zero_capacity_case_count = 4`, and
`positive_batch_reservation_count = 1`. Positive cases were
`CNYRUBF:LONG:QTY=2`, `CNYRUBF:SHORT:QTY=2`, `GLDRUBF:LONG:QTY=1`, and
`GLDRUBF:SHORT:QTY=1`. It proves account funding authority, FINAM margin
authority, and at least one executable contract-capacity case.

It does **not** prove that every N4 instrument has positive capacity,
simultaneous FULL N4 portfolio capacity, FULL/R15 production funding
sufficiency, permission to trade, trading-token readiness, or one-contract real
execution acceptance. USDRUBF and IMOEXF may remain zero-capacity at the current
account balance.

The raw external JSON, account identity, financial values, broker responses,
DPAPI material, runtime database, and runtime audit JSON remain outside Git.
No order-capable operation occurred.

## Authorization boundary

- `LIVE_TRADING_NOT_AUTHORIZED` remains in force.
- `REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remains in force.
- `NEW_ENTRIES_DISABLED` remains in force for the accepted REAL_READONLY path.
- Stage 8.10 is **NOT STARTED / NOT AUTHORIZED**.
- Stage 8.11 and Stage 8.12 are **NOT STARTED / NOT AUTHORIZED**.

## Current next action

The next lifecycle stage is Stage 8.10, but it is **NOT STARTED / NOT
AUTHORIZED**. Do not start it automatically. Any further gate requires separate
explicit authorization and must preserve the frozen Stage 7 production identity.

## Domain boundary

Do not mix TradingSystemLab with BBW, Level Touch, Round Level / Touch or other
projects.

## Update rule

Update this file after every accepted operational milestone/audit. The first
section must always reflect the latest actual blocker and authorization state.
