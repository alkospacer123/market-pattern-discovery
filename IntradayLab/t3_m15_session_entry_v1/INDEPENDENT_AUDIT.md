# Computational audit protocol

The second implementation uses Python standard library only: independent
boundary-first byte parser, recursive EMA/Wilder features, causal H1 alignment,
separate T1/T2 predicates and slice-reconstructed extrema instead of the primary
mutable running extrema. It imports no experiment engine or report implementation.

It compares every field of all CLOSED trades, terminal OPEN, period-end OPEN,
entry decisions, Stop decisions and gap logs. It recomputes PF, R, expectancy,
monthly coverage/share, DD, loss streaks, winner concentration, signal partitions,
T1 hours, T2 gap reasons, duration/frequency/night-gap exposure, winner lineage,
new trades/losses, subsequent chronology and November diagnostics. Numeric absolute
tolerance 1e-8; timestamps, counts, flags and strings exact. SHA checks separate.

Two fresh process runs independently regenerate all six full replays and reports;
all generated outputs, including their hash manifest, are compared byte by byte.
Audit status and field totals are recorded in AUDIT_RESULTS.json; repeats in
REPEATABILITY.json. The overall artifact SHA manifest is ARTIFACT_SHA256.json.

This is algorithmic independence by the same author. External reviewer audit is
PENDING, and no acceptance or next stage is authorized. GROSS_ONLY /
COSTS_DEFERRED / NOT_LIVE_READY. STOP at one Draft PR without Merge/Auto-Merge.
