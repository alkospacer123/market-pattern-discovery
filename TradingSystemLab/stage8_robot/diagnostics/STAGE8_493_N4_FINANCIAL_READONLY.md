# Stage 8 / Draft PR #493 — FINAM N4 financial READONLY checkpoint

**2026-10-13. Latest operator checkpoint: PHYSICAL_INTEL_N4_READONLY_GET_PASS / FINANCIAL_REPORT_CONTENT_NOT_INDEPENDENTLY_AUDITED / NO_REAL_ORDER_AUTHORITY.**

This is an existing Stage 8 acceptance preparation item, not a research phase. Do not merge, deploy, change the active production checkout, enable/start Task, rearm HALTED, modify LIVE SQLite, obtain a trading token or submit orders. Frozen T3/H1/TRAIL1, TRAIL1__N4_01__FULL__R15, N4 and FULL/R15 risk remain unchanged. Accepted LIVE checkout: 184e8c2b8fa092a606249ff293a4f507160bff29.

## Exact candidate files

| File | SHA-256 / identity |
| --- | --- |
| stage8_493_n4_financial_readonly.py | 68B477B929EB09E299A19F15A79E674F6A60ECF1DBB835A365E514BA3CDFB6D5, Git blob ee9a5cb29a8757c9bc6334e0368b92095ba507c8 (FINAM REST boolean and sanitized stage) |
| stage8-493-n4-financial-readonly.ps1 | 25360D4CA523CA03B53783E2DC6896776D92D02216861171407C94FD84434A71, Git blob 27a66143fa354b9a819144ccb57c8b95f4e81867 (safe child blocker + corrected Python pin) |
| test_stage8_493_n4_financial_readonly.py | Git blob 30311bb0b1965466ec2d4d6cda4c1ba88a352fab (REST boolean positive/negative cases and redaction checks) |

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


## Intel physical block after source verification / standalone child phase observability

Operator output 2026-10-13:
`EXACT_READONLY_SOURCE_HASHES=PASS`;
`FRESH_POST_ISOLATION_READONLY_GATE=PASS`;
`CLASSIFICATION=BLOCKED:FINANCIAL_READONLY_COLLECTION_BLOCKED`;
`NO_REAL_ORDER_AUTHORIZATION=YES`.
This confirms exact source hashes and a fresh physically passing isolation check at that observation; it **does not prove current N4 account funds, assets or margin**. The original diagnostic PowerShell wrapper suppressed the Python child reason. The blocked result must not be classified as insufficient cash, bad margin, or fill failure without more evidence.

The current candidate modifies only the two standalone READONLY diagnostic sources and synthetic tests: Python emits fixed uppercase phase labels on unexpected errors without exception contents or account data; PowerShell surfaces only `FINANCIAL_CHILD_CLASSIFICATION=BLOCKED:<SAFE_UPPERCASE_CODE>`, preserving the prior fail-closed exit and all pinned guards. The existing post-isolation verification, production checkout, runtime SQLite, Task, HALTED and trading/order endpoint boundary remain unchanged. Local synthetic success/redaction/negative-path checks PASS; native Windows physical rerun is pending.

**Use the latest SHA-256 values in the table above**, not earlier revisions in the historical log below. Do not publish the external private financial report to GitHub. No real-order authorization or two-contract eligibility results from this diagnostic correction.


## Intel follow-up: official REST boolean correction after physical BLOCKED

Operator's latest actual command returned `EXACT_READONLY_SOURCE_HASHES=PASS`,
`FRESH_POST_ISOLATION_READONLY_GATE=PASS`, and
`FINANCIAL_CHILD_CLASSIFICATION=BLOCKED:ASSET_PARAMS_ACCOUNT_OR_STATUS_INVALID`.
This is **not** evidence of insufficient equity, lack of broker permission, or real SLTP failure.

Independent verification against official FINAM documentation
`https://api.finam.ru/docs/rest/` confirms
`GET /v1/assets/{symbol}/params` sends top-level JSON **boolean**
`"is_tradable": true|false`. The candidate diagnostic incorrectly
expected gRPC-shaped `{"value": true}`. Its candidate-only parser now
accepts **exact** boolean true, **blocks** actual false as
`ASSET_NOT_TRADABLE_FOR_ACCOUNT`, and blocks absent/malformed types
as `ASSET_PARAMS_REST_TRADEABLE_SCHEMA_INVALID`. The
account ID and symbol binding checks stay mandatory.

