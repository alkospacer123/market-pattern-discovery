# ORB False-Break Fade v2 — 2023 conditional daywise research

**INCONCLUSIVE_UNRESOLVED. No accepted economic Baseline.** UNKNOWN and incomplete coverage prevent a verified continuous-account annual Net/PF/DD; these fields remain null. The tables below contain only known closed trades from independent days with an explicit, unproven starting FLAT assumption. UNKNOWN exposures and unknown entry orders remain in the ledger, with null outcomes.

v2 was formulated after inspecting v1 outcomes on 2023. Its configuration was frozen before this repeat at `6843dbf8037a9df6eae6f88e8d1301c9f60e24bd`; it is an exploratory in-sample retest, not independent OOS confirmation. No thresholds, dates, instruments, Stop or execution rules were tuned.

A uses pure M5, B adds SMA14 ATR with 0.30 sweep threshold over actual completed observations across sessions, C vetoes only a completed M15 close accepting a breakout beyond the opposite OR boundary, D combines the two. No M15 context is explicitly neutral. All use the immutable v1 entry/exit engine; A economics equal v1 daywise exactly. The one-full-M5 waiting period supplies timing only. Boundary Open fills are historical model assumptions, not proven broker fills.

| Architecture | Instrument | Signals | After filters | Admitted | Fills | Closed | UNKNOWN | PF C1 | PF C2 | Exp R C1 | + / − / 0 / uncovered |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A_BASE | USDRUBF | 169 | 169 | 158 | 138 | 137 | 1 | 0.964 | 0.657 | -0.313 | 7 / 5 / 0 / 0 |
| A_BASE | CNYRUBF | 72 | 72 | 67 | 62 | 59 | 3 | 0.542 | 0.274 | -0.229 | 4 / 4 / 4 / 0 |
| A_BASE | GLDRUBF | 76 | 76 | 67 | 47 | 40 | 10 | 0.622 | 0.586 | -0.436 | 2 / 4 / 0 / 6 |
| A_BASE | IMOEXF | 19 | 19 | 17 | 15 | 10 | 6 | 1.390 | 0.925 | -0.406 | 1 / 1 / 0 / 10 |
| B_IND | USDRUBF | 169 | 103 | 99 | 92 | 91 | 1 | 1.002 | 0.695 | -0.278 | 4 / 8 / 0 / 0 |
| B_IND | CNYRUBF | 72 | 48 | 47 | 44 | 41 | 3 | 0.580 | 0.263 | -0.177 | 4 / 4 / 4 / 0 |
| B_IND | GLDRUBF | 76 | 37 | 33 | 26 | 20 | 7 | 0.845 | 0.809 | 0.040 | 2 / 3 / 1 / 6 |
| B_IND | IMOEXF | 19 | 13 | 12 | 11 | 6 | 6 | 0.742 | 0.459 | -0.179 | 1 / 1 / 0 / 10 |
| C_MTF | USDRUBF | 169 | 164 | 154 | 135 | 134 | 1 | 1.023 | 0.688 | -0.306 | 7 / 5 / 0 / 0 |
| C_MTF | CNYRUBF | 72 | 69 | 64 | 60 | 57 | 3 | 0.572 | 0.279 | -0.238 | 4 / 4 / 4 / 0 |
| C_MTF | GLDRUBF | 76 | 71 | 62 | 43 | 37 | 9 | 0.587 | 0.552 | -0.522 | 1 / 5 / 0 / 6 |
| C_MTF | IMOEXF | 19 | 18 | 16 | 14 | 10 | 5 | 1.390 | 0.925 | -0.406 | 1 / 1 / 0 / 10 |
| D_MTF_IND | USDRUBF | 169 | 99 | 95 | 89 | 88 | 1 | 1.044 | 0.717 | -0.265 | 6 / 6 / 0 / 0 |
| D_MTF_IND | CNYRUBF | 72 | 46 | 45 | 42 | 39 | 3 | 0.629 | 0.268 | -0.188 | 4 / 4 / 4 / 0 |
| D_MTF_IND | GLDRUBF | 76 | 34 | 30 | 24 | 19 | 6 | 0.788 | 0.755 | -0.034 | 2 / 3 / 1 / 6 |
| D_MTF_IND | IMOEXF | 19 | 12 | 11 | 10 | 6 | 5 | 0.742 | 0.459 | -0.179 | 1 / 1 / 0 / 10 |

