# BBW Baseline R1 execution report

**Status: BLOCKED — the prepared market-data artifacts are not mounted in the
execution environment.**

## Scope

This was an execution-only attempt for `CNYRUBF`. No strategy code, baseline
configuration, parameter, filter, indicator, or input market-data file was
changed. Optimization and Robustness were not performed.

The intended Windows command, using the repository-documented artifact layout,
is:

```powershell
python -m bbw_system.baseline_cli `
  --symbol CNYRUBF `
  --feature-root C:\BBW\results\bbw_engine\R1 `
  --normalized-root C:\BBW\data\normalized `
  --output-root C:\BBW\results\baseline\R1
```

In the Linux execution environment, `C:\BBW` would normally be visible below
`/mnt/c/BBW`. Preflight checked these paths:

| Artifact | Expected Linux path | Result |
|---|---|---|
| BBW Engine feature root | `/mnt/c/BBW/results/bbw_engine/R1` | MISSING |
| normalized CNYRUBF root | `/mnt/c/BBW/data/normalized` | MISSING |
| new Baseline output root | `/mnt/c/BBW/results/baseline/R1` | MISSING |

A full-filesystem search also found no `NORMALIZED_MANIFEST.json`,
`CNYRUBF_H1_BBW_FEATURES.csv`, or `BBW_MANIFEST.json`. The repository status was
clean before both attempts (`## work`). Source market data was neither found nor
read, and was not copied into the repository.

## Execution attempts

The CLI was invoked twice with the same arguments:

```bash
PYTHONPATH=src python -m bbw_system.baseline_cli \
  --symbol CNYRUBF \
  --feature-root /mnt/c/BBW/results/bbw_engine/R1 \
  --normalized-root /mnt/c/BBW/data/normalized \
  --output-root /mnt/c/BBW/results/baseline/R1
```

Both attempts failed closed with exit code `2` and the identical diagnostic:

```text
Baseline failed closed: CNYRUBF_H1_BBW_FEATURES.csv not found under /mnt/c/BBW/results/bbw_engine/R1
```

This identical failure is not a successful determinism result. Because input
artifacts were absent, the CLI could not verify the normalized M15 manifest
hash, read features, generate trades, or write the requested output files.

## Requested results

| Item | Result |
|---|---|
| Result path | `C:\BBW\results\baseline\R1` (not created) |
| `BASELINE_TRADES.csv` | Not produced |
| `BASELINE_REPORT.md` | Not produced |
| Test period | Unavailable |
| Trades | Unavailable (not zero; run did not execute) |
| LONG / SHORT | Unavailable |
| Win rate | Unavailable |
| Mean R | Unavailable |
| Profit factor | Unavailable |
| Maximum losing streak | Unavailable |
| Mean trade duration | Unavailable |
| Result SHA-256 | Unavailable |
| Successful-run determinism | Not established |
| Ready for Robustness | **NO** |

An absent result is deliberately not reported as a zero-trade baseline.
Robustness must not begin until the artifacts are mounted, their manifest hashes
pass, the baseline succeeds twice, and both `BASELINE_TRADES.csv` SHA-256 values
are identical.

## Implementation and safety checks

The existing baseline implementation was inspected without modification. It:

- converts START-labelled H1 and M15 timestamps to their respective close times
  before events and signals become actionable;
- excludes the possible breakout candle from range construction and prevents a
  range from crossing a calendar-day boundary;
- rejects any input containing locked TRUE OOS year 2025;
- verifies normalized M15 against `NORMALIZED_MANIFEST.json` before reading it;
- hashes feature and M15 inputs before execution and fails if either changes;
- serializes trades deterministically and reports the SHA-256 of the exact CSV
  payload; and
- applies deterministic stop-first resolution to same-bar ambiguity.

The focused baseline test suite passed (`7 passed`). This validates the engine's
fixture-level causal and deterministic behavior, but it does not substitute for
the requested R1 run on the missing prepared artifacts.

## Unblock condition

Mount the existing, read-only `C:\BBW` artifact tree at `/mnt/c/BBW` (or supply
the actual accessible feature and normalized roots). Do not regenerate, modify,
or copy market-data inputs merely to bypass this preflight. Then run the command
twice and compare both the emitted JSON `sha256` field and an independent
`sha256sum` of `BASELINE_TRADES.csv`.