Independent local offline regression 15 PASS (4 N4 boolean true, 9
false/malformed cases, SHA-pinning and safety guards); the PR Python
test suite was updated with all N4 synthetic data and fail-closed
negative cases. These do not establish actual REST output or physical
broker trading eligibility. The pinned standalone PowerShell diagnostic
hash changed only to follow the new candidate Python SHA. There is no
modification to LIVE, frozen specification, operational authority,
production Task, HALTED, trading credentials, order endpoints, or
production SQLite. No merge.

Next permitted operation: transfer **both** current standalone candidate
files outside production, verify both new SHA-256 values in the current
table and repeat only the same READONLY command. If it blocks again,
record only fixed sanitized classifications; no unsafe fallback.

Decision: `N4_FINANCIAL_READONLY_REST_SCHEMA_FIX_OFFLINE_PASS_PHYSICAL_RERUN_PENDING`.


## 2026-10-13 — FINAM N4 physical READONLY GET: operator-reported PASS

The operator ran the two current SHA-pinned standalone candidate files on Intel and supplied the full sanitized console summary:

- Python SHA-256 `68B477B929EB09E299A19F15A79E674F6A60ECF1DBB835A365E514BA3CDFB6D5` — **MATCH**.
- PowerShell SHA-256 `25360D4CA523CA03B53783E2DC6896776D92D02216861171407C94FD84434A71` — **MATCH**.
- `EXACT_READONLY_SOURCE_HASHES=PASS`; `FRESH_POST_ISOLATION_READONLY_GATE=PASS`.
- `FINAM_N4_FINANCIAL_GET_READONLY=PASS`.
- `REPORT_SHA256=91749F6834D6E1A2837EA16D933F91DBACD46B728143DD463F9AF4FF979C8174`.
- `CLASSIFICATION=STAGE8_493_N4_FINANCIAL_READONLY_REPORT_CREATED_NOT_TRADE_AUTHORITY`.
- `FEES_REALIZED_R15_AND_TWO_CONTRACT_ELIGIBILITY=NOT_VERIFIED`, `NO_REAL_ORDER_AUTHORIZATION=YES`.

The report's **private bytes have not been independently supplied/recomputed** to this reviewer. The successful wrapper confirms its own validated FINAM account+orders GETs and four N4 asset+account-specific parameter GETs with strict REST tradeability booleans, two account/position/order observations and external create-only report; it does not certify complete cash-flow reconciliation, independent client fees, price/stop references, exact two-contract FULL/R15 viability, or real partial-fill SLTP semantics. The reported report digest must be locally recomputed before any later financial calculation. **Never commit or post the private JSON to public GitHub**. If supplying diagnostic extracts, omit account hash, account IDs, tokens and any raw REST fields.

**Next existing roadmap gate:** inspect and verify the local report digest and sanitized N4 cash/margin amounts OFFLINE; separately establish realized-equity authority, effective broker tariff, on-grid reference/initial stop, slippage/gap scenario and explicitly approved loss budget before considering any new real-order permission. Never force 2 contracts or conclude readiness from margin alone. Production Task remains Disabled/HALTED at the last successful isolation gate; no merge, deployment, rearm or order permission.

**Classification: STAGE8_493_PHYSICAL_FINAM_N4_FINANCIAL_GET_PASS_REPORT_BYTES_INDEPENDENT_AUDIT_PENDING.**


## 2026-10-13 — offline operator N4 field inspection with hash validation

The operator ran a standalone local-only reader on the external Intel financial report. Supplied stdout:
`REPORT_SHA256=PASS`, per-instrument N4 price steps match frozen
registry (`0.01,0.001,0.1,0.5`) and the FINAM trade lot equals `1` for all four.
Both LONG and SHORT account-bound initial-margin fields were present and parsed
successfully. The report hash is still
`91749F6834D6E1A2837EA16D933F91DBACD46B728143DD463F9AF4FF979C8174`.
The account-specific margin *amounts* have deliberately NOT been copied into
the public repository; they remain in the external private report and
operator conversation. The inspection did not call the broker.

