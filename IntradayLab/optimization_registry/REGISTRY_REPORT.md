# IntradayLab Master Strategy Registry

Base: f7a1ff5f12779a2b3dfbe5e4dbfe8f265096d3d8. Actual origin/main and merged PR #478 verified. Registry preparation only, 2026-10-11 Europe/Moscow.

**19 families; 247 published configuration/variant/reference records; 562 instrument/reference rows.** Types: 15 Baseline configurations, 66 execution variants, 6 diagnostic records and 160 historical references. Family definitions add 19 rows and contain no pooled trades. 74 qualifying configuration/instrument rows across 9 families; 488 nonqualifying rows. Historical rows with missing instrument attribution are separately counted.

All 490 remote branch heads were checked for an IntradayLab tree; 43 contain it. Metadata/bodies of 477 repository PRs were scanned, including all 42 IntradayLab-era PRs #437–#478. All 719 main IntradayLab files plus unique archived branch additions and referenced autonomous lineage were inspected/hash-recorded. RESEARCH_COVERAGE.csv classifies every result directory; SOURCE_FILE_INVENTORY.json pins 862 source objects.

| Instrument | Rows | ELIGIBLE | Excluded | Insufficient trades | Needs verification | Diagnostic |
| --- | --- | --- | --- | --- | --- | --- |
| USDRUBF | 105 | 36 | 69 | 41 | 22 | 6 |
| CNYRUBF | 230 | 24 | 206 | 53 | 147 | 6 |
| GLDRUBF | 105 | 14 | 91 | 63 | 22 | 6 |
| IMOEXF | 105 | 0 | 105 | 77 | 22 | 6 |
| NOT_AVAILABLE | 17 | 0 | 17 | 0 | 17 | 0 |

These counts describe saved research variants. They do not sum trades or imply independent samples. Every record uses the same 100 CLOSED / 40 days / 6 months gate. No historical PF filter. All failed requirements, including calendar failures, are listed alongside the primary status.

## Planning reference candidates

| Family / configuration | Instrument | CLOSED | Days | Months | C1 PF R | C1 PF price |
| --- | --- | --- | --- | --- | --- | --- |
| A / equal_high_low_m5_2023_a_v1 | CNYRUBF | 234 | 131 | 12 | 0.458 | 0.295 |
| A / equal_high_low_m5_2023_a_v1 | USDRUBF | 235 | 149 | 12 | 0.699 | 0.708 |
| B / high_low_cluster_m5_2023_b10_v1 | CNYRUBF | 164 | 92 | 12 | 0.396 | 0.361 |
| B / high_low_cluster_m5_2023_b4_v1 | CNYRUBF | 319 | 162 | 12 | 0.420 | 0.355 |
| B / high_low_cluster_m5_2023_b4_v1 | USDRUBF | 549 | 217 | 12 | 0.558 | 0.559 |
| B / high_low_cluster_m5_2023_b7_v1 | CNYRUBF | 217 | 115 | 12 | 0.465 | 0.462 |
| B / high_low_cluster_m5_2023_b7_v1 | USDRUBF | 123 | 86 | 12 | 0.487 | 0.462 |
| C / return_retest_rejection_m5_2023_c_v1 | USDRUBF | 102 | 82 | 12 | 0.626 | 0.642 |
| LEVEL_REJECTION / level_rejection_2023_m5_v1 | CNYRUBF | 213 | 99 | 11 | 0.789 | 0.715 |
| LEVEL_REJECTION / level_rejection_2023_m5_v1 | GLDRUBF | 128 | 70 | 6 | 0.645 | 0.656 |
| LEVEL_REJECTION / level_rejection_2023_m5_v1 | USDRUBF | 614 | 243 | 12 | 0.574 | 0.607 |
| R16 / r16_compression_breakout_2023_m5_v1 | CNYRUBF | 124 | 104 | 12 | 0.596 | 0.666 |
| R16 / r16_compression_breakout_2023_m5_v1 | USDRUBF | 246 | 178 | 12 | 0.689 | 0.834 |
| R17 / r17_orb_breakout_retest_2023_m5_v1 | CNYRUBF | 144 | 131 | 12 | 0.323 | 0.392 |
| R17 / r17_orb_breakout_retest_2023_m5_v1 | USDRUBF | 126 | 110 | 12 | 0.735 | 1.037 |
| R18 / orb_a_base_2023_canonical_v1 | USDRUBF | 137 | 119 | 12 | 0.582 | 0.964 |
| VWAP_MR / stage2_m5_conditional_v2_VWAP_MR | CNYRUBF | 345 | 174 | 12 | 0.108 | 0.083 |
| VWAP_MR / stage2_m5_conditional_v2_VWAP_MR | GLDRUBF | 114 | 77 | 6 | 0.870 | 0.784 |
| VWAP_MR / stage2_m5_conditional_v2_VWAP_MR | USDRUBF | 545 | 230 | 12 | 0.346 | 0.436 |
| MOMENTUM / stage2_m5_conditional_v2_MOMENTUM | CNYRUBF | 300 | 154 | 12 | 0.337 | 0.371 |
| MOMENTUM / stage2_m5_conditional_v2_MOMENTUM | GLDRUBF | 126 | 76 | 6 | 0.991 | 1.138 |
| MOMENTUM / stage2_m5_conditional_v2_MOMENTUM | USDRUBF | 594 | 238 | 12 | 0.662 | 0.759 |

