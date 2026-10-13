# Stage 8 / PR #493 — REAL FINAM SLTP multi-fill acceptance: decision protocol (NOT AUTHORIZED)

**Operator-ready design only. 2026-10-13. Classification: PHYSICAL_ACCEPTANCE_NOT_RUN / REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED.**

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
- Entry reference and stop must be on the authenticated tick grid, stop on the adverse side, quantity **exactly 2** allowed by unchanged FULL/R15 + margin floor rule; two contracts must be naturally eligible, never artificially upsize or change risk. Any result not exactly 2 => **NOT ELIGIBLE**, not a prompt to alter strategy.
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
