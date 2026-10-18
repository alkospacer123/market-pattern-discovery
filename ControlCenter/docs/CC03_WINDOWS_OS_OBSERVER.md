# CC-03 independent Windows OS READONLY observer

Metadata outcome: the first real Windows run disproved noninterference. `observer/` contains no production-file metadata implementation; preflight only inspects own CC directory attributes. The failed zero-access handle experiment is quarantined under `ci/metadata_experiment.py`; its expected-conflict test is **NOT** a passed metadata acceptance requirement.

Engineering scope: Issue [#524](https://github.com/alkospacer123/market-pattern-discovery/issues/524), CC-03 only. NO INTEL INSTALL, NO TRADING, NO H1 START/RESTART/REARM, NO FINAM, NO CC-04. Physical acceptance NOT_EXECUTED.

## Baseline and authority

PR [#534](https://github.com/alkospacer123/market-pattern-discovery/pull/534) merged 2026-10-16 08:06:41 UTC (11:06:41 MSK) as `a6e9634bc0a5db378fcff32ea1bc8591baaf1d3c`, parents `2f0c9592bbca012471da9cbb15fdfaa764d8e17f` and `aa9ce4eeac13d12fd4ca552932f3118730ae7c73`. That was the observer implementation baseline; the current preflight continuation starts at actual main `c9dea4e1fb728c97c3c14e70ae75adab6e6cfc94` after merged #541. ControlCenter tree at baseline `689e67353542e796daf8df93681cc72756a019f1`.

Protected baseline trees, also equal to supplied `2f0c959…`: TradingSystemLab `d27ac7153a4d25455112c1a6673d2b37a1784f43`; IntradayLab `9b71aeff75c49d3fc7b2fff7116b21d03fee5783`. The older #534 PR body mentions a historical IntradayLab tree; that is not substituted for the actual current baseline.

Read `TradingSystemLab/CURRENT_STATE.md`: latest operator-supplied checkpoint is ARMED generation 62 / Task Running / installed executable `3a18c8c24301c866a60f5d725de227288d48f7ec`. The historical HALTED statements in the original issue are superseded operational history. This observer has no current trading authorization source and reports UNKNOWN. It must never stop/rearm/change the existing robot to arrange a panel test.

Previous actual [Windows run 38868961076](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38868961076), job `116868260899`: full 337 PASS / 0 FAIL / 15 POSIX-only SKIP; immutable transport 12 PASS; reader 44 PASS. Job log reviewed. The two legacy replace requirements remain NOT_PASSED: opening JSON contents blocks unchanged `os.replace` producers. That reader remains disabled before file opening.

## Sources and limits

| OS fact | Exact source / binding | Failure | Authority and limitations |
| --- | --- | --- | --- |
| TASK_DISABLED / TASK_READY / TASK_RUNNING | Local Task Scheduler COM: Connect current token, GetFolder root, GetTask exact `TradingSystemLab-Stage8-Production`; SHA-256 of complete XML (UTF-8 bytes, no normalization), translated principal SID; before/after XML/state agreement | Missing, denied, changed, Queued/unknown, mismatch -> UNKNOWN with sanitized reason | Local Task configuration and sampled state only. No code attestation, robot health, broker connection, HALTED, authorization or absence of positions |
| PROCESS_OBSERVED | Local CIM Win32_Process for **one approved numeric PID**; exact creation epoch SHA-256, executable path lowercase SHA-256, full command line SHA-256, owner SID via GetOwnerSid; reread identity/creation | Different image, command, creation epoch or SID -> UNKNOWN; inaccessible -> UNKNOWN; exact PID missing -> PROCESS_ABSENT | Approved process epoch observed. PID absence says only that pinned process is absent; a restarted robot is not discovered automatically. No claim of zero positions or current in-memory code contents |
| Metadata | **DISABLED / CC03_METADATA_COMPATIBILITY_BLOCKED** | Native run 38873837179 observed producer Access denied even with zero desired access + all sharing | No production metadata path accepted, no metadata module imported by observer; schema rejects positive metadata facts. Failed experiment retained only in CI |

Full command line, Task XML, usernames, private paths, raw account IDs and environment variables are never exported or logged. Fingerprints remain configuration references, not credentials or proofs of broker identity. A process name alone never produces PROCESS_OBSERVED. Native APIs are local only; there is no broker/network API client. CIM/COM use the current token without enabling privileges or impersonation.

Process binding is intentionally conservative: a restart/command-line change requires an operator-reviewed new private binding. There is no name scanning, automatic rebinding, Task-to-broker authority, or fallback to legacy JSON. Python.exe alone is insufficient. Where a standard observer cannot read another account's process attributes, leave process observation disabled/UNKNOWN; do not grant admin or SeDebugPrivilege to make it green.

## Independent process and policy

`python -m observer.windows_os` is preview; `--execute` is a one-shot independent process, outside the UI import graph. `Start-Exporter.ps1 -OsObserver` uses this entrypoint after existing distinct SID, package and ACL checks. It grants no new Windows rights. The old exporter entrypoint remains blocked for live content. Nothing installs a Task/service in this change.

The observer accepts only administrator/SYSTEM-owned, non-writable-by-standard-user `private/os-policy.json` through the existing secure policy reader. Exact observer SID must match its own non-elevated token and differ from both production principals. Fixed production Task name, CC export root pin and typed allowlists are validated before probing. Receiver policy remains administrator-owned and separately binds source_id, random binding_id, account_alias, export_root_id and TTLs. `account_alias` is only an operator label; `account_binding=UNVERIFIED` is mandatory in OS envelopes, including with matching local policy. No VERIFIED_LIVE_READONLY upgrade exists.

Example policies are deliberately invalid/unapproved. Approval flags cannot authenticate themselves: the OS ACL, owner, source fingerprint and root pins form the local trust boundary. No private policy is packaged into the release manifest. No UI control accepts PID, Task name, command, path, policy or timeout. PowerShell receives policy over stdin and executes only the packaged fixed script with `-File`, not shell interpolation. The UI reads only completed CC export files.

Source operation limits: one OS Task/process PowerShell subprocess, total 6 seconds (each CIM operation <=2 seconds). Metadata probing is unconditionally disabled; the active observer has no production file path or metadata worker. Secure private-policy read is separately bounded at 2 seconds. Timeout yields UNKNOWN/TIMEOUT, never ABSENT or success. Publisher touches only CC-owned local NTFS with <=2048 entries and <=256 MiB; no production handle is held during publication. This is bounded one-shot collection, not a 1–2 second H1 content poll. Any future scheduling belongs solely to the separate CC identity, after physical approval, with no overlapping instances and an approved cadence/TTL.

## Envelope and UI

[Schema](CC03_WINDOWS_OS_SCHEMA.json) is distinct from historical heartbeat envelopes. Its sole authority is WINDOWS_OS_ONLY. Task and process carry actual observation UTC time, confidence, reason and typed value. Metadata placeholders are always UNKNOWN/DISABLED with null value; their timestamp is only the time the observer recorded that source was disabled. Generation time cannot substitute for observation time. Receiver checks checksum, exact schema, source binding, future times and individual TTL plus envelope TTL. Unknown TTL -> UNKNOWN; stale -> facts hidden / authority UNKNOWN. Latest corrupt export never falls back to old green data.

H1 summary remains UNKNOWN even with TASK_RUNNING and PROCESS_OBSERVED. Broker positions, signals, orders, FILL, ACTIVE SLTP, finances, PnL, deposits and drawdown remain unknown. M15 stays NOT_DEPLOYED / independent DEMO with no production authority. All ten operations buttons remain disabled. Restarting the panel only reloads snapshots; it cannot invoke the observer or change an OS/trading state.

## Windows verification and remaining gates

The existing unchanged `controlcenter-cc03-windows-native.yml` invokes the expanded ControlCenter test orchestrator. No new workflow, production variables, secrets, runner class or permission changes. Guarded `ci/Os-Fixtures.ps1` is a **mutating test harness**, excluded from the runtime graph; it can create/run/stop/delete only `CC03-CI-<32 hex>` disposable Tasks in a disposable GitHub-hosted VM. Production exact Task is never queried by tests. Test-only process lifecycle is limited to spawned child Python. No real Intel Task is used.

Native assertions cover Disabled/Ready/Running, missing/wrong Task, real Access denied under both standard SID tokens, exact process present/epoch/account mismatch/disappeared, stale/wrong source/account, actual timeout, 500 unchanged producer replaces concurrent with the active Task/process observer; a separate CI-only experiment explicitly reproduces metadata interference and recovery after closing handles, secure immutable OS transport and byte/root capacity stops, UI re-instantiation and before/after Task XML/state. Existing transport, ACL, installer/rollback and disabled-controls suites also run. See [execution evidence](CC03_OS_ACCEPTANCE.md) for actual run identifiers/counts; Linux tests do not establish Windows noninterference.

Current engineering result is **CC03_OS_READONLY_OBSERVER_PARTIAL**: Task/process OS mechanisms can be demonstrated; metadata noninterference failed and is disabled; production source/ACL/account/TTL binding, full heartbeat and broker data remain unavailable, runtime retention is not accepted, and Intel physical acceptance remains NOT_EXECUTED. Neither CI PASS nor this result is CC03_PHYSICAL_PASS or trading permission.

## Separate Intel permission-A preflight (plan only)

`python -m observer.intel_preflight` defaults to PREVIEW without policy/Task/process/root probes. `--execute` requires explicit operator A, an existing standard observer token, and a separate SYSTEM/Admin-owned `deployment/preflight-policy.json` in an already approved standalone review copy. It needs no installed CC users/roots or active OS source. It never publishes, installs or modifies ACL. Standard-user writes to policy ancestors/leaf are rejected. See [physical plan](CC03_PHYSICAL_ACCEPTANCE_PLAN.md), [private templates/approval](CC03_INTEL_PREFLIGHT_POLICIES.md), and [package report](CC03_INTEL_READONLY_PREFLIGHT_PACKAGE.md).

A first verifies exact Task XML/principal without PID query; optional previously approved PID/epoch then receives one targeted check; final Task observation brackets process acquisition. Running is accepted. Discrete identity/state disagreement blocks; natural restart/PID reuse remains PROCESS_UNKNOWN without discovery/rebinding. Task/PID match are configuration/OS observations, never executable-file attestation or trading health. No production checkout/JSON/metadata/SQLite/secret is read. Existing CC identities/roots may be NOT_PROVISIONED; existence is not effective ACL acceptance and `cc_acl=NOT_VERIFIED` remains in the report.

Independent report classifications include TASK_IDENTITY_MATCHED, TASK_RUNNING_OBSERVED, PROCESS_IDENTITY_MATCHED, PROCESS_UNKNOWN, ACCESS_DENIED, CCPANEL_NOT_PROVISIONED, OS_SOURCE_APPROVAL_REQUIRED and UNKNOWN. A PASS is a Task bracket observation only. B (own CC installation) and C (source/TTL/ACL approval + first export) are later separate decisions; none is implied by A. No Intel command was run in this preparation. The next decision is limited A; no CC-04.

Single-ccpanel audit #548: preflight policy/report v2 and explicit B readiness are described in [CC03_INTEL_PREFLIGHT_POLICIES.md](CC03_INTEL_PREFLIGHT_POLICIES.md). No exporter SID is required; A remains independent of B/C. Both pinned PowerShell children use process-scoped ExecutionPolicy Bypass only; machine/user/GPO policy is unchanged. No Intel execution is authorized by this package.