These references are chosen by the original fixed Baseline/corrective provenance, not highest PF. All 74 eligible records appear in OPTIMIZATION_CANDIDATES.csv and OPTIMIZATION_QUEUE.md.

## Evidence boundaries and historical results

13 executable families have frozen results in main. Bollinger/RSI is a fourteenth IntradayLab family on Draft #472, with signal-logic NEEDS_FIX. Five additional autonomous lineage ideas are retained as historical-only families: session VWAP exhaustion/reclaim (R14), prior-day sweep/reclaim (R15), complex structural false break, Gerchik M5 proxy and ORB direct. R16/R17/R18 and Bollinger historical variants remain under their existing family IDs. External lineage is labeled distinctly; this is not evidence of a 2023 IntradayLab run.

All 141 retained positive CMD/V4 candidates are included: 16 R15, 27 R16, 43 R17, 38 R18 and 17 legacy V4. BASE/STRESS bps metrics are in historical_reported_metrics, with exact archived source and configuration hash. Original retention selected profitable candidates, so this archive has selection bias. R16 historical 126 trades / 81 days / BASE PF 1.498609 and R18 survivor 36 / 33 / 2.331313 are preserved, not promoted. No 2026 candles were opened; reported 2026 history is already viewed and is not independent OOS. The permitted future Optimization history remains only 2023.

Cycles 14–18 report 336 frozen grid candidates (48 + 4×72). Only 124 individual positive cycle rows are persisted; 212 unretained per-configuration results are absent from the published registry. R14 has a published aggregate zero executed entries, not 48 verified economic Baselines. The 142-ID V4 declaration describes a search universe, not proof that every declared configuration was actually researched; only 17 retained DEV-positive results are available in the historical summary. Do not fabricate missing IDs/results or claim full recovery of unsaved local CMD outputs. Runners/contracts are inspected as provenance, never executed.

PR #463 contributes strict-year v1, v1-daywise and corrected v2 ORB A_BASE/B_IND/C_MTF/D_MTF_IND variants. Their archived independent audits are recorded, and journal aggregates are checked, but separate historical configuration/source acceptance is still required (NEEDS_VERIFICATION). Its canonical A BASE on main is assessed independently under the same numerical gate. The type HISTORICAL_REFERENCE never asserts present technical acceptance. This evidence requirement is applied without using PF.

PR #472 remains unchanged at 82ec9ffe61e18a43cd7510e398f6913b25f045e1. Its 180 CLOSED / 7 UNKNOWN are recorded, including USD 128 / 112 CLOSED days / 12 months, but the strict RSI comparison defect keeps NEEDS_VERIFICATION despite sample size. Two disputed signals did not fill; that fact does not turn a known signal defect into PASS. PR #460 and #462 contain rules-only freezes, with no saved economic results; FAST0 is explicitly hypothetical. No result is invented for them.

The early native-M30 context was blocked by unavailable delivery/composition evidence. It is DIAGNOSTIC_ONLY. Later causal M15/M30/H1 contexts built from exact observed M5 children have their own 128 saved cohorts and full independent audit; they are executable model variants, not a new strategy each. Swing M5/M15 and Trend M15/H1 are separate tested families. Range Rotation, Opening Drive Pullback, Liquidity Sweep reserve and unrun Level Breakout Retest suggestions in the roadmap are ideas, not published independent Baselines. Production TradingSystemLab R3/T2/T3 strategies are outside IntradayLab and are not imported.

## Discrepancies and methodological comparability

2,143 published CLOSED/calendar/economic comparisons match; numerical differences below 1e-20 R are Decimal28 final-digit reporting tails. Aggregation uses stored amounts at Decimal50; monthly signs treat tails within 1e-20 R as reporting zero. This does not change any trade, price, cost, outcome or admission threshold. C audit 1.0’s -2E-26 pooled summation-order defect is already disclosed and audited in immutable revision 1.1; no pooled price PF is computed here.

CLOSED entry dates define days and active months. Calendar month signs use saved closure timestamps. Coverage days, fill days with only unresolved positions and pre-inception months cannot count toward this sample. For example, historical ORB v2 A_BASE USD reports 120 entry days including an unresolved fill; the registry has 119 CLOSED entry days. This is a different denominator, not a changed result. Conditional quote/R totals are not continuous equity, annual Net, account return or capital-sizing evidence.

