# Stage 8 / Draft PR #493 — independent readiness audit (2026-10-13)

**Decision: PREPARATION_ONLY / REAL_FINAM_SLTP_MULTIFILL_ACCEPTANCE_BLOCKED.**
This is an independent, documentary READONLY evidence audit. It is **not** a physical Intel run, broker order permission, live deployment, or a new roadmap phase. Do not merge PR #493, change production Task/HALTED, use a trading token, send an order, modify LIVE SQLite or production checkout.

## Exact authority and scope

- Main inspected at: `0546e10d9977687a77638d76847b205c99223e16`. This is a GitHub snapshot, not a promise that `main` stays unchanged.
- Draft PR #493 initially reviewed at: `b1a20a45ccf26c2723276960a2eff242f87b7562`; open, draft, unmerged.
- LIVE accepted checkout pinned: `184e8c2b8fa092a606249ff293a4f507160bff29`. Immutable Stage7: T3/H1/TRAIL1 / `TRAIL1__N4_01__FULL__R15`, N4 USDRUBF,CNYRUBF,GLDRUBF,IMOEXF; R15 1.5% of realized equity per new position, max 6% aggregate nominal initial risk, min(R15, margin) rounded down, zero stays zero.
- Operator-reported isolated Intel snapshot: Task Disabled/stopped, HALTED, zero processes and quiescent lock, double READONLY broker/account/orders flat, unchanged SQLite before/after; `POST_ISOLATION_READONLY_PASS_NO_TRADE_AUTHORITY`. This snapshot is time-bounded.
- Intel physical OFFLINE tests: 158 PASS on `dac0cb789c1cf5f7655c01fb9323296a080da98e`. Not an actual partial fill or SLTP trigger.

## Historical order-linked price authority: previously established, limited scope

- Repository evidence: `independent_uploaded_finam_evidence_audit_20261013.json` reports SHA-256 and structural inspection of original supplied JSON artifacts: 20 PASS, zero FAIL, two consistent observations of Attempt 6, exact CNYRUBF price 12.748 for one contract, five historical one-contract fill sets over Attempts 2–6. It is a recorded earlier audit, not an additional `/trades` call in this review.
- Official FINAM contract: GET `/v1/accounts/{account_id}/trades` with `limit`, inclusive `interval.start_time`, exclusive `interval.end_time`; match account/order/symbol/side/trade ID/size/time/price. Historical receipt of HTTP200 and ACK match is evidence for **historical single-contract fills only**.
  https://api.finam.ru/docs/rest/
- A/B agreement and `len(trades)<limit` do **not** independently establish server retention, completeness when rows are missing, or safe future 1→2 growth. `currency=XXX` is a feed label, not RUB valuation. FORTS position average_price may be absent.
- Audit finding: candidate `finam_fill_price_readonly.py` catches `FinamError` and writes an observation report with `history_blocker`; the module's process can still exit 0. Therefore **exit code, REPORT_CREATED and report hash never mean fill PASS**. Human/independent gate must require report `history_http_status=200`, no history_blocker, exact target, FULL_REQUEST_MATCHED, stable unique fills. Correction after checking the actual PR code: generic `FinamAPI.trades(account_id,start=...,end=...,limit=...)` **does forward all three query parameters** when both interval bounds are supplied. The earlier 'ignores arguments' statement was stale. The explicit allowlisted `ReadonlyFillAPI.read_history` remains the established restricted diagnostic path; no code change is needed to the generic helper.

## Official public N4 instrument reference (NOT current client-specific broker funds)

| N4 | Tick price | Tick value RUB | Displayed lot | Public MOEX source |
| --- | ---: | ---: | ---: | --- |
| USDRUBF | 0.01 | 10 | 1000 | https://www.moex.com/ru/derivatives/perpetual-futures/USDRUBF |
| CNYRUBF | 0.001 | 1 | 1000 | https://www.moex.com/ru/derivatives/perpetual-futures/CNYRUBF |
| GLDRUBF | 0.1 | 0.1 | 1 | https://www.moex.com/ru/derivatives/perpetual-futures/GLDRUBF |
| IMOEXF | 0.5 | 5 | 10 | https://www.moex.com/ru/derivatives/perpetual-futures/IMOEXF |

