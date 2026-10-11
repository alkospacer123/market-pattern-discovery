# IntradayLab — Data Gap Skip / Backtester v2

**Technical implementation only. Draft PR, no merge. STOP after this task.**

Actual origin/main and task base: `4db30149d6c768caa82bd26a04ef80099816c815`.
PR #475 is MERGED with that merge SHA; PR #476 is MERGED at
`15c826cdf3c4fb9fa73e6f1ac9d247ac40e24dbf`. Independent Draft #472 stays OPEN,
draft, head `82ec9ffe61e18a43cd7510e398f6913b25f045e1`, untouched.
The final head SHA is in this task's PR description and chat; a file cannot
contain the SHA of its own containing commit.

## Explicit API and unchanged clocks

```python
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.data_quality import DATA_GAP_SKIP_V2
from IntradayLab.core.execution import ENTRY_NEXT_OPEN
from IntradayLab.core.reports import write_data_quality_reports

result = Backtester(
    rules, entry_mode=ENTRY_NEXT_OPEN, data_gap_policy=DATA_GAP_SKIP_V2,
    cost_ticks_per_side=1, allow_entry_bar_take=False,
).run(strategy, symbol, rows, start=start, end_exclusive=end)
write_data_quality_reports(new_output, result, {symbol: rows}, config, rules)
```

`LEGACY_UNKNOWN` remains the default; the legacy result is the original
`(signals, trades, days)` tuple. V2 is M5-only and returns `DataQualityResult`
with named `signals`, `trades`, `days`, `data_gap_skips` and
`data_quality_exclusions`. It requires no entry-bar Take. The reporting helper
accepts only a fresh directory under IntradayLab/work or IntradayLab/results.
Use the new reporting helper and `summarize_data_quality` with this result;
the old closed/UNKNOWN summarizer cannot account for a separate exclusion ledger.

The gap policy and entry clock are separate settings. `ENTRY_NEXT_OPEN` still
uses the immediate next M5 Open at the signal-close boundary. The default
`ENTRY_WAIT_ONE_BAR` still requires a whole waiting bar and the following Open;
a missing/invalid completed waiting bar keeps `NO_WAITING_BAR`, not a delayed
fill. No strategy or config enables v2 automatically. Frozen A/B/R16/R17 and
other signal rules, parameters, strategies and old UNKNOWN journals stay intact.

## Execution and accounting

Missing required entry M5 or nonfinite/nonpositive/off-grid Open:
`DATA_GAP_SKIP`, exact signal/attempt/detection time and reason, no fill, no
trade, no profit or loss, no roll to a later Open, no same-day latch. Future
signals can execute when observations permit. Missing completed signal inputs
still reach the unchanged strategy reset rules; no synthetic H/L/C is created.
Malformed ingestion schemas remain rejected by the unchanged pinned loader.

After a modeled fill, a missing/invalid exposed bar or exit Open produces
`DATA_QUALITY_EXCLUDED` in its own ledger. Retain instrument/signal ID, known
entry time/price, structural Stop, planned Take/risk, entry tick and known
one-side entry cost. Record gap interval, detection time and exclusion reason.
There is no exit price/time, resolved time, gross/net P&L or round-trip cost.
Completed invalid H/L/C is detected at its close; a missing/invalid required
Open is detected at that boundary. The known one-side cost is evidence of the
modeled entry, not an invented total economic outcome.

After exclusion, block new entries for the rest of the same day. Later
independent days retain `initial_flat_assumed=True`, `initial_flat_proven=False`
and `prior_exclusion_requires_flat_assumption=True`. This is an explicitly
conditional research reset, never evidence that the excluded real position
closed. A position resolved before a later missing interval stays CLOSED.

V2 exports:

- `trades.csv`: resolved CLOSED only.
- `signals.csv`: all strategy events, including skips and blocked signals.
- `data_gap_skips.csv`: skipped entry attempts.
- `data_quality_exclusions.csv`: known entries with unverifiable outcomes.
- `coverage_report.csv`: every declared research day/slot, complete/incomplete/
  pre-inception coverage, daily accepted/CLOSED/SKIP/EXCLUDED counts and FLAT evidence.
- `metrics.json`: per-instrument closed-only C1 economics, counts, exclusion
  fraction, coverage completeness and bias warning; pooled price economics and
  annual account returns/economics stay null.

`accepted_entries = CLOSED + DATA_QUALITY_EXCLUDED` is checked by signal IDs,
not just aggregate totals; no other accepted terminal states exist. Daily
coverage totals must match the ledgers. Each ledger forbids duplicate signal
IDs per instrument. Signals and skips intentionally cross-reference the same
event across two different ledgers. No ordinary trading status is UNKNOWN.

Stop-first, adverse Stop gaps at genuine Open, historical dated ticks, C1 one
tick per side, no entry-bar Take, session-flat, daily deadlines, trade windows
and development-date/no-future guards are unchanged. Incomplete or excluded
samples can bias PF; closed-only statistics never prove annual profitability
or a continuous broker equity curve.

## Synthetic examples and independent audit

All times below are MSK; all prices and M5 are synthetic.

