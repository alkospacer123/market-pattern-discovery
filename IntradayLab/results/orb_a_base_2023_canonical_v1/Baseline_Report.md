# Canonical Baseline — ORB FALSE-BREAK FADE A BASE M5

**Infrastructure: technical validation and independent audit recorded in audit.json.**
**Baseline: INCONCLUSIVE. Optimization is not authorized.**

2023-01-01—2023-12-31; one fixed strategy, no optimization. Source f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8.
All economics below are conditional known closures after model C1, one dated tick per side.
Annual PF/Net/Expectancy/Win Rate/DD are null because coverage and outcomes are incomplete.
The closed-only DD is a diagnostic sequence of known closures, not continuous portfolio equity.

| Instrument | Signals | Orders | Fills | Closed | UNKNOWN | PF price | PF R | Net R | Expectancy R | Win rate | DD R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| USDRUBF | 169 | 158 | 138 | 137 | 1 | 0.963788 | 0.581807 | -42.818523 | -0.312544 | 0.437956 | 53.675299 |
| CNYRUBF | 72 | 67 | 62 | 59 | 3 | 0.542493 | 0.622262 | -13.499572 | -0.228806 | 0.372881 | 17.596332 |
| GLDRUBF | 76 | 67 | 47 | 40 | 10 | 0.622004 | 0.487094 | -17.424734 | -0.435618 | 0.375000 | 18.731521 |
| IMOEXF | 19 | 17 | 15 | 10 | 6 | 1.390244 | 0.505110 | -4.060101 | -0.406010 | 0.400000 | 6.060101 |

USDRUBF: NO ECONOMIC BASELINE PASS; rejection reasons: `{"AMBIGUOUS_BOTH_SIDES": 6, "INVALID_STOP_GEOMETRY": 20, "NO_OR": 2, "NO_RECLAIM": 215, "NO_RECLAIM_AMBIGUOUS": 2, "POSITION_BUSY": 10, "SESSION_LIMIT": 1}`.
Unknown possible entries 0; known closures after a prior unresolved day 116.

CNYRUBF: NO ECONOMIC BASELINE PASS; rejection reasons: `{"AMBIGUOUS_BOTH_SIDES": 4, "INVALID_STOP_GEOMETRY": 5, "NO_OR": 6, "NO_RECLAIM": 293, "NO_RECLAIM_GAP": 4, "NO_RECLAIM_WINDOW": 1, "POSITION_BUSY": 5}`.
Unknown possible entries 0; known closures after a prior unresolved day 56.

GLDRUBF: NO ECONOMIC BASELINE PASS; rejection reasons: `{"AMBIGUOUS_BOTH_SIDES": 19, "INVALID_STOP_GEOMETRY": 17, "MISSING_EXECUTION_BAR": 3, "NO_OR": 9, "NO_RECLAIM": 95, "NO_RECLAIM_AMBIGUOUS": 2, "NO_RECLAIM_GAP": 2, "NO_RECLAIM_WINDOW": 1, "NO_WAITING_BAR": 2, "POSITION_BUSY": 5, "UNKNOWN_POSITION_BLOCK": 2}`.
Unknown possible entries 3; known closures after a prior unresolved day 40.

IMOEXF: NO ECONOMIC BASELINE PASS; rejection reasons: `{"AMBIGUOUS_BOTH_SIDES": 2, "INVALID_STOP_GEOMETRY": 1, "MISSING_EXECUTION_BAR": 1, "NO_OR": 4, "NO_RECLAIM": 21, "NO_RECLAIM_AMBIGUOUS": 1, "NO_RECLAIM_GAP": 3, "NO_WAITING_BAR": 1, "POSITION_BUSY": 1}`.
Unknown possible entries 1; known closures after a prior unresolved day 10.

## Source coverage

| Instrument | Full / eligible days | Pre-inception days | Missing expected slots | Invalid slots | All source M5 rows |
|---|---:|---:|---:|---:|---:|
| USDRUBF | 224/254 | 0 | 187 | 0 | 42576 |
| CNYRUBF | 82/254 | 0 | 1270 | 0 | 39362 |
| GLDRUBF | 5/124 | 130 | 932 | 0 | 18428 |
| IMOEXF | 2/34 | 220 | 566 | 0 | 4429 |

Every physical 2023 M5 row is validated, including pre-10:00 and evening observations. These outside-window rows warm indicators but cannot create entries.
Calendar weekends/declared holidays and pre-inception days do not create fictitious expected candles. The grid is the approved research contract, not a complete exchange calendar.
The September 13 exchange halt is identified diagnostically; it does not retrospectively change trade windows. The absent August 31 USD/CNY rows have an unproved source cause.
Missing slots are neither automatic missed trades nor source errors. Exact missing/invalid slots and source-cause limits are retained in coverage_events.csv.

## All twelve months — conditional known closures