MOEX public parameters agree with frozen reference and `moex_public_tick_crosscheck_20261013.json`. Displayed contract lot is not permission to reinterpret or upsize the existing execution quantity; the live FINAM `trade_lot_size` and broker symbol mapping must be authenticated separately.

MOEX public direction-specific initial GO observed on 2026-10-13: USDRUBF buy 12599.02 / sell 12603.17 RUB per contract (higher category figures 30686.99 / 30697.07); CNYRUBF buy 1004.16 / sell 1004.71 (category 2608.04 / 2609.47); GLDRUBF buy 1245.76 / sell 1246.78 (category 3145.88 / 3148.46). Public IMOEXF page last surfaced GO dated **2026-10-08**, buy 2343.18 / sell 2344.46 (category 5976.28 / 5979.55); it is stale relative to this audit. None of these numbers can replace the real client's current directional margin, broker category, free cash and risk capacity, and all can change.

## Brokerage costs and monetary gate

- Published MOEX tariffs: maker/taker distinction for trade registration, instrument-specific exchange transaction fees, and separate clearing/exercise costs. The displayed fee **for exercise** of a perpetual future is not the same as ordinary entry/exit commission and must not be blindly counted for a normal flatten.
  https://www.moex.com/s93
- FINAM's Regulation 26/12 took effect **2026-10-01**; published Regulation 26/13 is scheduled to take effect **2026-10-15**, thus not yet current on audit day. The client's effective tariff, any individual terms, fee minimums, account servicing, exact exchange and clearing charges, and applicable funding/roll cash flows must be determined from current broker/account evidence and authoritative tariff terms, not generic advertised plan rates.
  https://www.finam.ru/publications/item/opublikovan-prikaz-ob-utverzhdenii-reglamenta-brokerskogo-obsluzhivaniya-v-redaktsii-2612-20260916-1755/
  https://www.finam.ru/publications/item/opublikovan-prikaz-ob-utverzhdenii-reglamenta-brokerskogo-obsluzhivaniya-v-redaktsii-2513-20260930-1750/
- **UNOBSERVED CURRENT ACCOUNT INPUTS:** actual REAL_READONLY account status and hash binding at test time; realized equity RUB; portfolio variant and available cash RUB; current chosen-symbol/direction `/v1/assets/{symbol}/params?account_id=...` directional initial margin; authenticated instrument step/RUB tick value and trade lot; actual entry reference + stop; spread; client tariff; round-trip fees; any additional conservative gap/slippage ticks; explicit operator maximum cash-loss-and-cost budget.
- Exact proposed loss (two contracts): `2 * (abs(reference_entry - initial_stop) / exchange_tick * rub_per_tick + adverse_slippage_ticks * rub_per_tick) + round_trip_fees_rub`. Check on-grid, adverse-side stop; reference **nominal** loss <= 1.5% realized equity; *stress* loss+fees <= explicit operator budget; trade-specific margin and frozen FULL/R15 sizing must naturally result in **exactly two**, otherwise NOT_ELIGIBLE. All inputs must be trusted/fresh. This is an estimate, **not a cap on real loss** from gaps, outages, uncovered periods or uncontrolled stop execution.
- C1 research assumptions are not FINAM broker commission authority. No artificial test upsize and no fallback fixed margin/fee/cash values.

## Independent gate decision