A mechanical two-contract margin threshold can be computed by multiplying
the per-contract account-specific direction margin by 2; **that is not
permission** to trade exactly 2 contracts. Actual available cash, frozen
R15 realized equity, entry/stop distance and ROUND-TRIP fees must still be
independently checked. Because cash/equity was not included in this operator
snippet, it is explicitly `NOT_VERIFIED`, and because the full private JSON
was not provided the result is local-check evidence rather than an independent
byte-level review of that report.

Next offline step: use a separately hash-pinned, **read-only local file** to
display `account_financials` only: broker equity, unrealized PnL,
available cash, and MC/FORTS portfolio variant. Never print
`account_sha256`, account IDs, tokens or raw broker payloads; never upload
the full private JSON to public GitHub. Production realized equity requires
separate cash-flow reconciliation, which this report does not carry.

**Status:** `N4_ACCOUNT_BOUND_MARGIN_VALUES_OBSERVED_OFFLINE`;
`TWO_CONTRACT_R15_ELIGIBILITY_NOT_PROVEN`;
`FINAM_REAL_SLTP_MULTIFILL_NOT_TESTED`;
`REAL_ORDER_AUTHORIZED=NO`.


## 2026-10-13 — physical offline account financials, cash/margin threshold and next R15 reconciliation

The operator ran the local-only report reader after independent SHA-256 verification:
`REPORT_SHA256=PASS`, `PORTFOLIO_VARIANT=MC`, equity/available cash were
positive and equal, and unrealized PnL was zero. The client-specific numbers
were supplied to the operator review, **not copied to public GitHub**.
`REALIZED_EQUITY_R15=NOT_VERIFIED`, `CLIENT_FEES=NOT_VERIFIED` and
`REAL_ORDER_AUTHORIZED=NO` remain explicit.

Arithmetic comparison to the four previously observed directional GO values:
current available cash is sufficient for **two contracts of any single
frozen N4 symbol/side, taken individually** (at the 2026-10-13 snapshot).
It is NOT sufficient to collateralize two contracts each of all four
symbols simultaneously. This is only a per-instrument collateral threshold
under one-snapshot margin, not production order eligibility; does not
account for other reserved margin, intraday changes, broker fees, any
additional broker constraint, signal eligibility or the frozen 1.5% R15
per-position risk.

Production Stage 8.12 service derives realized equity as **FINAM broker
equity minus unrealized PnL minus persisted explained_external_cash_flows**,
with a separately stored `realized_equity`; raw broker equity alone cannot
be substituted. To close this limited blocker, an **independent local-only,
non-mutating, hash-pinned R15 read** of the existing external report and
`stage8-12-production.sqlite3` is prepared for the operator outside Git:
`stage8-493-r15-basis-readonly.py`; SHA-256
`B21C1B46E56A4CBF7ACE31EF3853D54071BC48921E51B7B1BE536FCEDD448908`.
It is standalone/offline, performs no FINAM request and no SQLite write,
requires the exact report hash, HALTED, frozen production/account identity,
SQLite `mode=ro`/`query_only`, flat local positions and zero unresolved
intents, and demands exact derived-versus-persisted R15 agreement.
Four synthetic local gates were tested: consistent ledger PASS; mismatched
realized equity, ARMED kill switch and altered report each BLOCKED.
**No Windows/Intel physical result is claimed for this utility.**

Even if the R15 basis matches, this does not establish two-contract quantity:
the relevant actual entry/stop, nominal per-contract loss, fees, slippage,
operator cash-loss budget and real 1→2 protective stop evidence remain unproven.
Never submit an order, rearm, merge or start Task based on these observations.

Classification:
`STAGE8_493_N4_MARGIN_CAPACITY_SINGLE_SYMBOL_2_LOTS_OBSERVED_R15_BASIS_UNVERIFIED_NO_TRADE`.


## 2026-10-13 — physical R15 state-key discrepancy, diagnosis only

