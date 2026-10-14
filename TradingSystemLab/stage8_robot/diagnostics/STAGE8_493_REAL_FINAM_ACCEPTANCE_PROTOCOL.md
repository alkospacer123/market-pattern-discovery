# Stage 8 / PR #493 — REAL FINAM SLTP multi-fill acceptance: decision protocol (NOT AUTHORIZED)

**Operator-ready design only. 2026-10-13. Classification: PHYSICAL_ACCEPTANCE_NOT_RUN / REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED.**

**ОПЕРАТОРСКОЕ УТОЧНЕНИЕ 14.10.2026 — TEST-ONLY QUANTITY EXCEPTION, СТАРШЕ РАННЕГО ОГРАНИЧЕНИЯ НА NATURAL QUANTITY=2.**

Пользователь отдельно разрешил **ровно 2 контракта CNYRUBF LONG на ОДНУ контролируемую реальную SLTP-приёмку** даже в ситуации, когда замороженный FULL/R15 при справочном входе и стопе выдаёт иное естественное количество (Intel 14.10.2026: reference H1 close=12.541, initial long stop=12.476, reference margin capacity=42, reference FULL/R15 quantity=11).

Это **только тестовая операторская заявка**; объём **не применяется** к действующему роботу, его стратегии, FULL/R15, стопам, конфигурации, результатам, N4 или LIVE SQLite. Раннее условие natural=2 НЕ применяется к этой одной тестовой заявке. Нельзя подгонять/выдумывать стоп, изменять размеры сигналов робота или превращать тест в MICRO cap.

Бюджет оператора **1000 RUB для сценарного планирования**, не гарантирует верхнюю границу гэпа/убытка. До POST необходимы authenticated entry/stop/bid-ask, tick RUB, комиссии/стресс-резерв, контролируемое закрытие, account/Task/HALTED/positions/orders и **отдельное точное разрешение на реальные ENTRY/SLTP/CANCEL/EXIT**. Данное согласие не разрешает orders, merge, deploy, rearm или task mutation.

Existing offline planner `stage8_493_sltp_operator_launcher.py` пока требует natural final R15=2 и **не готов для новой операторской test-only оговорки**: при необходимости изменяется только изолированная ветвь acceptance/gate в #493, НЕ production-код. `FINAM_FILL_AUTHORITY_VERIFIED=False` остаётся до физических доказательств.

This is the next item of the **existing** TradingSystemLab Stage 8 #493 roadmap. It is not a new research stage and cannot change frozen strategy/production. No candidate V2 merge, Task start/enable, rearm, real ENTRY/SLTP/CANCEL/EXIT, token substitution or runtime SQLite write is permitted by approval to *prepare* this plan. A separate, explicit and bounded user authorization is required **after** the READONLY report, risk budget and recovery plan have been reviewed.

## 1. Frozen production identity and physical checkpoint

- Production specification: `PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8`
- Active identity: `TRAIL1__N4_01__FULL__R15`; T3/H1/TRAIL1, N4 `USDRUBF, CNYRUBF, GLDRUBF, IMOEXF`.
- Risk calculation remains R15, **1.5% of current realized equity per new instrument position**, aggregate 6% nominal initial risk, margin/lot downward cap, zero remains zero. No MICRO cap and no changes to signals/stop strategy.
- Accepted and physically pinned LIVE checkout: `184e8c2b8fa092a606249ff293a4f507160bff29`; Stage 5 data `50f1fd2178c18b7ab3bd969be82ad01f47a34745`.
- Last physical Intel state: production Task `TradingSystemLab-Stage8-Production` **Disabled/stopped**, kill switch **HALTED**, old production PIDs absent, production lock free, FINAM two READONLY account/orders snapshots flat. This is timestamped evidence, NOT proof of future flatness. Durable code-bound authorization was **not revoked**.
- Draft PR #493 candidate V2: 158/158 offline tests PASS on exact detached commit `dac0cb789c1cf5f7655c01fb9323296a080da98e`, 2026-10-13 Intel. `FINAM_FILL_AUTHORITY_VERIFIED=False` and no real-order authorization; offline tests are not physical FINAM SLTP proof.
- Existing Stage 8.11 controlled-real acceptance is **one-contract**. This plan does not silently replace it with two-contract execution.

## 2. Mandatory READONLY evidence — the NEXT actual operation

**Reuse the already physically executed post-isolation broker probe**, not a new order-capable adapter. Under the normal Intel operator account, first verify its local bytes/SHA and run it while Task remains Disabled/HALTED:

```powershell
Get-FileHash "c:\tradingsystemlab\stage8-493-post-isolation-readonly.ps1" -Algorithm SHA256
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "c:\tradingsystemlab\stage8-493-post-isolation-readonly.ps1" -python "c:\tslaudit\fill493\venv\scripts\python.exe"
```

Expected wrapper SHA-256: `37DF9E1A8F4B0B18EE37D1ACC8757AD674160E878264B2746ED0E1BB3E66C201`. Its read-only broker module SHA-256: `92FC06D2FBA9D5D5062D3A3DC14BB74C8C3EFD32754A07585DC92D5CB7EA7A13`. The already used wrapper validates Task binding/disabled, absence of service processes, free production lock, HALTED identity, SQLite before-and-after and two fresh FINAM account+orders GET snapshots with an account-bound READONLY session (session creation is authentication, not a trade). Expected classification **`POST_ISOLATION_READONLY_PASS_NO_TRADE_AUTHORITY`** plus `POST_ISOLATION_BROKER_FLAT=PASS`. A physical failure, changed account, unexpected position/order, missing credential or any unexpected stdout means **BLOCKED / OPERATOR_REVIEW**, with **no** workaround by starting Task or using a trading token. No secrets or account IDs should be posted to GitHub/chat.

This probe establishes **flatness/isolation only**, not fresh available cash, exchange economics, fills, or stop triggering. Do not treat its PASS as a 2-contract real-order clearance.

## 3. Fresh risk authority — never substitute frozen or asserted numbers

Before a later **separately authorized** trade, obtain fresh, authenticated and timestamped values for the *chosen frozen N4 instrument* and direction:

- FINAM real account binding/status; zero positions and zero active orders (two fresh snapshots). A dormant heartbeat is expected while Task stopped.
- Realized equity, available cash, current directional initial margin, price step, tick value in **RUB**, lot size and expected spread; identify market session and actual bid/ask/stop from current completed/available data. Verify exchange instrument against frozen N4 mapping.
- Entry reference and initial stop must be authenticated, adverse-side and on-grid. **Production FULL/R15** must always size naturally with its unchanged 1.5% realized-equity and margin formula. **For the one specifically permitted isolated CNYRUBF LONG test only**, the operator has explicitly approved fixed test quantity=2 even when the otherwise unmodified production sizing reference is 11. Do not fake a strategy signal, increase quantity beyond 2, shift the stop to make natural quantity=2, or mutate LIVE production. Budget and protective/exit gates still apply; different instruments/volumes require separate consent.
- Record FINAM/exchange/clearing/broker commissions for entry+exit, price slippage/gap stress scenarios and an operator-selected, explicitly acknowledged cash budget **before** orders. Compute conservative *scenario loss*:
  `2 × (abs(entry_reference − initial_stop) / exchange_tick_size × tick_value_RUB + adverse_slippage_ticks × tick_value_RUB) + round_trip_fees_RUB`.
  Nominal initial stop loss **must** be ≤ 1.5% of realized equity, and the scenario loss+fees **must** be within the operator's separately specified acceptance cash budget. This is a *stress estimate*, not a guaranteed maximum: stop execution, gaps and outages can exceed it. Undefined cash budget, stale economics, missing or non-RUB tick authority, nonzero exposure or no trusted margin => **BLOCKED**.