| Gate | Decision |
| --- | --- |
| Frozen strategy/risk/identity | PASS; leave unchanged |
| GitHub main / Draft PR status | PASS at read snapshot |
| Operator-reported last Intel Task isolation / broker flatness | PASS at time of reported physical observation; recheck freshness before any authorized action |
| 158 Intel candidate V2 offline durability tests | PASS offline only |
| Historical Attempt 2–6 one-contract fill identity/price | PASS for saved evidence scope |
| Official MOEX N4 tick/step/lot reference | PASS public specification |
| Complete and durable future two-contract /trades fill history | NOT PROVEN |
| Fresh authenticated account margin, free cash, realized equity and exact two-contract R15 eligibility | BLOCKED: NOT COLLECTED |
| Client-specific active FINAM fee schedule and bounded all-in cash/gap/slippage risk | BLOCKED: NOT COLLECTED / NO APPROVED BUDGET |
| Independent audited operator-only real acceptance/recovery harness | BLOCKED: current `stage8_493_sltp_operator_launcher.py` is assertion-only and `--execute` refuses |
| Real broker 1→2 same-order partial fills + 100%-of-current-position protective stop across growth and restart | NOT PROVEN; GET echo of 100% is insufficient |
| Explicit authorization for order/stop/exit/cancel, test window and emergency handling | NOT RECEIVED |
| Candidate V2 merge/deployment/rearm | NOT AUTHORIZED |

**FINAL: `STAGE8_493_READONLY_DOCUMENTARY_AUDIT_COMPLETE_PHYSICAL_ACCEPTANCE_BLOCKED`.** Next work under the existing Stage8 roadmap: prepare/verify an authenticated, timestamped GET-only account+asset-params+fee evidence package on the isolated Intel diagnostic side, independently verify actual monetary R15 eligibility/fees/budget, audit a separate fail-closed order/recovery harness **offline**, then request separate explicit real-order authorization. No physical broker request was made by this GitHub documentary audit. No production files, task, token, SQLite, order endpoints or HALTED setting were modified.

## 2026-10-14 follow-up — final PR #493 audit of real one-shot and release boundary

This section **supersedes the stale 2026-10-13 pending-real-test entries above**
without rewriting their historic evidence. Audit GitHub MAIN:
`d6946056332ce71658a6ca933cefa0740a7570a2`; candidate reviewed:
`83c9fa0a3e2fc5c08ccfceb9ca4d173c843f066f`. PR is DRAFT,
UNMERGED, mergeable CLEAN after bringing MAIN into the candidate.
MAIN and the pinned Intel production checkout remain untouched by this
review; comparison MAIN→candidate finds exactly **98 changed files**
(**91 added / 7 modified**, zero removed; all inside TradingSystemLab).
The original frozen core, strategies, Stage7 production/risk identities,
N4 selection and historical TRUE OOS files are not among the changed paths.
Current MAIN updates to CURRENT_STATE, PROJECT_CONTEXT, production runbook,
passport and operator checklist are preserved in the candidate merge tree.

**Real one-shot 2026-10-14:** operator authorized one isolated CNYRUBF
LONG entry ×2 and a 100%-position SLTP. A durable 8-record external
operator journal proves one entry intent/ACK and one stop intent/ACK;
hashed ENTRY/SLTP order IDs match separate FINAM READONLY order
observations; no duplicate ENTRY is recorded. Two READONLY observations
with exposure +2 established one SLTP `WATCHING`, `SIDE_SELL`,
`quantity_sl=100`, `sl_price=12.23`, correct symbol/validity.
The candidate harness expected string `12.230` and therefore falsely
held on a textual price difference. Current Draft code compares finite,
positive Decimal values and retains all other stop, ID, side and
quantity guards. Operator's exact pinned commit check and **29/29
focused offline tests PASS** on Intel. No new FINAM order was submitted
during the code fix or audit.

Operator manually closed the two contracts, then independently removed
the remaining SLTP, which had persisted active while flat. Final two
FINAM READONLY observations: zero positions / zero active orders,
BUY and SELL regular orders FILLED, SLTP DISABLED;
`DOUBLE_BROKER_FLAT=PASS`. The 8 original journal records remain
immutable and end with operator HOLD; the manual SELL and stop
cancellation were performed outside this harness and are **not
falsely represented as automated recovery or journal entries**.
Operator reports actual BUY 12.533 / SELL 12.516 ×2; conditional
gross at frozen CNYRUBF tick economics is **−34 RUB before fees**,
not an independently reconciled order-linked AccountTrade receipt or
verified net broker charge.

