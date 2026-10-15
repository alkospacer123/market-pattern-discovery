# Roadmap 3.6 — post-ARM one-shot independent READONLY observation

**Scope:** separate diagnostics only. Does not amend or deploy `T3/H1/TRAIL1`, N4, FULL/R15, production task, the installed exact commit, FINAM trading authority, SQLite, Stage5 data or the kill switch. No ARMED/rearm, order submission, cancellation, backup or recovery.

- Production installed checkout must remain `3a18c8c24301c866a60f5d725de227288d48f7ec`, **not** current docs-only `main`.
- The Windows Task must already be enabled and `Running`; wrapper + two Python processes must be one parent/child tree.
- External switch must be `ARMED` generation **62**. Do not change generation to satisfy the probe.
- Current post-ARM heartbeat must be fresh, `HEALTHY`, reconciliation `PASS`, and match the independently read production SQLite ledger (read-only WAL aware, `mode=ro`, `query_only=ON`).
- `REAL_READONLY` FINAM CurrentUser DPAPI token must be accessible from the operator account; never use a Trading Token. Only session POSTs and account/orders/N4 schedules/bars GETs are permitted; *no* order/cancel/flatten/stop action.
- Actual FINAM positions must equal ledger positions, including direction and quantity. Active FINAM SLTP orders must match heartbeat/ledger stop IDs, cover 100% at GTC, and account for all active orders. A flat account is allowed but **not required**. An in-flight order or temporarily divergent snapshot is **BLOCKED**, not guessed as PASS.
- All four completed H1 expectations must match the latest FINAM schedule and bars; if no completed current session can be proven, return BLOCKED rather than invent freshness.
- Observe FINAM position/orders twice and recheck local heartbeat/switch/SQLite. If the robot advances during a sample, return BLOCKED and run another independent probe later; **never restart/rearm to make the check pass**.

**Intel v4 READONLY diagnostic isolation:** The observer uses a pinned, strict read-only copy of the position/order response parsers from production commit `3a18c8c…`, without importing `production_broker_state`'s unrelated `protective_stop_contract` → `production_runtime` → `pandas`/OpenBLAS dependency. Its PowerShell wrapper temporarily sets BLAS thread limits to 1 **only in the observer process**, restoring the operator environment on exit. This avoids the previously observed `OpenBLAS error: Memory allocation still failed after 10 retries` while preserving broker-state schema validation. The running production worker, Task, account, and strategy are unchanged. Nine synthetic tests and package integrity pass; physical FINAM/SQLite/WAL acceptance still requires an actual Intel run.

## On Intel

This branch is draft-only and does **not** modify production. Save the two scripts to a **separate operator diagnostics folder**, not to the installed production checkout, and run under the same account that owns the existing **REAL_READONLY** DPAPI credential. The PowerShell wrapper derives the pinned checkout, runtime and interpreter from the existing scheduled Task action.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\tslaudit\fill493\stage8-537-post-arm-readonly.ps1"
```

**Output:** `FINAL_POST_ARM_READONLY=PASS` only after all predicates hold; any refusal is `FINAL_POST_ARM_READONLY=BLOCKED:<code>` with a nonzero exit. No secret or account identifier is printed. Only the user/operator's physical Intel output can establish actual post-ARM status; GitHub review cannot substitute for it. If a genuine safety mismatch is reported, use the existing approved operator fail-closed procedure; this diagnostic intentionally does not mutate even the kill switch or broker state.

**Intel v5 LIVE-cycle consistency:** The v4 observation reached FINAM and established flat N4 positions, no active protective stops and position/stop linkage PASS; it ended with `LOCAL_STATE_CHANGED_DURING_OBSERVATION` because a healthy running worker updated the heartbeat timestamp/cycle during independent FINAM calls. The v5 diagnostic no longer requires byte-for-byte equality of the two heartbeat/ledger snapshots. Both snapshots must independently remain ARMED generation 62, HEALTHY, reconciliation PASS, account/commit-bound, fresh and unresolved-free. Heartbeat/SQLite cycles must match at both ends and advance monotonically; the kill switch, ledger positions/H1 watermarks/unresolved count, heartbeat protection/counts and both independent broker snapshots must remain semantically stable. Final broker positions and stop linkage are validated against the second local snapshot. Any true change returns BLOCKED; no robot, Task, FINAM order, or SQLite mutations are performed. The bundled offline v5 test suite passes 20/20 tests (including cycle progression and safety-state change rejection); only an Intel run can establish physical final PASS.

**Failure semantics:** A `BLOCKED` output is not proof of a broken strategy or absent stop if a live state changed during the observation; it is proof that this one-shot evidence cannot establish PASS. No blind rearm, Task mutation or automatic cancellation follows.