- The existing `stage8_493_sltp_operator_launcher.py` only checks **operator-asserted** values, not fresh broker proof; its `--execute` explicitly refuses. Hardcoded tick values in a planning fixture are **not** verified current exchange authority.

## 4. Mandatory order-linked fill history proof **before considering any live experiment**

FINAM's official `GET /v1/accounts/{account_id}/trades` uses `limit`, `interval.start_time` (inclusive) and `interval.end_time` (exclusive), with timestamped `AccountTrade` entries including order ID, trade ID, price, size, side and symbol. See official documentation `https://api.finam.ru/docs/rest/` and repository-pinned `diagnostics/official_fill_contract.json`. Historical Stage 8.11 records / earlier physical HTTP 400 do **not** establish current read authority; missing query parameters are a plausible historical explanation, not proof. Retrieve a **bounded READONLY historical ledger copy**, verify its SHA and exact order/account/side/symbol/size, and use `run-finam-fill-price-readonly.ps1` only in an isolated diagnostic checkout. Require HTTP200 and the precise historical order-linked fill facts, stable duplicate-free trade identities, complete time window and trace; HTTP400, empty/incomplete fills or mismatch => **HOLD**. Never fabricate a new trade merely to test the endpoint. A historical one-contract fill does not prove the broker's future two-contract stop semantics.

## 5. Future controlled-real acceptance — specification, NOT executable permission

A separately approved **operator-only** acceptance harness must be isolated from Windows Scheduled Task/production runner and the existing live database. It must be reviewed/tested fail-closed and constrained to one pre-authorized N4 symbol and direction, one deliberate market ENTRY of exactly two contracts, one primary `SLTP_QTY_MEASURE_PERCENT=100` stop, no duplicate POST if ACK/result unknown, and no automatic strategy entry or pyramiding. The user must sign off the instrument, direction, test window, observed available cash and margin, planned initial stop, stress/slippage/fees budget, exact operator, abort/recovery and permitted real operations.

The required *observable order of evidence* is:

1. Before POST: exact account/Task/HALTED/flatness/available funds and binding evidence; immutable intent, idempotency key and recovery instructions persisted **outside LIVE SQLite**.
2. ENTRY: one broker POST at most; ACK order ID does not equal fill. If broker position jumps immediately from 0→2, record `INCONCLUSIVE_FOR_PARTIAL_GROWTH` (not a 1→2 PASS).
3. If first partial fill is 1, prove that it belongs to the exact entry (FINAM AccountTrade), and observe the fresh broker position=1.
4. Install one broker protective SLTP at initial stop with 100% of *current position*; observe active broker order by same order/client IDs and validate fields. ACK or local `ACTIVE` alone does not prove coverage.
5. Observe a subsequent **same-entry** fill taking broker position 1→2; *freshly* verify the **same active protective order** continues to identify 100% of current broker position, and independently verify that FINAM **actually protects the second contract**. A GET response echoing `quantity_sl=100` cannot alone prove trigger-time behavior. If proof cannot be obtained without an unsafe trigger, classify `INCONCLUSIVE / OPERATOR_INTERVENTION_REQUIRED`; do not claim PASS.
6. Exit/flatten under the separately authorized recovery procedure, including cancellation/reconciliation of any residual ENTRY or stop only with broker-state proof. Require fresh broker position=0, all active orders=0, unresolved intents=0, no residual exposure, no unknown ACK or pending cancel. Never use a blind duplicate exit or automatically restart the robot.
7. Independently verify final read-only flatness twice and leave Task **Disabled**, switch **HALTED**. Only then close the *acceptance attempt* (which is still distinct from production rollout).

**Emergency branch:** unproven SLTP, stale broker read, missing fill history, two-sided/order mismatch, unexpected quantity, order status uncertainty, network timeout or gap => no second entry/stop/cancel POST without reconciled broker proof. Preserve intent and evidence and use a separately approved supervised emergency flatten/manual FINAM terminal procedure. `HALTED` does not flatten an already open real position; market/operational loss remains possible.

## 6. Current acceptance ledger and final decision

| Gate | Status 2026-10-13 |
| --- | --- |
| V2 1→2 growth/durable restart offline | **PASS, 158 tests** |
| Candidate PR #493 merged/deployed | **NO** |
| Production Task, kill switch | **Disabled / HALTED at last physical gate** |
| Current fresh READONLY flatness | **PENDING repeat** |
| Fresh exact 2-contract N4 funds/margin/costs | **NOT COLLECTED** |
| Historical FINAM AccountTrade GET / order fill matched | **NOT VERIFIED physically** |
| Real 1→2 partial fills and dynamic SLTP coverage | **NOT RUN** |
| Explicit monetary-loss/slippage budget and recovery approval | **NOT RECEIVED** |
| Operator consent for real-order transmission | **NOT RECEIVED** |
| Real production V2 rollout/rearm | **NOT AUTHORIZED** |

**Present status: `STAGE8_493_REAL_ACCEPTANCE_PREPARATION_ONLY` — next permitted action is fresh READONLY broker/Task probe.** No new research phase or strategy/risk modification.

## 2026-10-13 — Additional candidate single-command READONLY wrapper (not needed to change any LIVE component)

Candidate `stage8-493-real-acceptance-readonly-gate.ps1` was created solely to revalidate a physically previously PASSing post-isolation script by **exact local file SHA-256**, require Task Disabled + HALTED, delegate to the exact same READONLY Python/account/orders/SQLite/lock checks, demand five summary PASS markers and re-check Task/HALTED afterward. The wrapper does not itself access trading credentials or any trading/order/cancel endpoint. Its Git object SHA-1: `4118bb3a77217976ea5aae4efeb3850fcb8493a2`; fixed source revision `39c414b41435bdb94be9c9534b29fed323192fb5`. Independent static diff showed no Task enable/disable/stop/start calls, no order/cancel endpoint, no Git checkout change and no rearm. **Windows physical runner validation is PENDING**, so prefer the already proved direct `stage8-493-post-isolation-readonly.ps1` command above to avoid new tooling until needed.

A successful fresh READONLY flat/isolation probe closes **only** the broker flatness precheck. Do not turn the historical `/trades` HTTP 400 conjecture into fill-price authority or assert dynamic stop protection without separate real evidence. A cash-budget proposal and physical real-order approval remain outstanding; the one-contract Stage8.11 real acceptance boundary remains unchanged.

## 2026-10-13 — Intel READONLY post-isolation revalidation physically PASS

**Evidence received from the operator** (console output, not a fresh independent remote session): Local `stage8-493-post-isolation-readonly.ps1` SHA-256 was checked and exactly matched `37DF9E1A8F4B0B18EE37D1ACC8757AD674160E878264B2746ED0E1BB3E66C201`. The operator ran the previously proven direct post-isolation READONLY script, not a new real-order harness, using `c:\\tslaudit\\fill493\\venv\\scripts\\python.exe`. Output:

```text
=== stage8 #493 post-isolation readonly verification ===
NO_TRADING_TOKEN NO_SQLITE_WRITES NO_ORDER_OR_CANCEL NO_TASK_MUTATION NO_REARM
TASK_DISABLED_AND_PROCESS_ZERO=PASS
LOCK_HANDLE_QUIESCENT=PASS
SQLITE_POST_STOP_BEFORE_AFTER=PASS
FINAM_POST_STOP_TWO_SNAPSHOTS=PASS
CLASSIFICATION=POST_ISOLATION_READONLY_PASS_NO_TRADE_AUTHORITY
NO_REAL_ORDER_AUTHORIZATION=YES
```

