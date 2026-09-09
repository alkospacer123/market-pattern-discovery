# MarketAI 20-cycle multi-horizon validation

## Gate result and validation status

The physical audit found that the production `_known` and `_unknown` handlers
are fixed-label placeholders. This should block production validation under the
task's “if and only if” rule. The bounded two-process exercise was nevertheless
completed before that defect was classified, so its results below validate the
loader, causal alignment, scheduler, and persistence mechanics only. They do
not establish that genuine KNOWN/UNKNOWN discovery is operational.

## Commands and pre-run semantics

The isolated directory was freshly created at
`/tmp/marketai_20_cycle_validation_001/` with empty `memory/`, `logs/`, and
`reports/` directories. Baseline counts were zero for attempts, knowledge,
effects, unique IDs, and coverage.

Inspection established that `--cycles` is the number of loop iterations in one
invocation. In every iteration, `--budget` is the maximum unseen cells planned.
The research space contains only 28 semantic cells. Budget 2 would request 40
attempts over 20 cycles and necessarily produce six empty cycles after
exhaustion. Therefore budget 1 was selected: expected growth was exactly one
attempt per cycle, 10 per process, and 20 cumulative. These expectations were
written to `/tmp/marketai_20_cycle_validation_001/reports/pre_run_expectations.txt`
before either process ran.

```text
python scripts/run_multihorizon_research.py \
  --data-root /workspace/market-pattern-data \
  --memory-root /tmp/marketai_20_cycle_validation_001/memory \
  --cycles 10 --budget 1
```

The command above was run twice as separate Python processes. Process B used
the exact same memory path after process A terminated.

## Real-data safety

The data root physically contained CNYRUBF and USDRUBF Finam CSVs for all six
configured timeframes. `MarketDataLoader.discover` selected 22 actual source
files (two quarterly files for each intraday timeframe and one archive for each
D1 symbol). Eligibility was enforced from `<DATE>` values. The logical interval
was 2026-01-01 through 2026-08-31 inclusive; the D1 2026-09-01 rows remained in
the read-only source and were excluded.

The before and after manifests each covered the same 22 files. Both manifest
files had SHA-256
`54e0ecd4e825c0cec3ba119599d1ddcb1b3e34b82545be7178a6757ee1db2672`,
and byte comparison exited 0.

## Process results

| Process | Cycles | Exit | Wall time | New attempts | Final attempts | New knowledge | Final knowledge |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 10 | 0 | 9.526161 s | 10 | 10 | 16 | 16 |
| B (restart) | 10 | 0 | 6.624553 s | 10 | 20 | 18 | 34 |

Every process result row reported `planned=1` and `recorded=1`.

## Analytical checkpoints

Checkpoints were derived from append ordering; no process restart occurred at
cycles 5 or 15.

| Cumulative cycle | Attempts | Knowledge records | Attempt growth vs expected |
|---:|---:|---:|---|
| 5 | 5 | 8 | 5 = 5 |
| 10 | 10 | 16 | 10 = 10 |
| 15 | 15 | 26 | 15 = 15 |
| 20 | 20 | 34 | 20 = 20 |

Knowledge grows by one record per configured context timeframe, hence it is not
expected to equal the attempt count.

## Final state and coverage

| Dimension | Counts |
|---|---|
| Attempts | 20 total; 20 unique attempt IDs; 20 unique cell IDs |
| Knowledge | 34 total; 34 unique knowledge IDs |
| Separately persisted effects | 0 (effects are transient; knowledge stores their IDs) |
| Conclusions | positive 34; negative 0; unresolved 0 |
| Tracks (attempts) | KNOWN 10; UNKNOWN 10 |
| Symbols (attempts) | CNY 11; Si 9 |
| Horizons (attempts) | Scalping 6; Intraday 8; Medium-term 6 |
| Primary timeframes | M1 3; M5 7; M15 1; M30 3; H1 3; D1 3 |
| Context timeframes | M15 6; H1 14; D1 14 |
| Evidence state | EVALUATED 20; failed 0 |

All six configured timeframes were represented as primary timeframes, as well
as all eligible context timeframes.

## Anti-172 audit

| Check | Result | Evidence |
|---|---|---|
| Empty cycles | PASS | All 20 cycles recorded one attempt against budget 1. |
| Memory growth | PASS | Attempts increased at every checkpoint; knowledge increased with every cell. |
| Restart | PASS | Process B retained 10/16 process-A rows and grew to 20/34. |
| Duplicate identity | PASS | Zero duplicate attempt, cell, or knowledge IDs. |
| Scheduler loop | PASS | 20 attempts used 20 distinct semantic cells. |
| Track starvation | PASS | KNOWN 10, UNKNOWN 10. |
| Symbol starvation | PASS | CNY 11, Si 9. |
| Horizon starvation | PASS | All three horizons represented. |
| Timeframe starvation | PASS | All six primary timeframes represented. |
| Fake knowledge | FAIL | References match persisted attempts/evaluation IDs, but the evaluations are created independently after fixed-label handlers that perform no discovery. |
| Causality | PASS | 699,212 available context rows replayed; zero close-time violations. |
| Source mutation | PASS | Before/after manifests are byte-identical. |

The mechanical anti-172 properties passed, but the mandatory fake-knowledge
check failed at the scientific execution boundary. A positive distribution is
not treated as proof of profitability and no parameter or profit-factor search
was performed.

## Final verdict

**NOT READY FOR 100-CYCLE RESEARCH**