**Current exact executable boundary:** `execution_grid.py` retains
`FINAM_FILL_AUTHORITY_VERIFIED=False`. `live_execution.py` and
`production_service.py` block all candidate-revision ENTRY calls.
`run_from_environment()` without a manifest selects the existing
legacy profile (execution_revision unset); the manifest path is
one-shot `run_preview`, strict READONLY account/orders session,
structurally disconnected from a trading transport. The isolated
V2 migration/rollback rehearsal is therefore **not a deployable
authorized live trading runner**. Flipping the boolean, rearming the
old task or merging Draft files is not evidence of safe V2 activation.

**Remaining constraints within the EXISTING three-task roadmap:**

1. Actual 2026-10-14 BUY/SELL `AccountTrade` prices, size, IDs, fees:
   operator prices are plausible but have not been independently
   matched with bounded FINAM GET /trades. Use a separate GET-only
   diagnostic, no new ENTRY, no manual reprocessing of stale approvals.
2. Natural 1→2 within one ENTRY and actual percent-SLTP growth/trigger
   and restart behavior were **not observed** by direct 0→2. Preserve
   `INCONCLUSIVE`; do not promote an echo, simulation or successful
   direct two-lot stop placement to a physical partial-fill PASS.
   A further real-order test is **not authorized** by this audit.
3. Candidate V2 release wiring is not production-enabled; exact
   approval-bound production order transport, restart/halt handling,
   frozen FULL/R15 sizing, isolated state/cutover and operational
   authority require review under existing tasks 3.1–3.6. These are
   existing release boundaries, not a new phase.
4. The full PR release gate has NOT been rerun on the current merged
   HEAD. Historical 501-case / 57-case module PASS with documented
   baseline exclusions remains historical evidence. The new isolated
   29/29 PASS cannot be called a full release-regression PASS.

**Decision: CANDIDATE_STOP_TEXT_FIX_PASS / MANUAL_RECOVERY_PASS /
STAGE8_493_FINAL_PRODUCTION_RELEASE_NEEDS_FIX.** The factual two-contract
one-shot and durable journal should never be repeated simply to obtain
another sample. No merge, LIVE SQLite/Task/authorization change, rearm,
trading token usage or new order was performed by this audit.

## 2026-10-14 READONLY FINAM AccountTrade closeout (same test, zero new orders)

**This supersedes ONLY the unverified 2026-10-14 entry/exit fill-price
claim above**, not the unresolved future-history/stop-growth release gates.
Operator ran the separately provided
`stage8-493-final-fills-readonly.ps1` on Intel and supplied its sanitized
output; the agent did **not** independently download raw broker trade JSON,
account identifiers, or confidential local report bytes.

- READONLY session exact account binding: PASS.
- Existing flat account / broker order-ID linkage: PASS.
- BUY `order_id` SHA256 prefix `e21fc5a889385f34`:
  one bounded `AccountTrade` row, quantity 2.0, weighted fill price **12.533**.
- SELL `order_id` SHA256 prefix `4aeb70e7f7b93c22`:
  one bounded `AccountTrade` row, quantity 2.0, weighted fill price **12.516**.
- `ACCOUNTTRADE_20261014_LINKAGE=PASS_FOR_RETRIEVED_BOUNDED_HISTORY`.
  The calculation is 2 × (12.516−12.533) / 0.001 × 1 RUB/tick =
  **−34.000 RUB gross before fees**.
- `BROKER_NET_PROFIT_AND_COMMISSIONS=NOT_VERIFIED`;
  `HISTORY_RETENTION_AFTER_RESTART_AND_STOP_TRIGGER=NOT_PROVEN`.
- Wrapper PASS, no broker order/cancel/exit/stop POST, Task/kill switch unchanged,
  no LIVE SQLite writes or alteration of the immutable 8-record journal.

