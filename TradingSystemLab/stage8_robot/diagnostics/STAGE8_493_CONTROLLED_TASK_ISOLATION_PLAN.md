# Stage 8 #493 — reviewed plan for controlled isolation of existing HALTED production Task

Status: **PLAN ONLY / OPERATOR APPROVAL REQUIRED / NO CODE EXECUTION OR AUTHORIZATION**. Date 2026-10-13.

## Verified current checkpoint

Intel operator's exact `stage8-493-pre-isolation-readonly.ps1` v3 physical output:
- `PRODUCTION_PROCESS_SINGLE_BOUND_CHAIN=PASS`: `powershell.exe` PID 8536 -> `python.exe` PID 6260 -> `python.exe` PID 11608; both Python processes report pinned `184e8c2b8fa092a606249ff293a4f507160bff29` and production service; chain unchanged throughout diagnostics.
- `SQLITE_BEFORE_AFTER=PASS` (production SQLite strictly readonly, schema/identity/positions/pending/intents clean).
- `FRESH_BROKER_DOUBLE_SNAPSHOT=PASS` (exact FINAM readonly account-bound identity, no broker positions or active orders at two observed instants).
- `KILL_SWITCH_HALTED=PASS`, Scheduled Task `TradingSystemLab-Stage8-Production` still Running, readonly Task Disabled.
- Scheduled Task settings: startup trigger enabled, `restartcount=10` is **configured** automatic restart ceiling, `MultipleInstances=IgnoreNew`, `StartWhenAvailable=False`.

The diagnosis establishes a single observed service *chain*, not conclusive ownership of Windows Task process IDs and not future flatness. Do not assume absence of broker changes after the two observed snapshots.

## Explicit scope and prohibitions

- The freeze stays intact: production spec `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`, identity `TRAIL1__N4_01__FULL__R15`, frozen strategy and N4 unchanged.
- No real order/SLTP acceptance, no real trade token for this protocol, no rearm, no runner upgrade, no mutation of production SQLite, no stage8.11 one-contract acceptance.
- Leave `FINAM_FILL_AUTHORITY_VERIFIED=False`. Explicit risk/cost and order authorization for eventual maximum two-contract multi-fill acceptance is a **separate** later permission.
- The current diagnostic's `STOP_TASK_AUTHORIZED_BY_THIS_SCRIPT=NO` is binding. Do **not** issue `stop-scheduledtask`, `disable-scheduledtask`, `stop-process`, `set-scheduledtask`, `start-scheduledtask`, or any task/recovery action just from the PASS.

## Required approved implementation before touching LIVE

1. **Separate operator approval.** Review exact commands/script, allowed mutation (disable auto-start/restart and halt production Task), rollback/restore steps, required actor privileges, and a bounded abort behavior; explicitly approve those *specific* production changes. Do not conflate this with consent to submit a test order.
2. **Fresh time-bounded preflight.** Reverify current pinned checkout clean, Task name/action/principal and actual Task instance PID ancestry, single production Python parent-child chain, no competing service processes, kill switch HALTED, production account/identity/capacity boundaries and readonly broker account/orders double flat, production SQLite no pending/unresolved and empty positions. Snapshot and preserve task definition/settings in a separate diagnostic location. If any predicate changes, **abort with no mutation**.
3. **Prevent re-entry before stop.** Task has startup trigger and configured restart attempts; the permitted isolation implementation must first demonstrate a task restart-suppression procedure with Task Scheduler under the actual principal, then atomically disable/revoke permitted triggers/restart as necessary, confirm it cannot auto-relaunch, and only then stop the *identified scheduled Task*, not an arbitrary Python PID. This step is live operational mutation and is NOT AUTHORIZED yet.
4. **Validate actual isolation.** Check Scheduled Task disabled/not Running; verify the previous PowerShell PID and both Python PIDs have exited, no other service command/instance remains under the pinned runtime or checkout, no orphaned Python child and no session still capable of sending an order; inspect OS lock holder/quiescence without writing or deleting its path. If a descendant remains after Task-stop, **do not assume flat or manually kill it**: classify BLOCKED and execute a separately reviewed safe recovery decision.
5. **Post-stop independent verification.** The existing `stage8-493-finam-broker-flat-readonly.ps1` has an explicit `Task.State == Running` gate and is **not suitable** as a post-stop probe. Develop and independently test a separate **post-isolation** FINAM readonly account/orders probe bound to Task Disabled, no service PIDs/lock owner, the same readonly credential/account, kill switch HALTED and expected identity, and production SQLite consistency. Avoid relying on production heartbeat freshness after shutdown; it will become stale by design. Repeat broker snapshots to confirm no positions and active orders *after* isolation.
6. **Fail-closed outcome.** Success requires explicit `ISOLATED_HALTED` evidence with original task/restart settings preserved for authorized restoration; otherwise `BLOCKED_OPERATOR_RECOVERY_REQUIRED`. No entry authorization, no migration, no order. If an unexpected position/order appears, follow the separately approved broker emergency/reconciliation path; no automatic close/delete.
7. **Operational authority synchronization after actual mutation.** Immediately update CURRENT_STATE, roadmap, runbook, production passport, operator checklist with physical evidence, exact Task state, restoration procedure and operational HOLD. Independently verify GitHub `main` and actual Intel runtime; draft-branch documentation does not by itself represent LIVE authority.

## Next gate

Build/review a **non-executed** task-isolation executor and a separate post-stop readonly verifier, test with synthetic Task/PID fixtures and Windows PowerShell under an isolated test Task, then present the exact approved side effects for explicit user permission. Actual live isolation has not begun.