PF uses quote-unit P&L separately within each instrument; PF in normalized R is supplied too. Expectancy R weights each known closed trade by its own initial risk. Quote units across instruments are never summed into money/portfolio returns. Counts across architectures describe alternative experiments, not a pooled traded portfolio.

## UNKNOWN restart and factor contributions

| Architecture | Strict fills / closed / UNKNOWN | v1 daywise fills / closed / UNKNOWN | v2 daywise fills / closed / UNKNOWN | Strict-latched signals restored in v1 daywise |
|---|---:|---:|---:|---:|
| A_BASE | 28 / 24 / 4 | 262 / 246 / 20 | 262 / 246 / 20 | 304 |
| B_IND | 17 / 14 / 3 | 38 / 35 / 3 | 173 / 158 / 17 | 22 |
| C_MTF | 34 / 33 / 2 | 47 / 45 / 4 | 252 / 238 / 18 | 16 |
| D_MTF_IND | 4 / 4 / 0 | 4 / 4 / 0 | 165 / 152 / 15 | 0 |

Of 336 common reclaim signals, ATR readiness is 72 in v1 and 336 in v2; v2 sweep threshold passes 201. M15 vetoes 14 signals. D admits 191 filtered signals and has 165 fills. The sixteen source-level comparisons are in `three_models.csv`; the v1 strict/daywise change isolates the yearly UNKNOWN latch, while the v1/v2 daywise change isolates feature gates.

ATR and M15 effects are descriptive on the fixed 2023 sample. `architecture_comparison.csv` reports A→B, A→C, B→D and C→D for each instrument. Filtering consumes the first attempt; it never recycles episodes. Occupancy and within-day UNKNOWN can also change admitted membership. Read frequency, C2, normalized expectancy and concentration together with PF.

**ATR: reduces known losses in normalized R on this sample, without establishing a profitable factor.** A→B expectancy R improves on all four instruments, but three remain negative; GLD has only 20 known closes, +0.040 R expectancy but quote PF0.845. B has 173 fills versus A262 and every C2 quote PF is below1. ATR rejects135 of336 sweeps; unavailable-ATR rejects fall264→0. These are conditional in-sample improvements, not proof of robust economics.

**M15: no consistent economic improvement.** A→C reduces fills262→252. USD PF0.964→1.023 remains below the target with negative R expectancy; CNY R expectancy worsens, GLD PF and expectancy worsen, IMOEX known outcomes are unchanged. The new veto removes14 common signals versus the old277 direction/no-context rejections.

**Combination: no reliable synergy.** D has165 fills and152 known closes. Relative to B, USD improves slightly while GLD loses its small positive R expectancy, CNY R expectancy worsens, and IMOEX known outcomes stay unchanged. All four D expectancy R values are negative and C2 PF below1. There is no profitable Baseline to carry forward.

## Months and frequency

Every cell below is closed-only diagnostic Net R C1. `*` means that month has unresolved outcomes, `p` incomplete data, `—` no source coverage. Positive/negative/zero month counts in the first table use instrument-specific **Net quote P&L**, not the sum of normalized R; the two weight trades differently. Signs are descriptive known-cohort signs, even where a full monthly result remains unknown.

