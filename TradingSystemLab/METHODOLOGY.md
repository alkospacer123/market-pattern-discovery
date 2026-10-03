# Canonical research, production, and operational methodology

This file defines durable TradingSystemLab rules. Historical research identities
and verdicts are immutable; production and execution progression must fail closed.

## 1. Canonical research lifecycle

**Baseline → Optimization → Robustness → Walk Forward → TRUE OOS**.

Candidate freeze is identity fixation, not an extra research phase.

## 2. Research identity and OOS discipline

A research identity binds source/hash, parameters/hash, universe, timeframe/context,
date bounds, execution/cost assumptions and classification rules.

After freeze, identity remains immutable through Robustness, Walk Forward and TRUE OOS.
Revealed TRUE OOS is consumed and cannot become fresh OOS for a modified identity.

v1/v2/v3 historical verdicts remain immutable.

## 3. Causality and determinism

- no look-ahead or future fill;
- completed bars/context only;
- deterministic signal/entry/stop/trailing semantics;
- deterministic event ordering, trade IDs, serialization and reruns;
- source data external/read-only unless explicitly authorized otherwise.

## 4. Stage 7 production authority

Frozen production specification:
`PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`.

Active identity:
`TRAIL1__N4_01__FULL__R15`.

Frozen semantics:

- v3 perpetual / T3 / H1;
- USDRUBF + CNYRUBF + GLDRUBF + IMOEXF;
- TRAIL1 only;
- FULL load;
- R15 = 1.5% current realized-equity risk per new position;
- maximum nominal simultaneous initial risk 6%;
- realized equity only;
- one active position per instrument;
- no pyramiding;
- no session filter;
- no canonical fallback.

Runtime overlays not in Stage 7 may not be silently activated.

## 5. Stage 8 implementation principle

Stage 8 implements and operationally validates the exact Stage 7 identity.
It is not a strategy-selection or optimization stage.

All Stage 8 progression is gated. A later stage may only rely on prior accepted
authority and must not weaken fail-closed controls.

## 6. Research-to-robot conformance

Before broker readiness, the robot must reproduce frozen Stage 7 research authority.

Accepted conformance is 418/418 exact trades in both authority and production replay,
with deterministic hashes and zero mismatch classes.

This establishes implementation fidelity, not permission to trade.

## 7. Fail-closed architecture

- LIVE cannot be enabled by routine configuration.
- REAL_READONLY cannot transmit orders.
- unresolved binding/reconciliation/data/financial authority blocks progression.
- zero or invalid capacity blocks sizing/readiness.
- duplicate intents/orders are prevented by persisted idempotency.
- order intent is persisted before submission.
- exits/fees precede later same-timestamp entry sizing.

## 8. Stage 8.8 operational hardening

Stage 8.8 operational hardening is COMPLETE.
Stages 8.8.1, 8.8.2, 8.8.3, 8.8.4, 8.8.5, 8.8.6, and 8.8.7 are COMPLETE.

Operational authority includes:

- REAL_READONLY supervisor;
- CurrentUser DPAPI credential storage;
- task-principal/ACL hardening;
- schedule-aware H1 freshness;
- stale-data fault/recovery;
- SQLite backup/recovery and Windows WAL correctness;
- physical Intel final operational acceptance.

Completion of Stage 8.8 does not authorize execution.

## 9. FINAM financial authority

Account financial authority is account-type aware.

For the active production account:

- account type is `UNION`;
- exactly one `portfolio_mc` is authoritative;
- supported FORTS accounts may use `portfolio_forts` where applicable;
- unknown or mismatched portfolio shapes fail closed.

Earlier FORTS-only assumptions are historical evidence only.

## 10. Stage 8.9 funding / margin validation

Stage 8.9 is **COMPLETE** under
`STAGE_8_9_REAL_ACCOUNT_FUNDING_MARGIN_VALIDATION_COMPLETE`.

Accepted physical result:
`STAGE_8_9_10_POST_FUNDING_REVALIDATION_PASS=1`.
Reason: `ALL_AUTHORITIES_VALID`.

Accepted counts:

- `sizing_case_count = 8`;
- `positive_capacity_case_count = 4`;
- `zero_capacity_case_count = 4`;
- `positive_batch_reservation_count = 1`.

Stage 8.9 proves authenticated funding/margin authority and at least one positive
contract-capacity case. It does not prove positive capacity for every N4 instrument,
simultaneous all-N4 capacity, or execution permission.

Stage 7 R15 risk may not be increased automatically to manufacture capacity.

## 11. Trading credential separation

READ_ONLY and Trading Token credentials are separate security authorities.

Rules:

- both remain outside Git/logs/command-line arguments;
- both are bound to production/account identity;
- they may not silently substitute for one another;
- possession/provisioning/authentication does not authorize execution;
- Trading Token write permission is not equivalent to order acceptance.

## 12. Stage 8.10 lifecycle semantics

Stage 8.10 is **COMPLETE** under
`STAGE_8_10_TRADING_TOKEN_LIFECYCLE_COMPLETE`.

Stage 8.10.1 through Stage 8.10.8 are **COMPLETE**.

Accepted progression:

- 8.10.1 Preconditions;
- 8.10.2 secure Trading Token provisioning;
- 8.10.3 identity/account binding;
- 8.10.4 READ_ONLY vs Trading Token permission-boundary validation;
- 8.10.5 offline synthetic order-path construction/serialization;
- 8.10.6 fail-closed kill switch and safety gates;
- 8.10.7 Intel Trading Token session acceptance;
- 8.10.8 repository-only lifecycle closeout.

## 13. Order-path evidence boundary

Stage 8.10.5 validates local deterministic order construction/serialization only.

A synthetic intercepted POST is not:

- a real FINAM order request;
- broker acceptance;
- exchange acceptance;
- fill/cancel validation;
- permission to transmit a real order.

Real order endpoint count remains zero through Stage 8.10.

## 14. Kill-switch and execution authority

The production kill switch is an independent durable fail-closed control.

Canonical safe state is `HALTED`.

`ARMED` alone never authorizes trading. Exact separate execution authorization is also required.

Final Stage 8.10 accepted values:

- kill switch = `HALTED`;
- `execution_authorized = false`;
- `real_order_endpoint_called = false`;
- `real_order_count = 0`.

Missing/malformed/mismatched kill-switch state must block new entries.

## 15. Trading Token Intel acceptance boundary

Stage 8.10.7 validated Trading Token 1 on Intel with remote scope restricted to
`SESSION_CREATE_AND_DETAILS_ONLY`.

`readonly=false` validates only the token/session write-permission boundary.
It does not prove order permission or execution authorization.

The kill switch remained `HALTED` before and after authentication.

## 16. Stage 8.10 closeout boundary

Stage 8.10.8 is repository-only closeout and creates no new physical execution authority.

Stage 8.10 completion does not authorize Stage 8.11.

Stage 8.11 — Controlled Real Execution Acceptance — is **NOT STARTED / NOT AUTHORIZED**.
Stage 8.12 — FULL/R15 Production Authorization — is **NOT STARTED / NOT AUTHORIZED**.

Stage 8.11 is the first possible real-order gate, but it requires separate explicit authorization.

## 17. Live authorization boundary

`LIVE_TRADING_NOT_AUTHORIZED` remains authoritative.
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remains authoritative.

Do not infer real-order or LIVE authorization from:

- Stage 7 freeze;
- exact historical replay;
- REAL_READONLY binding;
- Stage 8.8 operational acceptance;
- Stage 8.9 funding validation;
- Trading Token provisioning/authentication;
- `readonly=false` permission evidence;
- offline order-path validation;
- Stage 8.10 completion.

## 18. Domain separation

TradingSystemLab remains separate from BBW, Level Touch, Round Level / Touch, and other projects.

## 19. Evidence standard

Use actual source/config/manifests/replay/audit and external-evidence hashes according
to `AUDIT_PROTOCOL.md`. Summary prose alone is not evidence.

Routine lifecycle status belongs primarily in `CURRENT_STATE.md` and `ROADMAP.md`.
