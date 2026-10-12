# Calculation and repeatability audit

**PASS for implementation checks; external reviewer audit PENDING.**

- Independent standard-library original replay: 1 442/1 442 closed trades, both frozen versions/four instruments; two terminal positions preserved without liquidation.
- Independent causal Stop recurrence: all 28 541 trajectory rows, including exit-at-open/gap handling, next-bar activation, ratchet, ATR contraction, signed SHORT and recorded/possible favorable bounds.
- Preentry features: 23 104 values checked using independently reconstructed daily ordinal H1, recursive EMA/Wilder ADX/ATR and prior Donchian. Availability timestamps checked exactly.
- First candles: 4 332 available horizon records (including the open-position diagnostics), fixed horizons and exposure censoring; 324 summary rows reconciled.
- Aggregations: 1 697 rows independently reconciled for instrument/year/month/direction/holding/carry/Stop/outcome, including all requested PF, Gross/Net/C1 R, closed-trade DD, MAE/MFE, positive-winner concentration and cost budgets.
- Original fixed-version comparison: 701 common entry pairs checked, no alternate exits simulated.
- Maximum numeric difference 4.73e-11; absolute tolerance 1e-8 for every numeric check, exact keys, booleans and timestamps. Detailed maxima in AUDIT_RESULTS.json.
- Six hand-calculated and causality checks PASS. The future-mutation test changes only synthetic 2023 bars; no actual TRUE OOS data is read.
- Two fresh process chains independently rerun diagnose.py → render_report.py → verify.py. All 25 generated CSV/JSON/report/SVG artifacts, hash manifests and audit outputs are byte-identical to each other and to the submitted outputs. See REPEATABILITY.json.
- All 29 completed Baseline files match the actual-main Git blobs. Data worktree is clean at the mandatory data commit; actual GitHub main refs rechecked. No existing discovery files changed. See SCOPE_CHECK.json.

The verifier does not import diagnose.py, pandas or numpy; it uses separate standard-library formulas and the already independently implemented PR #490 parser/indicator oracle. This establishes implementation independence, **not a separate human author or external auditor**. Trade classification and future movement remain retrospective; checks do not establish causal benefits of any proposed trading change or complete funding economics.
