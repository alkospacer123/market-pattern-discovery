# Intel Windows host: DPAPI-protected read-only startup

This deployment is **REAL_READONLY** and cannot transmit orders. It implements
the code path needed for Stage 8.8.4.3; it does not claim reboot or 24/7
validation. Keep the local Git checkout read-only for the task identity.

## Credential and identity model

`initialize-readonly-credentials.ps1` prompts locally (SecureString input) for
the read-only FINAM token and real account ID. It serializes schema version 1,
mode `REAL_READONLY`, the production ID obtained from the checked frozen Stage 7
authority, token, and account ID in memory, then protects it with Windows DPAPI
`CurrentUser`. Stable, non-secret entropy is
`TradingSystemLab.Stage8.RealReadonly.v1`.

Ciphertext is `<runtime>\secrets\finam-real-readonly.dpapi`. The adjacent JSON
metadata contains only schema, `CurrentUser` scope, creation time, production
ID, and SHA-256 of the Windows SID. It contains no token, account ID, or token
hash. Inheritance is disabled on the directory and files; only the exact
bootstrap SID is granted access. Bootstrap fails if this ACL cannot be applied
and verified. The checkout contains no generated credential.

The bootstrap identity, Scheduled Task identity, and supervisor identity must
be the same. Installation decrypt-verifies the store under the current SID,
shows only that Windows name and SID, and asks for that same user's Windows
password with `Get-Credential`. Task Scheduler/LSA stores its protected logon
credential. `LogonType Password` allows the AtStartup task to run before an
interactive desktop login; the task never runs as SYSTEM.

`run-readonly.ps1` treats DPAPI as authoritative. It does not fall back to or
mix existing environment credentials. After validating SID metadata, DPAPI
scope, schema, mode, and production ID, it places both values only in its own
process environment for the child Python preflight and supervisor. It never
uses `setx`, User/Machine environment persistence, registry storage, command
arguments, or credential output.

## Operator sequence

From a PowerShell session running as the exact future task user:

1. Checkout the intended commit, make it read-only to this identity, and run
   the Stage 7/8 audits plus offline preflight.
2. Choose an explicit external runtime root (normally
   `C:\TradingSystemLab\runtime`). The bootstrap creates `secrets`.
3. Run `initialize-readonly-credentials.ps1 -RuntimeRoot <runtime>`. Enter the
   token/account only into the local secure prompts.
4. Run `verify-readonly-credentials.ps1 -RuntimeRoot <runtime>` and require
   `DPAPI_CREDENTIAL_STORE_PASS` plus all four sanitized booleans.
5. Run `install-task.ps1 -Checkout <checkout> -RuntimeRoot <runtime>`. Confirm
   the displayed name/SID is exactly the bootstrap identity and answer the
   secure Windows credential prompt.
6. Inspect the registered principal and action. Credential values must not be
   arguments. The policy is `RemoteSigned`, because this repository has no
   trusted Authenticode signing infrastructure; `AllSigned` would knowingly
   make these unsigned local scripts non-executable. Do not use `Bypass`.
7. Start the task manually once.
8. Inspect sanitized heartbeat and SQLite cycle continuity; require healthy
   reconciliation, zero positions/orders, disabled entries, and zero real
   orders transmitted.
9. Only then conduct the physical Intel host reboot acceptance.

The trigger is AtStartup, failures restart up to 10 times at two-minute
intervals, the execution limit is long, and Task Scheduler uses `IgnoreNew` as
defense in depth. The supervisor's `InstanceLock` remains final authority.

**Never paste FINAM token/account ID into Git, ChatGPT, Codex task text, Task
Scheduler arguments, or ordinary environment persistence.** Never print or
record the decrypted payload. Direct manual Python supervisor calls may still
use temporary caller-process environment variables; the Windows launcher does
not.

## Rotation and recovery

To rotate the read-only token: stop the task; rerun the interactive bootstrap
under the exact same task user; run sanitized verification; start the task; and
inspect heartbeat/SQLite. A changed task identity requires a fresh bootstrap
under that identity and exact principal verification—never weaken DPAPI to
LocalMachine.

Mutable state remains outside Git: `state\stage8-readonly.lock`,
`state\readonly-supervisor.sqlite3`, rotating logs, atomic sanitized heartbeat,
audit output, and operator-managed verified backups. Never filesystem-copy a
live WAL database. `LIVE_TRADING_NOT_AUTHORIZED` and
`REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED` remain in force.

The only Stage 8.8.6 supervisor state authority is
`<runtime>\state\readonly-supervisor.sqlite3`; `stage8.sqlite3` is unrelated and
must never be selected. With the supervisor stopped, run
`python -m TradingSystemLab.stage8_robot.backup_state --runtime-root <runtime>`.
Select the emitted filename for
`python -m TradingSystemLab.stage8_robot.restore_state --runtime-root <runtime> --backup-filename <filename>`.
Restore success means only that validated continuity state was committed. Start
the existing REAL_READONLY supervisor afterward and require its normal account,
orders, schedule, H1 freshness, expected-H1, entries-disabled and read-only-token
reconciliation before accepting recovery.
