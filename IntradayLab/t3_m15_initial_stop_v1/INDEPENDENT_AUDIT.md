# Independent implementation audit

**Technical PASS — external reviewer audit PENDING.** GROSS_ONLY /
COSTS_DEFERRED / NOT_LIVE_READY. This is same-author algorithmic validation.
It does not establish independent reviewer approval or execution economics.

The auditor imports neither this experiment's engine/research/diagnostics nor
TradingSystemLab. It uses the frozen #490 auditor's separate timestamp-first
parser and recursive smoother, independently derives H1/ATR/ADX/EMA/Donchian,
and implements all four initial stops. Its position representation differs
from the main engine; extrema are reconstructed from historical slices.
It reproduces all 32 instrument-level paths (8 configuration replays × 4).

| Artifact family | Fields compared |
| --- | --- |
| CLOSED trades | 327120 |
| Signal/entry opportunities | 403400 |
| Every occupied-bar Stop decision | 1760157 |
| Terminal OPEN | 160 |
| Year-end OPEN snapshots | 168 |
| Overall/year/month/instrument/direction metric fields | 76144 |
| Risk quantiles, validity, lineage, new entries, gaps, narrow stops, equity, objectives | 207239 |
| Total | 2774388 |

Numeric absolute tolerance is 1e−8; observed maximum discrepancy is
5.4569682106375694e−12. Counts, identities, timestamps, booleans and reasons
match exactly. Full and historical-prefix SHA, pinned Git blob IDs and source
coverage endpoints are independently verified. Future OHLC parsing is false.

The pre-variant CONTROL gate compares every common non-cost field with both
#490 and #495 (21 and 39 fields per CLOSED respectively) and all shared OPEN
state fields: 1442 CLOSED + 2 terminal OPEN, zero differences. Historical C1/net
and pseudo-tick cost-unit diagnostics are explicitly excluded; dated exchange
tick geometry is separately calculated for this study.

The original gate mistakenly compared two absent timestamps as unequal. The
failed comparison is retained under preflight_history/. Before any variant
results, commit 82662ac1 corrected missing-value equality and added its regression
test. No execution rules, stops, parameters or data window changed. Initial
freeze f96194ee and the correction are retained, never amended away.

See AUDIT_RESULTS.json for all path counts and per-field maximum deltas;
TEST_RESULTS.txt and PRE_VARIANT_GATE.json for the 24-test pre-result gate.
REPEATABILITY.json records two full fresh-process byte repeats. Source data,
roadmap, frozen studies and TradingSystemLab remain unchanged; exact final
artifact hashes and file scope are supplied separately.