| Scenario | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A_BASE USDRUBF | -1.751p | -5.067p | -2.850* | -11.107p | -6.052p | -7.881p | -0.164p | -5.266p | -5.176p | -2.897 | 4.225p | 1.168 |
| A_BASE CNYRUBF | 0.000p | 0.000p | 0.333p | 0.000p | 0.000* | 1.000* | -1.583p | -2.419* | -4.886p | 2.137p | -6.115p | -1.967 |
| A_BASE GLDRUBF | — | — | — | — | — | — | -0.556* | -4.635* | -3.234* | -2.725* | -0.439* | -5.835p |
| A_BASE IMOEXF | — | — | — | — | — | — | — | — | — | — | -2.582* | -1.478* |
| B_IND USDRUBF | -0.832p | -4.000p | -3.179* | -9.571p | 0.648p | -7.800p | 1.336p | -4.789p | -3.010p | 1.172 | 4.323p | 0.435 |
| B_IND CNYRUBF | 0.000p | 0.000p | 0.333p | 0.000p | 0.000* | 1.000* | -0.333p | -2.419* | -4.886p | -0.482p | -0.253p | -0.227 |
| B_IND GLDRUBF | — | — | — | — | — | — | -0.556* | -0.555* | 0.000* | 1.404* | 2.556* | -2.047p |
| B_IND IMOEXF | — | — | — | — | — | — | — | — | — | — | -1.182* | 0.105* |
| C_MTF USDRUBF | -1.751p | -5.067p | -2.850* | -11.107p | -6.052p | -7.881p | -0.164p | -4.197p | -3.676p | -1.828 | 4.225p | -0.717 |
| C_MTF CNYRUBF | 0.000p | 0.000p | 0.333p | 0.000p | 0.000* | 1.000* | -1.583p | -1.086* | -4.886p | 2.137p | -6.115p | -3.356 |
| C_MTF GLDRUBF | — | — | — | — | — | — | -0.556* | -6.085* | -4.699* | -1.706* | -0.439* | -5.835p |
| C_MTF IMOEXF | — | — | — | — | — | — | — | — | — | — | -2.582* | -1.478* |
| D_MTF_IND USDRUBF | -0.832p | -4.000p | -3.179* | -9.571p | 0.648p | -7.800p | 1.336p | -3.720p | -1.510p | 1.172 | 4.323p | -0.165 |
| D_MTF_IND CNYRUBF | 0.000p | 0.000p | 0.333p | 0.000p | 0.000* | 1.000* | -0.333p | -1.086* | -4.886p | -0.482p | -0.253p | -1.616 |
| D_MTF_IND GLDRUBF | — | — | — | — | — | — | -0.556* | -2.005* | 0.000* | 1.404* | 2.556* | -2.047p |
| D_MTF_IND IMOEXF | — | — | — | — | — | — | — | — | — | — | -1.182* | 0.105* |

`monthly.csv` contains 192 rows, counts, C1/C2 Net/PF/expectancy, covered days and missing-bar classification. Positive share is positive / all source-covered months, including covered zero-trade months. `scenario_summary.csv` records frequency, no-entry days, positive share, win rate, realized reward/risk, worst trade, diagnostic drawdown and largest/top-three winning-P&L concentration. `direction_report.csv` separates LONG and SHORT for every scenario.

