> Python base update: see [CC03_PYTHON312_BASE.md](CC03_PYTHON312_BASE.md). B preflight now requires the protected full CC-owned CPython 3.12.10 base/media provenance and offline Wheelhouse; no launcher fallback. All commands below remain subject to separate A/B/C approval.

# CC-03 Intel installation — single `ccpanel` review plan

**CODE/DOCUMENTATION ONLY / NOT_EXECUTED.** Operator decision in [#524](https://github.com/alkospacer123/market-pattern-discovery/issues/524#issuecomment-6241614427) overrides the historical dual-SID model and 2-second UI polling. One standard Windows account `ccpanel` is the **only proposed runtime identity**. Existing `ccobserver` and `ccexporter` are not deleted and not used. None of the actions below was executed on Intel by this PR.

Existing H1 is **LIVE ARMED/RUNNING** (last documented installed commit `3a18c8c24301c866a60f5d725de227288d48f7ec`; this is historical evidence, not a new current physical read). No H1 Task/process/kill-switch/authorization, production files, SQLite/WAL, FINAM, trading token, strategy, risk, account, or configured robot may be touched. No merge, install, live producer or user activation is authorized by this document.

The earlier roadmap decisions remain separate:
- **A — physical OS READONLY preflight:** existing Task/process metadata only from approved standard observer, no provisioning or H1 production file opens. Does not imply B/C.
- **B — package/venv/panel:** one `ccpanel` identity, administrator-owned CC roots/ACL, signed/reviewed package with explicit operator approval; **DEMO/UNKNOWN only** until C.
- **C — real source/receiver:** separate physical acceptance of source, account binding, TTL, noninterference and authority. This single-SID B package **deliberately disables** `Start-Exporter.ps1 -Execute`, so C cannot be inferred from B. No FINAM token/DPAPI secret may be transferred to `ccpanel`.

## Release prerequisites

1. Independently review actual `main` and exact Draft PR head; accept **manual UI (#546)** and this **single-ccpanel** change as one audited future release. They are separate drafts; neither alone should be physically installed. Freeze a merged/adjudicated commit, package manifest and file hashes only after explicit operator merge decision.
2. Windows 2022, Python 3.12 x64. Keep tested offline pinned wheelhouse and hashes outside H1, checked before writing into CC roots. No online dependency installation on Intel. Do not substitute the older 97-file staged package or a different manifest.
3. Prior to B approval, inspect the actual account `ccpanel` (SID, Enabled, standard non-admin token), verify that `ccobserver` and `ccexporter` remain unused/disabled as documented, and independently inspect the existing fixed `C:\Control Center` root. **This PR does not create/enable/alter Windows accounts or ACLs.** If ccpanel is disabled, no valid SID, or no effective read/listen access, B is BLOCKED.
4. Pre-provision empty `app`/`venv` and separate `data` roots **only under a separate B authorization** by the local administrator. Roots owner SYSTEM/Administrators, explicit protected DACL, no reparse/junction/hardlinks, no production grants. `ccpanel` must never own or mutate program/policy or export files.

| `C:\Control Center` subtree | SYSTEM / Administrators | `ccpanel` |
| --- | --- | --- |
| `app` (includes admin-owned receiving policy) | Full | Read/Execute |
| `venv` | Full | Read/Execute |
| `data` parent | Full | Read/Execute |
| `data\export` | Full | Read/Execute **only** |
| `data\logs` | Full | Modify |
| `data\private` | Full | **No access** |

`Common.ps1` checks SID, owner, protected ACL and listed rights, but is only one layer: physical independent **effective token** tests remain mandatory. `receiver-policy.json` must not be created/approved to assert authority until C. Active `os-policy.json`/`source-policy.json` in private are not supported by the single-ccpanel exporter and cannot be read by the panel.

## Operator entrypoints (PREVIEW by default)

The following are *illustrative future commands*, not an execution request. Each PowerShell command is on one lowercase line. From an independently validated ControlCenter package, previews must not write, install, activate or access H1.

```powershell
& '.\deployment\preflight.ps1'
& '.\deployment\install.ps1'
& '.\deployment\start-panel.ps1'
& '.\deployment\start-exporter.ps1'
& '.\deployment\verify.ps1'
& '.\deployment\uninstall.ps1'
```

Only after distinct B authorization, `ccpanel` SID validation, path/ACL review, pinned release and wheelhouse checks, local administrator may perform the existing `Preflight.ps1 -Execute -PanelSid <sid> -Wheelhouse <approved-local-path>` and `Install.ps1 -Execute -PanelSid <sid> -Wheelhouse <approved-local-path>` operations. Preflight is read-only; Install writes only CC-owned app/venv and never creates a Task or launches Streamlit. No installer operation is included in the approval for read-only source A.

On future start, **only** the standard (not elevated) `ccpanel` token may invoke `Start-Panel.ps1 -Execute -PanelSid <sid>` to launch Streamlit at **127.0.0.1:8501**, with CORS/XSRF enabled and no external firewall bind. The elevated but READONLY `Verify.ps1 -Execute -PanelSid <sid>` checks release/ACL/dependencies, exact single loopback listener + owner SID and that unapproved H1 source is UNKNOWN. A displayed Task Running/HEALTHY cannot be invented from a listener or stale file.

**Disabled exporter:** `Start-Exporter.ps1 -Execute` always throws `CC03_SINGLE_CCPANEL_EXPORTER_DISABLED` before touching policy/source. No broker, Task, H1 file, producer, or FINAM read is permitted. Separate C acceptance will need its own reviewed safe external producer; neither app refresh nor the OS-only Task observer is a broker-health source. Known Windows legacy heartbeat `os.replace` interference (`WinError 5`) remains BLOCKED.

## Native acceptance, logs and rollback

- First require **new** GitHub-hosted Windows-native PASS specifically for one actual disposable nonadmin SID: effective read `app/venv/export`, denied write `app/venv/export/data parent`, denied `private`, permitted `logs`, rejected exporter, single owned loopback listener, no outside Task mutations, bounded uninstall preserving `data`. Old **two-SID CI PASS** is not proof.
- Then a distinct Intel physical B authorization and before/after checks must verify only CC-owned changes. PREVIEW is not proof of actual privileges or deployed health. Keep raw SID/path/source evidence private, do not publish Windows credentials/FINAM tokens.
- At first source unknown, leave all broker health, FINAM orders, filled trades, equity, SLTP and H1 position data UNKNOWN. All 10 trading control buttons remain disabled. M15 remains NOT_DEPLOYED.
- Rollback requires stopping **only** the CC panel launched under ccpanel; never kill/restart H1, alter Task or production SQLite. `Uninstall.ps1` requires exact checked own manifest and own venv marker, removes only CC app/venv while preserving CC export/log/private data. On ACL/hash mismatch fail closed.
- Remote access requires later separately approved VPN/tunnel or authenticated HTTPS proxy. Do not bind 0.0.0.0, expose port 8501 publicly, disable XSRF/CORS, or give `ccpanel` administrative permissions.

**Current result of this code-only change:** no Intel install, no active OS/H1 source, no activation and no change to trading runtime. Continue CC-03 only; CC-04 and beyond are not unlocked.
