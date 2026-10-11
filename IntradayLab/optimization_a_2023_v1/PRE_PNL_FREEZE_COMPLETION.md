# Complete pre-P&L freeze v2 — publication correction only

Initial publication `76692d0bd89af2501ea04b52c0792b25cd7cab18` was incomplete:
the repository's existing global `*.csv` ignore rule omitted GRID.csv.
The freeze guard failed while checking committed dependencies, before opening
any candle source or evaluating historical P&L. No real-data run occurred.

GRID.csv is explicitly force-added in the complete freeze v2 commit. The
guard obtains the latest source_commitments.json commit and verifies every
dependency against that exact complete tree. Trailing whitespace is removed
from the new auditor before historical execution. No parameter, criterion,
signal, execution or economic formula is changed. Synthetic tests are rerun
before complete freeze publication. Initial history is preserved.

The complete freeze SHA is recorded in every result's freeze_manifest.json.
All 144 evaluations, both full repeats and independent audit start only after
this complete freeze v2 is committed, pushed and verified. This correction
does not involve historical P&L or a selected subset of the grid.