| Scenario | LONG / SHORT fills | C1 win rate | Net R | Diagnostic DD R | Worst R | Largest / top3 winner share | Positive covered months |
|---|---:|---:|---:|---:|---:|---:|---:|
| A_BASE USDRUBF | 60 / 78 | 0.438 | -42.819 | 53.675 | -3.000 | 0.045 / 0.126 | 0.583 |
| A_BASE CNYRUBF | 25 / 37 | 0.373 | -13.500 | 17.596 | -3.000 | 0.104 / 0.264 | 0.333 |
| A_BASE GLDRUBF | 19 / 28 | 0.375 | -17.425 | 18.732 | -3.000 | 0.282 / 0.459 | 0.333 |
| A_BASE IMOEXF | 10 / 5 | 0.400 | -4.060 | 6.060 | -3.000 | 0.596 / 0.947 | 0.500 |
| B_IND USDRUBF | 42 / 50 | 0.451 | -25.266 | 35.290 | -3.000 | 0.063 / 0.173 | 0.333 |
| B_IND CNYRUBF | 19 / 25 | 0.366 | -7.267 | 11.380 | -2.000 | 0.134 / 0.339 | 0.333 |
| B_IND GLDRUBF | 10 / 16 | 0.500 | 0.801 | 3.648 | -1.105 | 0.331 / 0.584 | 0.333 |
| B_IND IMOEXF | 7 / 4 | 0.500 | -1.077 | 3.077 | -1.400 | 0.696 / 1.000 | 0.500 |
| C_MTF USDRUBF | 60 / 75 | 0.440 | -41.066 | 50.037 | -3.000 | 0.046 / 0.129 | 0.583 |
| C_MTF CNYRUBF | 25 / 35 | 0.368 | -13.555 | 17.150 | -3.000 | 0.112 / 0.282 | 0.333 |
| C_MTF GLDRUBF | 16 / 27 | 0.351 | -19.321 | 20.628 | -3.000 | 0.320 / 0.522 | 0.167 |
| C_MTF IMOEXF | 9 / 5 | 0.400 | -4.060 | 6.060 | -3.000 | 0.596 / 0.947 | 0.500 |
| D_MTF_IND USDRUBF | 42 / 47 | 0.455 | -23.297 | 32.721 | -3.000 | 0.065 / 0.179 | 0.500 |
| D_MTF_IND CNYRUBF | 19 / 23 | 0.359 | -7.323 | 10.046 | -2.000 | 0.147 / 0.370 | 0.333 |
| D_MTF_IND GLDRUBF | 9 / 15 | 0.474 | -0.649 | 5.098 | -1.105 | 0.355 / 0.626 | 0.333 |
| D_MTF_IND IMOEXF | 6 / 4 | 0.500 | -1.077 | 3.077 | -1.400 | 0.696 / 1.000 | 0.500 |

## Stop and transaction-cost diagnosis

| Architecture | Stop band | Fills / closed / UNKNOWN | C1 Net R | C2 Net R | Mean modeled C1 / initial price risk |
|---|---|---:|---:|---:|---:|
| A_BASE | LE_2_TICKS | 23 / 23 / 0 | -50.500 | -86.500 | 1.565 |
| A_BASE | GT_2_LE_5_TICKS | 46 / 44 / 2 | -18.033 | -40.333 | 0.510 |
| A_BASE | GT_5_TICKS | 193 / 179 / 14 | -9.270 | -36.022 | 0.147 |
| B_IND | LE_2_TICKS | 12 / 12 / 0 | -26.000 | -43.000 | 1.417 |
| B_IND | GT_2_LE_5_TICKS | 28 / 26 / 2 | -3.433 | -16.200 | 0.498 |
| B_IND | GT_5_TICKS | 133 / 120 / 13 | -3.376 | -20.745 | 0.143 |
| C_MTF | LE_2_TICKS | 23 / 23 / 0 | -50.500 | -86.500 | 1.565 |
| C_MTF | GT_2_LE_5_TICKS | 45 / 43 / 2 | -16.533 | -38.333 | 0.510 |
| C_MTF | GT_5_TICKS | 184 / 172 / 12 | -10.969 | -37.243 | 0.151 |
| D_MTF_IND | LE_2_TICKS | 12 / 12 / 0 | -26.000 | -43.000 | 1.417 |
| D_MTF_IND | GT_2_LE_5_TICKS | 27 / 25 / 2 | -1.933 | -14.200 | 0.498 |
| D_MTF_IND | GT_5_TICKS | 126 / 115 / 11 | -4.413 | -21.152 | 0.144 |

`stop_risk_report.csv` separates all 48 instrument/architecture/band cases, including PF C1/C2 and expectancy. No minimum-Stop filter is added. C1 one tick per side and C2 two ticks per side replace costs on exactly the same fills. Cost/risk of one or more means costs can consume the entire gross risk before profit; the band evidence must be read with its sample count, not treated as a new optimized threshold.

