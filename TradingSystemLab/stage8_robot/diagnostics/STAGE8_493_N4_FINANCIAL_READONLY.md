# Stage 8 / Draft PR #493 — FINAM N4 financial READONLY checkpoint

**2026-10-13. Status: OFFLINE_CANDIDATE_PASS / PHYSICAL_INTEL_GET_PENDING / NO_REAL_ORDER_AUTHORITY.**

This is an existing Stage 8 acceptance preparation item, not a research phase. Do not merge, deploy, change the active production checkout, enable/start Task, rearm HALTED, modify LIVE SQLite, obtain a trading token or submit orders. Frozen T3/H1/TRAIL1, TRAIL1__N4_01__FULL__R15, N4 and FULL/R15 risk remain unchanged. Accepted LIVE checkout: 184e8c2b8fa092a606249ff293a4f507160bff29.

## Exact candidate files

| File | SHA-256 / identity |
| --- | --- |
| stage8_493_n4_financial_readonly.py | CF366762E7CB4B75EB25317E890FD59D6F5F4FB88299B85FBE1904FEB3D16F2B, Git blob 608bf691f3ce1748d8a4d42299475f3130ca5151 |
| stage8-493-n4-financial-readonly.ps1 | DB37C177FED0D34FEB502C15BD462C3D915AA161D4ED2825366639912464E168, Git blob 138966f73d401dbf8c026ce51280d8e3f5971378 (corrected source/hash verification) |
| test_stage8_493_n4_financial_readonly.py | Git blob 8ff3706d5199bcb8e12fcb1d2f46375c20f7c70a |

**Local independent synthetic pytest: 16 passed.** Both executable source files and the test file were byte-for-byte matched to these Git blob IDs. Python compiled successfully; PowerShell static forbidden-mutation verb audit PASS. **Operator invoked the original Windows PowerShell wrapper twice, but both attempts stopped at the initial hash guard before any financial GET. The corrected wrapper has NOT yet been physically run on Intel; no fresh N4 economics were collected.** None of these tests accessed FINAM or LIVE.

## GET-only and isolation boundary

The new PowerShell diagnostic reuses the already physically PASSed stage8-493-post-isolation-readonly.ps1 with exact pinned SHA-256 37DF9E1A8F4B0B18EE37D1ACC8757AD674160E878264B2746ED0E1BB3E66C201. It requires fresh Task Disabled / process zero / HALTED / free lock / unchanged SQLite READONLY / FINAM double broker-flat evidence before financial queries.

The new Python transport permits POST only to /v1/sessions and /v1/sessions/details for **session authentication**, then GET only of the exactly bound account, account orders, and N4 asset + account-specific asset params. All trading POST, SLTP POST, DELETE/cancel, other-account reads, trading token substitution, and /trades requests are forbidden. Account is authenticated to precisely one REAL_READONLY account identity. All four instruments are bound to the frozen LIVE CSV. Strict double flatness, active order, account identity, parsed N4 step/lot/directional RUB initial margin and financial snapshot consistency are checked.

Private create-only JSON output: c:\tslaudit\fill493\stage8-493-n4-financial-readonly-20261013.json. Only SHA of account is stored; no token/account ID/raw REST payload. It reports broker account equity, unrealized profit, available cash, MC/FORTS variant, N4 FINAM price step, trading quantity lot, contract size, both directional initial margins. **Do not commit this private report to public GitHub.** Preserve its SHA. It is outside LIVE SQLite, repo, production checkout.

**Caveat:** broker-reported equity is *not* the accepted production realized R15 equity. Current production derives realized = equity - unrealized_profit - explained_external_cash_flows with separate persistent authority; explained cash flows were deliberately not read by this tool. FINAM asset GET does **not** certify RUB tick value/commission/tariff. Frozen MOEX RUB tick values are only named **reference** values. Current fee schedule, actual signal entry/stop, spread/slippage, explicit monetary-loss budget, two-contract natural eligibility and physical 1→2 SLTP protection remain blocked. No PASS status in this tool means live-order readiness.

## Intel operator procedure — only new READONLY diagnostic

Transfer just the two new candidate scripts into c:\tradingsystemlab (not the pinned LIVE checkout), using these exact destination filenames:

- stage8_493_n4_financial_readonly.py → c:\tradingsystemlab\stage8-493-n4-financial-readonly.py
- stage8-493-n4-financial-readonly.ps1 → c:\tradingsystemlab\stage8-493-n4-financial-readonly.ps1

Leave the previously verified stage8-493-post-isolation-readonly.ps1, its adjacent Python modules, the Task, HALTED and production checkout untouched. Before running, verify two local hashes against the table with Get-FileHash -Algorithm SHA256.

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "c:\tradingsystemlab\stage8-493-n4-financial-readonly.ps1" -Python "c:\tslaudit\fill493\venv\scripts\python.exe"

Expected if **all** physical GET checks pass:

    FRESH_POST_ISOLATION_READONLY_GATE=PASS
    FINAM_N4_FINANCIAL_GET_READONLY=PASS
    REPORT_SHA256=<sha256>
    CLASSIFICATION=STAGE8_493_N4_FINANCIAL_READONLY_REPORT_CREATED_NOT_TRADE_AUTHORITY
    FEES_REALIZED_R15_AND_TWO_CONTRACT_ELIGIBILITY=NOT_VERIFIED
    NO_REAL_ORDER_AUTHORIZATION=YES

CLASSIFICATION=BLOCKED, malformed/changed account data, parser/import/version failure or missing scratch directory means STOP, independent review; do not bypass, trade, start Task or change tokens. Report uses exclusive create; an approved repeat requires a new filename via -Output within existing external c:\tslaudit\fill493.

## Intel physical false-block and strictly diagnostic correction (2026-10-13)

- Operator verified that the installed financial Python SHA-256 matched `CF366762E7CB4B75EB25317E890FD59D6F5F4FB88299B85FBE1904FEB3D16F2B`, installed previous post-isolation wrapper SHA-256 matched `37DF9E1A8F4B0B18EE37D1ACC8757AD674160E878264B2746ED0E1BB3E66C201`, and the original financial wrapper matched its initial release SHA-256.
- The initial two attempts stopped with `BLOCKED:EXACT_READONLY_SOURCE_HASH_MISMATCH` **before** finance GET. The cause is the **new wrapper's nested array pair iteration**, not evidence of source tampering. No broker financial numbers were collected; no order authority.
- Candidate PS-only correction replaces `foreach ($row in @(@(...), @(...)))` with two explicit, separately pinned `Test-Path` + `Get-FileHash` guards, distinguishable fail codes, and `EXACT_READONLY_SOURCE_HASHES=PASS` on success. It retains all original pinned SHA values, old post-isolation guard, Task/HALTED checks, and no trade permissions.
- New candidate PS SHA-256 `DB37C177FED0D34FEB502C15BD462C3D915AA161D4ED2825366639912464E168`; Git blob `138966f73d401dbf8c026ce51280d8e3f5971378`. Added `test_stage8_493_financial_readonly_wrapper_guard.py`, **3/3 synthetic/static regressions PASS on independent Linux runner** (native PowerShell not available), alongside prior Python 16/16 PASS. This **does not** establish Intel native execution; new version requires operator physical rerun.
- Only candidate diagnosis changed; the immutable production checkout, Task, kill switch, trading credentials, LIVE SQLite and previous proven wrapper remain untouched. Keep any private FINAM report out of public GitHub.

## Roadmap gate

- Previous Intel Task isolation/broker flatness: **PASS at previous observation** only; new wrapper will repeat.
- Python GET-only collector: **16 OFFLINE synthetic tests PASS**, exact Git objects checked.
- Native Windows runner and fresh REAL FINAM N4 funds/margin: **PENDING operator run**.
- Realized R15 basis, current effective client fees, two-contract scenario loss: **NOT VERIFIED**.
- Independently audited, safely recoverable real SLTP acceptance tool: **NOT APPROVED**.
- Real 1→2 same-order fills, dynamic SLTP protection and restart: **NOT RUN**.
- Real order/Task activation/PR merge: **NOT AUTHORIZED**.

**Decision: STAGE8_493_N4_FINANCIAL_READONLY_CANDIDATE_READY_PHYSICAL_GET_PENDING.** Next independent step after physical READONLY report is to evaluate verified values, current client tariff/realized basis and two-contract budget under unchanged FULL/R15; no physical trade follows automatically.
