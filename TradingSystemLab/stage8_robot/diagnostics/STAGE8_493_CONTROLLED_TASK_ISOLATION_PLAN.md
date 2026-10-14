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

## 2026-10-13 operator authorization, staged executable package — NOT YET EXECUTED

The operator explicitly authorized continuing with controlled production Task isolation (not trading) in the chat after physical v3 READONLY PASS. This approval covers *only* the bounded disable-before-stop action of the exact pinned `TradingSystemLab-Stage8-Production` Task, provided the fresh safety preflight and reviewed executable hold points pass. There is **no authority** to place an order, rearm, deploy V2, change strategy/parameters, delete/mutate SQLite, force-kill a PID, restart Task automatically, or merge the Draft PR.

Added to this Draft PR:
- `stage8-493-controlled-task-isolation.ps1` — by default **check-only**. Validates pre-isolation scripts' hashes, task action/commit/runtime, HALTED, performs fresh v3 process + production SQLite + FINAM double-snapshot preflight, and identifies exact Python/Powershell chain. Only the explicit `-execute` flag may begin mutation. The executor exports an immutable original Task definition into a new timestamped file under `c:\tslaudit\fill493`, checks the backup, marks the attempt as mutated **before** invoking `disable-scheduledtask`, validates disable, then invokes `stop-scheduledtask` for the named root Task. No arbitrary process kills. Verifies both original PID exits, no active service process, disabled Task; calls post-stop verifier.
- `stage8-493-post-isolation-readonly.ps1` — independent, nonmutating post-stop checker requiring Task Disabled, zero service processes, exclusive read-only open of the existing OS lock, HALTED identity, production SQLite before/after and two new real-readonly FINAM snapshots, with strict script SHA checks. It does **not** use Task=Running or heartbeat-freshness preconditions after shutdown.
- `stage8_493_post_isolation_broker_readonly.py` — only session setup/details and readonly GET account/orders against the exact bound FINAM account. No broker order/cancel POST, no trading token. Historical heartbeat may be stale but its identity/counter fields must remain canonical; exact new broker state must be flat.
- `tests/test_stage8_493_controlled_task_isolation.py` — 15 local synthetic/static offline checks PASS (not a native Windows integration test, not real FINAM proof). All exact source blobs and checksum are published with the candidate scripts.

**Execution hold point**: physical Intel **check-only first**, no changes. After its PASS, allowed explicit `-execute` invocation as operator-owned action under the existing authorization, but never conflate offline PASS with native TaskScheduler proof. An `-execute` attempt ends at either `ISOLATED_HALTED_PENDING_GITHUB_OPERATIONAL_SYNC` or `BLOCKED_OPERATOR_RECOVERY_REQUIRED` if mutation began; it does not automatically restore/rearm or kill orphans. If any blocker occurs, the operator must provide the complete sanitized output and stop.

After physical mutation, the required **same-task closeout** is urgent: inspect Intel Task disabled, process zero, broker flat, SQLite clean, and reconcile CURRENT_STATE, roadmap, runbook, production passport and checklist with actual evidence; then independently recheck GitHub `main`. Neither this Draft PR nor an offline simulation is LIVE authority. No Task mutation has occurred in this chat at the time of this document.

## 2026-10-13 — Physical Intel Task isolation EXECUTE PASS, main operational docs merged

With express operator authorization, the operator physically ran the exact approved `stage8-493-controlled-task-isolation.ps1 -execute` and supplied this full terminal output:

```text
=== stage8 #493 controlled production Task isolation ===
NO_REAL_ORDERS NO_REARM NO_TRADING_TOKEN NO_LIVE_SQLITE_MUTATION
FRESH_PROCESS_SQLITE_FINAM_HALTED=PASS
IDENTIFIED_TASK_POWERSHELL_PID=8536
IDENTIFIED_SERVICE_ROOT_PID=6260
IDENTIFIED_SERVICE_CHILD_PID=11608
TASK_DEFINITION_BACKUP_SHA256=2714BB09FF571EFAE748509F5D3C3BC8DD5F38460173E1A13EF5AEE752DF906E
TASK_DISABLED_RESTART_SUPPRESSED=PASS
TASK_STOP_COMMAND_COMPLETED=YES
TASK_AND_ALL_IDENTIFIED_PROCESSES_EXITED=PASS
POST_STOP_FINAM_SQLITE_LOCK_GATE=PASS
CLASSIFICATION=ISOLATED_HALTED_PENDING_GITHUB_OPERATIONAL_SYNC
TASK_MUTATION_ATTEMPTED=True
REAL_ORDER_AUTHORIZED=NO
REARM_PERFORMED=NO
```

**Current operational classification:** `STAGE8_493_PRODUCTION_TASK_ISOLATED_HALTED`, sourced from operator-observed Intel command. The production Task is Disabled and stopped, scheduled auto-start/restart suppressed, previous PowerShell/Python PIDs exited; post-stop strict FINAM READONLY two zero-position/zero-active-order broker snapshots, production SQLite before/after and existing production state lock quiescence all PASS. The original Task XML was backed up outside Git under `c:\tslaudit\fill493` (SHA-256 above; exact timestamped filename and bytes not independently retrieved). The kill switch was verified HALTED; no new trade or rearm. Durable production authorization was not deleted or rewritten. This is a bounded observation, not proof of perpetual broker flatness.

**Immediate operational-doc closeout completed:** a dedicated docs-only PR #502 was merged at GitHub `main=365108fc6e154123f24670a0a0098f5b1683ae6b` and independently audited, updating exactly 6 Markdown files: `TradingSystemLab/CURRENT_STATE.md`, `PROJECT_CONTEXT.md`, `ROADMAP.md`, `stage8_robot/PRODUCTION_RUNBOOK.md`, `PRODUCTION_STRATEGY_PASSPORT.md`, `PRODUCTION_OPERATOR_CHECKLIST.md`. Previous ARMED/Running sections are historical and explicitly superseded. Confirmed `main` diff contains *only six additions-only Markdown file changes*. No change to source/strategy/config/active checkout or frozen Stage7 `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`/`TRAIL1__N4_01__FULL__R15` / risk. Draft PR #493 remains **unmerged**. The pending candidate V2 100% SLTP multi-fill acceptance launcher is not real-order-authorized; the existing Stage8.11 1-contract acceptance limit and `FINAM_FILL_AUTHORITY_VERIFIED=False` remain unchanged.

**Next permitted work:** review and test an independent operator-only multi-fill SLTP acceptance harness and rollback/recovery *offline*; no broker POST/CANCEL, no Task restore/restart, no rearm or fill-authority unlock without new explicit user approval and current broker risk/capacity evidence.