| Month | Instrument | Closed | UNKNOWN | PF C1 price | Net R | Expectancy R | Win rate | DD R | Coverage class | Full / incomplete / pre-inception days |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 2023-01 | USDRUBF | 10 | 0 | 1.190476 | -1.750980 | -0.175098 | 0.500000 | 4.450980 | PARTIAL_DATA | 16/5/0 |
| 2023-01 | CNYRUBF | 2 | 0 | — | 0.000000 | 0.000000 | 0.000000 | 0.000000 | PARTIAL_DATA | 3/18/0 |
| 2023-01 | GLDRUBF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-01 | IMOEXF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-02 | USDRUBF | 6 | 0 | 0.190476 | -5.066667 | -0.844444 | 0.166667 | 5.066667 | PARTIAL_DATA | 15/4/0 |
| 2023-02 | CNYRUBF | 0 | 0 | — | 0.000000 | — | — | — | PARTIAL_DATA | 1/18/0 |
| 2023-02 | GLDRUBF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/19 |
| 2023-02 | IMOEXF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/19 |
| 2023-03 | USDRUBF | 15 | 1 | 1.012500 | -2.850057 | -0.190004 | 0.466667 | 4.328324 | UNKNOWN | 19/3/0 |
| 2023-03 | CNYRUBF | 1 | 0 | — | 0.333333 | 0.333333 | 1.000000 | 0.000000 | PARTIAL_DATA | 0/22/0 |
| 2023-03 | GLDRUBF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-03 | IMOEXF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-04 | USDRUBF | 8 | 0 | 0.227273 | -11.107143 | -1.388393 | 0.125000 | 11.107143 | PARTIAL_DATA | 15/5/0 |
| 2023-04 | CNYRUBF | 0 | 0 | — | 0.000000 | — | — | — | PARTIAL_DATA | 2/18/0 |
| 2023-04 | GLDRUBF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/20 |
| 2023-04 | IMOEXF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/20 |
| 2023-05 | USDRUBF | 11 | 0 | 0.551282 | -6.051924 | -0.550175 | 0.363636 | 7.559861 | PARTIAL_DATA | 18/3/0 |
| 2023-05 | CNYRUBF | 0 | 1 | — | 0.000000 | — | — | — | UNKNOWN | 0/21/0 |
| 2023-05 | GLDRUBF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-05 | IMOEXF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-06 | USDRUBF | 12 | 0 | 0.376471 | -7.880952 | -0.656746 | 0.333333 | 10.466667 | PARTIAL_DATA | 17/4/0 |
| 2023-06 | CNYRUBF | 1 | 1 | — | 1.000000 | 1.000000 | 1.000000 | 0.000000 | UNKNOWN | 1/20/0 |
| 2023-06 | GLDRUBF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-06 | IMOEXF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-07 | USDRUBF | 8 | 0 | 1.277778 | -0.164234 | -0.020529 | 0.500000 | 3.784524 | PARTIAL_DATA | 20/1/0 |
| 2023-07 | CNYRUBF | 3 | 0 | 0.214286 | -1.583333 | -0.527778 | 0.333333 | 2.583333 | PARTIAL_DATA | 2/19/0 |
| 2023-07 | GLDRUBF | 4 | 2 | 0.750000 | -0.555937 | -0.138984 | 0.500000 | 1.047619 | UNKNOWN | 0/15/6 |
| 2023-07 | IMOEXF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-08 | USDRUBF | 19 | 0 | 1.092308 | -5.266446 | -0.277181 | 0.421053 | 7.125923 | PARTIAL_DATA | 21/2/0 |
| 2023-08 | CNYRUBF | 5 | 1 | 0.190476 | -2.419048 | -0.483810 | 0.200000 | 3.419048 | UNKNOWN | 9/14/0 |
| 2023-08 | GLDRUBF | 6 | 1 | 0.300283 | -4.635445 | -0.772574 | 0.333333 | 5.005445 | UNKNOWN | 0/23/0 |
| 2023-08 | IMOEXF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/23 |
| 2023-09 | USDRUBF | 13 | 0 | 0.827586 | -5.176263 | -0.398174 | 0.461538 | 7.204040 | PARTIAL_DATA | 19/2/0 |
| 2023-09 | CNYRUBF | 4 | 0 | 0.000000 | -4.885714 | -1.221429 | 0.000000 | 4.885714 | PARTIAL_DATA | 7/14/0 |
| 2023-09 | GLDRUBF | 6 | 3 | 1.084034 | -3.234145 | -0.539024 | 0.333333 | 5.117148 | UNKNOWN | 0/21/0 |
| 2023-09 | IMOEXF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/21 |
| 2023-10 | USDRUBF | 10 | 0 | 1.092308 | -2.896996 | -0.289700 | 0.500000 | 5.660632 | CONDITIONAL_AFTER_UNKNOWN | 22/0/0 |
| 2023-10 | CNYRUBF | 11 | 0 | 0.987179 | 2.137275 | 0.194298 | 0.545455 | 2.431818 | PARTIAL_DATA | 20/2/0 |
| 2023-10 | GLDRUBF | 12 | 1 | 0.738095 | -2.725093 | -0.227091 | 0.333333 | 3.947174 | UNKNOWN | 1/21/0 |
| 2023-10 | IMOEXF | 0 | 0 | — | — | — | — | — | NO_COVERAGE | 0/0/22 |
| 2023-11 | USDRUBF | 13 | 0 | 2.218750 | 4.224823 | 0.324986 | 0.615385 | 1.424242 | PARTIAL_DATA | 21/1/0 |
| 2023-11 | CNYRUBF | 14 | 0 | 1.062500 | -6.115263 | -0.436804 | 0.285714 | 8.461854 | PARTIAL_DATA | 16/6/0 |
| 2023-11 | GLDRUBF | 4 | 3 | 1.021739 | -0.439001 | -0.109750 | 0.500000 | 2.717949 | UNKNOWN | 1/21/0 |
| 2023-11 | IMOEXF | 3 | 3 | 0.000000 | -2.581818 | -0.860606 | 0.000000 | 2.581818 | UNKNOWN | 0/13/9 |
| 2023-12 | USDRUBF | 12 | 0 | 2.000000 | 1.168316 | 0.097360 | 0.583333 | 3.171078 | CONDITIONAL_AFTER_UNKNOWN | 21/0/0 |
| 2023-12 | CNYRUBF | 18 | 0 | 1.336634 | -1.966822 | -0.109268 | 0.444444 | 3.730249 | CONDITIONAL_AFTER_UNKNOWN | 21/0/0 |
| 2023-12 | GLDRUBF | 8 | 0 | 0.454259 | -5.835112 | -0.729389 | 0.375000 | 6.724001 | PARTIAL_DATA | 3/18/0 |
| 2023-12 | IMOEXF | 7 | 3 | 2.714286 | -1.478283 | -0.211183 | 0.571429 | 4.400000 | UNKNOWN | 2/19/0 |