**Decision:** Section 2 repeat READONLY broker flat/isolation check is **PASS** as observed at this physical checkpoint. The row `Current fresh READONLY flatness: PENDING repeat` in the initial 2026-10-13 table above is superseded by this entry; it is **PASS for this observation only**, not continuous flatness. The narrower additional wrapper `stage8-493-real-acceptance-readonly-gate.ps1` is **not claimed physically run**.

All the separate real-order prerequisites remain unsatisfied: current authenticated N4 2-contract cash/margin/tick/fees/slippage budget, exact live AccountTrade fill authority, broker-proven 1→2 active SLTP coverage on actual trigger, and separately signed explicit real-order permission, emergency flatten and risk budget. **No real trade authorized; no Task restoration/rearm, no candidate PR merge or LIVE checkout change.** Next roadmap step is READONLY historical fill authority and cost/margin evidence preparation, not execution.

## 2026-10-13 — Separate N4 broker finances READONLY candidate prepared (offline only)

The operator approved continued preparation, **not** trading/rearm/merge. Candidate only in Draft PR #493: strict independent GET-only N4 finance collector, hash-pinned Intel PowerShell wrapper and 16 synthetic offline tests. See [STAGE8_493_N4_FINANCIAL_READONLY.md](STAGE8_493_N4_FINANCIAL_READONLY.md).

- New Python SHA-256 CF366762E7CB4B75EB25317E890FD59D6F5F4FB88299B85FBE1904FEB3D16F2B (Git blob 608bf691f3ce1748d8a4d42299475f3130ca5151).
- New PowerShell SHA-256 D46DB28F6437214809B9647CBD4BEC6B12167C6F83FD1AF063ACE25175DBD9D9 (Git blob 412423068758a8554acc2538fe48b30fdfa36d83).
- 16 passed synthetic only; PowerShell static no-mutation check PASS. Native Intel execution **NOT RUN**.
- Uses previously physically passed post-isolation GET-only gate afresh; validates exact REAL_READONLY account identity and double flatness; FINAM session POSTs only for authentication, GET account/orders/assets/params N4; no order/SLTP/cancel/trades endpoints, trading token, live SQLite/Task/checkout writes.
- The create-only output is private under c:\tslaudit\fill493; it will NOT be committed. FINAM available cash, account equity, price-step, lot and LONG/SHORT initial margin are only known after a physical GET. Broker equity is NOT yet accepted realized R15 equity; commissions, stress cash budget, exact two-contract eligibility and real 1→2 dynamic SLTP protection remain NOT VERIFIED.
- **Next:** operator may install only the two hash-verified standalone diagnostic scripts outside LIVE checkout and execute the documented READONLY command. After receiving its sanitized output and privately supplied hashed report, perform independent financial/provenance audit. No real order follows automatically.

Classification: STAGE8_493_N4_FINANCIAL_READONLY_CANDIDATE_READY_PHYSICAL_GET_PENDING / REAL_ORDER_AUTHORIZED=NO / LIVE_PRODUCTION_READY=NO.


## 2026-10-13 — physical FINAM N4 financial READONLY checkpoint (no real-order authority)

After the previously accepted isolation pass and the candidate-only FINAM REST `is_tradable` boolean diagnostic correction, the operator supplied Intel console evidence:
`EXACT_READONLY_SOURCE_HASHES=PASS`,
`FRESH_POST_ISOLATION_READONLY_GATE=PASS`,
`FINAM_N4_FINANCIAL_GET_READONLY=PASS`,
`REPORT_SHA256=91749F6834D6E1A2837EA16D933F91DBACD46B728143DD463F9AF4FF979C8174`,
`CLASSIFICATION=STAGE8_493_N4_FINANCIAL_READONLY_REPORT_CREATED_NOT_TRADE_AUTHORITY`,
`FEES_REALIZED_R15_AND_TWO_CONTRACT_ELIGIBILITY=NOT_VERIFIED`,
`NO_REAL_ORDER_AUTHORIZATION=YES`.

**Update to historical table in §6 above:** current READONLY isolation+FINAM account/N4 margin GET is **PASS on the dated operator observation**, not PENDING/NOT COLLECTED. The full **two-contract eligibility, fees and stress-loss decision remains NOT VERIFIED** because report contents have not been independently examined and accepted realized equity, entry/stop, client tariffs and loss budget remain missing. The private JSON exists outside production at `c:\tslaudit\fill493\stage8-493-n4-financial-readonly-20261013.json`, with the SHA printed above; keep it off public GitHub and exclude account hash/IDs/tokens from excerpts.

There is **no** change to Stage 7 identity, LIVE checkout, production Task Disabled/HALTED authority, the frozen methodology, real SLTP partial-fill acceptance status, Draft PR merge/deployment status, or any order permission. The next step is local **OFFLINE** evidence inspection and economic evaluation, not another physical trade.

**Checkpoint classification: FINAM_N4_READONLY_FINANCIAL_GET_PASS / REAL_ORDER_ACCEPTANCE_STILL_BLOCKED.**


## 2026-10-13 — verified offline N4 margin display; R15 authority still blocked

The operator reported `REPORT_SHA256=PASS` from an offline local
inspection of the previously verified private FINAM report. The four frozen
N4 symbols have validated price steps and `trade_lot_size=1`; their
account-specific directional initial margin values were displayed locally.
Private per-account RUB margin amounts remain outside the public repository.

**This completes only the reported N4 margin-field observation.**
Current broker equity and available cash have not yet been supplied for
independent financial evaluation. Moreover, broker equity is not equivalent
to frozen FULL/R15 realized equity without explained-cash-flow adjustment,
and no entry/initial-stop reference, client-specific round-trip commission,
slippage stress or explicitly approved loss budget is established.

The next operation is an **offline read of the existing external JSON's
whitelisted account_financials**, only after rechecking its exact SHA-256.
Do not call broker, query trading credentials, start Task, rearm, alter
production or attempt a real order. Real 1→2 partial-fill stop coverage is
still unproven and requires separate explicit authorization.

Checkpoint: `N4_MARGIN_OBSERVED_CASH_AND_R15_UNVERIFIED_NO_TRADE_AUTHORITY`.


## 2026-10-13 — offline account-cash observation and two-lot GO-only threshold

The operator's SHA-validated **existing external JSON** was read locally
without new broker calls: portfolio `MC`, nonnegative account unrealized
PnL (observed zero), valid broker equity and available cash. Financial
amounts stay outside public GitHub. Comparing the observed client-specific
N4 directional margin values to that available cash established the narrow
**2 contracts of one N4 instrument fit margin at this snapshot**; two each
across all four simultaneously do not. Neither statement is FULL/R15 trade
authorization.

Next local-only gate: verify the frozen production SQLite's
`explained_external_cash_flows`, persisted `realized_equity`, account hash,
database identity and HALTED state using exact report SHA-256 and SQLite
`mode=ro`+`query_only`. A standalone operator scratch utility was prepared
and four synthetic local negative/positive controls tested; native Intel run
remains pending. Client-specific fees, actual entry/stop loss and approved
slippage/budget, and dynamic real SLTP 1→2 partial fill remain **UNVERIFIED**.
Production Task Disabled/HALTED and zero real-order authorization are preserved.

Checkpoint: `N4_TWO_LOT_MARGIN_CAPACITY_ONLY_PASS_R15_RISK_AND_REAL_SLTP_BLOCKED`.


