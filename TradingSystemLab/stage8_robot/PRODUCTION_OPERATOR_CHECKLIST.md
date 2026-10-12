# Stage 8.12.4 — H1 timestamp backfill production operator checklist

## Newly accepted physical evidence — 2026-10-12

- [x] Fix PR #484 isolated exact-code targeted tests: 60/60 PASS (full Stage 8 suite pending).
- [x] FINAM GET-only immutable H1 N4: 4/4 PASS; 2 ignored historical backfills + 2 append-ready bars per N4 at probe; broker positions/orders/unresolved intents 0/0/0. External SHA-256 `2fe51ccd6ab57682579f222158b12413eaae6020abe21aec7afa188d3afddb43`.
- [x] Isolated one-cycle production shadow with SQLite copy: unchanged prefix 4/4 PASS, 3 bars appended per N4 to shadow only, shadow heartbeat `HEALTHY`, reconciliation `PASS`. External SHA-256 `4799a0b426cd62d143a0b3fdba6035ef44f11dde6654676568b1a28e3a8fbded`.
- [x] Confirmed old LIVE checkout/authorization/SQLite/Tasks not modified by shadow; kill switch `HALTED` generation 59.
- [ ] Controlled LIVE exact-code rollout after backups, full applicable audit and commit-bound authorization migration.
- [ ] Fresh LIVE-runtime `HEALTHY/PASS`, verified flat account/zero unresolved intents and separate explicit re-arm approval.


## Current gate: HALTED / NOT REARMED (2026-10-12)

This checklist supersedes the historical **ARMED** daily-operations checklist until a new explicit operator decision. Existing production authorization remains bound to the previously accepted code commit; its existence is not approval to re-arm after this incident.

### A. Physical safety baseline (reported, recheck on Intel)

- [ ] Verify kill switch remains `HALTED`, generation at least 59. Do not change it.
- [ ] Confirm production task state and actual pinned production checkout; production service may remain Running in HALTED state.
- [ ] Verify positions=0, unresolved intents=0, active orders and protective coverage consistent with exact FINAM account authority.
- [ ] Record a fresh heartbeat, reconciliation result, cycle_count, last completed H1, and recent fault codes.
- [ ] Confirm REAL account, N4 bindings, Stage7 identity and persisted authority hashes unchanged.
- [ ] Preserve existing external runtime state and SQLite continuation; **no deletion, manual insertion, rewriting, or reseeding**.
- [ ] No `git pull`, automatic update or unattended activation of production checkout.

### B. Code and regression verification

- [ ] Check actual GitHub `main`; PR #484 code merge: `184e8c2b8fa092a606249ff293a4f507160bff29`.
- [ ] Independently run full project tests and targeted H1 splice/continuation/safety regressions against that exact source.
- [ ] Existing-timestamp FINAM OHLC revision leaves accepted OHLC unchanged.
- [ ] Late FINAM-only backfilled H1 at/before immutable authority.max() is ignored, not inserted.
- [ ] Persisted continuation prefix and already accepted history unchanged.
- [ ] Exact latest authority seam present: only strictly newer completed bars append.
- [ ] Missing exact latest seam / no overlap => fail closed.
- [ ] Duplicate or out-of-order FINAM timestamps => fail closed.
- [ ] Persisted continuation corruption => fail closed.
- [ ] Missing/stale current completed H1 => fail closed.
- [ ] Confirm frozen T3/H1/TRAIL1/N4/FULL-R15, 6% ceiling, sizing, execution semantics and research results unchanged.

### C. Intel preactivation: HALTED, GET-only/zero-order

- [ ] Separately stage and verify the **exact tested code commit** on Intel without moving the active LIVE checkout automatically.
- [ ] Ensure kill switch remains HALTED throughout the preactivation.
- [ ] Run operator-controlled zero-order preactivation, with physical N4 data and persisted H1 continuation validated without modification of historical prefix.
- [ ] Require fresh `health_status=HEALTHY`, `reconciliation_status=PASS`, positions=0 and unresolved intents=0.
- [ ] Confirm fresh H1 and heartbeat; no repeated splice fault; exact account, Stage5 commit and accepted code hash proven.
- [ ] Capture sanitized external evidence, timestamps, code and data commit hashes, test counts and preactivation result.
- [ ] If any criterion fails, remain HALTED and do not proceed.

### D. Commit-bound authorization and re-arm — separate permission required

- [ ] Determine whether new accepted code commit requires authorization rollover. Never copy/modify an existing authorization by hand or reuse an incompatible commit-bound record.
- [ ] Revalidate accepted authority, operational checks, and safe operator-controlled rollover, **only with separately explicit operator permission**.
- [ ] Re-arm **only after new explicit user/operator authorization**. The permission to implement the H1 fix is not permission to re-arm.
- [ ] Following any separately approved re-arm, verify first fresh heartbeat, PASS reconciliation, zero unexpected intents/orders, correct position protection and active code hash.
- [ ] Update `CURRENT_STATE.md`, `PROJECT_CONTEXT.md`, `ROADMAP.md`, `METHODOLOGY.md`, runbook, README, provenance, strategy passport and checklist after the physical decision; verify actual GitHub `main` again.

**Fail-closed rule:** no forced entries, no changed sizing or strategy, no manual persisted history edit, no automatic `git pull` on LIVE.
