# CC-03 OS READONLY acceptance: PARTIAL

**CC03_OS_READONLY_OBSERVER_PARTIAL**. Task/process observer demonstrated on real Windows; metadata and legacy content sources remain BLOCKED and disabled. **Intel physical NOT_EXECUTED**. No trading authority is inferred or changed.

Draft [PR #541](https://github.com/alkospacer123/market-pattern-discovery/pull/541), roadmap [#524](https://github.com/alkospacer123/market-pattern-discovery/issues/524). Base after merged #534: `a6e9634bc0a5db378fcff32ea1bc8591baaf1d3c`. No merge/auto-merge/Intel actions. All changed paths ControlCenter; existing workflow unchanged.

## Successful native engineering run

[Windows run 38890829808](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38890829808), job `116939655825`, successful 2026-10-16 11:05 UTC / 14:05 MSK. HEAD `e8c7666f3e840cf3e6aa6cab88ad909828e9c1c9`; tested synthetic PR merge `aebb9d3130f9306994ba88db43194c0014b1b042`; ControlCenter tree `8e2095b540c324416ed465ce9254432354627548`. Complete execution log and result JSON reviewed. This report commit changes only documentation and package checksums; the final exact-HEAD rerun URL/counts are recorded in the PR description after execution.

Standard unchanged `windows-2022`, Microsoft Windows Server 2022 Datacenter build 20348; disposable local D: NTFS; CPython **3.12.10 x64**, pytest 8.4.2 and the existing 44 hash-pinned wheel set. No self-hosted/larger runner, production variables, credentials or workflow permission changes.

| Actual Windows group | PASS | FAIL | SKIP |
| --- | ---: | ---: | ---: |
| Windows reader | 44 | 0 | 0 |
| Immutable transport | 12 | 0 | 0 |
| Historical CC-03 source/authority | 27 | 0 | 0 |
| OS observer contract + native APIs | 37 | 0 | 0 |
| Full ControlCenter pytest | **375** | **0** | **15 POSIX-only** |

Groups are subsets/repeated verification, not additive totals. Full Linux engineering suite: 354 PASS / 0 FAIL / 36 Windows-only SKIP. Linux is not native Windows acceptance. All 15 Windows skips are existing POSIX descriptor injections with native equivalents; exact names/reasons in [machine-readable results](CC03_OS_NATIVE_RESULTS.json). No metadata or new OS scenario was skipped or xfailed. Expected-conflict regressions are distinguished below from source acceptance.

`manifest.py --check`, `pip check`, eight deployment PowerShell syntax checks/seven previews PASS. New fixed OS probe and guarded CI fixture scripts executed natively. Two distinct standard user SIDs: actual token, private desktop/Python/spawn, 10 effective ACL probes, positive readonly Task and true Access denied under each SID PASS. Actual installed observer entrypoint under exporter SID rejects missing/unapproved OS policy before probing and publishes nothing. Separate-SID synthetic immutable publication remains PASS. Offline installation, invalid-wheel-before-write rejection, child-owned `127.0.0.1:8501` HTTP 200, Verify, unapproved legacy exporter fail-closed, own process cleanup and Uninstall/data retention PASS.

[Execution artifact: logs, JUnit, environment, package/dependencies, rehearsal](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38890829808/artifacts/12042047232), SHA-256 `53faa862d065b25131f13b1e360328db70e4eeb38c6b79a8dafaeb1a4c9b96e1`, expires 2026-11-15 11:05:22 UTC / 14:05:22 MSK.

## Requested scenarios and practical limits

| Scenario | Actual evidence / result |
| --- | --- |
| 1 Task Disabled | PASS: native exact XML/SID identity, TASK_DISABLED, before/after unchanged |
| 2 Task Ready | PASS: native TASK_READY, before/after unchanged |
| 3 Task Running | PASS: native disposable Task TASK_RUNNING, no robot HEALTHY inference |
| 4 Missing Task | PASS: UNKNOWN/NOT_FOUND |
| 5 Wrong Task identity | PASS: wrong XML hash and principal SID -> UNKNOWN |
| 6 Access denied | PASS: real protected disposable Task under both standard SIDs -> UNKNOWN/ACCESS_DENIED |
| 7 Process exists | PASS: exact test-child PID, creation epoch, image, command fingerprint and SID -> PROCESS_OBSERVED |
| 8 Process disappeared | PASS: pinned PID missing -> PROCESS_ABSENT; not proof of robot absence/flat broker |
| 9 Wrong process identity | PASS: image/command/creation epoch/owner mismatches -> UNKNOWN |
| 10 Stale observation | PASS: snapshot or individual TTL expired/unknown -> positive facts hidden, authority UNKNOWN |
| 11 Probe timeout | PASS: actual PowerShell process timeout bounded; UNKNOWN/TIMEOUT, not absence |
| 12 Producer concurrent with allowed observer | PASS: actual Task/process acquisition while unchanged synthetic producer performs 500 os.replace calls |
| 13 No producer interference | **PASS for enabled Task/process observer: 500/500, zero producer errors**; metadata disabled before any file access |
| 14 Wrong account/source | PASS: receiver binding mismatch -> UNKNOWN, never VERIFIED; matching OS account label still UNVERIFIED |
| 15 H1 absence vs M15 | PASS: missing H1/export leaves M15 independently NOT_DEPLOYED/DEMO; no production authority |
| 16 Panel restart | PASS: separate AppTest instantiations and actual panel lifecycle preserve disposable Task XML/state; all 10 controls disabled |

No physical H1 Task, production process or trading state was sampled to manufacture these tests. The runtime import/capability boundary and synthetic/disposable state checks demonstrate no trading mutator path; actual Intel before/after remains a separate physical gate.

## Metadata failed: deliberately not connected

First [native engineering run 38873837179](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38873837179), job `116884027834`, HEAD `19b05ebfa9964ec1b97f91ec515a5ed521c26329`: full **369 PASS / 2 FAIL / 15 POSIX-only SKIP**, OS group **31 PASS / 2 FAIL / 0 SKIP**. One failure was UTF-8 test-source decoding via Windows cp1252, corrected with explicit UTF-8. The material failure was **metadata noninterference NOT_PASSED**: zero desired access plus READ|WRITE|DELETE sharing still caused `PermissionError(13, Access is denied)` in the unchanged synthetic os.replace producer. Full job log reviewed; no producer code change/retry workaround was introduced.

Consequent safety decision: move the failed experiment to `ci/metadata_experiment.py`; runtime observer imports no metadata implementation and accepts no production filesystem paths. `metadata_enabled=true` fails before native probing. Receiving schema rejects positive metadata facts and requires UNKNOWN/DISABLED placeholders. A CI-only regression reproduces the conflict and proves the same 500 replaces recover after all experimental handles close. Its PASS means **the blocker was reproduced and isolation retained**, not metadata acceptance. Legacy JSON content remains independently `CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED` from #534.

## Available observations and unavailable trading data

| Data | Verified mechanism | Actual Intel availability now | Authority |
| --- | --- | --- | --- |
| Exact Task state + observation timestamp | PASS in real Windows CI, including standard SID | UNKNOWN until existing ACL/binding accepted; never queried here | WINDOWS_OS_ONLY |
| Exact pinned process epoch present/missing + timestamp | PASS in real Windows CI | UNKNOWN; another account may deny attributes, automatic rebind forbidden | WINDOWS_OS_ONLY, no code/broker attestation |
| Source identity, confidence, individual freshness | Schema/receiver/native transport PASS | Source policy/TTLs not physically approved | Local source binding only; account UNVERIFIED |
| File presence/mtime/size/file identity | Experiment could obtain values but failed noninterference | **BLOCKED / DISABLED**, not connected | None |
| Heartbeat / HEALTHY / broker contact / kill-switch state / trading authorization | No safe approved source | UNKNOWN; legacy JSON and metadata disabled | None |
| Completed H1 bars / signals / NO SIGNAL reasons | No approved emitted telemetry | UNKNOWN | None |
| Positions / orders / FILL / active broker protective stops / reconciliation | No FINAM or production SQLite/WAL source | UNKNOWN, never zero/flat/protected by inference | None |
| Equity / PnL / deposits / cashflows / drawdown | No approved accounting feed | UNKNOWN | None |
| M15 | Independent synthetic display only | NOT_DEPLOYED, no CC-04 work | NO_RUNTIME_AUTHORITY |

[Future source specification](CC03_FUTURE_TELEMETRY_SPEC.md) covers each required field's existing contract, read safety, expected producer, authority, freshness, account binding and current blocker. It does not authorize H1 changes. [Retention](CC03_EXPORT_MAINTENANCE.md): no automatic deletion, 2048 entries / 256 MiB bounded stop; native tests preserve the sole open confirmed snapshot and outside data on capacity/root failure. Runtime cleanup remains NOT_ACCEPTED.

## Integrity and handoff

| Protected Git tree | Base = tested HEAD |
| --- | --- |
| TradingSystemLab | `d27ac7153a4d25455112c1a6673d2b37a1784f43` |
| IntradayLab | `9b71aeff75c49d3fc7b2fff7116b21d03fee5783` |

Both also equal supplied `2f0c9592bbca012471da9cbb15fdfaa764d8e17f`; protected diff and workflow/root-roadmap diff empty. No strategies/configuration/research/production code, Task, SQLite/WAL, authorization, kill-switch or broker actions. Latest CURRENT_STATE's running ARMED checkpoint is operator history, not current panel telemetry.

Next physical step is a **plan only**: after independent PR audit and a separate operator decision, validate the offline CC package/private OS-policy template and existing Intel READONLY permissions under separate standard CC SIDs; bind exact existing Task XML/principal and pinned process epoch without changing the H1 state, checkout, Task or ACL. Leave inaccessible sources UNKNOWN. The detailed [physical plan](CC03_WINDOWS_OS_OBSERVER.md#next-physical-step-plan-only) keeps metadata/content disabled and requires separate approved before/after checks. No installation or physical command is executed here.

**STOP for independent audit. NO MERGE / NO AUTO-MERGE / NO INTEL INSTALL / NO H1 START/RESTART/REARM / NO FINAM / NO CC-04.**