## Execution and fixed candidate

OR 10:00–10:15, sweep 1 dated tick, reclaim 2 ticks inside on same/next completed M5; first attempt per side/day is consumed, even if it fails.
Stop at episode extreme ±1 sweep-dated tick; target 1.5 gross R, rounded outward on entry-dated grid; holding 60 calendar minutes. No ATR, MTF or minimum Stop filter.
Signal at reclaim close; one full following M5 closes; Open-only model entry at the next boundary. Stop-first on ambiguous OHLC; no entry-bar Take; adverse Stop gap at Open; Take at target without favorable gap improvement.
Events sharing a signal timestamp use ascending signal_id, matching the frozen #463 executable ledger; one pending/open position is admitted per instrument. A both-sided sweep candle consumes both attempts without entry.
Trading windows 10:00–14:00 / 14:05–18:50; afternoon starts 14:15 on March 13–20. Scheduled TIME/SESSION_FLAT uses exact Open, with adverse Stop gap precedence.
Missing waiting bar: NO_WAITING_BAR, no order. Missing entry Open: UNKNOWN possible fill. Missing exposed bar/mandatory exit: UNKNOWN, no invented exit or net. Same day is blocked; next day assumes FLAT conditionally.
Intrabar exits are intervals [start,end], not exact exchange timestamps. Missing-slot discovery metadata is the interval end; no missing price is replaced.

## Frozen #463 comparison

Reference commit `9c65d03aae117c6d88bbb4e6186f6a4fbb6b73ec`; A BASE v2 daywise only. Fully sufficient instrument-days: 313; compared trades: 171; discrepancies: 0.
historical_comparison.json includes row-set and field checks for signals, admission, entry, Stop, Take, exit and C1, plus incomplete-day diagnostics. Historical code/config/artifacts were read through git show and remain untouched.

One implementation discrepancy was found and fixed before canonical freeze: two GLD signals at 2023-10-06 10:35 were emitted in callback order. Applying the frozen ascending signal_id tie-break restores identical admission and trade identity. Parameters were not changed; final comparison has zero discrepancies on incomplete days as well.

## Reproduction and limits

Run `python3 IntradayLab/tools/run_canonical_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/replay` then `python3 IntradayLab/tools/audit_canonical_baseline.py --data-root /workspace/market-pattern-data --output IntradayLab/work/replay`.
Determinism and technical-test receipts are stored separately in validation.json. Provenance pins input prefix bytes/hashes, code/config hashes, historical reference and protected root trees.
C1 is a research cost assumption, not verified broker fees. This normalized historical model does not establish queue fills, capital, margin or live authority.
NO ECONOMIC BASELINE PASS is retained for negative known-closure diagnostics. Overall and sparse/unknown instruments remain INCONCLUSIVE; no candidate moves to Optimization.
Lifecycle stays Baseline → Optimization → Robustness → Walk Forward → TRUE OOS. 2024 and 2025+ were not read. No Merge, next stage or LIVE. TradingSystemLab is read-only and not imported.