Operator verified standalone R15 read-only checker SHA-256
`B21C1B46E56A4CBF7ACE31EF3853D54071BC48921E51B7B1BE536FCEDD448908`
and ran it against the existing quiescent Intel runtime. It returned
`CLASSIFICATION=BLOCKED:R15_STATE_KEYS_MISSING` and
`REAL_ORDER_AUTHORIZED=NO`.

The Python checker requires six named production SQLite state keys:
`database_identity`,
`production_service_identity`,
`explained_external_cash_flows`,
`realized_equity`,
`starting_realized_equity` and
`production_positions`. It did not identify which
particular key was absent; it deliberately did not substitute broker
equity or insert any state. The exact frozen production-service code
treats absent starting equity / absent persisted equity differently
during bootstrap versus continued operation: missing keys must be
investigated before any state decision, not silently repaired.

A separate **local-only** key-name inventory was prepared for the Intel
operator, SHA-256
`28EA316089D572C10C9FCEEC9F9D2CF4A646C7D3675C833D3ABE4CB274009199`.
It displays only PRESENT/MISSING for those six known keys after checking
HALTED, SQLite `mode=ro` and `query_only`. No account
data, token, state values, FINAM API, order or SQLite writing. Six
synthetic offline tests PASS; **no physical Intel inventory result yet**.
This standalone script remains outside production; no production
code/config or schema was changed.

Classification: `R15_BASIS_UNVERIFIED_KEY_INVENTORY_PENDING`;
`REAL_ORDER_AUTHORIZED=NO`. The existing PRICE_GRID V2
candidate remains offline PASS / not deployed; broker SLTP dynamic
partial-fill acceptance remains unproven.


## 2026-10-13 — independently reproduced absent-position-key semantics

The Intel operator executed the original SHA-pinned R15 checker and received
`CLASSIFICATION=BLOCKED:R15_STATE_KEYS_MISSING`. A subsequent SHA-pinned,
SQLite `mode=ro`/`query_only` key-name inventory physically returned
`HALTED_IDENTITY=PASS` and `PRODUCTION_SQLITE_MODE_RO_QUERY_ONLY=PASS`.
Of six checked keys, **only `production_positions` was MISSING**. The
other five (`database_identity`, `production_service_identity`,
`explained_external_cash_flows`, `realized_equity`,
`starting_realized_equity`) were PRESENT. No value was changed and no
position/order was created.

Independent code verification against accepted LIVE commit
`184e8c2b8fa092a606249ff293a4f507160bff29` shows that
`ProductionRuntime.open_positions()` uses
`self.store.get("production_positions", {})`. The existing candidate
`stage8_493_isolation_sqlite_readonly.py` likewise uses
`state.get("production_positions", "{}")`. Thus the absent key represents
an allowed empty local state; the **standalone R15 audit script** was
incorrect to demand its presence. This is an overly strict diagnostic,
**not** a production defect and not evidence that broker risk is wrong.

A corrected isolated, standalone READONLY script was prepared outside
production as `stage8-493-r15-basis-readonly-v2.py`, local SHA-256:
`785A85BC2656593F54FB6E62FD092307E3619E175DAA31CC3C0B993C463E9090`.
It retains the five mandatory key requirements and accepts
`production_positions` absent **or** a present, empty JSON object.
Present nonempty/malformed positions, missing required keys, changed
report SHA, ARMED switch or divergent persisted-vs-broker R15 remain
fail-closed. It reads SQLite only via `mode=ro`/`query_only`, makes no
broker call, and cannot repair/insert state. **10/10 offline synthetic
regressions PASS**, including exact no-SQLite-file-mutation checks.
**Intel physical execution of the corrected v2 script is still pending.**

Stage 7 strategy, position sizing, accepted production checkout,
operational Task, HALTED and frozen source code remain unchanged.
No account cash amount or R15 value is promoted into the public repository.

Classification: `R15_DIAGNOSTIC_OPTIONAL_POSITION_KEY_FALSE_BLOCK_RESOLVED_OFFLINE`;
`R15_REALIZED_BASIS_INTEL_V2_VERIFICATION_PENDING`;
`REAL_ORDER_AUTHORIZED=NO`. SLTP 1→2 actual FINAM acceptance and deployment
remain blocked.


## 2026-10-13 — Intel exact R15 local READONLY v2: PASS for snapshot, funding provenance open

