# ORB_FALSE_BREAK_FADE_M5 — Stage 2 four architectures

**INCONCLUSIVE_UNRESOLVED — no economic Baseline PASS.** Complete fixed-rule 2023 replay finished; incomplete historical coverage and unresolved paths prevent full annual claims. No parameters changed after P&L.

Base main `9914ebbc97e3ba1fded1b6f06fb4bd66a82c2811`; pre-P&L freeze `8291f0efb7346b0bf4f01331caffd5eee7a242cc`. Fixed A BASE / B ATR14 / C completed M15 / D both; exactly16 C1 scenarios, C2 replacement on identical fills.

All PF/expectancy/month signs in the following table are **closed-only diagnostics**, not complete annual performance. Expectancy is normalized Net R per closed trade; raw quote units remain separate by instrument. Annual Net/PF/DD are null in every incomplete scenario. Intrabar outcomes have an interval, not an invented exact fill time.

| Architecture | Instrument | Fills / closed / unknown | C1 PF | C1 exp R | C2 PF | C2 exp R | + / − / 0 / uncovered months |
|---|---|---:|---:|---:|---:|---:|---|
| A_BASE | USDRUBF | 22 / 21 / 1 | 1.012 | -0.315 | 0.627 | -0.693 | 2 / 1 / 9 / 0 |
| A_BASE | CNYRUBF | 4 / 3 / 1 | null | 0.111 | 0.000 | -0.800 | 1 / 0 / 11 / 0 |
| A_BASE | GLDRUBF | 1 / 0 / 1 | null | null | null | null | 0 / 0 / 6 / 6 |
| A_BASE | IMOEXF | 1 / 0 / 1 | null | null | null | null | 0 / 0 / 2 / 10 |
| B_IND | USDRUBF | 5 / 4 / 1 | 0.786 | -0.804 | 0.450 | -1.289 | 1 / 1 / 10 / 0 |
| B_IND | CNYRUBF | 7 / 7 / 0 | 1.040 | 0.048 | 0.392 | -0.208 | 2 / 1 / 9 / 0 |
| B_IND | GLDRUBF | 3 / 2 / 1 | 0.763 | 0.211 | 0.718 | 0.173 | 1 / 1 / 4 / 6 |
| B_IND | IMOEXF | 2 / 1 / 1 | 0.000 | -1.222 | 0.000 | -1.444 | 0 / 1 / 1 / 10 |
| C_MTF | USDRUBF | 22 / 22 / 0 | 1.474 | -0.316 | 0.931 | -0.725 | 5 / 6 / 1 / 0 |
| C_MTF | CNYRUBF | 8 / 8 / 0 | 1.517 | 0.340 | 0.608 | 0.116 | 3 / 1 / 8 / 0 |
| C_MTF | GLDRUBF | 3 / 3 / 1 | 1.977 | -0.862 | 1.766 | -1.558 | 1 / 2 / 3 / 6 |
| C_MTF | IMOEXF | 1 / 0 / 1 | null | null | null | null | 0 / 0 / 2 / 10 |
| D_MTF_IND | USDRUBF | 4 / 4 / 0 | 0.750 | 0.041 | 0.429 | -0.100 | 1 / 2 / 9 / 0 |
| D_MTF_IND | CNYRUBF | 0 / 0 / 0 | null | null | null | null | 0 / 0 / 12 / 0 |
| D_MTF_IND | GLDRUBF | 0 / 0 / 0 | null | null | null | null | 0 / 0 / 6 / 6 |
| D_MTF_IND | IMOEXF | 0 / 0 / 0 | null | null | null | null | 0 / 0 / 2 / 10 |

Month signs describe known closed cohorts even when the monthly classification is UNKNOWN/PARTIAL_COVERAGE. `monthly_report.csv` contains all192 rows and full-null versus diagnostic fields. GLD starts July11, IMOEX November14; uncovered months are never zero-profit months. Unexpected halts/missing rows remain gaps; no synthetic prices.

PF above uses quote-unit P&L separately within each instrument. Expectancy R gives each trade equal initial-risk weight; differing initial risk can produce PF>1 with negative R expectancy. `metrics.json` also supplies PF in R, quote expectancy, win rate, average win/loss and realized reward/risk. No raw quote-unit portfolio is summed.

