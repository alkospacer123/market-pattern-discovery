# BBW CORE v1 Trade Management Reconstruction

This package is an isolated, read-only forensic layer over the current BBW
Baseline. It reconstructs the causal sequence:

`Range -> Breakout -> M15 Retest -> Confirmation -> Entry -> Structural Stop`

and reports the current implementation (**FACT**) beside `BBW_SPEC_v1.md`
(**EXPECTED**). It does not import Optimization, Candidate, Robustness, or the
execution engine, and it never feeds reconstructed values back into a strategy.

Run it with:

```bash
bbw-trade-management-audit \
  --feature-root <BBW-engine-output> \
  --normalized-root <normalized-data-root> \
  --output-root <new-audit-directory>
```

The output directory contains `RANGES.csv`, `BREAKOUTS.csv`, `RETESTS.csv`,
`ENTRIES.csv`, `SUMMARY.json`, and `REPORT.md`. Source files are hashed before
and after the run. Calendar year 2025 is rejected as locked TRUE OOS.

The audit's fixed conclusion for the current Baseline is **NON-CONFORMANT**:
the range/breakout/retest skeleton exists, but entry uses the confirmation
close rather than the next M15 open; the simulator does not move the stop at
+1R/+2R, reserve a single portfolio position, or apply costs and slippage.