In A, the23 known trades with Stop≤2 ticks have20 negative,2 zero and1 positive net C1 outcomes (aggregate −50.5 R; C2 −86.5 R). Their modeled C1 is at least1R and can exceed the 1.5R target for a one-tick risk. The >2–5 group has44 known closes and−18.033 R C1; the >5 group has179 known closes and−9.270 R C1. Small Stops are particularly harmful, but larger Stops also do not establish profitable aggregate diagnostics. Normalized R sums here are descriptive equal-risk statistics across instruments, not money or an actual portfolio curve. No filter is introduced from these observations.

## Coverage and independent audit

| Instrument | Source rows | Observed / expected days | Missing expected M5 | Before-inception trading days |
|---|---:|---:|---:|---:|
| CNYRUBF | 39362 | 253 / 254 | 1270 | 0 |
| GLDRUBF | 18428 | 124 / 124 | 932 | 130 |
| IMOEXF | 4429 | 34 / 34 | 566 | 220 |
| USDRUBF | 42576 | 253 / 254 | 187 | 0 |

`coverage_events.csv` distinguishes actual absent expected M5, invalid volume, planned intraday/calendar closures and pre-inception periods. Windows retain the frozen historical contract: 10:00–14:00 and 14:05–18:50 MSK, with 14:15 reopening March13–20. A gap in an expected slot is an observed source absence, not proof of its market cause. No synthetic OHLC or gap repair is used. USD/CNY start Jan3, GLD Jul11, IMOEX Nov14. Historical CNY tick is 0.01 before Sep27 19:00 MSK and 0.001 after, validated by original boundary tests and every real trade.

**Independent internal algorithm audit PASS**, 312134 gate/signal/trade field comparisons, 7980 A-control trade fields, 0 discrepancies; 320 independently reconciled economic cohorts and 960 monthly fields. The auditor uses a separate bounded source reader, backward OR/M15 reconstruction, prefix-sum ATR, independent gate selection and separate chronological trade state machine. It never calls production trade-outcome functions. `trade_source_map.csv` maps every modeled trade/UNKNOWN to source M5 row references, including absent slots. Original synthetic tests cover Stop-first, entry-bar Take suppression, gaps, outward targets, Time/Session Flat, execution clocks and UNKNOWN/NONFILL; added cases cover daily restart, ATR continuity, stale M15 and deliberate gate corruption. This is internal algorithm verification; external PR review remains pending.

Both readers verify fixed 2023 prefix bytes/SHA-256; 2024+ bytes read = 0. Validation records deterministic repetition, tests, protected blobs, data ref and remote heads. Annual strict Net/PF/DD are never filled with daily assumptions; all old v1 artifacts and TradingSystemLab remain unchanged.

Technical corrections in this retest: constrain daywise outputs to the new v2 directory; exclude each manifest from its own hashes so repeats are stable; preserve NO_OR/daily flags on physically absent whole dates; use actual covered bars in monthly coverage; report C2 and modeled cost/risk for Stop groups; enforce frozen v2 config bytes; independently reconstruct filter gates before trade audit. The first real run caught a forward-path reason-label error (GLD Aug1): a later signal was labelled UNKNOWN_POSITION_BLOCK before the future missing slot. The daywise wrapper now reports POSITION_BUSY until the gap is reached; this changes no fills or economics and leaves strict v1 unchanged. An adversarial regression case verifies it.

## Decision

**INCONCLUSIVE_UNRESOLVED — no economic Baseline PASS.** Daywise diagnostics can identify weak or promising in-sample cohorts but cannot establish uninterrupted full-year account economics with missing paths. The targeted PF≥1.6 also requires positive expectancy, enough independent trades, monthly regularity, acceptable concentration and C2 durability; a single high PF is insufficient. Stop at existing Draft PR #463, without merge, Stage3, Walk Forward, TRUE OOS or another strategy.