## Frequency, risk and concentration (closed-only diagnostic)

| Architecture | Instrument | LONG / SHORT fills | Fills / observed day | No-entry observed days | C1 Net R | C1 DD R | Worst R | Largest winner share |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A_BASE | USDRUBF | 10 / 12 | 0.087 | 236 / 253 | -6.625 | 10.718 | -2.000 | 0.241 |
| A_BASE | CNYRUBF | 2 / 2 | 0.016 | 250 / 253 | 0.333 | 0.000 | 0.000 | 1.000 |
| A_BASE | GLDRUBF | 0 / 1 | 0.008 | 123 / 124 | null | null | null | null |
| A_BASE | IMOEXF | 0 / 1 | 0.029 | 33 / 34 | null | null | null | null |
| B_IND | USDRUBF | 4 / 1 | 0.020 | 248 / 253 | -3.214 | 4.000 | -2.000 | 1.000 |
| B_IND | CNYRUBF | 5 / 2 | 0.028 | 247 / 253 | 0.339 | 1.467 | -1.222 | 0.500 |
| B_IND | GLDRUBF | 3 / 0 | 0.024 | 121 / 124 | 0.423 | 1.027 | -1.027 | 1.000 |
| B_IND | IMOEXF | 2 / 0 | 0.059 | 32 / 34 | -1.222 | 1.222 | -1.222 | null |
| C_MTF | USDRUBF | 11 / 11 | 0.087 | 233 / 253 | -6.945 | 9.404 | -3.000 | 0.243 |
| C_MTF | CNYRUBF | 1 / 7 | 0.032 | 245 / 253 | 2.719 | 1.000 | -1.000 | 0.455 |
| C_MTF | GLDRUBF | 2 / 1 | 0.024 | 121 / 124 | -2.587 | 4.053 | -3.000 | 1.000 |
| C_MTF | IMOEXF | 0 / 1 | 0.029 | 33 / 34 | null | null | null | null |
| D_MTF_IND | USDRUBF | 3 / 1 | 0.016 | 249 / 253 | 0.163 | 0.689 | -0.467 | 0.917 |
| D_MTF_IND | CNYRUBF | 0 / 0 | 0.000 | 253 / 253 | null | null | null | null |
| D_MTF_IND | GLDRUBF | 0 / 0 | 0.000 | 124 / 124 | null | null | null | null |
| D_MTF_IND | IMOEXF | 0 / 0 | 0.000 | 34 / 34 | null | null | null | null |

## Factor contribution (fixed architecture comparisons)

| Change | Instrument | Fills before → after | Diagnostic ΔNet R | Diagnostic PF before → after |
|---|---|---:|---:|---:|
| A_BASE->B_IND | USDRUBF | 22 → 5 | 3.411 | 1.012 → 0.786 |
| A_BASE->B_IND | CNYRUBF | 4 → 7 | 0.006 | null → 1.040 |
| A_BASE->B_IND | GLDRUBF | 1 → 3 | 0.423 | null → 0.763 |
| A_BASE->B_IND | IMOEXF | 1 → 2 | -1.222 | null → 0.000 |
| A_BASE->C_MTF | USDRUBF | 22 → 22 | -0.319 | 1.012 → 1.474 |
| A_BASE->C_MTF | CNYRUBF | 4 → 8 | 2.386 | null → 1.517 |
| A_BASE->C_MTF | GLDRUBF | 1 → 3 | -2.587 | null → 1.977 |
| A_BASE->C_MTF | IMOEXF | 1 → 1 | 0.000 | null → null |
| B_IND->D_MTF_IND | USDRUBF | 5 → 4 | 3.378 | 0.786 → 0.750 |
| B_IND->D_MTF_IND | CNYRUBF | 7 → 0 | -0.339 | 1.040 → null |
| B_IND->D_MTF_IND | GLDRUBF | 3 → 0 | -0.423 | 0.763 → null |
| B_IND->D_MTF_IND | IMOEXF | 2 → 0 | 1.222 | 0.000 → null |
| C_MTF->D_MTF_IND | USDRUBF | 22 → 4 | 7.108 | 1.474 → 0.750 |
| C_MTF->D_MTF_IND | CNYRUBF | 8 → 0 | -2.719 | 1.517 → null |
| C_MTF->D_MTF_IND | GLDRUBF | 3 → 0 | 2.587 | 1.977 → null |
| C_MTF->D_MTF_IND | IMOEXF | 1 → 0 | 0.000 | null → null |