## 2026-10-13 — actual R15 SQLite key-presence gate blocked

Intel operator's hash-pinned standalone, local-only R15 reader returned `CLASSIFICATION=BLOCKED:R15_STATE_KEYS_MISSING` and `REAL_ORDER_AUTHORIZED=NO`. It did not identify the missing key and did not justify substituting broker equity, creating a new state key, changing production SQLite, or modifying frozen FULL/R15. See `STAGE8_493_N4_FINANCIAL_READONLY.md` for the six-key allowlist and the isolated, read-only key-name inventory prepared for the next Intel observation.

**Gate result:** Broker cash and directional N4 margin observations PASS at their timestamp; realized R15 basis still **UNVERIFIED / BLOCKED**, client commissions and actual entry/stop economics unverified, real SLTP 1→2 dynamic coverage unverified. Production remains Task Disabled / HALTED at last physical acceptance, and no merge, real order, deploy, rearm or restoration is authorized.


## 2026-10-13 — R15 key inventory confirms an optional empty position key

The Intel operator's independent SHA-pinned SQLite `mode=ro`/
`query_only` inventory returned all five necessary R15/identity state
keys `PRESENT` and the sole missing key `production_positions`.
Frozen LIVE `ProductionRuntime.open_positions()` explicitly reads
`get("production_positions", {})`, so the initial strict diagnostic's
`R15_STATE_KEYS_MISSING` is a **false block for absent empty-position
state**, not authorization to create a key or alter LIVE.

An isolated R15 read-only v2 checker was prepared outside production:
SHA-256 `785A85BC2656593F54FB6E62FD092307E3619E175DAA31CC3C0B993C463E9090`;
10 synthetic tests PASS. It tolerates only the exact optional
empty-position case and retains all R15/identity/account,
HALTED, report-hash and no-writes gates. Physical Intel v2 check pending.

**No R15 economic approval is implied** until the exact independent
derived-vs-persisted R15 comparison succeeds. The client fee/slippage,
stop entry reference, real 1→2 partial-fill protection and separate
real-order authorization remain blocked. No candidate merge, Task
restart, trading, rearm or production mutation.


## 2026-10-13 — Intel R15 snapshot PASS, remaining capital provenance gate

The operator completed the standalone hash-pinned R15 v2 READONLY
comparison with `REPORT_SHA256=PASS`,
`PRODUCTION_SQLITE_QUERY_ONLY=PASS`,
`STATE_IDENTITY_AND_ACCOUNT_HASH=PASS`,
`HALTED_AND_LOCAL_FLAT=PASS` and
`R15_BASIS_CONSISTENCY=PASS_SNAPSHOT_ONLY`.
The previous missing optional `production_positions` key is not a
production defect; the accepted LIVE runtime explicitly defaults it
to an empty dict. None of the database content was modified.

**Financial readiness is not yet approved.** The beginning-vs-current
realized-equity difference is material while persisted
`explained_external_cash_flows` is zero. The physical reconciliation
proves snapshot consistency, *not* that a cash transfer was correctly
classified or that the economic R15 authority is fully reconciled.
Any operator ledger/statement review is READONLY and outside Git;
do not infer funding or post private amounts to this public repo.
Do not set a new value in the live SQLite or change frozen risk.

Full client commissions/slippage and a bounded operator cash-loss
budget are not yet accepted. Exact quantity 2 must follow naturally
from R15+margin (never forced); genuine broker 1→2 partial fills and
trigger-time 100%-SLTP coverage are not proven. No production rearm,
Task enable/start, real orders, candidate merge or deployment
are authorized.

**Classification: `STAGE8_493_R15_SNAPSHOT_PASS_EXTERNAL_FLOW_PROVENANCE_PENDING_REAL_SLTP_NOT_RUN`.**



## 2026-10-13 — operator funding confirmation and R15 accounting hold

The operator confirmed that the previously unexplained account balance
increase was an **external deposit** and verified the current broker
balance. Do not publish the personal amount or account data to GitHub.
This closes the *origin-identification* question but not the R15 ledger
accounting gate: physically inspected production SQLite still reported
`explained_external_cash_flows=0`. The frozen live service calculates
`realized_equity = broker_equity - unrealized_profit -
explained_external_cash_flows`, so recording the confirmed deposit as
an external flow would materially change R15 risk capacity compared to
the current persisted basis. No automatic deposit adjustment or
reinterpretation of the frozen FULL/R15 formula is permitted.

Before physical multi-fill SLTP acceptance or production reactivation,
independently reconcile exact funding dates and scope against the
existing accepted capital-accounting policy and ledger evidence, then
obtain explicit approval for any narrowly specified production-state
correction. Preserve a byte-exact backup, broker flatness and HALTED,
and synchronize operational documents *after* any separately authorized
production fix. No script here changes LIVE SQLite, code, risk model,
Task, token, order permission, or kill switch.

Status: `DEPOSIT_CONFIRMED_R15_CAPITAL_ACCOUNTING_HOLD`.
Candidate #493 is not merged or deployed; real FINAM 1→2 SLTP
coverage still NOT VERIFIED, and real orders remain NOT AUTHORIZED.



## 2026-10-13 — deposit behavior verified in source; preserve LIVE hold

Operator explicitly authorized **continued offline preparatory work**,
not unbounded real-order submission, candidate deployment or rearming.
Source audit confirms the existing FULL/R15 **new-entry** sizing reads
the latest broker equity after unrealized PnL and the persisted
external-flow subtraction; it then enforces the existing current GO
and 1.5% per-new-position cap. No production risk algorithm change is
needed merely to make funded capital alter future sizing, provided the
deposit is included in the accepted risk-equity basis. An operator's
cash deposit is **not a strategy gain**.

Candidate-only synthetic regression source added at
`tests/test_stage8_493_funding_auto_sizing_offline.py`;
the actual exact-candidate test run is **PENDING**, although a separate
7-case independent arithmetic crosscheck PASS exists. The accounting
meaning and future handling of `explained_external_cash_flows` remain
an explicit documented decision gate because writing a deposit there
**reduces** risk capital under accepted LIVE math. The operator's
consent to continue does not authorize silently changing that field.
No private money balances were published to GitHub.

Proceed on the **existing roadmap**, not a new methodology:
(1) resolve non-PnL funding classification for R15 and inspect client
fees and stress/stop-risk budget, (2) independently audit the
operator-only physical multi-fill SLTP acceptance/recovery harness and
obtain **specific** order/flatten/cancel authorization for a bounded
test, (3) physical acceptance with final flat/HALTED audit, then (4)
separate merge/rollout/rearm authorization and current-state/roadmap/
runbook/passport/checklist synchronization after any production fix.
Full 1→2 broker stop coverage is still NOT PROVEN. No test may force
a two-contract R15 quantity; absent a natural exact-two eligible
signal, the experiment is NOT ELIGIBLE.

**Current gate: `FUNDING_NEW_ENTRY_CODE_SEMANTICS_VERIFIED_OFFLINE_TEST_PENDING_REAL_SLTP_NOT_AUTHORIZED`.**



## 2026-10-13 — runbook §4.3 cashflow hold is operationally binding

Main's accepted production runbook §4.3 explicitly says no
automatic deposit/withdrawal classification currently exists and
that any external flow during LIVE requires a controlled operator
procedure before changed-equity sizing. This is separate from
the already-proven frozen new-entry calculation based on fresh FINAM
equity, and **overrides any casual assumption that new deposits may be
made unattended**.

