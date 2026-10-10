# IntradayLab — LEVEL_REJECTION_M5 FAST execution V1

**2026-10-10 — user-approved immediate rerun with changed execution clocks. Freeze before new P&L.**

Old T10/T15 assumptions were unmeasured, and remain in archived results/ongoing #460. This new run changes ONE dimension: signal-to-Open execution clocks. No adjustments to historical C1, 3R, 6-M5 level, Stop, signal structure, 30min dedup, exit policy or parameters. Full rules in `../config/stage2_level_rejection_m5_fast_execution_v1.json`.

## New fixed clock matrix

| Label | Signal M5 t..t+5 complete at | Model entry Open | Epistemic status |
| --- | --- | --- | --- |
| **FAST0** | t+5 | **t+5** | Optimistic simultaneous completed-bar-to-next-open; real data feed and execution latency NOT certified. Main fast hypothesis, NOT automatically live-causal. |
| **FAST5** | t+5 | **t+10** | One full five-minute interval after completed bar, strict-future M5 Open; conservative causal cross-check. |

Ex: signal bar 10:00–10:05 -> FAST0 Open 10:05, FAST5 Open 10:10. Do NOT reinterpret T10/T15 as the same clocks. No arbitrary additional 10 or 15 minutes waiting. The first-next-open 10:05 is coincident with the candle close; its true fill is NOT established without timestamped market delivery/order-latency evidence, and it may overstate deployable performance.

## Unchanged fixed economic assumptions

- Four instruments USDRUBF/CNYRUBF/GLDRUBF/IMOEXF, pinned `market-pattern-data/forever` exact **2023** only, original source SHA and prefix bytes; 2024 WF / 2025+ TRUE OOS locked unread.
- Exactly prior PR459 rejected known six-bar level, dated one-tick breach and close back inside, prior one-tick structural Stop, at least four-tick initial price risk, 30-minute same-direction dedup, and causal previous-bar-only signal. Session windows and historical CNY tick unchanged.
- Exact timestamp Open, one position/symbol, busy and all rejected/unknown events recorded. Entry may inspect the Open at its modeled event, but not subsequent high/low/close/volume from that entry candle as a pre-entry filter.
- Same initial Stop, gap worse Open, stop-first even on entry M5, no entry-bar Take, later Take one-tick penetration, full-net C1 after-cost **3:1** (`d=3s+8t`), no 2R comparison in this batch.
- Same failed-reclaim exit, 120min max hold and mandatory flat before end, adapted clock-only to FAST0/FAST5 with no prior-bar hindsight. Missing target M5/exposed bars UNKNOWN fail-closed and no false annual P&L.
- C1 historical 1 tick each entry and exit; C2 cost stress 2 ticks each side **instead** on identical trades; all 12 months, full event ledger, no PF/Net/DD annual PASS when unknown/incomplete; no capital sizing, external costs, real FINAM orders.

## Run now, do not diagnose until results

Implement, test, and execute the FAST0/FAST5 matrix and independent oracle on full physically available 2023. Produce baseline files under `IntradayLab/results/stage2_level_rejection_m5_fast_execution_v1/`: exact trades, audit events, signal/opportunity/busy/UNKNOWN reconciliation, every monthly symbol/direction/cost report, Net PF, Net R, expectancy, positive/negative/unknown months, drawdown, TP/SL/flat frequency, FAST5 vs FAST0, verification hashes, protected trees, all tests. Never read 2024/2025+, change prior reports, tune signal/Take/Stop, auto-merge or launch further strategy. Keep #460 work preserved separately.

**Stopping condition:** Draft PR with reproducible results and independent code/data audit; no economic PASS inferred solely from fast nominal fill.
