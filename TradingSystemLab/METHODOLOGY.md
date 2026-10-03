# Canonical research, production, and operational methodology

This file defines durable TradingSystemLab rules. Historical research identities
and verdicts are immutable; production/operational work must fail closed.

## 1. Canonical research lifecycle

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Candidate freeze is identity fixation, not an extra research phase.

## 2. Research identity and OOS discipline

A research identity binds strategy source/hash, parameters/hash, universe,
timeframe/context alignment, date bounds, execution/cost assumptions and
classification rules.

After candidate freeze it remains immutable through Robustness, Walk Forward and
TRUE OOS. Revealed TRUE OOS is consumed and cannot become fresh OOS for a later
modified identity.

v1/v2/v3 historical verdicts remain immutable.

## 3. Causality and determinism

- no look-ahead or future-fill;
- only completed context bars are visible;
- signal/entry/stop/trailing semantics are deterministic;
- event ordering, trade IDs and serialization are deterministic;
- source data remain external/read-only unless explicitly authorized otherwise.

## 4. Post-v3 retrospective evidence

Stages 1–6.x are evidence-to-production analysis, not a second OOS lifecycle.
Stage 5 retrospective economic authority remains `CORRECTED_SINGLE_C1`.

Structural and basket reassessments that used 2025–2026 are retrospective.
Admitted structural rules are not automatically production-approved.

## 5. Stage 7 production authority

Production specification:
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.

Active identity:
`TRAIL1__N4_01__FULL__R15`.

Frozen production semantics:

- v3 perpetual / T3 / H1;
- USDRUBF + CNYRUBF + GLDRUBF + IMOEXF;
- TRAIL1 only;
- FULL load;
- R15 = 1.5% current realized-equity risk per new position;
- maximum nominal simultaneous initial risk 6%;
- one active position per instrument;
- no pyramiding;
- no session filter;
- no canonical fallback;
- unrealized PnL excluded from sizing.

`CANONICAL__N4_01__FULL__R15` is reference evidence only.

Runtime overlays not included in the frozen production specification may not be
silently activated.

## 6. Research-to-robot conformance

Stage 8 must reproduce Stage 7 before broker activation.

Required evidence includes exact trade count, timestamps, direction, prices,
state, R, deterministic reruns, immutable strategy parameters and no fallback
identity.

Accepted conformance reproduces 418/418 trades exactly in both authority replay
and production replay.

## 7. Fail-closed Stage 8 architecture

- LIVE cannot be enabled by routine runtime configuration.
- REAL_READONLY cannot transmit orders.
- unresolved binding blocks progression.
- reconciliation failure blocks entries.
- stale/invalid market data blocks entries.
- missing/invalid financial authority blocks sizing.
- zero contract capacity blocks readiness.
- duplicate intents/orders are prevented by persisted idempotency.

Intent is persisted before submission. Exit/fee realization precedes later
same-timestamp entry sizing.

## 8. Stage 8.8 operational hardening

Stage 8.8 operational hardening is COMPLETE.
Stages 8.8.1, 8.8.2, 8.8.3, 8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

Accepted controls include:

- REAL_READONLY operational supervisor;
- CurrentUser DPAPI credentials;
- matched non-SYSTEM task principal and ACL hardening;
- schedule-aware H1 freshness;
- stale-data fault/recovery;
- fail-closed SQLite backup/recovery;
- Windows WAL/handle correctness;
- final physical Intel operational acceptance.

Repository-side tests are evidence of code behavior; physical Intel acceptance is
separate evidence and is required for operational closure.

## 9. H1 freshness rule

Expected H1 completion is derived from authenticated FINAM schedules rather than
wall-clock assumptions.

Only a completed one-hour interval wholly contained in a valid session creates an
expected bar. Closed weekends, empty schedules, future sessions and schedule gaps
do not create synthetic expectations. Malformed schedule evidence fails closed.

`STALE_COMPLETED_H1_DATA` must:

- produce `UNHEALTHY` / `FAULT`;
- keep entries disabled;
- not advance successful cycle/H1 state;
- never call order-capable paths;
- clear only after authenticated fresh data recovery.

## 10. State backup and recovery

SQLite backup/recovery must be identity-bound, checksummed, schema-validated,
single-instance protected and non-destructive on restore failure.

Recovery must correctly handle WAL/SHM state and Windows file-handle semantics.

## 11. FINAM account authority is account-type aware

Funding authority is not hardcoded to one portfolio family.

For the active production account:

- account type is `UNION`;
- exactly one `portfolio_mc` is the authenticated financial authority;
- supported FORTS accounts may use `portfolio_forts` where applicable;
- mismatched/unknown oneof shapes fail closed.

Earlier FORTS-only assumptions are historical implementation evidence, not
current authority.

## 12. Stage 8.9 funding and margin validation

Stage 8.9 separates four concepts that must never be conflated:

1. authenticated account financial schema;
2. authenticated equity/margin values;
3. correct sizing arithmetic/batch-budget behavior;
4. actual positive contract capacity under frozen Stage 7 risk.

Passing 1–3 does **not** imply 4.

Stage 8.9.8 established the corrected UNION/`portfolio_mc` authority.
Stage 8.9.9 physically revalidated the corrected model.

The current physical result has `positive_capacity_case_count = 0`.

Therefore current status is
`BLOCKED_INSUFFICIENT_CONTRACT_CAPACITY` with reason
`ZERO_CONTRACT_CAPACITY`.

Zero capacity is a distinct readiness blocker. It must not be relabeled
funding-ready, nor used to justify loosening Stage 7 risk automatically.

## 13. Risk and sizing discipline

`FROZEN_TICK_SIZE = 0.001` and C1 remain historical research-normalization/
evidence concepts where applicable; they are not the live fee model.

Stage 7 R15 risk cannot be increased merely to manufacture positive capacity.
Stage 8 may only cap quantity downward using authenticated cash/margin/lot
constraints.

Unknown or zero capacity must fail closed.

## 14. Credential and secret discipline

Secrets never enter Git, logs or command-line arguments.

Windows readonly credentials use DPAPI `CurrentUser`, are production-ID-bound,
principal/SID-bound and ACL-hardened. Tampering, wrong identity or invalid
security state fails closed.

## 15. Live authorization boundary

`LIVE_TRADING_NOT_AUTHORIZED` remains authoritative.
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remains authoritative.

Stage 8.10 trading-token integration is not started/authorized. Stage 8.11/8.12
execution is not authorized.

Do not infer live authorization from:

- Stage 7 freeze;
- exact historical replay;
- authenticated instrument binding;
- Stage 8.8 physical operational acceptance;
- Stage 8.9 financial-schema validation.

## 16. Current progression rule

Stage 8.9 is not complete while `ZERO_CONTRACT_CAPACITY` remains.

Do not advance automatically to Stage 8.10. Any capacity-resolution work requires
explicit user authorization and independent audit, while preserving frozen Stage
7 identity and fail-closed semantics.

## 17. Domain separation

TradingSystemLab remains separate from BBW, Level Touch, Round Level / Touch and
other research domains.

## 18. Evidence standard

Use actual source/config/manifests/ledgers/replay/audit and external-evidence
hashes according to `AUDIT_PROTOCOL.md`. Summary prose alone is not evidence.

Routine current-state updates belong primarily in `CURRENT_STATE.md` and
`ROADMAP.md`.