Do not change `explained_external_cash_flows` or force a particular
new risk basis via a diagnostic script. Before reactivation the
confirmed previous deposit must be handled under the agreed accounting
authority; for future deposits an explicit narrowly reviewed
operator procedure (or separately authorized and verified flow
classifier) is necessary. Current candidate tests only describe
mathematical behavior and do not authorize that procedure.

The next **real SLTP test** remains a different, explicitly
user-authorized broker/order boundary. No order/SLTP/cancel or Task/
kill-switch/production SQLite/merge action is approved in this turn.



## 2026-10-13 — funding behavior regressions added before SLTP approval

The accepted LIVE code already reads fresh broker equity and available
cash and recalculates **new** FULL/R15 entry quantities using the
unchanged 1.5% risk and directional margin/lot floor. Open positions
are not increased automatically upon deposit. The production runtime
does **not** independently identify a new bank deposit: the stored
`explained_external_cash_flows` is subtracted. The operator-confirmed
external deposit remains a factual account event; no adjustment to
SQLite/accounting was authorized and no funding rule is being
silently redefined.

Candidate-only synthetic regression source
`tests/test_stage8_493_funding_auto_sizing_offline.py` has been
added; independent 7-case arithmetic scenarios PASS, while exact
new-module pytest execution on pinned Intel is still PENDING.
Tests neither establish current broker trade eligibility nor prove
future automatic deposit classification, live fill protection,
round-trip commissions or SLTP 1→2 semantics.

Continue only within the existing Stage 8 roadmap: settle funding
capital-accounting policy explicitly, run pinned offline tests,
finish non-order-capable SLTP acceptance/recovery review and money
budget, then seek a **separate bounded real-order authorization**.
No merge/deploy/rearm, Task change or production SQLite modification.


## 2026-10-13 — independent operator-plan exact FULL/R15 sizing gate (candidate only)

Independent comparison to frozen `ProductionRuntime.plan_entry()`, `risk.size_position()`, and `margin.cap_r15_by_margin()` found a narrow operator-plan error: checking only that *two contracts do not exceed* R15/margin lets an asserted two-contract test plan pass when frozen sizing would select more than two. Example, with entirely synthetic CNYRUBF values: realized basis RUB 10,000, reference entry 12.750, stop 12.740, cash RUB 10,000, initial GO RUB 1,000; a two-contract plan loses RUB 20 nominally and fits both limits, but frozen FULL/R15 would produce min(15 R15, 10 margin) = **10 contracts**, not exactly two. No LIVE trade was attempted.

**Candidate-only correction:** standalone order-incapable `diagnostics/stage8_493_sltp_operator_launcher.py` now computes reference R15 and margin quantities with exact `Decimal` floor for frozen N4 lot=1 and rejects unless their minimum is exactly two. The original operator-assertion preconditions remain explicitly unverified; `--execute` still refuses. Added test fixtures for both R15-limited and margin-limited natural two-lot plans, over-capacity negative cases, and cross-checks against the actual frozen `risk.py` and `margin.py`. No frozen engine, production account, order capability, runbook, risk rule, positions, SQLite or LIVE service was changed.

**Verification status on these new commits:** source/diff reviewed; new exact-HEAD pytest **PENDING PHYSICAL INTEL RUN**. Do not claim PASS based on prior 9/9 funding tests, the old operator-plan tests, or 158/158 prior V2 regressions. This correction closes only an **offline plan-consistency gap**, not a physical FINAM SLTP 1→2 acceptance or final cash-loss authority. Any actual same-entry partial fill remains conditional on separately reviewed order/recovery harness, timestamped FINAM evidence and explicit trade authorization. If an initial two-contract order fills 0→2 in one observation, the broker growth proof stays **INCONCLUSIVE**, not PASS.

**Classification:** `OPERATOR_TWO_LOT_REFERENCE_SIZING_FIX_PENDING_PYTEST`; `FINAM_FILL_AUTHORITY_VERIFIED=False`; `REAL_ORDER_AUTHORIZED=NO`; `LIVE_PRODUCTION_READY=NO`.

## 2026-10-13 — physical Intel 26-test operator-plan gate and independent recovery boundary

The operator supplied actual Intel PowerShell output for the exact standalone `stage8-493-sltp-plan-offline-pytest.ps1` with SHA-256
`1ED1B7364FFD5847D385260D871F9E99E5341E7DD08F68168A63BAC1D8D24ADE`.
It fetched a detached worktree pinned to PR commit `30b205d79352ddcc6fd3f848a5dd019a80ded418`, verified exact blobs for both the planner and tests, and ran the whole `test_stage8_493_sltp_operator_launcher.py` module:
**26 PASSED in 0.20s / 0 failed**; Task Disabled before and after; `NO_LIVE_STATE_OR_ORDER_OPERATIONS_IN_SCRIPT=YES`; `LIVE_PRODUCTION_READY=NO`. This is independently evaluated **operator console evidence**, not a second independent remote run, and it does not upgrade the earlier 158-test V2 set to an unfiltered latest-HEAD pass.

Independent source audit of the next operator-execution/recovery boundary:

1. `stage8_493_sltp_operator_launcher.py` **only checks asserted planning fields**; `--execute` rejects. Its fresh market/account, loss/fees, margin and isolation flags are **not broker observations**. The now-corrected natural two-lot R15/margin floor is a synthetic reference check only.
2. The existing `controlled_real_acceptance.py` Stage 8.11 adapter has `MAX_ACCEPTANCE_QUANTITY = 1`, `_payload` refuses quantity other than one, `_reconcile_position` accepts only signed {-1, 0, 1}, and its normal one-contract lifecycle has **no SLTP installation/growth step**. It cannot be reused to test 1→2 by changing only an argument; **do not weaken/change the accepted Stage 8.11 boundary**.
3. Frozen candidate V2 supplies a percentage-of-current-position SLTP payload and read-side validation of a broker-order *description*; neither means real FINAM protection of the second contract at stop triggering. Observed same-entry 0→2 full fill is **INCONCLUSIVE**, not two-stage growth PASS.
4. A future **separate operator-only harness**, not the active runner and not LIVE SQLite, needs independent tests for: one persisted ENTRY intent and one POST only; account-/symbol-/side-bound immutable order/fill identity; actual 0→1 same-order history; install exactly one SLTP; 1→2 same order plus fresh 100% protection observations; fail closed on stale/missing/contradictory evidence, unknown POST, partial resting ENTRY, delayed response, stop/exit race, session close and disconnect; separately permitted broker-state-reconciled cancellation/flatten, double final flat/no-order probe and sticky HALTED final state. Manual broker-terminal recovery is mandatory when safe automated flatten cannot be proven. No second entry to manufacture partial fills.
5. Before any test-day POST, require a fresh readonly flat/account/N4/GO read, confirmed R15 capital-policy basis and natural final quantity=2, actual selected trade stop/tick and conservative monetary loss estimate including fees/slippage, a specific capped operator-approved acceptance budget and permission for **entry, stop, cancel and recovery exit**. No stage-to-stage approval inheritance.
6. The existing accepted LIVE source and account remain out of scope. PR #493 may not be merged, installed or rearmed until physical acceptance and subsequent separately approved controlled release checks.

**Audit decision: `OPERATOR_PLAN_PYTEST_26_PASS`; `TWO_CONTRACT_REAL_EXECUTION_HARNESS_NOT_IMPLEMENTED`; `PHYSICAL_FINAM_SLTP_GROWTH_NOT_VERIFIED`; `LIVE_PRODUCTION_READY=NO`.** No live operations are authorized by this documentation.


## 2026-10-13 — isolated two-lot operator core, transport disconnected

