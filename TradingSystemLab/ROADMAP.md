# Evidence-based roadmap

## Governing research rule

The original H1 research lifecycle remains:

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

v1/v2/v3 are historical and immutable. The active roadmap is the frozen Stage 7
production specification plus Stage 8 operational/broker readiness.

## Historical research generations

- v1 — historical discovery / MTF evidence.
- v2 — complete; all four final TRUE OOS studies `BORDERLINE`.
- v3 Perpetual — complete; T2/M30 `BORDERLINE`, T2/H1 `BORDERLINE`,
  T3/M30 `PASS`, T3/H1 `PASS`.

## Post-v3 Stages 1–6.x

Closed historical evidence:

- Stage 1 master evidence consolidation;
- Stage 2 portfolio/diversification analysis;
- Stage 3 trade anatomy/failure analysis;
- Stage 4 structural hypothesis freeze;
- Stage 5 structural validation under `CORRECTED_SINGLE_C1`;
- Stage 6 / 6.x production-decision and retrospective reassessment evidence;
- focused N4 FULL four-case technical closeout.

The user explicitly selected TRAIL1 N4 FULL R15 from the final fixed N4 evidence.

## Stage 7 — Production Specification Freeze

**COMPLETE.**

Production specification:
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.

Sole active identity:
`TRAIL1__N4_01__FULL__R15`.

Frozen:

- v3 perpetual T3/H1;
- USDRUBF + CNYRUBF + GLDRUBF + IMOEXF;
- TRAIL1;
- FULL;
- R15 = 1.5% realized-equity risk per new position;
- max nominal initial risk 6%;
- no session filter;
- no pyramiding;
- no canonical fallback.

`CANONICAL__N4_01__FULL__R15` is reference only.

## Stage 8 — Robot / FINAM integration

**ACTIVE. LIVE TRADING NOT AUTHORIZED.**

Historical research-to-robot conformance remains 418/418 exact in both authority
and production replay with deterministic hashes and zero mismatch classes.

All four production instruments remain `AUTHENTICATED_REAL_READONLY`.

## Stage 8.8 — operational hardening

Stage 8.8 operational hardening is COMPLETE.
Stages 8.8.1, 8.8.2, 8.8.3, 8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

### Stage 8.8.5 — stale H1 protection

Status: `STAGE_8_8_5_STALE_DATA_PROTECTION_COMPLETE`.

Accepted audited source commit:
`1c1c2bb5458827f200bc753e7e64db0272b33a8f`.

External Intel evidence SHA-256:
`C57554AE3AE54018EC1E558108520088C1883718F0406E7B6C6669B4696A9CBC`.

Schedule-aware stale-data fault injection/recovery passed on Intel. Entries
remained disabled and no order-capable call was made.

### Stage 8.8.6 — SQLite backup/recovery

Status: `STAGE_8_8_6_SQLITE_RECOVERY_INTEL_ACCEPTANCE_COMPLETE`.

Accepted code commit:
`dc2b79e74817e71435eee20103ae617e13067d8e`.

External Intel evidence SHA-256:
`1A9B62D4BFC0E7384898C9DF9659E54E50E0E202BD44CE19413864AC2ECA14D6`.

Accepted backup SHA-256:
`00b5e4ca2b389d55389b6b57ac73b5e557c11b72daab8d6e118311613e0aa3b0`.

Accepted manifest SHA-256:
`3d0ef1d7cb11ee592be32550625e8badefc596108f4d0c34eff6c5e12ceba822`.

Accepted baseline logical-state SHA-256:
`13f01f1009768ddce65dce079f70486f2cbc2508cd1ea8ec4787414a78e0d3be`.

### Stage 8.8.7 — Final Operational Audit

Status: `STAGE_8_8_7_FINAL_OPERATIONAL_AUDIT_INTEL_ACCEPTANCE_COMPLETE`.

Accepted code commit:
`bda46f57f0f977e05593c46b55851c40c4ad34fe`.

External Intel acceptance evidence SHA-256:
`181225F29A966179AB513121C3CBACD31401752956EFC9A22253A8EFBF94766E`.

Final physical acceptance passed with REAL_READONLY, entries disabled, healthy
reconciliation/watermarks, zero unresolved orders and no live order transmission.

