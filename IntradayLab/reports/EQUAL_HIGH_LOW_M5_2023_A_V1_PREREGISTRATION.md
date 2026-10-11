# EQUAL_HIGH_LOW_M5 — A_v1 preregistration before P&L

Decision date: 2026-10-11, Europe/Moscow. One fixed first family A Baseline, no parameter search. Base main `d438c72f9fce5c3bf1d30c9b169d14b97079e768`, PR #473 merged and decisions present in ROADMAP/PROJECT_CONTEXT. Separate Draft #472 remains untouched at `82ec9ffe61e18a43cd7510e398f6913b25f045e1`.

Source: pinned clean read-only `market-pattern-data` at `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Only exact approved four 2023 M5 prefixes (104795 rows, 5833704 bytes), no 2024 price bytes (WF), no 2025+ (TRUE OOS). Input paths, Git blobs, row/byte budgets and SHA-256 are inherited unchanged from approved source manifests. Real broker execution, delivery latency, capital, funding and margin are unproved: this is a conditional research execution model.

## Signal and cluster identity

SHORT: last three consecutive, valid, completed M5 in the same approved window/day/tick regime have exactly the same High on that dated price grid; last Close < common High. LONG mirrors Low and Close > common Low. No rounding tolerance, round-number requirement, extra candle, indicator or MTF.

A cluster is a maximal contiguous run of equal extremes, independently for High/SHORT and Low/LONG. Consume once on its first qualifying three-bar rolling window, irrespective of eventual admission or fill. Third Close equal to the extreme is not a signal; the first later qualifying exact three-bar window may signal once. A changed extreme, missing/invalid bar, nonconsecutive callback, session/day boundary or changed tick resets that side/run. An expired signal is never carried to another Open/session. ID: symbol + calendar date + direction + maximal-run first start + level in dated grid ticks. Simultaneous qualifying LONG and SHORT are both rejected as `AMBIGUOUS_BOTH_SIDES`; consume both. No post-result direction selection.

## Execution contract and frozen parameters

| Parameter | Value |
| --- | --- |
| Version / TF | A_v1 / M5 |
| Consecutive touches | 3 |
| Extreme tolerance | 0 historical ticks |
| Structural Stop buffer | 1 signal-date tick |
| Stop bounds at actual entry | 3–12 entry-date ticks, inclusive |
| Rebound distance from cluster | 0–4 entry-date ticks, inclusive |
| Target | FULL_NET_C1_R = 3 |
| Calendar hold | <=120 minutes |
| Cost | C1, one dated tick per side |
| Entry | ENTRY_NEXT_OPEN |
| Entry-bar Take | Disabled, inherited conservative convention |
| Same-bar conflict | Stop-first |
| Session flat | Approved window end−5m Open |
| Extra daily deadline / reserve | None |

At a boundary: complete previous interval/exits → current Open protection/deadline → completed-bar signal → scalar Open admission → model fill. Signal close = immediately next M5 start. No waiting M5 and no entry H/L/C/Volume in admission. Default ENTRY_WAIT_ONE_BAR and old ledger fields remain unchanged, including M15 behavior.

Stop SHORT = cluster High+tick; Stop LONG = cluster Low−tick. No artificial relocation. At actual next Open, check dated grid; rebound side; positive risk; maximum Stop; minimum Stop; maximum rebound distance, in that deterministic order. Reasons: `OPEN_WRONG_SIDE_OF_CLUSTER`, `INVALID_STOP_GEOMETRY`, `STOP_ABOVE_12_TICKS`, `STOP_BELOW_3_TICKS`, `ENTRY_MORE_THAN_4_TICKS_FROM_CLUSTER`. Session/busy/UNKNOWN refusals precede submission. Missing/invalid Open is UNKNOWN possible fill under the common conservative contract, not a presumed nonfill and never a later-Open substitute. Pre-fill geometry refusals produce no fill, trade P&L or C1.

Without tick transitions inside a cluster, risk = rebound distance+1 tick. The given min3/max12/rebound<=4 therefore permits risk3–5 ticks, rebound2–4. Max12 remains a redundant upper protection; it is not relaxed after results. Analytic preflight tests all four grids (CNY old/new separately), without P&L. Gross target distance = 3s+8t, outward grid rounding; planned (distance−2t)/(s+2t)=3. Actual costs use each fill's dated tick. Report gross-risk R as (gross−actual C1)/s separately from the full net/net ratio.

Approved windows remain 10:00–14:00 and 14:05–18:50 MSK, with 14:15 PM start during 2023-03-13 through 2023-03-20. Flat at end−5m and earlier at entry+120m. Resident Stop first, including entry interval; entry-bar Take disabled. Adverse Stop gaps close at actual Open. Scheduled exits read only Open. UNKNOWN retains unknown prices/P&L as null, known entry cost separately, blocks its current day, and all subsequent days require a persistent conditional-FLAT assumption. No continuous broker-equity claim.

## Freeze and reports

Strategy, shared execution changes, independent auditor, runner, tests, config/hash, pre-P&L geometry/source-grid receipts, scope manifest and this contract are committed together **before any A_v1 historical P&L**. Config hashes all executable dependencies; runner/auditor verify them and the config against the creation commit before source reads. No changes to frozen trading code or parameters after results. One canonical run and two identical repeats, not multiple selected Baselines.

Preserve all directional candidates (ambiguity distinguished), qualified signals, exact refusal reasons, CLOSED/UNKNOWN, dated fills, complete 12-month/instrument/direction reports, sample frequency, gross/C1/net, PF in gross-risk R and instrument price units, average wins/losses, exit types, conditional DD/concentration. No incompatible instrument-price portfolio sum. Reuse the existing common evidence policy, with full annual numbers null if coverage/outcomes are incomplete. Negative conditional C1 expectation means NO ECONOMIC BASELINE PASS; missing evidence means INCONCLUSIVE. Optimization is never automatic.

Independent verification uses backward maximal-run reconstruction and raw forward paths, no production strategy/Backtester/loader/metrics imports. It is an independent implementation by the task agent, not external human or second-agent acceptance. Re-run old frozen candidates in the default engine and require identical economic artifacts; only replay code-identity metadata may reflect current core, original bytes stay intact.

## Oracle and STOP

ENTRY_CLOSE_ORACLE is not an executable Backtester mode. Store separate hypothetical Close-filled diagnostics, with the same fixed signal/Stop/limits/C1 and subsequent M5 path, own occupancy and UNKNOWN state. Never mix Oracle with the trading ledger or economic PASS. Clearly expose paired signal IDs and Close-vs-Open differences.

After first Baseline, audit and Draft PR: STOP; no merge. B accumulation of 4/7/10 Highs/Lows (later 4–10), C independent pullback/retest strikes, optimization of touches/Stop/Take 2/3/5/7/10R, trailing, MTF and filters are future documented work only, requiring separate tasks and economic grounds. TradingSystemLab, all non-IntradayLab paths, live robot/broker settings, every old strategy/config/result and market-pattern-data remain protected.