Following explicit permission to continue **preparatory engineering and offline tests**, a separate operator-only core was added under `diagnostics/stage8_493_operator_harness.py` and a new synthetic negative-path module `tests/test_stage8_493_operator_harness.py`. Exact candidate Git blobs respectively `6e409e47ed5afc032278b09156e3bbd2df33e80d` and `f5c0199421c177595167adad1a665c92914c2564`. Only these two new files were added in this engineering task; the frozen Stage7/8.11 execution, risk and strategy modules were not changed.

The new code has a deliberately **disconnected broker Port protocol**. There is **no FinamAPI import, DPAPI loader, CLI `--execute`, real session instantiation, Task operation, production sqlite access, or unattended cancel/flatten capability**. A physical adapter capable of authenticated real-order execution has **not** been implemented or authorized. The core is not a production executable.

Independently prepared and executed in a local Linux offline interpreter, the exact byte-for-byte Git blob copies passed **15 tests, 0 failures** (scope: synthetic fake-port tests only). The cases include: one entry + one 100%-SLTP stop intent, durable journal before each simulated submission, 0→1 then 1→2 same-entry event, no false real coverage proof after a 100% GET echo, immediate 0→2 fill first installs a two-lot 100%-SLTP before classification INCONCLUSIVE, missing order-linked fills, forged broker account, wrong/terminal/wrong-side/50%-SLTP observations, unknown ACK on entry and stop, restart without duplicate POST, pending entry remainder preventing recovery and double-flat evidence. Local source blob hashes were independently compared with remote GitHub exact hashes after commit. The **physical Intel exact-head pytest run is still pending** and must not be claimed PASSED.

Important recovery limitation: the disconnected core returns `MANUAL_BROKER_TERMINAL_RECOVERY_REQUIRED` when stop/exit races or pending entry exposure cannot be safely resolved, rather than submitting a blind market exit or cancelling a protective stop. An operational two-contract, credential-bound, separately reviewed real FINAM operator bridge and its supervised recovery drill remain **not implemented**. The core's injected `Port` must never be bound to a real writable session on the strength of these synthetic tests. The 1→2 second-contract **real stop-trigger behavior is unproven**. Final double flatness is an evidence check, not broker-trigger proof. `FINAM_FILL_AUTHORITY_VERIFIED=False` and LIVE prohibition remain unchanged.

**Next existing-roadmap work:** exact-HEAD isolated Intel offline pytest; independent audit/fail-closed tests of a future real broker adapter and operator-owned recovery, historical GET /trades fill completeness, time-bounded same-account R15/margin/tick and cash budget; only then separately request explicit real-order permission. **No merging PR #493, real orders, LIVE SQLite writes, task restart or rearm.**

**Current: `TWO_LOT_OPERATOR_CORE_SYNTHETIC_15_PASS_LOCAL_ONLY`; `INTEL_PYTEST_PENDING`; `REAL_TRANSPORT_AND_EMERGENCY_BRIDGE_BLOCKED`; `LIVE_PRODUCTION_READY=NO`.**


## 2026-10-13 — Intel operator core physically PASS, narrow double-flat audit correction

The operator provided the Intel SHA-256 and full PowerShell output for the
hash-pinned standalone `stage8-493-operator-core-offline-pytest.ps1`:
SHA-256 `52B4DC9B46D977314DA614E0E2A1A27977EA11BCF737E86945B9687574D31228`.
The script physically fetched PR #493 at exact `198d94b88d75e48881c8c3233e3277f501feb359`,
verified operator core source blob `6e409e47ed5afc032278b09156e3bbd2df33e80d`
and test blob `f5c0199421c177595167adad1a665c92914c2564`.
Intel reported **15 passed in 3.83 seconds**, `PRODUCTION_TASK_DISABLED_AND_HALTED=PASS`,
`PRODUCTION_TASK_STILL_DISABLED=PASS`,
`NO_LIVE_STATE_OR_ORDER_OPERATIONS_IN_SCRIPT=YES`,
`LIVE_PRODUCTION_READY=NO`. These are operator-observed physical offline test results, not broker SLTP evidence.

Follow-on independent review found a **candidate-only final-double-flat false-positive**:
the previous disconnected operator core counted two snapshots with numeric position zero and
no truthy `order.active`, even if the ENTRY ACK was missing, a listed order omitted its
`active` field, the entry still had a nonzero remaining quantity, a known SLTP had
disappeared from the observation, or duplicate order IDs were supplied. Such a response
must never count as reliable terminal recovery evidence.

The isolated core's `final_flat()` now additionally requires an acknowledged immutable
entry intent, a uniquely observed inactive ENTRY with exact integer remaining quantity 0,
any acknowledged stop uniquely observed as inactive, boolean status fields, and two
consecutive full-read observations. Absence/contradiction writes a sticky operator hold,
not a successful recovery classification. Six dedicated synthetic negative tests were added
for missing ACK (before/after uncertain ENTRY POST), nonzero entry remainder, missing
terminal stop, missing active status and duplicate order IDs. This still does **not**
establish actual broker freshness, prove fill/stop semantics, or provide any writable
FINAM adapter. The now-expanded test module has **not** been physically run on Intel at
the latest head; previous 15/15 applies **only** to pinned pre-correction `198d94b8`.

The old one-contract acceptance adapter and entire production/strategy configuration remain
unchanged. The confirmed 47,500 RUB deposit and `explained_external_cash_flows=0`
make R15 capital-flow treatment an **independent blocking operator-policy reconciliation**:
never treat the deposit as strategy profit, silently subtract it from sizing capital,
or edit production SQLite without separate consent and a backup/rollback plan.
The latest reviewed `execution_grid.FINAM_FILL_AUTHORITY_VERIFIED=False` independently
blocks V2 production entries; it must not be toggled by tests or a historical 1-lot fill.

**Classification: `OPERATOR_CORE_INTEL_15_PASS_PRIOR_PIN`;
`FINAL_FLAT_FAIL_CLOSED_FIX_NEW_TESTS_PENDING_INTEL`;
`REAL_FINAM_TWO_CONTRACT_ACCEPTANCE_NOT_AUTHORIZED`;
`LIVE_PRODUCTION_READY=NO`.**


## 2026-10-13 — Intel 21-test terminal recovery PASS and disconnected FINAM evidence mapping

**Physical Intel observation from operator:** the previously delivered
`stage8-493-operator-final-flat-offline-pytest.ps1` SHA-256 matched
`E572DD668EFD19584F53D1A26F81FF0CAF49BC89C1134A1729DD6EB72AF4C5C5`.
The script checked exact PR commit `3b7d6d7874358d66a6c9dbe65bc54763b91feb90`,
new final-flat tests blob `9207c8c878602c46884e347f5baecae778330873`,
operator core blob `96568614634f9f1ee050874def8884293af7e90c`,
and reported **21 passed in 1.94 seconds** with `PRODUCTION_TASK_DISABLED_AND_HALTED=PASS`,
`PRODUCTION_TASK_STILL_DISABLED_AND_HALTED=PASS`,
`NO_LIVE_STATE_OR_ORDER_OPERATIONS_IN_SCRIPT=YES`,
`PHYSICAL_BROKER_SLTP_VERIFIED=NO` and `LIVE_PRODUCTION_READY=NO`.
The previous provisional `FINAL_FLAT_FAIL_CLOSED_FIX_NEW_TESTS_PENDING_INTEL` is superseded
**only for that exact pinned commit** by `FINAL_FLAT_FAIL_CLOSED_INTEL_21_PASS`.
There was no new broker request, real order, merge, runtime write, authorization or task mutation.

