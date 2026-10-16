# CC03 Intel READONLY preflight package

**CODE PREPARATION ONLY.** Engineering classification: **`CC03_INTEL_READONLY_PREFLIGHT_PACKAGE_READY`**. Native boundaries are verified on disposable hosted Windows sources; actual Intel remains unverified. Intel execution `NOT_EXECUTED`; physical acceptance `NOT_VERIFIED`. No result here equals CC03_PHYSICAL_PASS.

## GitHub provenance and scope

Repository `alkospacer123/market-pattern-discovery`; continuation of #524, previous #541 MERGED. Actual fetched main/base: `c9dea4e1fb728c97c3c14e70ae75adab6e6cfc94`. Branch `codex/cc03-intel-readonly-preflight`; [Draft PR #542](https://github.com/alkospacer123/market-pattern-discovery/pull/542). Actual GitHub source head observed and accepted by native CI: `ad9a93350f27242801ed81852b65da96a27a3264`; tested GitHub merge-ref checkout `73b4f234e4ea04b09fe4baa1b506510f3657e304`. The final evidence-only commit changes this report/roadmap/manifest and CI evidence packaging, with the same runtime and tests. Its actual head is recorded in the PR metadata/body and companion `CC03_INTEL_PREFLIGHT_CHECKSUMS.json`; it cannot be embedded in a file belonging to that same commit. Final-head CI is available on the PR Checks tab. Only `ControlCenter/` changes; existing workflow unchanged, GitHub-hosted windows-2022 only. No protected production/research code changes or Intel access.

Protected Git tree IDs at actual base (must match final head):

| Tree | Before | After |
| --- | --- | --- |
| TradingSystemLab | `d27ac7153a4d25455112c1a6673d2b37a1784f43` | `d27ac7153a4d25455112c1a6673d2b37a1784f43` |
| IntradayLab | `9b71aeff75c49d3fc7b2fff7116b21d03fee5783` | `9b71aeff75c49d3fc7b2fff7116b21d03fee5783` |

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

Native run [38897646729](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38897646729), job [116961868943](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38897646729/job/116961868943), completed **2026-10-16 12:06:03 UTC / 15:06:03 MSK**, conclusion **success**. Existing unchanged workflow `controlcenter-cc03-windows-native.yml`; GitHub-hosted Windows Server 2022 / 10.0.20348, CPython 3.12.10 x64. Tested ControlCenter tree `10a84cd7c526021866fa9975e16a6cee142158fa`, base/head/merge checkout above.

| Verification | Actual result |
| --- | --- |
| Full ControlCenter pytest on Windows | **400 PASS / 0 FAIL / 15 POSIX-only SKIP** |
| New preflight tests | **25 PASS / 0 FAIL / 0 SKIP** (22 logic/boundary + 3 native) |
| Existing OS observer tests | 37 PASS / 0 FAIL / 0 SKIP |
| Windows reader / immutable transport / source | 44 / 12 / 27 PASS |
| Package manifest / pip check / PowerShell preview | PASS |
| Real two-standard-SID rehearsal | PASS: preflight Running, real Task Access denied, missing own roots, PREVIEW, unapproved EXECUTE refusal under each token |
| Disposable Task XML/state before/after | PASS, including standard SID + panel lifecycle |
| Existing installer/ACL/panel/rollback rehearsal | PASS on disposable VM only |
| Existing synthetic Task/process noninterference | 500/500 unchanged producer replacements, PASS |
| Local full pytest before Windows acceptance | 376 PASS / 38 platform SKIP; final added direct native readiness test is skipped on POSIX and accepted on Windows |
| Protected trees / only-ControlCenter diff / unchanged workflow | PASS at base and accepted source head; repeated for final review commit |

Evidence [artifact 12044224134](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/38897646729/artifacts/12044224134), `cc03-windows-native-38897646729-1`, upload-reported ZIP SHA-256 `18b6b0719e1d02d1b9843542c8c684abcec1170b18255e5c54085dd21b6fd7a3`. Reviewed decoded job log and its environment/results/acceptance records; artifact retention 30 days. The artifact digest is GitHub's upload result, not a claim of independent Intel evidence.

The initial run 38896827307 correctly blocked the standard-token rehearsal at readiness (pytest itself 399 PASS). Readiness's child environment was then aligned with the existing proven Windows OS helper allowlist, and direct native missing-root regression plus both standard-token checks passed. No elevated fallback, rights relaxation or production change was introduced. Earlier failure is excluded from acceptance.

Verified SHA-256 of the accepted runtime/templates (independently recomputed locally; native manifest check PASS):

| Package file | SHA-256 |
| --- | --- |
| `observer/intel_preflight.py` | `df5d36fdf45f2ec6efded7467083436cf20e096b8edc814c9077fc0862c01279` |
| `observer/Read-OsFacts.ps1` | `e747dc8cd787394e0bee0fd27cf8fac506545790d7713ff9a4055d7147e2e1b6` |
| `observer/Read-PreflightReadiness.ps1` | `06b6df0ed8c73d08c293012e31ab4bb6f0b5131624fd3bb65b2ee5b99313e81b` |
| `deployment/preflight-policy.example.json` | `bc9d2eee9fc06c41c0f6a070cd5d79f865c03dbf67595aa5fae61c6d535d5579` |
| `deployment/os-policy.example.json` | `2eb59be707bbfc651f111d40a0bcb8cb6f902dd87e3cbfa841b19a26945b093c` |
| `deployment/receiver-policy.example.json` | `f38e727f08d0ff43849a8aa581f3ecc060e8ff17d22b683b841ccb3eb4beeff6` |

Accepted source-head manifest SHA-256: `b8fe0ccd3aa5880ebb781fe8dee9066e36affe456c9cf40aa40e12052b646d9a`. This source manifest precedes the evidence-only report update. The final package manifest includes the finalized report, so its SHA-256 and the final ZIP digest are in the separate companion checksums record in the final-head Windows artifact and final PR body; no self-referential manifest hash is claimed here. The final-head Windows CI artifact also contains `CC03_INTEL_PREFLIGHT_CHECKSUMS.json` with actual base/head/checkout/tree and SHA-256 of ZIP/manifest. It is generated only after every check passes and the ZIP manifest plus every one of its 97 entries is independently checked against archived bytes; an empty/incomplete ZIP cannot receive READY. Archive construction and validation run first, before the full suite. Files are packaged as raw bytes, preserving the tested manifest independently of Git Windows EOL filters. Final deliverable `CC03_INTEL_READONLY_PREFLIGHT_PACKAGE.zip` contains only the manifest-verified bytes of the final checked-out ControlCenter Git tree, with no private policies, wheels, credentials or Intel evidence.

**STOP. Next separate operator decision: permission A for limited physical Intel READONLY preflight. No Intel execution, B installation, C source approval/export, merge, auto-merge or CC-04 occurred.**
