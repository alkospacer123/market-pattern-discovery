# A_v1 final validation note — reporting correction

**Trading signal/execution audit PASS. Final reproducibility/default-mode verification PASS using `verify_equal_high_low_baseline.py`.**

The first historical A_v1 P&L was run only after freeze commit `f880b3c4ac0fd2cb6d997d7680a1e427a2537340`. Config SHA-256 `cec9b815e1479d7999acf77442840d507eaa5f4e078573e0da4b9d34abc6521a` and all 26 pre-P&L dependency hashes remain unchanged, including the original validator. No trading parameters, signal grammar, Stop, Take, source budget, cost rule or Backtester were changed after results.

The pre-P&L validator's old-regression helper selected every internal field of the archived oracle. Some rejected canonical signal rows do not serialize those annotations: for `USDRUBF_2023-01-03_-1_1235`, internal oracle `window_end` is 2023-01-03 14:00 MSK while the saved rejected-row field is blank. The canonical economic files already matched byte-for-byte. The original frozen standalone validator therefore remains FAIL on this reporting-field comparison; it is not silently rewritten or claimed to pass.

A separate reporting-only verifier, added after P&L, selects the exact `signal_keys` / `trade_keys` published inside each unchanged original independent auditor. It also checks the original Swing/Trend context fields, raw-source signals, prices, CLOSED/UNKNOWN paths and CSV economics. It changes only the validator's helper references in memory and records its own SHA-256 in `validation.json`; no archived code, config or result is changed. It cannot select a different A_v1 outcome.

The completed verifier checks two repeats, each matching all 23 canonical deterministic artifacts byte-for-byte. Six default-mode replays match 93 stored economic/result files in total (canonical14, Level15, R16 14, R17 13, Swing16, Trend21), plus 8428226 original independent audit fields. New A_v1 independent audit checks 212520 fields. Full source-read guards cover exactly the four declared 2023 prefixes; no 2024+ price bytes. All 507 protected existing IntradayLab files and 3303 repository files outside IntradayLab remain unchanged; the five authorized existing-file edits are core Backtester/execution/README and ROADMAP/PROJECT_CONTEXT. market-pattern-data is clean on its pinned HEAD; Draft #472 head is unchanged.

Commands from repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 IntradayLab/tools/run_equal_high_low_baseline.py --data-root /workspace/market-pattern-data
PYTHONDONTWRITEBYTECODE=1 python3 IntradayLab/tools/audit_equal_high_low_baseline.py --data-root /workspace/market-pattern-data
PYTHONDONTWRITEBYTECODE=1 python3 IntradayLab/tools/verify_equal_high_low_baseline.py --data-root /workspace/market-pattern-data
```

476 tests passed before P&L (30 new). Algorithmic audit is an independent implementation by the task agent, not external human signoff. Coverage/outcomes remain INCONCLUSIVE. USD/CNY/IMOEX have negative conditional after-C1 expectancy; GLD has only nine known closures and ten UNKNOWN. Oracle is separate idealized diagnostics and cannot qualify PASS. No Optimization, next candidate, merge or LIVE.