MODELLED with an accounted resolved terminal path in the legacy journals maps to known CLOSED for this registry; UNRESOLVED stays historical UNKNOWN. Missing-entry UNKNOWN and filled unknown paths are distinct. Legacy no_bar_no_model_fill stays a nonfill/skip receipt; it is never relabeled CLOSED. C retains DATA_GAP_SKIP separately and accepted entries reconcile as CLOSED + DATA_QUALITY_EXCLUDED. Archived UNKNOWN are neither erased nor retroactively transformed into skip/exclusion. Absent/not-applicable values use NOT_AVAILABLE and field-specific reasons, including undefined PF with no losses and no-closure economics.

Exact repeated cohorts and overlapping architecture/delay/family opportunities are disclosed in OVERLAP_DISCLOSURE.md. The 74 ELIGIBLE rows are provenance-specific configuration/instrument records, not 74 independent data sets, and their trades are not summed. C2 replacement stresses retain saved values separately in COST_STRESS_REFERENCES.csv; 304 overlays do not increase configuration/trade sample counts.

Substantial unknown/excluded shares remain visible even for ELIGIBLE. CNY A and B include many unresolved outcomes; C CNY has 16/77 excluded entries (20.8%), and C IMOEX 2/5 (40%). C USD has 2/104 (1.9%). Selection bias and coverage restrictions prevent an annual-profitability claim. No arbitrary uncertainty/PF cutoff is added to the common gate.

## Exclusions and Optimization requirements

Every excluded configuration/instrument and all its failures are listed in EXCLUDED_CONFIGURATIONS.md and INSTRUMENT_ELIGIBILITY.csv. No instrument in Swing Pullback (maximum 50 CLOSED), Trend Pullback (maximum 70), Squeeze M5 or Squeeze M15 qualifies. GLD/IMOEX A/B/C and R16/R17/ORB sparse cohorts fail the count gate; GLD Level Rejection, VWAP and Momentum include qualifying cohorts. Historical external families without 2023 reproducible CLOSED journals require separate verification and do not enter the queue.

The queue is A, B, C, then Level Rejection, R16, R17, R18, VWAP and Momentum. Its order is a working order, never a ranking by historical PF. ELIGIBLE means only eligibility for separately authorized research Optimization. PF >= 2.0 after C1, positive expectancy, sufficient closed sample, regular positive monthly performance, controlled drawdown/concentration and neighboring-parameter stability are future goals, not claimed achievements. Use only available 2023 history. Potential tuning directions are family-specific in the registry. Before each individual task freeze grid, budget, concrete parameters, Take 2R–10R convention and candidate IDs; no grid search or chosen optimum appears here.

## Audit, reproduction and protected scope

REGISTRY_AUDIT.json is a separate algorithmic audit using an independent reader and float/fsum calculations, with no imports from build_registry.py or strategy/Backtester code. It verifies saved journal statistics, source/config hashes, equal eligibility criteria, missing-value explanations, coverage and protected diff. It relies on previously published signal/execution audits; it does not re-audit signals by reading candles. This is an internal computational audit, not a second human or second-agent signoff. Historical evidence gaps remain explicit despite registry PASS.

Run python IntradayLab/optimization_registry/build_registry.py and then python IntradayLab/optimization_registry/audit_registry.py from a checkout with the pinned Git objects. These commands read Git result/config/code objects and write only the registry. Fetch the refs named in DISCOVERY_SNAPSHOT.json if absent. They never open market-pattern-data, import trading models or run a replay. Hash and catalogue files make extraction paths/selectors inspectable.

Only additions under optimization_registry and current-status insertions in ROADMAP, PROJECT_CONTEXT and ARCHITECTURE_DECISION are changed. All old document sections, strategies, core, configs, frozen results, TradingSystemLab and the live robot are preserved. market-pattern-data remains read-only at f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8, with a clean Git status. Zero source candle files are opened, including zero 2024+ bytes. Draft #472 is not mutated. No Optimization, economic Baseline, Robustness, WF, TRUE OOS, merge or auto-merge. STOP after this Draft PR.


## Artifacts

- COST_STRESS_REFERENCES.csv
- DISCOVERY_SNAPSHOT.json
- EXCLUDED_CONFIGURATIONS.md
- INSTRUMENT_ELIGIBILITY.csv
- MASTER_STRATEGY_REGISTRY.csv
- OPTIMIZATION_CANDIDATES.csv
- OPTIMIZATION_POLICY.json
- OPTIMIZATION_QUEUE.md
- OVERLAP_DISCLOSURE.md
- PUBLISHED_METRIC_RECONCILIATION.json
- README.md
- REGISTRY_AUDIT.json
- REGISTRY_COUNTS.json
- REGISTRY_REPORT.md
- REPRODUCIBILITY.json
- RESEARCH_COVERAGE.csv
- SOURCE_FILE_INVENTORY.json
- STUDY_CATALOG.json
- audit_registry.py
- build_registry.py
