# Current Artifact Storage Status

Inspection time: 2026-09-11 (UTC). No pipeline, research cycle, smoke run,
backtest, validation, strategy generation, market-data access, or TRUE OOS 2025
access was performed.

## Requested locations before the synthetic test

| Location | Exists | Apparent size | Files | Readable |
|---|---:|---:|---:|---:|
| `/workspace/market-pattern-artifacts/` | no | n/a | 0 | n/a |
| `/workspace/autonomous_runs/` | no | n/a | 0 | n/a |
| `/tmp/marketai_executable_signal_smoke_001` | no | n/a | 0 | n/a |

The three requested locations contained no artifact bundles at inspection time.
Consequently, none of `manifest.json`, `source_commit.txt`,
`data_manifest.sha256`, `backtest_results.jsonl`,
`strategy_candidates.jsonl`, `validation_reports.jsonl`,
`strategy_rankings.jsonl`, or `executable_signal_definitions.jsonl` was found
under them. The absent smoke bundle documented elsewhere in this repository was
therefore not available for forensic audit.

## Implementation finding

The configured default is an ordinary absolute filesystem directory,
`/workspace/market-pattern-artifacts`. It survives producer-process exit and is
visible to later processes in the same workspace, but the repository cannot
promise that an external task runner will retain or remount `/workspace`
between independently provisioned containers. At inspection time there was no
root directory and no run registry. The v2 verification in this change creates
an atomic `runs_registry.json`, requires a nonempty mandatory artifact inventory,
and verifies every recorded SHA256 and JSONL record count before accepting
`READY_FOR_AUDIT`.

## Post-test inventory

The synthetic verification subsequently created the persistent root, two
10-file/1,590-byte bundles (the primary and its byte-identical comparison), and
a readable 211-byte `runs_registry.json`. The primary requested files are listed
with exact sizes in `ARTIFACT_HANDOFF_VERIFICATION_REPORT.md`. The legacy-named
`backtest_results.jsonl`, `strategy_candidates.jsonl`,
`validation_reports.jsonl`, `strategy_rankings.jsonl`, and
`executable_signal_definitions.jsonl` remain absent because the current v2
schema uses `backtests.jsonl`, `strategies.jsonl`, `validations.jsonl`,
`rankings.jsonl`, and `signals.jsonl`, respectively.