**Updated audit verdict:** `EXISTING_TWO_LOT_BUY_SELL_ACCOUNTTRADE_PASS`,
`ENTRY_SLTP_JOURNAL_IDS_MATCH_BROKER_PASS`, `MANUAL_DOUBLE_FLAT_PASS`,
`STOP_PRICE_DECIMAL_FIX_29_OF_29_PASS`, **candidate live release
`NEEDS_FIX`**. Real natural 1→2 coverage, stop trigger semantics and
restart retention were not established by this single 0→2 trade.
The next work is still release task 3.1: a bounded review of existing V2
readiness and operator approval gates, not another trading experiment.
`FINAM_FILL_AUTHORITY_VERIFIED=False` must remain unchanged until separately
approved physical authority is sufficient. PR is not authorized to merge,
deploy or rearm by this diagnostic.

## 2026-10-14 review — bounded stop-growth fail-closed correction

The official FINAM Trade API schema specifies that
`SLTP_QTY_MEASURE_PERCENT` interprets `quantity_sl=100` as 100% of
the position **at the time of execution**, not at SLTP creation.
Source: https://api.finam.ru/docs/rest/ (POST PlaceSLTPOrder, `sl_qty_measure`).
This is authoritative **contract semantics**, not physical proof of
timing, stop fills, market gaps or races in a natural same-ENTRY 1→2 event.
The real operator trade observed exactly one broker SLTP `WATCHING`
at 100% while holding the immediate full two-contract position.

The independent code review identified a narrow safety issue:
candidate `production_runtime.py` could accept a fresh matching
broker SLTP echo after later position growth and resume normal
management, while its own durable growth evidence explicitly stated
`real_finam_dynamic_coverage_proven=False`.

**Candidate-only corrective decision (not LIVE deployed):** keep the
exact same active SLTP ID, unchanged percent payload, original immutable
stop intent and current observed exposure; persist the fresh account/order
growth observation but **always enter sticky `HALTED` /
`OPERATOR_INTERVENTION_REQUIRED` on growth after SLTP became ACTIVE**.
Do not post another ENTRY/SLTP/EXIT/cancel, infer true stop-trigger
coverage, or resume automatically on restart. If the broker echo is
missing/mismatched, the pre-existing missing-stop HALT still applies.
Growth *before* the initial SLTP submission continues to refresh the
actual position quantity before the one first protection POST.

Focused synthetic tests of matched/mismatched growth, retained stop
ID, sticky HALT, existing V2 no-entry guard and restart are updated in
`test_stage8_493_partial_growth_candidate.py` and
`test_finam_durable_fill_handoff.py`. **Intel execution of these updated
tests remains PENDING**; no PASS is claimed until the pinned GitHub
checkout is independently tested. The 29/29 earlier one-shot harness PASS
remains valid for its unchanged original scope, not for this new fix.

**Release decision stays NEEDS FIX.** This reduces the specific failure
mode without making natural 1→2, stop-trigger or broker fill history
retention PASS. A production V2 entrypoint/commit-bound authorization,
HALTED migration and isolated cutover still require separate release
work and explicit operator authorization under existing tasks 3.1–3.6.
No frozen strategy, N4, FULL/R15, Stage7 identity, LIVE source,
production Task, LIVE SQLite or trading authorization were changed.

## 2026-10-14 — Intel pinned growth HALT regressions 89/89 PASS

**Operator-reported physical Intel OFFLINE result; not a live broker
or deployed-production test.** The exact pinned commit was
`b2f7c18112a01fbe79aa53720e1c466c91426542`.
`stage8-493-growth-halt-offline-tests-v6.ps1` reported:
`LOCAL_PINNED_COMMIT_ONLY_NO_NETWORK=YES`;
`PINNED_TREE_FILE_COUNT=629`; 8 Stage7 provenance files;
`RAW_GIT_BLOBS_VERIFIED=629/629`.
Exact Git blobs for
`production_runtime.py` (`1f6e1d1e43c2a2bffb97a4bedbd0779b92fa6944`),
`test_stage8_493_partial_growth_candidate.py`
(`e58571e8f311cdf20107c463c79b2b495a3f1860`),
and `test_finam_durable_fill_handoff.py`
(`b2758b269475a605b6a1bf29526471a555cfc99f`) all PASS.

