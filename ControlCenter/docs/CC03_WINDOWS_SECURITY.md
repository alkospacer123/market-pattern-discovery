# CC-03 Windows security boundary

The current hosted evidence is in [CC03_WINDOWS_HOSTED_ACCEPTANCE.md](CC03_WINDOWS_HOSTED_ACCEPTANCE.md). Native transport acceptance and legacy live-source compatibility are separate decisions. Neither authorizes Intel installation.

## CC-owned immutable transport

`exporter/snapshot.py` publishes only into the independently provisioned ControlCenter export root. It creates an exclusive `.cc03-*.tmp`, writes at most 131072 bytes, flushes/fsyncs and closes it, then uses Windows `os.rename` to a previously nonexistent `h1-<20 digit time_ns>-<uuid32>-<sha256 of bytes>.json`. Windows rename refuses an existing destination. It never overwrites or deletes a published snapshot. A reader holding an old leaf therefore does not obstruct the next publication. File content still has its schema digest and independently accepted source/account binding; a filename digest supplies integrity, never producer authority.

The receiver requires an independently installed `ReceiverPolicy.export_root_id` (NTFS volume/file index triple). A spawned native worker pins all ancestors and that root before bounded discovery (at most 2048 total directory entries). Only exact completed names participate; the lexicographically last completed name is read. Temporary/partial files are ignored. An invalid latest snapshot causes UNKNOWN; there is no fallback to an older file. Clock reversal may leave an older name selected and TTL then expires; no freshness is inferred from the name. There is no automatic deletion/retention writer. At the entry limit the producer stops; beyond the limit discovery fails closed; offline maintenance is required before this capacity is reached. This bounded proof-of-transport is not an unattended production retention policy.

The reader uses local fixed NTFS only, drive-letter absolute paths. UNC/device namespace, ADS, traversal, reserved DOS names, trailing dot/space, reparse/junction/symlink and hardlink leaves are rejected. Kernel32 handles request no write/create/truncate access. Each ancestor is opened no-follow with LIST_DIRECTORY/READ_ATTRIBUTES/READ_CONTROL and READ|WRITE sharing, denying DELETE to pin its identity. Leaves request GENERIC_READ with READ|DELETE sharing and deny in-place writes. Final canonical path, type, attributes, volume/file index, link count, size, modification/creation times, exact bounded read length and pathname reopens are verified. Directory identity/attributes are rechecked; directory timestamps legitimately change during child publication. Completed-file SHA-256 must match its name. Root substitution, changed leaf, partial read, wrong pin or API/ACL error fails closed. No insecure read fallback exists.

A spawned process bounds I/O; parent waits two seconds for its response then terminates/joins. This is not a hard real-time guarantee on OS process creation or kernel scheduling. Administrator/kernel compromise, approved exporter compromise and writable memory mappings are outside this boundary.

## Legacy H1 live source: BLOCKED

Actual Windows run 38862976125 proved `PermissionError [WinError 5]` when an unchanged `os.replace` producer tries to replace a file with an observer handle open. Nine access/share combinations did not solve it. No further flag search is used as a fix. Neither H1 source producers, their directory, publication scheme nor ACLs are changed.

`read_source` now raises `CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED` **before opening any source or ancestor**. The one-shot CLI collector also blocks the default live-source path. Injected readers are reserved for synthetic contract tests; no CLI bypass exists. Stopped/historical-file reads do not establish live compatibility. The two former failing native scenarios now explicitly reproduce the incompatibility and demonstrate producer recovery after handles close. Their expected-conflict results are not a claim that the original live compatibility requirement passed. A separate concurrency regression proves that the disabled observer opens no legacy leaf while the unchanged producer continues publishing.

## ACL and identities

Intel B1 layout (operator-readonly verified 2026-10-17): protected `C:\Control Center` with frozen 97-file package plus separate empty `app`, `venv`, `data/export`, `data/logs`, `data/private`. Production root policy is unchanged for CI sandbox: the existing GitHub-hosted disposable override remains restricted to its temporary tree. The root itself is for trusted code review; panel/exporter receive only required traversal at the root, their actual read/write grants are on their own subtrees. All three role accounts initially remain DISABLED; actual role token access is NOT_VERIFIED. No live source is approved.

## Current CC-03 single-ccpanel directory permissions

| CC resource | SYSTEM / Administrators | ccpanel standard token |
| --- | --- | --- |
| app / venv / data parent | Full | Read/Execute |
| export (immutable completed snapshots) | Full | Read/Execute; **no publish/write/delete** |
| logs (CC-only) | Full | Modify |
| private (disabled source policies) | Full | **No access** |

Root owner must remain SYSTEM or Administrators, inheritance disabled. The only non-privileged SID allowed in installed CC subtree ACLs is the independently verified local **enabled** `ccpanel` SID. Installed entrypoints check exact SID and non-admin token; neither scripts nor tests grant privileges or modify H1. The former `ccobserver` / `ccexporter` accounts are left untouched and unused on Intel. CI provisions/removes precisely one temporary standard user only inside its hosted disposable sandbox.

Panel cannot write program, environment, receiving policy or export root; it cannot access `data/private`, FINAM secrets, DPAPI material or H1 production files. One account cannot safely perform the former private source-exporter role; `Start-Exporter.ps1 -Execute` **always fails closed**. Real CC telemetry remains UNKNOWN until a separately audited source/producer and physical authority review, not by pretending CCPanel can self-certify account identity, health or fills.

The separate-SID launch diagnostic creates a target-user environment block rather than inheriting runneradmin environment, gives each role a writable temporary directory within its existing allowed write root, and checks native process startup, actual token SID, working directory, venv access and Python spawn before Streamlit. Each role process uses a newly created private noninteractive window station/desktop with a protected SYSTEM/Administrators/target-SID DACL; no existing desktop ACL is changed. This resolved the actual `_ctypes` DLL initialization failure and pre-CLR PowerShell wait. Target-owned inheritable standard handles capture early output. No privileges, existing desktop ACL, execution policy, CORS/XSRF or GitHub token permissions are relaxed. The actual evidence determines whether startup passed.

## Evidence interpretation

Older hosted-acceptance transcripts and earlier two-SID diagrams below are historical and apply to the *superseded* two-account rehearsal only. They are not the acceptance record for this one-ccpanel change; the new Draft PR Windows run must pass independently. Exact OS/FINAM source authority remains unapproved.

## Acceptance boundaries

All twelve original native scenarios must execute without Windows SKIP; legacy conflict remains an explicit negative compatibility result. New immutable transport concurrency/substitution tests and deployment acceptance are independent requirements. Fifteen documented POSIX descriptor injections may skip on Windows; a Windows-native skip is incomplete. Any security failure is fail-closed. Physical identities/ACLs, H1 source/account binding, approved TTL/calendar, before/after checks and operator installation authorization remain separate Intel gates. Live legacy monitoring remains prohibited.