ATR14 and M15 change admission to shared first-attempt episodes; rejected attempts are not recycled. Trade membership may also differ because occupancy/UNKNOWN blocking differs. D must be assessed against both individual factors, not selected for maximum PF. Filter attribution is descriptive 2023 evidence and is not causal proof of improvement or permission for optimization.

**ATR14: no demonstrated economic improvement.** Of 336 common reclaim signals,264 lack the frozen warmup and30 fail the sweep threshold. B has17 model fills across alternative instrument cases; its closed PF remains at or below1.040. This is severe attrition, not an accepted profitable factor.

**M15: no demonstrated stable improvement.** USD closed PF rises1.012→1.474, but R expectancy stays negative and C2 PF falls below1. CNY has8 closed trades, C1 PF1.517 and C2 PF0.608. GLD PF1.977 rests on3 closed trades, negative R expectancy and one winner supplying all winning P&L; full annual paths remain unresolved. These results do not establish the requested economic plateau.

**ATR14 + M15: primarily suppresses frequency.** D has only4 USD trades and zero fills on CNY/GLD/IMOEX. USD C1 PF0.750, C2 PF0.429; no accepted improvement versus A/B/C. No parameters, symbols or months are changed in response.

## Execution and limitations

Signal = reclaim close; one full subsequent M5 closes; submit and hypothetical exact boundary Open fill. Waiting-bar prices provide no extra confirmation. Stop is known history extreme plus/minus dated tick, TP1.5 gross R outward grid; no old T10/T15/FAST or 3R net rule. Resident Stop-first; entry-bar TP forbidden; adverse Stop gaps use worse Open; favorable Take gaps receive no improvement. Time=60 calendar minutes or B−5 Session Flat. Missing entry=UNKNOWN, missing exposure=UNKNOWN; fail-closed per architecture/instrument through end2023. Unknowns never become NONFILL/zero P&L.

The ledger contains84 scenario records:75 closed outcomes,8 unresolved filled exposures and1 unknown possible entry. Architectures are alternatives, so these counts are audit workload, not portfolio trade volume. Fail-closed blocking starts on USD March9 in A/B, CNY May26 in A, GLD July20 in A / November29 in B / October3 missing entry in C, IMOEX November15 in A/C and December29 in B. Later signals remain in the rejection ledger rather than invented executions. Coverage has187 /1270 /932 /566 missing approved-window bars for USD/CNY/GLD/IMOEX respectively. No coverage or gap repair was attempted.

CNY tick0.01 before 2023-09-27 19:00 MSK and0.001 thereafter. Strategy windows finish18:50, so the exact transition is validated synthetically; real post-switch fills use0.001. No M1 accessed. Both production and independent source readers read exact2023 prefixes and zero2024+ bytes.

## Audit and integrity

Independent algorithm audit: **PASS**, 141740 compared fields, 0 discrepancies. Raw-source backward features and chronological order/position oracle import no production strategy/outcome functions. Metric/month/coverage reconciliation saved separately. `trade_source_map.csv` references every accounted order/trade's OR, episode, waiting, entry and observed exposure source row, including absent rows, without copying raw candle data. Unknown detection timestamps are distinct from resolution; unknown outcomes have no resolved timestamp. External independent review is still pending.

Protected root trees and every existing main IntradayLab blob are compared unchanged in the manifest. New files only; source repository remains read-only. Frozen pre-P&L fingerprint and implementation SHA are in manifest. Deterministic repeated artifact hashes and synthetic/full IntradayLab tests are saved in validation artifacts.

## Decision

**INCONCLUSIVE_UNRESOLVED — economic Baseline is not established.** Every architecture lacks sufficient stable after-C1/C2 evidence; isolated high PF does not overcome tiny samples, negative R expectancy or UNKNOWN. The incomplete/unknown year prevents a conclusive full-year economic verdict, and closed-only diagnostics do not justify PASS. Historical Cycle18 selected2026 CNY M1 survivor is a different data/execution experiment and not verification here. Stop at one Draft PR: no merge, Stage3, next strategy,2024 WF,2025+ TRUE OOS or LIVE.
