# T3 H1 / M15 PARTIAL_TP_2R_50 — audit only

Start with [PROTOCOL_RU.md](PROTOCOL_RU.md), then [REPORT_RU.md](REPORT_RU.md).
No production imports with broker side effects, no API/trading operations.
The preliminary target-price gap credits were superseded after a feasible-price
audit. See EXECUTION_CORRECTION.json and the protocol's explicit correction.
Final resting-limit fills use observed Open on favorable gaps; the scalar audit
checks every new TP fill against the candle range and price grid.
Python 3.11+, pandas 2.2.3, numpy 2.3.5; no other third-party dependencies.

Use two read-only data checkouts. H1 must be at
`50f1fd2178c18b7ab3bd969be82ad01f47a34745`, M15 at
`f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Keep source history and
PR #540's exact commit recorded in SOURCE_MANIFEST.json. Never copy raw market
data into this repo. The initial GitHub main was
`38489db7e69336548a583f968f13aab49c20913b`; exact immutable source hashes are
checked before each fresh run. Source feature functions are reused read-only;
position execution and scalar audit are separately written here.

```bash
PYTHONDONTWRITEBYTECODE=1 python audit_only/t3_h1_m15_partial_tp_2r_50/test_synthetic.py
PYTHONDONTWRITEBYTECODE=1 python audit_only/t3_h1_m15_partial_tp_2r_50/run.py --h1-data /workspace/work/t3-h1-data --m15-data /workspace/market-pattern-data --output /workspace/work/t3-partial-fresh
PYTHONDONTWRITEBYTECODE=1 python audit_only/t3_h1_m15_partial_tp_2r_50/repeat.py --h1-data /workspace/work/t3-h1-data --m15-data /workspace/market-pattern-data --scratch /workspace/work/t3-partial-repeats
```

All output directories must be fresh. `repeat.py` runs the entire raw replay
three times in separate processes. It compares every output by direct bytes and
SHA256 and writes REPEATABILITY.json. Committed CODE_FREEZE.json authenticates
the final source used for these runs. SHA256SUMS covers all study files except
itself. Git anchors the protocol, source gates, implementation and publication.

CSV schemas:

- TRADES: one row per original position and variant; two explicit .5 legs,
  fills, gross R, normalized H1 C1 costs, initial immutable risk and residual.
- MONTHLY: long form CONTROL/PARTIAL; each H1 lifecycle/fold is separate;
  FRACTIONAL_REFERENCE rows contain R, EXECUTABLE_INTEGER rows contain unknowns.
- SUMMARY: gross R/PF and calendar statistics; H1 disjoint baseline+OOS summary
  excludes WF. Gross and normalized C1 are not real monetary Net.
- FEASIBILITY: each potential executable entry has unknown qty/margin where
  historical authority is missing, not a fabricated zero or model contract.
- TRACE/SIGNALS/MARKS gzip: derived event states/observed-close R marks, no raw
  source OHLCV. OPEN_BOUNDARIES retains terminal open positions of cold-start
  studies. MONTH_SIGN_TRANSITIONS, EXPOSURE and WINNER_GIVEBACK are diagnostic.

FRACTIONAL audit can PASS while CASH_MODEL_NOT_VALIDATED and INCONCLUSIVE remain.
One Draft PR, external audit pending, no merge/auto-merge/LIVE.