**Actual changed-module pytest:** `89 passed in 9.88s`,
`PYTEST_EXIT_CODE=0`;
`RESEARCH_HEAD_UNCHANGED=PASS`,
`CLASSIFICATION=STAGE8_493_PINNED_GROWTH_HALT_REGRESSIONS_PASS`,
`WRAPPER_CLASSIFICATION=PASS`.
The tests include same-ID 100%-SLTP growth, rejection of mismatched/missing
orders, sticky HALT with operator intervention, retention of the existing
backstop, non-resubmission and restart behavior. The test fixtures are
**synthetic**; this is not a physical natural 1→2, actual stop-trigger,
broker retention after real restart, or FULL-PR regression PASS.

**Result update:** the narrow candidate-only stop-growth fail-closed
code fix is `OFFLINE_REGRESSION_PASS` at the pinned commit. The earlier
29/29 stop-price harness test, real 2026-10-14 BUY/SELL bounded
AccountTrade and manual double-flat recovery remain separately
accepted in their stated scope. `FINAM_FILL_AUTHORITY_VERIFIED=False`
and the production V2 entry/activation path remain closed. The
release verdict is **`STAGE8_493_PRODUCTION_RELEASE_NEEDS_FIX`**,
not `LIVE_PRODUCTION_READY`. No additional real order, task action,
SQLite mutation, rollout or rearm is justified by these offline results.
The next work is the existing Stage 8 roadmap task 3.1 release
review/closure, not another partial-fill experiment.

## 2026-10-14 — roadmap 3.1 explicit V2 release-selector audit

**Scope:** only the existing frozen three-task roadmap, currently point 3.1.
Actual GitHub MAIN at inspection was
`d6946056332ce71658a6ca933cefa0740a7570a2`; Draft #493 is not
merged and its earlier pinned 89/89 growth HALT tests remain PASS for
the *unchanged* growth runtime and its two test modules.

**Exact failure identified:** `production_service.run_from_environment()`
normally instantiates `ProductionService` without `execution_revision`
(legacy profile). The manifest-bound `release_candidate_runner.run_preview()`
chooses V2 but is once-only, GET/READONLY and has no order transport.
Neither is proof of continuously running, authorized V2 production.

**Minimal PR-only release-wiring correction:** an explicit
`--execution-revision` option forwards `EXECUTION_REVISION` only when
selected. The legacy/no-flag path is unchanged. The V2 mode immediately
rejects a wrong revision, coexistence with readonly manifest, and any
attempt to start while the compiled
`FINAM_FILL_AUTHORITY_VERIFIED=False`. This refusal occurs before the
service/SQLite/FINAM/Task transport is opened. Even with a hypothetical
future separately accepted fill gate, a pre-existing V2 state database
and exact commit/account production authorization are prerequisites;
the actual runtime validates schema/revision rather than adopting
legacy SQLite. Environment variables alone cannot select V2. The
prior READONLY preview remains separately order-incapable.

Five synthetic tests are added to the existing release-preparation
test module for closed-gate refusal before any broker or SQLite
operation, invalid revision, incompatible preview mode, missing
isolated V2 state/commit-bound authorization, and the explicit
selection vs unchanged legacy default. **These new tests have NOT yet
been run on Intel; no PASS or LIVE readiness is claimed for this
new selector until exact pinned release tests are independently run.**

**Unchanged blockers, no invented new stage:** natural 1→2 and
real stop-trigger/restart retention remain unobserved physically.
Existing fail-closed growth HALT and official percent-at-execution
semantics reduce risk but do not retroactively prove the physical
scenario. The new selector neither turns on the fill gate nor writes
a V2 authorization; a valid commit/account record alone is not
separate operator approval of V2. Physical cutover, fresh broker
flatness and local-intent authority, external state archive and safe
rollback, genuine V2 authorization, any flag rearm and automatic
trading remain confined to the previously documented tasks 3.2–3.6
and require their separate user approvals.

