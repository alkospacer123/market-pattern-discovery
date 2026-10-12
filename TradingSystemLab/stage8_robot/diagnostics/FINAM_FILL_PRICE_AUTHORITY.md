# FINAM fill price authority — PR #493 follow-up

**PROPOSED / NOT DEPLOYED. Source found in official schema; physical acceptance remains BLOCKED. LIVE_CHANGES=NONE. REAL_ORDER_ENDPOINT_CALLS=0.** This work adds one read-only diagnostic and offline tests; it does not enable the proposed execution profile or change FINAM production transport, strategy or state.

## Concrete finding

Official `FinamWeb/finam-trade-api@52c95c8672542c2f89fbee2a4016774e73a0caa4` (commit dated 2026-10-01) describes:

- [`GET /v1/accounts/{account_id}/trades`](https://github.com/FinamWeb/finam-trade-api/blob/52c95c8672542c2f89fbee2a4016774e73a0caa4/proto/grpc/tradeapi/v1/accounts/accounts_service.proto#L107) with `limit`, `interval.start_time`, `interval.end_time`; 400 is explicitly “Неверно передан интервал”. Start is inclusive, end exclusive. Swagger marks individual query fields optional; this does **not** prove that the server accepts the existing completely unbounded request.
- [`AccountTrade`](https://github.com/FinamWeb/finam-trade-api/blob/52c95c8672542c2f89fbee2a4016774e73a0caa4/proto/grpc/tradeapi/v1/trade.proto#L13): `trade_id`, `order_id`, `account_id`, `symbol`, `side`, `size`, `price` (“Цена исполнения”), timestamp and currency. This is the smallest documented source of price-of-this-order using the existing REST API.
- [`Position.average_price`](https://github.com/FinamWeb/finam-trade-api/blob/52c95c8672542c2f89fbee2a4016774e73a0caa4/proto/grpc/tradeapi/v1/accounts/accounts_service.proto#L268): explicitly **not populated for FORTS**. It cannot substitute for fills of N4 futures. `current_price` also is not execution price.
- `OrderState` provides identity, executed/remaining quantity and status, but no executed-price field. Request `limit_price`/`stop_price` are not MARKET fill prices. SubscribeTrades exposes the same trade type through a stream, but would add transport/reconnect requirements and supplies no proven restart history contract here; it is not introduced.

Exact schema extracts, source URLs and four file hashes are in `official_fill_contract.json`. They are documentary authority, not physical broker evidence.

Existing `finam_api.trades()` sends only `/trades`, omitting all interval/limit query parameters. `broker.fills()` reads `account.trades`, although GetAccount is not trade history authority. Both findings are confirmed in code. The omission is a plausible explanation of the historical 400, **not a confirmed explanation of the actual server error**: raw error bodies and Intel responses are unavailable in this environment. Production API/adapter code is not changed on this assumption.

## Attempts 2–7 and retained evidence

The current main, accepted provenance, recovery validators and attempt7 implementation were inspected. Original external Intel evidence/logs/ledger files are not mounted here; their bytes were not fabricated or independently rehashed in this follow-up.

| Attempt | Accepted external evidence SHA-256 | What the retained authority proves about price |
|---|---|---|
| 2 | `0954B5C3D62444BA9AE59519386B0FC454D85C987BE1BAC04B82CA6C671B15A0` | One ACK, +1 CNY position, no proven trade rows at immediate reconciliation; later manual close. No price. |
| 3 | `9206841E4C9E25F126AB6C7032326B4F0778F6CF65D44AF3DA3549D8E677AD65` | Recovery validator binds OIR with ACK/+1 position/zero proven fills; history-detail 404 later allowed by immutable evidence plus flat account. No price/retention proof. |
| 4 | `F0EADA84724509A197BE7F851B2530535DAA7B1A8EC062D8943CCB905C5BA2EF` | Recovery validator binds OIR, +1 position, zero proven fills and manual-close recovery. No price. |
| 5 | `E67127A4727C4B5505F52877A9AFDE29447551DF781E5420DD4F7695CAC92F85` | Same bounded ACK/position/OIR authority; no accepted price rows. |
| 6 | `8921A4A9FC1A44DD0407D405B32B54B03A87F6949AFBCC6DA446F1FDC58BDE3B` | OIR/+1 position and account-only manual-close recovery; no price. |
| 7 | `704BFCC19B1A63F490192C0D8D0E4715BFECF77664296AFEF47E5B80FBF64B5F` | Accepted position-authoritative entry/flatten PASS. `broker_fill_count=2` is calculated from entry/flatten boolean flags in `stage8_11_physical_acceptance.py`, not two authenticated `AccountTrade.price` rows. |

Historical PASS is not reclassified. `_reconcile_position()` changes intent status based on exact quantity; it does not persist trade price rows. Earlier order-detail expiry does not prove `/trades` expiry or retention. The accepted roadmap forbids restoring old synchronous order/trades convergence as normal quantity proof. A separately accepted **price evidence** contract must preserve position-authoritative exposure reconciliation.

## One minimal READONLY scenario for Intel

`finam_fill_price_readonly.py` uses the existing FinamAPI transport under a strict allowlist: POST session/authentication, GET account, GET **bounded** trades. It rejects **all orders URLs, including GET order/detail**, and every trading/cancel operation before transport. The scenario needs no new SDK, stream, token provisioning or production configuration.

Inputs:

1. A stable standalone **copy of an already existing historical Stage8.11 backup** outside RuntimeRoot and the diagnostic checkout, with its known SHA-256. It must include one ACK order ID for an entry from attempts 2–7. An attempt3–6 pre-recovery backup is sufficient; an attempt7 copy is optional. The scenario does not create a backup from the running database. Canonical LIVE database filenames and WAL/shm sidecars are rejected.
2. The exact historical entry intent key and a closed UTC interval covering that order's execution, taken from existing evidence/log timestamps. If the exact sub-interval is unavailable, use an explicitly bounded historical interval covering the known attempt, then inspect completeness. Do not guess a fill from an empty response.
3. The existing READONLY DPAPI credential, retrieved by the existing getter under its existing owner. No trading token, authorization or kill-switch change.
4. A reviewed isolated checkout of this Draft PR, existing Python venv, and a new `.json` output path in an existing audit directory outside RuntimeRoot/checkout.

The wrapper is `run-finam-fill-price-readonly.ps1`. It never calls task/process/kill-switch/state controls and never updates the production checkout. Example with operator-supplied existing paths/times (placeholders must be replaced by actual evidence):

```powershell
& 'C:\TSLAudit\candidate-checkout\TradingSystemLab\stage8_robot\diagnostics\run-finam-fill-price-readonly.ps1' `
  -RuntimeRoot '<existing LIVE runtime root; credentials read only>' `
  -ExpectedDiagnosticCommit '<reviewed 40-character PR head SHA>' `
  -LedgerCopy 'C:\TSLAudit\historical-ack-copy.sqlite3' `
  -LedgerSha256 '<known SHA-256 of that existing standalone copy>' `
  -IntentKey 'stage8.11.attempt6:CNYRUBF:entry' `
  -StartTime '<actual historical interval start RFC3339 UTC>' `
  -EndTime '<actual historical exclusive end RFC3339 UTC>' `
  -Output 'C:\TSLAudit\fill-observation-A.json' `
  -Python '<existing venv python.exe>'
```

Run the **same scenario in a new process** with output `fill-observation-B.json`, plus `-PreviousReport ...A.json -PreviousSha256 <reported hash>`, to observe whether the identical historical fill set is still available. No restart/stop of LIVE is needed. This observes retention across diagnostic process restart and elapsed time, not an indefinite server-retention guarantee.

The report verifies local copied ACK account/client/instrument/side/quantity, matches **only** its exact broker `order_id`, rejects identity/unit/grid errors, deduplicates identical `trade_id` rows, rejects conflicting duplicates/overfills, and reports partial/full/unknown coverage. Weighted price is stored as an **exact rational**, with a Decimal value labelled display-only; no rounded average is passed as authoritative runtime fill. Individual fills must be on the authenticated N4 grid. Current account quantity may be flat after historical exit and is never used as historical price proof.

No documented pagination token/ordering/retention guarantee was found. `row_count >= limit` or a nonempty unknown cursor fails closed: do not invent pagination or claim full history. Empty history, 400, 404, missing identity/currency, partial coverage, or changed fills remain blockers. Reports contain only selected facts/field names and hashed account/order/trade identity, never token/secret or full account payload. SQLite copy is opened `mode=ro&immutable=1`, checked byte-for-byte before/after, without sidecar creation.

**The scenario was prepared and tested offline, not run on Intel.** No actual FINAM response is claimed. A full matching diagnostic observation is evidence to review; it does not automatically enable fill authority, migration, production or ordinary trading.

## Candidate risk audit and separate proposed MARKET contract

| Requirement | Current evidence / limitation |
|---|---|
| Quantity from executable stop | PASS: existing candidate sizing and independent 1422-signal rational oracle remain valid. No raw quantity reuse. |
| Reference is not actual fill | PASS offline: separate fields; real fill remains null; no account average/current price fallback. |
| Actual R/cash calculation | PASS for supplied offline synthetic fill: `R_actual=abs(fill-S_exec)`; cash = R/step × tick_value × filled quantity. Real bridge/price authority not accepted. |
| Partial/unknown and no duplicate entry | Inhibition PASS: unexpected partial quantity leaves the intent unresolved and prevents another entry. Exact matching multi-fill accumulation is tested in the diagnostic only. |
| Preserve protection | Existing fully confirmed exposure with unknown price retains the precommitted backstop and blocks normal management/new entries. **New partial exposure before initial protection is not handled by candidate runtime:** it rejects non-final quantity before creating a stop. This must be fixed and independently accepted before enabling MARKET entry. No protective workaround is deployed. |
| TRAIL1/FULL/R15/N4/frozen T3 | Unchanged; existing offline suite remains control. Proposed profile remains closed and unselected. |

Consequently `STOP_TICK_GRID_CANDIDATE=NEEDS_FIX` for the **complete broker execution acceptance** requested here, while the stop-grid/sizing/TRAIL1 replay components retain offline PASS. This is a newly explicit partial-protection gap, not a failure of the grid rounding formula. No already-open LIVE position is changed by this work.

**Proposed separate execution accounting contract (NOT ACCEPTED / NOT IMPLEMENTED):** keep MARKET and the existing FULL/R15 reference-price 1.5% sizing plus 6% aggregate nominal budget; never promise a strict actual-loss ceiling. Record final matched fill set, exact weighted price, actual initial R/cash and reference budget separately. Partial/unknown exposure must receive verified 100%-of-current-position precommitted protection before normal management; unknown outcome must never resend entry. Freeze TRAIL1 actual entry/R only after complete price/quantity authority, preserving raw/reference evidence. If actual risk exceeds the reference budget or authority is missing/inconsistent, keep protection, block normal trading/new entries and require review; no automatic resize/compensating trade or new parameter is proposed. Gap stop fills, fees and slippage can further exceed initial nominal risk. Accepting this accounting distinction requires separate approval; it does not alter R15 or replace MARKET with LIMIT.

## Remaining acceptance

`FINAM_FILL_PRICE_SOURCE=FOUND_DOCUMENTED_TRADES_HISTORY`; `ORDER_IDENTITY_VERIFIED=BLOCKED`, `PARTIAL_FILL_RECONCILIATION=BLOCKED`, `RESTART_RETENTION=BLOCKED`, `ACTUAL_R15_RISK=BLOCKED`, `LIVE_PRODUCTION_READY=NO`.

Next: inspect the READONLY A/B reports against immutable ACK/physical evidence; prove correct interval request succeeds with real price/unit/identity/coverage. If history is unavailable or clipped, obtain FINAM's exact supported retrieval/retention contract rather than invent it. Real partial/restart price coverage remains unproven by one-contract attempts; existing historical multi-fill evidence is needed if available. Then prepare the narrow price handoff/durable fill retention and partial-protection fix in PR #493, with exact identity/idempotency tests, **before** any separate LIVE acceptance. The diagnostic/profile must not enable itself from observed success.