**Next roadmap preparation (Draft PR only):** add
`diagnostics/stage8_493_finam_readonly_observation.py` and
`tests/test_stage8_493_finam_readonly_observation.py` as **disconnected, strictly READONLY
REST response normalizers**. They reuse the existing strict
`production_broker_state.position_quantities()/order_views()`, verify account hash,
selected N4 position versus other exposures, full order IDs/remaining
quantities, SLTP percent/price/validity and bounded order-linked
`AccountTrade` identity/price/tick/side/interval/pagination constraints.
New exact Git blobs are `1cacbcf1a05ce1284b2bd239c2244204734b00c3` and
`02946b6777af5ccd8fc9cf7cfd3eb831bb778d80`.
The parsers have **no network client, DPAPI, production DB, FinamAPI import,
API order, cancel, flatten, or ability to authenticate**. Pure response
normalization never establishes freshness, stable broker retention, actual
SLTP trigger-time 2-lot protection, or execution permission.

The new mapping test module and the earlier operator harness must be physically
tested together on a newly pinned Intel detached worktree before this bridge can
be classified as synthetically verified. Its full physical adapter / emergency
recovery wiring is **NOT IMPLEMENTED**, not covertly authorized by READONLY
mapping tests. A future writable bridge must receive a **new specific**
order/flatten/cancel authorization, current client R15/margin/cash-flow
reconciliation, exact selected symbol/direction and monetary budget, a fresh
broker flat gate and operator-supervised recovery with no duplicate POSTs.
A two-contract growth GET echo remains insufficient to certify real SLTP protection.
Previous Stage 8.11 one-contract acceptance cannot be repurposed.

**Status: `INTEL_OPERATOR_CORE_21_PASS_EXACT_HEAD`;
`FINAM_READONLY_RESPONSE_BRIDGE_TESTS_PENDING_INTEL`;
`TWO_CONTRACT_WRITABLE_BRIDGE_NOT_BUILT`;
`PRODUCTION_DISABLED_HALTED`;
`LIVE_PRODUCTION_READY=NO`.**


## 2026-10-13 — Intel 42 PASS and official percent-of-position execution semantics

**Physical offline test from operator:** hash-pinned
`stage8-493-finam-readonly-bridge-offline-pytest.ps1` had observed SHA-256
`7B47D1A7E0DD32CF5FE5FB59D85B61E89D51A56700051B851AB9B1D03A99ABA5`.
It fetched precise candidate `a2bd378c86bc5dc7fca7c24cbb20f06095f8580d`,
verified exact new FINAM READONLY source blob
`1cacbcf1a05ce1284b2bd239c2244204734b00c3`,
its tests blob `02946b6777af5ccd8fc9cf7cfd3eb831bb778d80`,
and prior 21-test operator-core blobs
`96568614634f9f1ee050874def8884293af7e90c` /
`9207c8c878602c46884e347f5baecae778330873`.
Result: **42 passed in 4.39 s, zero failures**. Task remained
Disabled/HALTED throughout. No LIVE files, FINAM session, real order,
cancel, production checkout, token or SQLite was modified. These are
user-supplied Intel console facts, not new actual broker observations.