| Event | Evidence | Result |
| --- | --- | --- |
| 2023-01-04 10:20 signal | Immediate 10:20 M5 absent | DATA_GAP_SKIP; no trade or later substitute |
| Same day 10:40 signal | Open 100.90, SHORT, Stop 101.02, Take 100.72 | Modeled entry exists |
| Same day 10:50 | Required M5 absent | Separate exclusion; entry retained; no exit/P&L |
| Same day 11:10 signal | Unresolved opened position | DATA_QUALITY_POSITION_BLOCK |
| 2023-01-05 10:20 signal | Independent conditional FLAT | CLOSED at known 11:20 Open 100.80; C1 0.02, net +0.08 |
| Same day 13:45 signal | Session-flat 13:55 Open 100.95 | CLOSED; C1 0.02, net -0.07 |

The example has **3 accepted entries = 2 CLOSED + 1 EXCLUDED**, plus **1 SKIP**;
exclusion share is **1/3**. The six CSV/JSON reports and synthetic inputs are
in [the example](../results/data_gap_skip_v2_technical_validation/synthetic_example).

**513 full unittest PASS**: all 496 archived tests plus 17 new tests. The stock
archived suite initially gave 495/496 PASS because one synthetic A_v1 audit
requires the historical core SHA. The new validator supplies actual current
core hashes in memory to that audit's synthetic config; every original test,
assertion, config and auditor file is preserved. This metadata exception is
explicit in [validation](../results/data_gap_skip_v2_technical_validation/new_mode_validation.json)
and [the full log](../results/data_gap_skip_v2_technical_validation/tests.log).

**12 independently audited synthetic cases, two byte-identical repeats each**:
combined accounting, missing entry, invalid Open, skip/recovery, missing
exposure, same-day blocking/next-day FLAT, Stop before gap, adverse Stop gap,
entry-bar Take prohibition, missing session-flat Open, invalid exposure and
invalid exposed Open. The separate raw-M5/CSV auditor imports only Python's
standard library; it reconstructs paths, costs/P&L/PF/DD, completeness and
counts without production loader, engine, calendar, strategy or metrics.
Corruption tests detect a forged PF, removed exclusion and false coverage count.
This is implementation independence by the task agent, not external human signoff.

## Byte regressions of every previous Baseline

**18 unchanged approved batches; 252 deterministic result files byte-identical.**
All ten common-core candidates also passed their unchanged independent signal/path/economics auditors.

| Archived batch | Byte-identical result files | Result |
| --- | ---: | --- |
| b10 | 19 | PASS |
| b4 | 19 | PASS |
| b7 | 19 | PASS |
| canonical | 14 | PASS |
| equal_high_low | 21 | PASS |
| level_rejection | 15 | PASS |
| r16 | 14 | PASS |
| r17 | 13 | PASS |
| stage2_causal_mtf_v1 | 10 | PASS |
| stage2_complete_architectures_v1 | 10 | PASS |
| stage2_exit_only_ablation_v1 | 7 | PASS |
| stage2_m5 | 7 | PASS |
| stage2_m5_conditional_v2 | 12 | PASS |
| stage2_squeeze_m15_v1 | 15 | PASS |
| stage2_squeeze_v1 | 11 | PASS |
| stage2_vwap_payable_cap_v1 | 9 | PASS |
| swing_pullback | 16 | PASS |
| trend_pullback | 21 | PASS |

Full hashes, actual read receipts, replay metadata exceptions and no-overwrite evidence:
[regression_receipts.json](../results/data_gap_skip_v2_technical_validation/regression_receipts.json).
The standalone MTF README pin predates main; README was verified equal to this task base.
Its initial comparator used gzip OS=3 instead of the original GzipFile OS=255.
Rechecking completed outputs with the original deterministic container gave exact archive equality; no trading code or output was altered.
The runtime guard enforced 2023 limits; for this batch loader provenance equality is retained, while transient guard receipts were lost at the initial comparison failure. This limit is disclosed in its receipt.

## Reproduction and protected scope

```bash
python -m IntradayLab.tools.validate_data_gap_v2 --output IntradayLab/work/fresh_gap_tests
python -m IntradayLab.tools.verify_data_gap_v2_regressions \
  --data-root /workspace/market-pattern-data --output IntradayLab/work/fresh_gap_regressions
python -m IntradayLab.tools.verify_data_gap_v2_earlier \
  --data-root /workspace/market-pattern-data --output IntradayLab/work/fresh_earlier_regressions
```

These are isolated compatibility checks of approved frozen configurations,
not new economic studies or parameter selection. Historical runners pin old
core identities, so the explicit replay adapter supplies current identities
only in memory, verifies frozen non-core dependencies against the task base,
and documents previously merged identity changes. Two early fixed-output
runners redirect only their destination to scratch. No old published file is
overwritten; no raw source is copied into this repository.

Only approved pinned source `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, exact
2023 M5 prefixes. Actual read guards enforce the byte budgets for both new
prefix and old FileIO/line-budget readers. **Zero 2024+ / 2025+ market bytes
read.** Fetching the old ORB `9c65d03` Git object restored a missing published
2023 reference artifact; it changed no checkout/source file.

All changes are in IntradayLab. TradingSystemLab, its live robot, brokerage
settings/capital, outside project paths, source checkout and Draft #472 are
unchanged. Frozen strategy/config/result/test/audit/runner files are preserved.
Full changed-file inventory, hashes and regression receipts are in the
technical validation directory. **No v2 historical strategy Baseline, model C,
Optimization, Robustness, WF, TRUE OOS, LIVE or merge ran.**
