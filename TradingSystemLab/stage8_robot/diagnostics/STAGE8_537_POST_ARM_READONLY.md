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

## On Intel

This branch is draft-only and does **not** modify production. Save the two scripts to a **separate operator diagnostics folder**, not to the installed production checkout, and run under the same account that owns the existing **REAL_READONLY** DPAPI credential. The PowerShell wrapper derives the pinned checkout, runtime and interpreter from the existing scheduled Task action.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\tslaudit\fill493\stage8-537-post-arm-readonly.ps1"
```

**Output:** `FINAL_POST_ARM_READONLY=PASS` only after all predicates hold; any refusal is `FINAL_POST_ARM_READONLY=BLOCKED:<code>` with a nonzero exit. No secret or account identifier is printed. Only the user/operator's physical Intel output can establish actual post-ARM status; GitHub review cannot substitute for it. If a genuine safety mismatch is reported, use the existing approved operator fail-closed procedure; this diagnostic intentionally does not mutate even the kill switch or broker state.

**Failure semantics:** A `BLOCKED` output is not proof of a broken strategy or absent stop if a live state changed during the observation; it is proof that this one-shot evidence cannot establish PASS. No blind rearm, Task mutation or automatic cancellation follows.