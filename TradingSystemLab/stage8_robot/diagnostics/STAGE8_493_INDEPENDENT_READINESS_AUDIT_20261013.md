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
- Audit finding: candidate `finam_fill_price_readonly.py` catches `FinamError` and writes an observation report with `history_blocker`; the module's process can still exit 0. Therefore **exit code, REPORT_CREATED and report hash never mean fill PASS**. Human/independent gate must require report `history_http_status=200`, no history_blocker, exact target, FULL_REQUEST_MATCHED, stable unique fills. Related generic `FinamAPI.trades(start,end,limit)` currently ignores all three optional arguments; use the explicit allowlisted `ReadonlyFillAPI.read_history` path for any new diagnostic, not that generic helper.

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