**Independent source finding on the disputed broker SLTP percentage rule:**
official, exact source
[FinamWeb/finam-trade-api, `orders_service.proto` at
`52c95c8672542c2f89fbee2a4016774e73a0caa4`](https://github.com/FinamWeb/finam-trade-api/blob/52c95c8672542c2f89fbee2a4016774e73a0caa4/proto/grpc/tradeapi/v1/orders/orders_service.proto)
documents `sl_qty_measure`: if `SLTP_QTY_MEASURE_PERCENT`, `quantity_sl`
means 0–100% **of the position at the time of execution** (Russian:
`процент (0–100) от позиции на момент исполнения`). The matching
`SLTPOrder` Swagger definition at the same official commit repeats
this documented meaning. This is authoritative **schema/contract
semantics** supporting intention to dynamically size an active 100%
protective stop after a 1→2 growth. It is NOT physical observation of
the new 2-contract order's triggering, broker-side rule acceptance,
latency, position growth/stop race, price execution or failure behavior.
Do not upgrade `FINAM_FILL_AUTHORITY_VERIFIED=False` or LIVE readiness
on the strength of a documented rule or 100% GET echo alone.

**Independent current GitHub main** at the audit moved to
`d6946056332ce71658a6ca933cefa0740a7570a2` from
`fa188b51fbd27df5a51a43a9742bc772a1c17abd`; verified comparison
shows only `IntradayLab/` changes. The production runbook blob in
main remains `31950f6a82b2c004cec31c450fe59d7774ea5de5`.
No approved TradingSystemLab LIVE code or frozen identity changed.

**Next existing Stage 8 acceptance gates (no extra research phase):**
(a) reconciled `explained_external_cash_flows`/deposit policy for FULL/R15
without altering frozen risk formula; (b) fresh authenticated
account margin/cash/flat/GO and naturally calculated exact two contracts
for a specific N4 price/stop; (c) explicit operator monetary loss/slippage
budget; (d) actual separate operator-only two-contract writable adapter
and independently tested fail-closed recovery with preserved durable
intent and no-repeat POST, broker token isolation, reconciliation and
operator terminal escape route; (e) new, narrowly scoped authorization
for any real entry, protection, cancel, flatten. An actual
0→2 immediate fill remains inconclusive for observing the 1→2 partial
growth sequence and must never generate another entry.
No candidate merge, LIVE deployment, task rearm, kill-switch reset,
or real orders are authorized by these evidence checks.

**Classification:** `INTEL_READONLY_BRIDGE_AND_OPERATOR_CORE_42_PASS`,
`FINAM_PERCENT_AT_EXECUTION_DOCUMENTED`,
`ACTUAL_TWO_CONTRACT_SLTP_NOT_PHYSICALLY_VERIFIED`,
`LIVE_PRODUCTION_READY=NO`.


## 2026-10-13 — approved deposit-inclusive R15 and separate reporting-only funding attribution

The operator has expressly authorized treating prior contributed funds as **FULL/R15 trading capital**, not strategy profit. Verified current accepted service code: \`realized_basis = broker_equity - unrealized_profit - explained_external_cash_flows\`, and \`explained_external_cash_flows\` is subtractive for risk sizing; it was **zero** at the last Intel read. The approved policy **does NOT approve writing the contribution amount to this subtraction field**, changing Stage7/T3/H1/TRAIL1, R15/6%, or modifying any operating SQLite value. Existing broker-equity-derived FULL/R15 automatically includes capital on the next safe approved snapshot while leaving external cash flows unclassified for PnL reporting.

A small, isolated, purely arithmetic \`stage8_493_capital_pnl_readonly.py\` and offline tests were added to separate **net external contributions for reporting** from the frozen **deposit-inclusive risk-capital authority**. It checks exact account hash, production identity, monetary Decimal semantics, contribution dedupe, per-flow origin, zero sizing deduction and a consistent persisted realized basis. It computes contribution-adjusted account change but explicitly refuses any assertion of independently audited trading profit. No private client amounts, reports, credentials or account identifiers are stored in public GitHub. No code path to a FINAM API, SQL write, Task or order endpoint is included.

This is **not** an automated future deposit classifier. Section 4.3 of main \`PRODUCTION_RUNBOOK.md\` continues to require an operator-controlled deposit/withdrawal procedure before unsupervised LIVE sizing. A financial statement audit with true transaction dates/fees/funding remains separate from the risk sizing equation. For the controlled real two-contract SLTP acceptance, independent physical account funds/GO, exact natural quantity=2, explicit monetary loss/stress allowance, operator recovery and separate order authorization are still missing.

**Current gate:** \`CAPITAL_POLICY_APPROVED_CANDIDATE_ONLY\` / \`SEPARATE_REPORTING_PYTEST_PENDING\` / \`PRODUCTION_SQLITE_UNCHANGED\` / \`REAL_ORDER_AUTHORIZED=NO\`.


## 2026-10-14 — bounded two-contract CNYRUBF LONG acceptance exception (candidate only)

The operator has approved precisely **one** separate, controlled REAL SLTP
acceptance scenario for **CNYRUBF@RTSX LONG, quantity 2**, with a **1000 RUB
scenario-loss-and-cost budget**. This is an exception to the acceptance
quantity only, **not** a change of the frozen production strategy, N4, FULL/R15,
risk sizing, stop logic, operational authorization or Intel checkout.

In this same PR the isolated **order-incapable** two-contract planning launcher
no longer requires `natural_FULL_R15_quantity == 2`. It still requires
2-lot margin/cash coverage, stop below entry on the 0.001 tick grid and
`2 * stop_ticks * 1 RUB + estimated_roundtrip_costs <= 1000 RUB`.
Natural R15 and margin quantities remain **reference-only** outputs.
The separate one-attempt write policy is likewise scoped only to CNYRUBF LONG,
2 contracts, the 1000 RUB scenario including explicit per-contract adverse
slippage allowance and fees, bounded action IDs and independent fresh physical
account/margin/budget/recovery and operator-approval callbacks. None of these
operator-asserted values alone proves the current broker price or commissions.

**Physical gate outstanding within roadmap task 2.2:** new, authenticated
same-account FINAM executable reference price/spread, stop price, current
long-side 2-lot GO/free cash and applicable tariff + exchange fees, adverse
slippage buffer, broker terminal/manual flatten/cancel readiness, independent
operator-only executable wiring and exact one-shot authorization for
ENTRY/SLTP/CANCEL/EXIT. Test quantity is not blocked by the previous 11-lot
robot reference. The order endpoint remains uninvoked; no LIVE mutation,
production rearm, merge or deployment is authorized by this amendment.


### 2026-10-14 reference illustration for operator decision — NOT a trade ticket

Official public MOEX CNYRUBF instrument page (checked on 2026-10-14):
last displayed trade **12.565**, price tick **0.001**, reference tick value
**1 RUB/contract**, public LONG initial margin **1007.53 RUB** at first
concentration level or **2616.79 RUB** with category, exchange registration
fee **0.58 RUB/contract per transaction**. Thus illustrative LONG two-contract
margin is **2015.06 / 5233.58 RUB**, respectively; both are **not** the
client's real-time FINAM GO or free cash. The quote is publicly delayed,
not a broker-executable ASK or authenticated acceptance price. Source:
https://www.moex.com/ru/derivatives/perpetual-futures/CNYRUBF

A conservative **illustration only** at reference entry 12.565 and rounded
protective stop 12.265 (300 ticks) yields 2 x 300 x 1 = **600 RUB** nominal
initial stop loss. If the independently authenticated worst-case combined
entry/exit slippage allowance is 50 ticks per contract (100 RUB total)
and the independently verified total roundtrip broker/exchange/clearing fee
budget is at most 100 RUB, bounded scenario total = **800 RUB**, within the
operator's **1000 RUB scenario budget**. These 50-tick/100-RUB allowances
are proposed testing ceilings, **not observed FINAM fees/slippage**;
gaps, broker errors and extra costs can exceed them. A different executable
ASK requires a newly computed tick-grid stop, instrument price band check,
scenario and fresh explicit approval receipt: do not blindly reuse 12.265.

For the actual test, obtain fresh authenticated executable ASK/liquidity for
2 contracts, the exact client LONG GO/free cash, applicable client tariff and
round-trip all-in fees, stop acceptance rules and terminal recovery access.
Constrain the approval receipt to that same observed entry reference, verified
stop, quantity 2, adverse slippage/tariff cap, valid 30-minute authorization
window, one-shot durable IDs and current physical gate. Require no active
orders/positions and Task Disabled/HALTED immediately before ENTRY. If the
fresh projection exceeds the fixed 1000 RUB, abort before trading. If an
unexpected fill, partial state, reject, ACK loss or stop race appears, hold
and use separately authorized operator-supervised terminal recovery, not a
blind duplicate POST or concurrent stop cancellation/market flatten.

**Proof boundary:** a direct 0->2 fill with 100%-SLTP ACK/GET echo is not a
real 1->2 growth/stop-trigger test. Do not mark it PASS solely on stop
presence; require the actual accepted physical completion evidence defined
above, including final flatness and zero active orders. A 0->2 fill may need
an independently authorized terminal flatten and be INCONCLUSIVE. This
historical/prior example does not authorize real ENTRY/SLTP/CANCEL/EXIT.


## 2026-10-14 — Intel two-contract FINAM focused READONLY acceptance inputs (operator console)

Operator ran isolated `stage8-493-cny-live-readonly-v2.ps1`; reported
`read_only_source_hash=pass`, `fresh_isolation_and_broker_flat=pass`,
`classification=focused_cny_quote_and_2lot_margin_readonly_pass_not_trade_authority`.
FINAM `CNYRUBF@RTSX` authenticated READONLY observed at
**2026-10-14T12:09:41.823811+00:00**: best ASK **12.548**, worst ASK for
2 contracts **12.548**; client cash **49,969.56 RUB**; current broker
LONG initial margin for 2 contracts **2,371.571998 RUB**; illustrative
300-tick stop **12.248**, nominal initial risk **600 RUB**. External private
report SHA-256: `55317debe381bfc0000d5c725c0a1a5ec2ae7ac1e2577ded2d1ab628629c07da`.
The full private JSON was not independently received; this is verified
**operator console** evidence, not direct account credentials or new server
observations by the reviewer. No order, cancel, Task mutation or LIVE SQLite.

**Task 2.2 checkpoint:** client 2-lot margin/cash and bid/ask depth PASS for
this timestamp only. The quantity exception is independent of natural
production R15 sizing, and 44/44 pinned Intel synthetic tests PASS at
candidate `16b8964ab8a872b365ddb557526bbcefddb50db9`. The
proposed fee/slippage envelope 50 adverse ticks per contract (100 RUB)
plus total roundtrip costs ceiling 100 RUB results in illustrative
**800 RUB** = 600 + 100 + 100, leaving 200 RUB of the approved
**1,000 RUB** scenario budget. These two expense ceilings are **NOT**
verified actual client rates or executable fill limits. It is a scenario
budget, **not a guaranteed loss cap** (price gaps, liquidity and rejects).

The actual client tariff must be confirmed for the accepted tariff plan and
execution channel. FINAM Regulation 26/12 is effective on 2026-10-14;
Regulation 26/13 starts 2026-10-15 and cannot be used as today's authority.
Public web tariff rates cannot prove this private account's effective rate;
MOEX normal trade-registration fees must not be conflated with separate
contract-exercise clearing fees. The independent bounded LIVE operator
launcher and proven supervised emergency EXIT/CANCEL recovery are still
pending; do not claim this snapshot proves SLTP acceptance or real
1-to-2 growth. A future trade requires a new fresh time-bounded price, cash,
margin, state/Task/kill-switch and independently approved exact-action receipt.

**No real ENTRY/SLTP/CANCEL/EXIT authorization, candidate merge, deploy or
rearm was performed. Existing roadmap: finish task 2.2, then task 3.**