**Current classification:** `STAGE8_493_3_1_V2_SELECTOR_CODE_READY_TESTS_PENDING`;
`LIVE_PRODUCTION_READY=NO`. This candidate-only edit is not a
production deployment or authority change; do not update the LIVE
current-state/runbook/passport/checklist to claim production changed.

## 2026-10-14 — Intel V2 selector exact release-module regression 118/118 PASS

**Evidence supplied by Intel operator, not direct agent access to the
physical Intel host.** The offline v8 launcher executed on a temporary
pinned checkout of `d2dfefe9415c6097476793637ac102fc2b84cbcf`
(the exact candidate source plus two documentation updates after the
closed-selector change). Reported output:

- `PINNED_COMMIT=EXACT_LOCAL_OBJECT_PRESENT_NO_NETWORK`;
  `PINNED_TREE_FILE_COUNT=630`, 8 frozen Stage7 provenance files;
  `RAW_GIT_BLOBS_VERIFIED=630/630`.
- Exact pinned `production_service.py` and
  `tests/test_release_preparation.py` blob checks: PASS.
- Exact root `audit_only/stop_tick_grid_20261012/full_available_raw_signals.csv`
  oracle Git blob `2f6cfbbd941a2a89bfbd9e3d28154dbe9bc7b132`
  included and validated. The earlier v7 outcome (117 PASS,
  one missing-oracle FileNotFoundError) was caused by an incomplete
  temporary archive, not a demonstrated release-code failure.
  The repo CSV, strategy and results were not rewritten.
- `test_release_preparation.py`: **118 passed in 21.45s**;
  `PYTEST_EXIT_CODE=0`,
  `STAGE8_493_PINNED_V2_SELECTOR_RELEASE_TESTS_PASS`,
  `WRAPPER_CLASSIFICATION=PASS`;
  `RESEARCH_HEAD_UNCHANGED=PASS`.
- The launcher had **no** FINAM, token, order, cancel, LIVE SQLite,
  production Task or rearm operations.

**Scope of PASS:** the five added synthetic tests establish that explicit
V2 selection stays blocked before service/SQLite/FINAM initialization
while `FINAM_FILL_AUTHORITY_VERIFIED=False`; wrong revisions and mixing
a V2 trading selector with the READONLY manifest are rejected; state
existence and commit/account authority are mandatory in a synthetic
hypothetical-open-gate test; and the default legacy selector is
unchanged. Existing release-preparation tests also PASS on this pinned
checkout. These results complement the previously accepted **89/89**
growth-HALT and **29/29** normalized SLTP operator-harness tests; counts
must not be combined into an invented single full-suite run.

**Task 3.1 release audit decision:** `V2_SELECTOR_RELEASE_OFFLINE_PASS`
and `STOP_GROWTH_FAIL_CLOSED_OFFLINE_PASS`, but **`LIVE_PRODUCTION_READY=NO`**.
The live compiled fill authority remains FALSE; natural same-ENTRY 1→2,
stop trigger and actual broker history retention after restart are not
proven by these synthetic tests or the immediate 0→2 real one-shot.
No documented acceptance is silently upgraded. The existing isolated
readonly candidate / cutover rehearsal is not an authorized
continuously trading deployed V2 instance. Commit-bound production
authorization, immutable backups, actual Intel cutover, and rearm require
distinct operator decisions within **existing roadmap 3.2–3.6**, never
via these tests. No new phase, backtest or trade experiment is added.

The present candidate can be assessed for **guarded merge review** only;
that is distinct from LIVE authorization. This diagnostic neither
requests nor performs merging #493, changing the entry gate, swapping
production checkout/SQLite, writing credentials, or placing orders.

## 2026-10-14 — final task 3.1 guarded merge decision

**Only the fixed three-task roadmap is authoritative.** Task 3.1 has
two DIFFERENT outcomes, which must not be conflated:

- **`STAGE8_493_3_1_GUARDED_SOURCE_MERGE_REVIEW_PASS`**
  for a **source-only, closed** GitHub merge to `main`, with **no**
  Intel deployment, LIVE checkout switch, trading authorization, new
  production SQLite state, Task/rearm action, or order endpoint access.
  This is a scoped audit recommendation, **not an operator merge
  authorization**. Draft PR #493 remains unmerged pending an explicit
  decision at task 3.2.
- **`STAGE8_493_LIVE_PRODUCTION_RELEASE_NOT_ACCEPTED`**
  for a trading-capable rollout/rearm. Do not set
  `FINAM_FILL_AUTHORITY_VERIFIED=True`, treat the existing legacy
  authorization as transferable, or represent code-only merge
  acceptance as permission to trade.

**Reviewed exact public GitHub authority:** MAIN
`d6946056332ce71658a6ca933cefa0740a7570a2`;
candidate PR #493 HEAD at audit
`7408b542ae91b337c3b46084823e8847812c0f12`,
DRAFT, UNMERGED, CLEAN/mergeable; 98 changed paths, all restricted to
`TradingSystemLab/` (91 added, 7 modified, zero removals).
Strategy T3, Stage7 frozen production specification, Stage5 TRAIL1
source, `stage8_robot/strategy_core.py`, `risk.py`,
`production_authorization.py`, `specification.py`,
`CURRENT_STATE.md`, `PROJECT_CONTEXT.md`, production RUNBOOK,
STRATEGY PASSPORT and OPERATOR CHECKLIST were directly compared
against MAIN using Git blob SHA: **IDENTICAL** for all twelve files.

**Acceptance evidence and limits retained without reruns:**

- One isolated real FINAM CNYRUBF LONG ×2 ENTRY plus a 100% SLTP:
  broker ACK/ID, active order observation, bounded BUY AccountTrade
  and manual SELL AccountTrade quantity/price verified in the
  operator logs. Manual exit/cancel followed by broker double-flat
  reconciliation. Gross **−34 RUB before fees**; net charges unknown.
  No live 1→2 growth or actual SLTP trigger proof.
- Exact Intel synthetic/offline PINNED PASS: SLTP decimal fix 29/29;
  growth fail-closed 89/89; explicit V2 selector/release 118/118
  (including exact Git blob and original raw-signal oracle).
  These are distinct runs on independently recorded pinned commits,
  not one fictitious all-project full-suite PASS.
- PR candidate closed `FINAM_FILL_AUTHORITY_VERIFIED=False`.
  Explicit V2 selector refuses before FINAM/SQLite service
  initialization, normal legacy selector remains unchanged,
  readonly isolated release preview is still order-incapable.
  Entry-layer runtime and transport guards also independently
  reject candidate ENTRY while the compiled authority is false.
- No published GitHub check-runs and no commit status contexts
  for the audited HEAD (GitHub aggregate status pending / 0
  reported checks); operator Intel logs are the available
  regression evidence, **not CI certification**.
- Existing historical unfiltered expanded-suite failures and
  partial real fill/stop/restart evidence gaps are **not
  relabeled as PASS** or silently removed by this conclusion.

**Minimal remaining roadmap decisions:** task **3.2** requires a
separate **explicit approval for code-only merge** and subsequent
verification of the actual merged GitHub `main`; nothing deploys
automatically as part of that review. Tasks **3.3–3.5** retain their
existing separate production cutover, immutable backup/rollback,
fresh broker/SQLite authority and operational-doc reconciliation.
Task **3.6** retains independent trading activation authorization
and fail-closed risk/stop/history gates. These are **not new phases**.
The 1→2 physical INCONCLUSIVE case is to be handled through the
pre-existing sticky HALT/OIR policy without demanding another
unapproved real trading experiment. No LIVE state has been observed
again by this GitHub review; last Intel HALTED/Task Disabled/flat
state is operator-reported at the earlier observation time.

**3.1 is complete strictly for code-only guarded merge review.**
LIVE trading approval remains NOT GRANTED and no merge or production
action was performed by this audit.
