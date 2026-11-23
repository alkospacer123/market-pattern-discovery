# Kimi Code — Windows source workspace, safety gates and operator handoff

**Status (2026-11-23): SOURCE_CHECKOUT_PASS_OPERATOR_OUTPUT / KIMI_EXAMS_NOT_RUN / OFFLINE_EXECUTOR_NOT_READY / LIVE_UNKNOWN.** The operator supplied Windows PowerShell output confirming the checkout and clean source tree. This document is not evidence of Kimi tool access, actual Windows isolation, tests, installed release or LIVE state. Approved source baseline for preparation: `market-pattern-discovery/main@1413273a1a312802a0ced7a06a4eb73f050d2ec3`; always recheck the actual HEAD when work begins.

## 1. Single source and workspace

- Canonical approved **source**: `alkospacer123/market-pattern-discovery` / `main` with commit and blob SHA evidence. `main` is not the production installation.
- **Only designated Kimi Code source checkout on Intel Windows**: `C:\KimiSandbox\market-pattern-discovery` (NTFS). One checked-out repository containing the three logical knowledge projects: `V20_TradingSystem_M15/`, `ControlCenter/`, `TradingResearchLab/`; retain `TradingSystemLab/`, `IntradayLab/`, `audit_only/` as verified dependencies, plus `recovery/`, `.github/` and root instructions. Sparse checkout is acceptable; *missing paths are not evidence that Git history was deleted*.
- Temporary `D:\KimiSandbox\market-pattern-discovery` was removed by the operator; `D:` is external Expansion/exFAT, not the permanent Kimi workspace. Do not recreate it. **Do not treat a removable SSD as a sandbox or use Recovery media for agent experimentation.**
- Production `C:\V20Lab`, `C:\Control Center`, `C:\TradingSystemLab`, `C:\IntradayLab` (and any FINAM/DPAPI/account configuration) are **not** Kimi Code working trees. Do not use `git pull`, package installation, tests, diagnostics or cleanup inside these directories as part of onboarding.
- A folder on `C:` is a **working-copy boundary**, not an OS privilege or execution boundary. With the same Windows account Kimi tools may access other paths unless separately restricted.

## 2. Phase-II permission gates

**Before subscription:** GitHub source/documents verified; Kimi Code authenticated under the same account and `Always Ask` selected, per operator. Kimi OAuth application found, with broad repository scope. OAuth authorization does **not** prove actual Kimi Work/Code tool reads. Windows operator command confirmed `C:` checkout HEAD `1413273a1a312802a0ced7a06a4eb73f050d2ec3`, required files and clean worktree; Kimi Code opening the workspace and all tests remain **NOT TESTED**.

**Stage A — source exam:** Read repository files, inspect Git SHA/history, classify active versus historical and missing artifacts. Do not assume Kimi Chat projects, Work plugins and Code share instructions automatically. Three logical projects have different passports. Kimi Code starts in the sole approved checkout. Kimi GitHub work is on a task branch; require approval for writes, PR, merge.

**Stage B — offline execution exam:** Tests that execute arbitrary project code or install dependencies require a separate, genuinely isolated executor (e.g. approved GitHub-hosted Actions with no broker secrets or a separately configured disposable VM). No initial execution of unreviewed scripts on production Intel, even inside `C:\KimiSandbox`. Capture commands, stdout/stderr, exit codes, versions, source commit and diff. Network/broker operations prohibited for tests. If isolation or data is absent: `BLOCKED`, not `PASS`.

**Stage C — post-exam expansion:** After three-project Chat/Code exams and verified GPT↔Kimi Draft-PR handoff, the operator may separately authorize read-only access to necessary production *non-secret* source/config/diagnostic material for parity checks. Each access needs purpose, path allowlist, mode, evidence and expiry/closure. Production edit, process control, deployment, real FINAM orders/SLTP and ARM/HALT are **not** automatically unlocked by exam success; they need their own reviewed live-operation protocol and explicit operator authorization. The purpose is full agent competence with equivalent safety rules to GPT, not a permanent knowledge restriction.

## 3. GitHub write and review rules

- Kimi OAuth authorization may permit broad repository operations. GitHub `Protect main` ruleset requires PR, CI and disallows force-push/deletion; do not assume that OAuth scope alone enforces safe behavior. Do not bypass rules or auto-merge.
- Use a reviewed separate branch, Draft PR, source/base SHA, diff, test evidence, GPT peer review and operator decision. Any unexpected change to LIVE files/processes is a stop condition.
- Never introduce FINAM tokens, DPAPI exports, account numbers, personal logs, private SQLite or secret environment variables into Git, Kimi attachments, the test executor or handoff.

## 4. Remote control, Computer Use and Browser Extension

- These are **optional future capabilities**, not permanently forbidden or automatically trusted. Retain the plugins; grant specific sessions only when needed. `Always Ask` in Kimi Code does not guarantee identical controls in Kimi Work.
- Remote inspection and Git/source work may be piloted from a phone with explicit approval, recorded scope and ability to stop. No unattended GUI clicks in real FINAM/Control Center sessions, no blind retry of unknown-result commands, no automatic ARM, trade or SLTP modification.
- Before extending remote control to production, separately test authentication, least privilege, audit trail, kill/deny paths, unknown-result fail-closed and an operator confirmation gate.

## 5. Acceptance and subscription decision

Required evidence to declare `C_SOURCE_WORKSPACE_READY`:
1. `C:` is NTFS with adequate free space, working tree physically at `C:\KimiSandbox\market-pattern-discovery`.
2. `git rev-parse HEAD` matches the explicitly pinned commit or a newly approved exact base.
3. `git status --porcelain` is empty, required root instructions, V20, CC, TRL and shared dependencies are present.
4. No scripts, FINAM calls, real tasks or changes to production paths were invoked.
5. Kimi Code `Always Ask` confirmed. For Kimi Work, verify per-action manual approvals **if the installed version supports them**; otherwise leave PC/browser automation ungranted for LIVE. Any Remote Control/Computer Use mode is not silently authorized for LIVE.

**Subscription gate:** Monthly Kimi Pro is a one-month capacity/quality experiment before deciding annual Pro versus annual Max. Subscription may be purchased after preparatory acceptance, **without** conflating payment with sandbox execution permission. Actual GitHub plug-in proof, creation of third Chat project, examinations and isolated runtime tests begin only after payment.

**Evidence/status vocabulary:** `PREPARED` / `SOURCE_READ_PASS` / `OFFLINE_TEST_PASS` / `CHAT_EXAM_PASS` / `CODE_EXAM_PASS` / `HANDOFF_PASS` / `LIVE_UNKNOWN` / `COLD_RESTORE_NOT_TESTED`. Never infer latter stages from earlier ones.

References: [root AGENTS](../../AGENTS.md) · [documentation authority](../DOCUMENTATION_AUTHORITY_2026-11-22.md) · [three project passports](../README.md) · [Kimi exam and handoff](EXAM_AND_HANDOFF.md) · [Roadmap](../../ROADMAP.md).
