# Independent audit — BOLLINGER_RSI_REENTRY_M15

**Overall signal-logic verdict: NEEDS_FIX. No technical signal-logic PASS is claimed.**

**PASS** for exact frozen numeric-program conformance, actual prices/Stop/Take/C1, all CLOSED and UNKNOWN, economic metrics, all 12 months, directions and coverage. Checked 345440 formation fields, 1275918 signal/ledger fields, 6480 coverage fields, 221 instrument metric fields, 4824 report/day fields, and 8409 mathematical-oracle trade fields.

The independent weighted80 oracle itself had tiny strict-comparison drift on flat Close. This post-P&L reporting verifier cancels the shared decay before the RSI ratio and independently reconstructs Decimal28 from raw prefixes to check the frozen numeric program. No production strategy/indicator/Backtester/metric imports are used for these oracles. Indicator tolerance remains the predeclared absolute 1e-22; discrete decisions and trade prices/accounting are exact.

**Unresolved defect in the frozen strategy:** roundoff in the strict RSI comparison can create a formal signal with identical B/C Close. Mathematically Wilder RSI is unchanged on a zero price change.

- `USDRUBF_2023-03-16_1800`: frozen SIGNAL, mathematical NO_RSI_IMPROVEMENT; REJECTED / TRADE_DEADLINE. B/C Close=76.87; RSI 74.43901149162470461788723299 → 74.43901149162470461788723298.
- `CNYRUBF_2023-08-14_1100`: frozen SIGNAL, mathematical NO_RSI_IMPROVEMENT; NONFILL / RISK_BELOW_FOUR_TICKS. B/C Close=13.9; RSI 87.72075370164252626441372009 → 87.72075370164252626441372008.

Neither discrepancy produced a model fill. The common-factor-free mathematical oracle yields exactly the same filled trade IDs, every CLOSED/UNKNOWN, prices, C1 and P&L. The mathematical funnel is diagnostic only and does not replace canonical signals/pending/orders. Both frozen spurious signals remain in signals.csv and in the canonical reported funnel.

Frozen strategy, indicators, parameters, runner, original auditor and common core are byte unchanged since the pre-P&L commit. No corrected strategy or second economic Baseline was run. The original frozen audit entrypoint still fails on its own numerical discrepancy; use the final verify tool for complete factual auditing and this honest NEEDS_FIX verdict. A separate future decision is required to repair/retest.

Pinned source/byte hashes and observed unbuffered reads prove zero 2024+ price bytes. UNKNOWN has no assigned P&L; annual economics are INCONCLUSIVE and all four instruments have negative conditional known-close expectancy (NO ECONOMIC BASELINE PASS). No cross-instrument monetary pooling. Validation receipts cover 496 pre-P&L tests, two deterministic repeats, six old Baseline regressions and preservation of all 512 existing files. Independent implementation verification is not external human signoff.