The operator provided SHA-256 match for the standalone diagnostic v2
(`785A85BC2656593F54FB6E62FD092307E3619E175DAA31CC3C0B993C463E9090`)
and the actual Intel stdout:
`REPORT_SHA256=PASS`,
`PRODUCTION_SQLITE_QUERY_ONLY=PASS`,
`STATE_IDENTITY_AND_ACCOUNT_HASH=PASS`,
`HALTED_AND_LOCAL_FLAT=PASS`,
`R15_BASIS_CONSISTENCY=PASS_SNAPSHOT_ONLY`,
`TRADE_FEES_STOP_DISTANCE_AND_SLTP=NOT_VERIFIED`,
`REAL_ORDER_AUTHORIZED=NO`.

All five mandatory R15/identity state keys were available, and the
optional absent `production_positions` key correctly represented a
clean empty local state. The broker-account report and persistent
production R15 basis agree exactly according to the accepted LIVE
formula. **This closes the R15 hash/key/schema/snapshot-consistency
blocker only.**

A separate capital-provenance check remains necessary: the operator's
starting-realized-equity snapshot differs materially from the latest
current-realized-equity snapshot while persisted
`explained_external_cash_flows` is zero. The change may reflect later
funding, but the script does not prove the economic origin or whether
the cash-flow accounting is correct for the frozen R15 rule.
Do not automatically relabel all such changes as profit, adjust risk
or write to SQLite. This provenance is **OPEN / NOT VERIFIED**;
private account amounts and transfer details stay outside public GitHub.

Also not established: current on-grid market reference entry and
initial stop, exactly-two-contract risk-constrained sizing (as opposed
to margin-only feasibility), client round-trip fees, slippage/gap
cash-loss budget, genuine FINAM 1→2 partial fills and trigger-time
SLTP protection, independent physical order acceptance and user
authorization. Prior N4 financial reports are snapshot-only and can
become stale. No new FINAM call, trading credential or real order
was used by this R15 local check.

**Checkpoint: `R15_SQLITE_SNAPSHOT_CONSISTENCY_PASS_FUNDING_PROVENANCE_OPEN`;
`FINAM_REAL_SLTP_MULTIFILL_UNVERIFIED`;
`REAL_ORDER_AUTHORIZED=NO`.**



## 2026-10-13 — operator confirms prior funding provenance

The account operator explicitly confirmed that the difference between the
starting and latest account balance was a **deposit**, not trading profit,
and confirmed the latest broker balance. These figures remain in the
private operator evidence and are not published to the public repository.
The earlier provenance classification `FUNDING_SOURCE_NOT_CONFIRMED`
is superseded by `EXTERNAL_FUNDING_SOURCE_OPERATOR_CONFIRMED`.

This **does not** reconcile the frozen LIVE ledger: the operator's
hash-verified R15 read reported persisted
`explained_external_cash_flows=0` while the subsequent deposit had
already been received by the broker account. The accepted production
`ProductionService._realized_basis()` uses
`broker_equity - unrealized_profit - explained_external_cash_flows`.
Consequently recognizing a new external flow in that field would
mathematically change the nominal FULL/R15 risk base and may prevent
two-contract eligibility, even while broker margin remains sufficient.
Alternatively treating funded capital as part of the current risk
capital requires explicit authoritative reconciliation; it cannot be
silently chosen by a diagnostic tool.

**Do not modify SQLite, reset starting equity, relabel the deposit as
trading PnL, or change the frozen formula/sizing/strategy.** An
independently reviewed funding-accounting decision and explicitly
authorized, backup-and-reconcile procedure are prerequisites to any
operational adjustment. The operator's factual confirmation is not
authorization for any production mutation.

**Current gate: `FUNDING_ORIGIN_CONFIRMED_R15_LEDGER_TREATMENT_UNRESOLVED`**;
FINAM real 1→2 stop coverage and explicit real-order authorization remain
blocked. Candidate PR #493 still Draft / not deployed.



## 2026-10-13 — frozen FULL/R15 deposit-scaling regression design

Following operator approval to **continue candidate-only offline engineering**,
the accepted LIVE source (`184e8c2b8fa092a606249ff293a4f507160bff29`)
and the candidate source were compared for financial behavior:

