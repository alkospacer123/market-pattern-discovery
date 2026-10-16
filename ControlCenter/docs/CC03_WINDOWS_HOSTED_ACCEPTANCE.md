# CC-03: Windows audit corrections in Draft PR #534

**CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED.** Own immutable transport and legacy live-source compatibility are separate. No `CC03_WINDOWS_NATIVE_PASS` or `CC03_PHYSICAL_PASS` is claimed. Same [Draft PR #534](https://github.com/alkospacer123/market-pattern-discovery/pull/534), same branch `codex/controlcenter-cc03-windows-native`; no new phase, merge, auto-merge, Intel or trading operations.

## Actual Windows evidence

Primary engineering run [38868278178](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38868278178); complete decoded job log read and preserved. [Raw logs/JUnit/environment/deployment artifact](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38868278178/artifacts/12032118261), SHA-256 `c3336b7477c92a60ad22fd8da50c1541ec6e5a2c07cb0bee01c09c9b7241974b`, expires 2026-11-15. The PR description records the final report-commit HEAD/run and independent repeat, avoiding a self-referencing commit hash in this manifest-covered file.

- PR head: `c09b4881d53466799ea0bd543e66223118354199`.
- Tested synthetic merge SHA: `f3235053c99f25beda06aeeed3ed20bce84cec15`.
- Base: `cb7e1cc32694fb97fba3c7f9200f9a492d8eebea`.
- Tested ControlCenter tree: `7797cdd2c34d5a5e83e01b9093347b8e56d3e429`.
- Standard GitHub-hosted `windows-2022`, Windows Server 2022 Datacenter build 20348, local fixed NTFS.
- Python `3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]`, **64-bit**; pytest 8.4.2. Exact Python 3.12.10 and 44 SHA-256-pinned Windows wheels; freeze in artifact.

| Actual pytest execution | PASS | FAIL | SKIP |
| --- | ---: | ---: | ---: |
| windows-reader | 44 | 0 | 0 |
| windows-transport | 12 | 0 | 0 |
| cc03-source | 27 | 0 | 0 |
| full-suite | 337 | 0 | 15 |

`manifest.py --check`: exit 0; `pip check`: exit 0. Windows-native SKIP count: **zero**. Fifteen POSIX-only skips are listed below; none converted from a native failure.

## A. CC-owned publication

Exporter now publishes closed, fsynced temporary bytes by Windows rename to a unique completed filename containing a timestamp, UUID and SHA-256. It never overwrites an open published file. Receiver discovers the latest exact completed name inside held no-reparse ancestor/root handles, with an independently installed NTFS root identity pin, bounded directory enumeration and 128 KiB file limit. It verifies filename digest, schema digest, file identity/size/times/link count, canonical path and before/after pathname identity. Partial names are ignored; an invalid completed latest file produces UNKNOWN, without last-good fallback. Source/account provenance and TTL checks remain independent. Directory timestamps are excluded from identity comparison because legitimate child publication changes them; identity and attributes remain checked.

Native transport tests hold an old snapshot open throughout 24 concurrent publications and overlapping reads, require all publications to finish, and verify byte/schema integrity. Substitution, hardlink/symlink, directory, oversize, wrong root pin, changed file and discovery/publisher capacity failures are tested. The publisher refuses new writes at 2048 total directory entries; receiver rejects enumeration beyond that bound. No automatic deletion or production retention policy is introduced. Offline maintenance is a residual deployment gate.

## B. Legacy producers remain incompatible

Audit baseline [38862976125](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38862976125) remains **323 PASS / 2 FAIL / 15 POSIX SKIP**. Its two original compatibility requirements are **NOT PASSED**: an open observer leaf causes `os.replace` WinError 5. No new Win32 share/access flag search was used as a fix. H1 producers, source directories and publication scheme are unchanged.

`read_source` and default CLI collection now fail closed with `CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED` before any legacy source open. Existing conflict tests were explicitly changed into executable negative compatibility regressions: they reproduce the conflict and demonstrate producer recovery after handles close. Their pytest PASS means expected incompatibility was reproduced; it does **not** satisfy the original live compatibility requirement. A separate real concurrent legacy producer test confirms that a disabled observer does not interfere; it reads no heartbeat/kill-switch data. Injected synthetic contract readers are not a CLI bypass or proof of live monitoring. Stopped-source reads are not used as evidence of continuous compatibility.

All twelve original native scenarios execute:

| Executed native regression | Actual pytest result |
| --- | --- |
| `test_native_read_and_hardlink` | PASSED |
| `test_native_symlink[False]` | PASSED |
| `test_native_symlink[True]` | PASSED |
| `test_native_junction_reparse` | PASSED |
| `test_native_legacy_replace_conflict_requires_live_block` | PASSED |
| `test_native_api_missing` | PASSED |
| `test_native_missing_oversize_and_directory` | PASSED |
| `test_native_existing_writer_and_pinned_directory` | PASSED |
| `test_native_insufficient_file_acl` | PASSED |
| `test_native_legacy_concurrent_conflict_and_release` | PASSED |
| `test_native_policy_with_untrusted_write_acl_is_rejected` | PASSED |
| `test_native_admin_owned_policy_accepts_then_rejects_weak_ace` | PASSED |

Ten original security scenarios are accepted when passing; the two legacy replacement scenarios remain negative compatibility evidence. No native FAIL was changed to SKIP/XFAIL.

## Separate-SID startup and deployment

PowerShell 5.1 parser checks all eight deployment files; all seven entrypoints run safe preview, including Probe-H1Task. Probe-H1Task -Execute is never run. Rehearsal uses only its own GUID-named RUNNER_TEMP tree and two disposable standard local users. Passwords remain in memory, absent from process arguments/bootstrap/logs.

| Actual runtime check | Result |
| --- | --- |
| separate_sid_acl | PASS: 10 actual access probes under two distinct non-admin logon tokens |
| invalid_wheel_regression | PASS: bad hash rejected before any target write |
| install | PASS: real offline install into disposable ACL-provisioned roots |
| panel_listener | PASS: HTTP health 200, 127.0.0.1:8501 owned by CCPanel SID S-1-5-21-3213014087-2684668049-2838998412-1003 |
| panel_verify | PASS: low-privilege panel and real loopback-only listener; receiver remains UNKNOWN without approved source |
| exporter_fail_closed | PASS: separate-SID one-shot rejected unapproved policy, published nothing beyond the explicitly synthetic CI probe |
| physical_source | OUT_OF_SCOPE: physical H1 source/account/TTL authority remains a separate Intel gate |
| process_cleanup | PASS: own panel process tree exited and listener removed; exporter already exited |
| uninstall | PASS: own package/venv removed, disposable private/export/log data retained |
| status | PASS |

Startup diagnosis was independent of Streamlit: run [38867672338](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38867672338) captured a direct Python `_ctypes` DLL initialization failure, while native cmd exited normally. Earlier PowerShell had one thread waiting in LpcReply before CLR/bootstrap. Environment cleanup, a null/empty desktop comparison and stdio alone did not resolve it. Run 38868278178 resolved both Python DLL initialization and PowerShell startup by assigning each launched role process a **new private noninteractive window station/desktop**. Its protected DACL grants only SYSTEM, Administrators and that target SID. Existing stations/desktops and all token privileges are untouched; no user is granted access to the runner's interactive desktop. Handles are retained for the child lifetime and closed after exit.

Actual direct probes print `PYTHON_ACTUAL_SID`, `IDENTITY_WINDOWSTATION=CC03-<guid>`, `IDENTITY_DESKTOP=CC03`, exact venv executable/cwd, and `ntfs_read_spawn=PASS` for both CCPanel (`...-1003`) and CCExporter (`...-1004`). The listener is a descendant of the launched panel tree with CCPanel owner SID. Its base Python executable shown by CIM is the normal Windows venv redirector behavior; the venv path/version is separately recorded by each direct probe.

Native launcher uses an explicit target-user environment block and role-writable temporary/profile directories within existing allowed write roots. It supplies explicit target-owned inheritable stdin/stdout/stderr handles. Native command and direct Python/spawn probes run before PowerShell; bootstrap separately records/verifies actual SID, cwd/PID and venv version. Streamlit must bind only 127.0.0.1:8501, answer health 200, and its listener must be owned by CCPanel SID; Verify independently checks listener ownership. CCExporter independently proves immutable publication of a clearly synthetic UNVERIFIED/UNKNOWN snapshot, then the actual Start-Exporter rejects an unapproved private policy without additional publication. No synthetic fixture claims broker/source authority. Only created process trees are stopped; listener removal and data contents after Uninstall are checked. Any uncompleted check remains unverified, never inferred from previews.

ACL matrix, administrator-owner requirements, CORS/XSRF, execution policy, account isolation and existing Windows privileges are preserved. Real positive/negative file access uses two non-admin logon tokens. No filesystem ACL is applied outside the disposable CC tree; new private GUI objects receive the narrow role DACL described above. Full source/ACL physical acceptance is not inferred from CI.

## POSIX-only skips

Reason: `POSIX descriptor fault injection; native Windows equivalents in test_windows_reader.py`.

- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[file_symlink]`
- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[directory_symlink]`
- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[ancestor_symlink]`
- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[hardlink]`
- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[fifo]`
- `tests.test_h1_fault_injection.test_unsafe_files_and_ancestors_rejected[directory]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[replace]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[truncate]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[grow]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[rewrite]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[symlink]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[root_replace]`
- `tests.test_h1_fault_injection.test_partial_write_and_path_races_fail_closed[root_symlink]`
- `tests.test_h1_fault_injection.test_no_secure_platform_primitive_fails_closed`
- `tests.test_h1_fault_injection.test_read_uses_no_write_capability_or_external_systems`

## Scope and remaining gates

Only `ControlCenter/` and `.github/workflows/controlcenter-cc03-windows-native.yml` may differ. Workflow remains pull_request/path-filtered, contents: read, windows-2022, timeout 15 minutes, sparse checkout, persist-credentials false, pinned action commits. No self-hosted/larger runner, pull_request_target, repository secrets, production environment variables, remote sessions or trading operations. Previous read attempts to administrative Actions settings returned 403/404; actual standard runner execution establishes CI availability, not access to those settings.

| Protected tree | Base = head |
| --- | --- |
| TradingSystemLab | `d27ac7153a4d25455112c1a6673d2b37a1784f43` |
| IntradayLab | `c4f6e652ba442a575ad5711cb3f55841f860f484` |

Protected diff is empty. Frozen identities, strategies, production configuration, SQLite/WAL, H1 Task, kill switch, authorization and FINAM logic are untouched. Legacy live compatibility is unresolved; continuous real H1 monitoring remains prohibited. Physical identities/ACLs, real heartbeat/kill-switch source, account binding, approved TTL/calendar, before/after checks and separate operator installation authorization remain Intel acceptance gates. No CC-04. STOP after independent repeat and scope checks.