## Stage 8.9 — Funding / margin readiness

**COMPLETE.** Stage 8.9 is **COMPLETE**.

Canonical status: `STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.

### Stage 8.9.8 — account-authority correction

Status: `STAGE_8_9_8_COMPLETE`.

The production account is `UNION`; the authenticated funding authority is exactly
one `portfolio_mc`. The earlier FORTS-only assumption is historical only.

Portfolio-variant evidence SHA-256:
`60A529DB021B39E1C6117D01CCF3AB5B8B331073D407782E90383E4D124BADC5`.

Account financial-shape evidence SHA-256:
`EED27193E35F46FFCF13CFB4A2F2EAA4AB87A35F967D78139E97BFA885009371`.

The earlier FORTS-only result is historical provenance only:
`BLOCKED_ACCOUNT_FINANCIALS_UNAVAILABLE` / `FORTS_PORTFOLIO_MISSING`, accepted
code `5deedb49f16d9f2525c430383a029017cd9a53ce`, diagnostic SHA-256
`2911D7857B9404E5178FF1A754A9168845E457A9349CEF7B1AFD0E088E06BF46`, and
summary SHA-256
`59A9ADD4BD229C7A7BF3E20337E494F90CF90082208469AD5A694A4B075D852B`.
It is not a current blocker.

### Stage 8.9.9 — physical revalidation

Stage 8.9.9 is **PHYSICAL REVALIDATION COMPLETE**.

The pre-funding zero-capacity result is historical provenance only:
`BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY` / `ZERO_CONTRACT_CAPACITY`, accepted
code `c461911fdceddf54a2a6fe6768574dd93f4844d1`, diagnostic SHA-256
`F307D3F5ADC4525FF304B9582F683B89A097FC9BCFB502E8150FC98D2625860F`, summary
SHA-256 `F36B16565F9E08C38B3264831DCA94A65390275F7A2B78A3C6C90302E4A7C09B`, and
`positive_capacity_case_count = 0`. It is not a current blocker.

### Stage 8.9.10 — post-funding closeout

Stage 8.9.10 is **COMPLETE**.

Accepted physical code commit:
`1013a5a2324e015ab3bc047a7b9af9064552cd10`.

Physical result: `STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1`.
Classification: `STAGE_8_9_FUNDING_MARGIN_VALIDATED`.
Reason: `ALL_AUTHORITIES_VALID`.

External diagnostic report SHA-256:
`C87400F845B73A666B95C83DA2E3B6B710F36F3210AD4AD175BFDABB453864D5`.

External physical summary SHA-256:
`099F85A0DCCF94D404411CFFAC2F5D8C80D606C5C1B5AA2F5B650E8BF5FEB636`.

Accepted counts are `sizing_case_count = 8`,
`positive_capacity_case_count = 4`, `zero_capacity_case_count = 4`, and
`positive_batch_reservation_count = 1`. This establishes account funding and
FINAM margin authority plus at least one executable contract-capacity case.

It does **not** establish positive capacity for every N4 instrument,
simultaneous FULL N4 portfolio capacity, or FULL/R15 production funding
sufficiency. It does not authorize trading, a trading token, or real execution.

## Later gates

- Stage 8.10 — **NOT STARTED / NOT AUTHORIZED**.
- Stage 8.11 — **NOT STARTED / NOT AUTHORIZED**.
- Stage 8.12 — **NOT STARTED / NOT AUTHORIZED**.

`LIVE_TRADING_NOT_AUTHORIZED` remains in force.
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remains in force.
`NEW_ENTRIES_DISABLED` remains in force for REAL_READONLY acceptance paths.

## Current handoff

Stage 8.9 is complete. The next lifecycle stage is Stage 8.10, but it is
**NOT STARTED / NOT AUTHORIZED** and must not begin without separate explicit
authorization.

## Persistent constraints

- no live trading without explicit separate authorization;
- no runtime mutation of Stage 7 identity;
- no canonical fallback;
- no fabricated cash/equity/margin/capacity;
- no reinterpretation of REAL_READONLY success as live authorization;
- no mixing with BBW / Level Touch / Round Level projects;
- no rewrite of historical v1/v2/v3 verdicts.
