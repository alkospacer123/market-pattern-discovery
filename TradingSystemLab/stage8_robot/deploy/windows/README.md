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

## Persistent read-only architecture

The post-install process is `Windows startup` → `run-readonly.ps1` → connected
`server_preflight.py` → `readonly_supervisor` → continuous REAL_READONLY
observation. The launcher fixes `FINAM_MODE=REAL_READONLY` and
`NEW_ENTRIES_DISABLED=true`; it passes neither the secret nor account identifier
on the command line. `real_account_smoke` remains a manual funding/binding
diagnostic and is not the persistent service target.

The external runtime root contains:

* `state\stage8-readonly.lock` — lifetime process lock;
* `state\readonly-supervisor.sqlite3` — cycle, connectivity, reconciliation,
  clean-account, and per-instrument completed-H1 continuity state;
* `logs\stage8-readonly.log` — bounded rotating operational log;
* `diagnostics\stage8-heartbeat.json` — atomically replaced sanitized heartbeat;
* `audit\` — reserved external audit output; and
* `backups\` — operator-managed verified SQLite backups.

The supervisor verifies the read-only session, enumerated active account, empty
positions and active orders, and completed H1 observations for all N4 instruments.
It never sizes positions and has no broker/order lifecycle. Transient operational
failures use bounded exponential backoff and persistent faults terminate non-zero
for the Scheduled Task restart policy. Safety faults terminate immediately without
trying to alter broker state.

## Install and recovery

1. Run `server_preflight.py --offline --state-directory <runtime>\state`, then the
   connected preflight under the service identity.
2. Install with `install-task.ps1`; inspect the task before enabling it.
3. On boot the supervisor acquires its lifetime lock, opens its dedicated operational
   SQLite state, reconnects, and reconciles the expected clean account. Entries are
   unconditionally disabled. Unexpected broker state is reported but never changed.
4. Schedule `backup_state.py <state-db> <backup-dir> --keep 14`. It uses SQLite's
   online backup API and verifies `PRAGMA integrity_check`.

To restore, stop the task, retain the damaged database, integrity-check the chosen
backup, restore it into `state`, and run offline then connected preflight. Start the
task only after reconciliation. Never filesystem-copy a live WAL database.

Operational logs use bounded rotating files; audit logs are JSONL. Heartbeats are
atomically replaced and contain only production ID, account hash, timestamps,
reconciliation state, entry gate, and unresolved-order count. Do not log secrets or
raw account identifiers.

`LIVE_TRADING_NOT_AUTHORIZED` remains in force after deployment. The supervisor
code is ready for Intel operational acceptance; this documentation does **not**
claim that real 24/7 Intel validation is complete.
