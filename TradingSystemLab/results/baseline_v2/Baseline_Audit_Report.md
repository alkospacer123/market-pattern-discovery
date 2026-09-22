# TradingSystemLab v2 — Phase 1 Baseline Audit

## Verdict

**PHASE_1_BASELINE_COMPLETE**

The 24-run development-only C1 baseline was rebuilt from the original H1
methodology. T2 and T3 use their canonical constructor defaults. T3 uses causal,
non-overlapping four-execution-bar context that resets at each local trading-day
boundary; this intrinsic strategy context is not Phase 7 MTF research.

`normalized_research_tick_size = 0.001` is the frozen H1 research cost unit for
all instruments, not an exchange tick-size claim. Broker and economic cost audit
work remains outside Phase 1.

## Audit checks

- PASS: exactly 24 unique T2/T3 × instrument × timeframe runs and all five required files.
- PASS: frozen strategy hashes and original baseline parameter manifests.
- PASS: development-prefix provenance, actual data bounds, zero duplicate input timestamps, and no 2025+ input/trades.
- PASS: C1 only; no optimization, ranking, selection, walk-forward, or Phase 7 MTF research.
- PASS: unique trade IDs, valid LONG/SHORT directions, and entry time not after exit time.
- PASS: trades count, PF, expectancy, Net R, Max DD, and Win Rate independently recalculated from every trades.csv and matched metrics.json.
- PASS: all 24 result rows matched Baseline_Report.md.
- PASS: two consecutive runner executions produced byte-identical canonical artifacts (verified before this report was generated).

## Run-level reconciliation

| Strategy | Instrument | Timeframe | Trades | PF | Expectancy R | Net R | Max DD R | Win Rate | Audit |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| T2 | Si | M30 | 269 | 1.1527 | 0.0733245 | 19.7243 | -25.6555 | 0.330855 | PASS |
| T2 | Si | H1 | 126 | 2.0415 | 0.420567 | 52.9914 | -6.77017 | 0.420635 | PASS |
| T2 | CNY | M30 | 138 | 1.21047 | 0.0998732 | 13.7825 | -19.4574 | 0.304348 | PASS |
| T2 | CNY | H1 | 54 | 3.84079 | 1.18711 | 64.1038 | -6.3696 | 0.425926 | PASS |
| T2 | GD | M30 | 218 | 0.906142 | -0.0447276 | -9.75062 | -20.2573 | 0.334862 | PASS |
| T2 | GD | H1 | 114 | 1.27821 | 0.134595 | 15.3438 | -17.3024 | 0.342105 | PASS |
| T2 | BR | M30 | 257 | 1.30391 | 0.144625 | 37.1686 | -14.9602 | 0.36965 | PASS |
| T2 | BR | H1 | 129 | 1.36745 | 0.162285 | 20.9347 | -7.56892 | 0.372093 | PASS |
| T2 | MIX | M30 | 299 | 1.33834 | 0.159784 | 47.7754 | -17.2305 | 0.354515 | PASS |
| T2 | MIX | H1 | 154 | 0.89128 | -0.0518645 | -7.98713 | -24.3792 | 0.305195 | PASS |
| T2 | NG | M30 | 257 | 1.59319 | 0.275486 | 70.7999 | -11.1488 | 0.381323 | PASS |
| T2 | NG | H1 | 130 | 1.85768 | 0.376782 | 48.9816 | -5.60536 | 0.4 | PASS |
| T3 | Si | M30 | 276 | 1.65967 | 0.288079 | 79.5099 | -19.5072 | 0.42029 | PASS |
| T3 | Si | H1 | 148 | 1.78672 | 0.301795 | 44.6657 | -5.89342 | 0.405405 | PASS |
| T3 | CNY | M30 | 148 | 1.70182 | 0.31635 | 46.8198 | -9.53984 | 0.425676 | PASS |
| T3 | CNY | H1 | 69 | 2.55541 | 0.597587 | 41.2335 | -4.32233 | 0.463768 | PASS |
| T3 | GD | M30 | 272 | 1.06824 | 0.0313847 | 8.53663 | -15.7364 | 0.356618 | PASS |
| T3 | GD | H1 | 114 | 1.67855 | 0.292574 | 33.3534 | -8.38364 | 0.429825 | PASS |
| T3 | BR | M30 | 285 | 0.993404 | -0.00323144 | -0.920961 | -21.146 | 0.357895 | PASS |
| T3 | BR | H1 | 131 | 1.06831 | 0.0319933 | 4.19113 | -23.9022 | 0.381679 | PASS |
| T3 | MIX | M30 | 285 | 1.43271 | 0.183129 | 52.1917 | -9.92938 | 0.414035 | PASS |
| T3 | MIX | H1 | 144 | 1.21106 | 0.0947256 | 13.6405 | -13.6039 | 0.409722 | PASS |
| T3 | NG | M30 | 297 | 1.57377 | 0.240529 | 71.437 | -7.11119 | 0.441077 | PASS |
| T3 | NG | H1 | 135 | 1.23156 | 0.107159 | 14.4664 | -7.49591 | 0.377778 | PASS |

Total audited trades: **4449**.

## Separate historical integrity issue

The old `true_oos_validation` tree-hash mismatch reported by
`TradingSystemLab/tests/test_execution_spec_audit.py` is unrelated to this Phase 1
rebuild. Historical TRUE OOS files and their expected hash were not modified.
