# Autonomous run artifacts v1

The production multi-horizon command can export a compact, deterministic run
bundle after the trading pipeline completes:

```text
/workspace/autonomous_runs/
├── manifest.json
├── source_commit.txt
├── data_manifest.sha256
├── hypotheses.jsonl
├── strategies.jsonl
├── signals.jsonl
├── backtests.jsonl
├── validations.jsonl
└── rankings.jsonl
```

Pass `--artifacts-root /workspace/autonomous_runs` together with
`--data-manifest PATH` to `multihorizon-research`. The manifest path identifies
an external inventory of the read-only source data; only its SHA-256 digest is
written. Source candles are neither opened by the exporter nor copied into the
repository or run bundle.

All JSONL records are serialized canonically and sorted by their canonical
representation. Empty stages still produce empty files. `manifest.json`
records each file's count and digest, the Git source commit, and explicit
ZERO LOOK-AHEAD / locked-2025 declarations. It contains no wall-clock value, so
exporting unchanged memory again produces byte-identical files.

The two export arguments are an inseparable pair and the command fails closed
when only one is supplied. The export occurs only after the bounded research
and trading stages return successfully; a partial run is not labelled
`COMPLETED`.
