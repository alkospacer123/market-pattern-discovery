# Intel Windows host deployment (no order authorization)

The installed task is **REAL_READONLY** and cannot transmit orders. Keep the Git
checkout read-only for the service identity. Put mutable data outside it, under a
runtime root with separate `state`, `audit`, `logs`, `diagnostics`, and `backups`
directories. Grant that identity access only to the runtime root.

## Secret injection

Use a dedicated Windows service account. Store `FINAM_API_SECRET` and
`FINAM_REAL_ACCOUNT_ID` in that account's protected environment (for example,
retrieve them at logon from Windows Credential Manager into the process
environment). Never put either value in Git, a `.ps1` file, Task Scheduler
arguments, or diagnostic output. A read-only FINAM token is mandatory.

## Install and recovery

1. Run `server_preflight.py --offline --state-directory <runtime>\state`, then the
   connected preflight under the service identity.
2. Install with `install-task.ps1`; inspect the task before enabling it.
3. On boot the process acquires the state lock, opens the existing SQLite state,
   reconnects, and reconciles positions, active orders, fills, and durable intents.
   New entries remain disabled until reconciliation succeeds; REAL_READONLY keeps
   them disabled even after success. An unresolved intent blocks entries and is
   never blindly retried.
4. Schedule `backup_state.py <state-db> <backup-dir> --keep 14`. It uses SQLite's
   online backup API and verifies `PRAGMA integrity_check`.

To restore, stop the task, retain the damaged database, integrity-check the chosen
backup, restore it into `state`, and run offline then connected preflight. Start the
task only after reconciliation. Never filesystem-copy a live WAL database.

Operational logs use bounded rotating files; audit logs are JSONL. Heartbeats are
atomically replaced and contain only production ID, account hash, timestamps,
reconciliation state, entry gate, and unresolved-order count. Do not log secrets or
raw account identifiers.

`LIVE_TRADING_NOT_AUTHORIZED` remains in force after deployment.
