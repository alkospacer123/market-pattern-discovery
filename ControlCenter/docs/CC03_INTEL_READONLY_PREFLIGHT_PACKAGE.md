# CC03 Intel READONLY preflight package

**CODE PREPARATION ONLY.** Engineering classification pending native Windows evidence: `CC03_INTEL_READONLY_PREFLIGHT_NEEDS_FIX` until required checks finish. Intel execution `NOT_EXECUTED`; physical acceptance `NOT_VERIFIED`. This document is updated with actual CI evidence before preparation completes. No result here equals CC03_PHYSICAL_PASS.

## GitHub provenance and scope

Repository `alkospacer123/market-pattern-discovery`; continuation of #524, previous #541 MERGED. Actual fetched main/base: `c9dea4e1fb728c97c3c14e70ae75adab6e6cfc94`. Branch `codex/cc03-intel-readonly-preflight`; final PR/head and tested checkout recorded below after CI. Only `ControlCenter/` changes; existing workflow unchanged, GitHub-hosted windows-2022 only. No protected production/research code changes or Intel access.

Protected Git tree IDs at actual base (must match final head):

| Tree | Before | After |
| --- | --- | --- |
| TradingSystemLab | `d27ac7153a4d25455112c1a6673d2b37a1784f43` | pending final tree check |
| IntradayLab | `9b71aeff75c49d3fc7b2fff7116b21d03fee5783` | pending final tree check |

Read actual `TradingSystemLab/CURRENT_STATE.md`: latest documented installed executable `3a18c8c24301c866a60f5d725de227288d48f7ec`, T3/H1/TRAIL1, `TRAIL1__N4_01__FULL__R15`, RUNNING / ARMED generation 62, separate operator trading authorization and independent physical READONLY PASS. Historical operator checkpoint only. Current Intel state is not observed or guaranteed by this preparation. Disabled/HALTED is not a prerequisite; never arrange it for CC.

## Package and checksums

Standalone operator entrypoint `observer/intel_preflight.py`, fixed READONLY `Read-OsFacts.ps1` and own-root/SID `Read-PreflightReadiness.ps1`. No UI invocation, publisher, broker client, production file/metadata interface or installation in preflight. Private templates: preflight approval A, OS source and receiver approval C. Templates remain unapproved with absent bindings; no actual SID/PID/account hash/TTL is supplied.

`deployment/manifest.json` lists SHA-256 for every shipped package file except itself, caches/environments and active runtime policies. Verify `python deployment/manifest.py --check` from the authenticated review copy. Exact source digests, manifest digest and native results are recorded below. A checksum is integrity evidence; authenticate revision/manifest through review. No active private policy or real Intel report is committed.

## Exact commands

Use existing Python 3.12 x64 from an already authorized standalone review copy, cwd its `ControlCenter` root; never the robot checkout. No venv/pip/installer command belongs to A.

```powershell
python -m observer.intel_preflight
```

Default PREVIEW prints planned checks, permissions, forbidden actions and possible classifications. It does not query token, policy, Task, processes, robot files, CC roots or broker.

Future limited EXECUTE, **only after separate operator permission A** and independently verified protected `deployment/preflight-policy.json` in the existing approved review copy, under its existing standard observer token:

```powershell
python -m observer.intel_preflight --execute
```

No path/Task/PID/command override flags exist. It emits one sanitized JSON report to stdout and exit 0 only for a matched unchanged Task bracket. Explicit private evidence capture, if wanted, uses an already authorized sink. The script writes no report/export. Policy secure read is bounded 2 seconds plus worker cleanup; readiness <=6 seconds; at most three exact Task/process subprocesses <=6 seconds each, no polling/retry loop.

## Data obtained and independent results

Own SID/non-elevated standard token agreement; exact full Task XML UTF-8 SHA-256 and translated principal comparison, actual sampled Task state, before/after agreement; optional pre-approved PID creation/image/command/owner comparison; actual access under that token. Only fixed own CC directory attributes/existing SID translation; missing objects stay NOT_PROVISIONED, no provisioning. CC ACL remains NOT_VERIFIED until independent effective-rights review.

Report separately records TASK_IDENTITY_MATCHED, TASK_RUNNING_OBSERVED, PROCESS_IDENTITY_MATCHED, PROCESS_UNKNOWN, ACCESS_DENIED, CC_IDENTITIES_NOT_PROVISIONED, OS_SOURCE_APPROVAL_REQUIRED and UNKNOWN. Missing/restarted PID/wrong epoch/denied identity never triggers discovery or rebinding. Matching XML/command does not attest executable contents or installed checkout. Before/after agreement is discrete observation, not proof of uninterrupted identity/state.

ROBOT_HEALTHY, BROKER_CONNECTED, TRADING_AUTHORIZED, POSITION_FLAT, STOP_PROTECTED, positions/orders/fills/SLTP/capital/PnL stay UNKNOWN. No kill-switch/heartbeat JSON, production git/hash, SQLite/WAL, secrets, environment or token content is opened. No FINAM or Task mutation operation is present. Missing process permission does not justify H1 ACL or administrator grants.

## Intel-only checks and outcomes

Intel still requires actual approved standard SID, Task XML/principal evidence, optional independent worker-to-PID/epoch binding, existing read grants, actual bracket, existing CC provisioning and separate effective SID/ACL review. These have not run here. Task-only A can PASS with PROCESS_UNKNOWN and missing CC roots; this never approves C.

| Outcome | Meaning |
| --- | --- |
| PASS | Standard observer matched and exact Task identity/state unchanged across bracket; Running is allowed. Independent process/provisioning UNKNOWN remains visible |
| BLOCKED | Invalid token, unreadable/mismatched/drifting Task, insufficient standard-token proof; no repair or mutation |
| NOT_VERIFIED | PREVIEW, unsupported platform, absent/unapproved/inaccessible protected policy, or unexpected observation error |

Package READY requires native hosted tests of new boundaries and complete ControlCenter/manifest CI. Fixable test/code defects → NEEDS_FIX. Proven inability to perform safe targeted OS reads within existing authority → BLOCKED. Hosted success is not physical PASS; actual Intel permissions may still block A.

## Separate next decisions and cancellation

**A** limited READONLY preflight only. **B** own CC installation/accounts/roots/panel only after another decision. **C** OS source approval and first real export only after another decision with binding/TTL/ACL evidence. See [physical plan](CC03_PHYSICAL_ACCEPTANCE_PLAN.md), [policies](CC03_INTEL_PREFLIGHT_POLICIES.md), [installation](CC03_INTEL_INSTALLATION_PLAN.md). No merged approval.

A cancellation: stop only its own console/preflight, retain sanitized evidence. No server changes to roll back. B cancellation: stop only known own CC consoles and separately approved manifest/marker-bound CC uninstall; no H1 Task/process/ARM/SQLite actions. C cancellation: stop only own exporter, leave source UNKNOWN/STALE, preserve evidence; no production ACL repair. STOP after Draft PR/checks/report, no merge/auto-merge/Intel execution/panel/real export/CC-04.

## Actual verification record

Pending native hosted run and final protected-tree verification.