- On every snapshot, the unchanged production method computes
  `broker_equity - unrealized_profit - explained_external_cash_flows`
  and stores the resulting risk basis in production state. Only a new
  entry uses the latest basis, with frozen `0.015` risk fraction and
  current available broker cash plus directional margin; existing
  positions are **not pyramided or rescaled** on funding alone.
- With the currently observed external-flow field at **zero**, an
  increase in FINAM equity due to funding is included in the risk basis
  on the next healthy service snapshot and scales a future eligible
  entry automatically (subject to stop loss per contract, full lots,
  broker GO, session and authorization).
- If a deposit is instead added to the exact
  `explained_external_cash_flows` subtraction field, its value is
  **excluded** from the risk base. That is a meaningful operational
  accounting policy decision, not a harmless bookkeeping write.
- The operator confirmed that the earlier capital increase was a
  deposit, not trading profit. The risk basis may correctly include
  funded capital while **trading PnL reporting must not** classify a
  deposit as strategy return. This review does not alter either
  financial state or frozen LIVE methods.

An isolated candidate-only test was added:
`tests/test_stage8_493_funding_auto_sizing_offline.py`. Its inputs are
**fully synthetic**, not client-specific balances. It exercises the
actual `ProductionService._realized_basis`, frozen `risk.size_position`
and `margin.cap_r15_by_margin`, with an in-memory state store and zero
FINAM connectivity. Scenarios: sequential deposits increase risk and
new-entry contract counts, unrealized PnL does not, an explained flow
is subtracted, low risk remains quantity=0, invalid/excessive
subtractions fail closed, and prior position evidence is not resized.
An **independent 7-case arithmetic check PASS** ran in the analysis
environment; the actual new candidate pytest module has **NOT YET
EXECUTED on an exact candidate checkout** and must not be marked PASS
until it does. Do not claim true future cashflow classification from
synthetic tests or presume private FINAM statement verification.

**Decision:** `AUTO_NEW_ENTRY_SIZING_PRESENT_IN_FROZEN_CODE`;
`DEPOSIT_AS_TRADING_PNL_NOT_AUTHORIZED`;
`EXTERNAL_FLOW_POLICY_AND_FEES_STILL_PENDING`.
No modification to runtime SQLite, LIVE process/Task, token, kill
switch, frozen R15/6%, strategy, results, or production code. Next
existing Stage8 #493 acceptance items: confirm deposit risk-accounting
convention without changing frozen sizing, review current client
tariff/slippage budget and prepare independent real FINAM SLTP 1→2
proof under a later, separately authorized controlled acceptance.



## 2026-10-13 — existing production runbook prohibits unattended deposits

Independent audit of actual GitHub main
`TradingSystemLab/stage8_robot/PRODUCTION_RUNBOOK.md` §4.3 establishes
a hard **operational** rule: the currently running/frozen Stage 8.12
service has **no automatic external cash-flow classification** and
operators must **not** deposit or withdraw during LIVE and assume the
robot distinguishes it from trading PnL; any new flow needs a controlled
operator procedure **before new sizing from the changed account**.

This supersedes any possible reading of the previous code audit as
approval of **unattended future deposits**. The code computes a new
risk-capital value from the current broker equity automatically; the
runbook nevertheless rejects unrestricted deposit/withdrawal
automation in the absence of accepted funding attribution. The
historical operator-confirmed deposit and 2026-10-13 R15 snapshot PASS
do not establish a production-grade automatic flow classifier.

**Minimal existing-roadmap decision:** prepare a narrowly scoped
separate READONLY funding reconciliation/statement evidence process
and obtain explicit approval for any production handling of new flows.
Do not invent a new strategy, percentage, phase, setting, DB writer or
risk formula. Until the runbook is updated after a separately approved
production fix, future deposits during LIVE remain
`CONTROLLED_OPERATOR_PROCEDURE_REQUIRED`. No production SQLite
value, Task, checkout, token or broker order was changed in this work.

**Gate remains: `AUTOMATIC_FUNDING_CLASSIFICATION_NOT_IMPLEMENTED` /
`REAL_SLTP_ACCEPTANCE_NOT_PROVEN`.**
