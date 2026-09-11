# Persistent autonomous-run artifacts v2

The canonical storage root is **`/workspace/market-pattern-artifacts`**. It is a
workspace path, not `/tmp` and not a process-specific directory. Every export
is isolated below `<root>/<run_id>/`; callers may supply `--run-id`, otherwise a
deterministic identifier is derived from source commit, data-manifest hash, and
seed.

Each run contains `manifest.json`, `source_commit.txt`,
`data_manifest.sha256`, the six stage JSONL files (`hypotheses`, `strategies`,
`signals`, `backtests`, `validations`, and `rankings`), and three diagnostic
files: `audit_metadata.json`, `direction_bias_report.json`, and
`horizon_report.json`. The audit metadata contains per-strategy definitions,
per-backtest trade diagnostics, and pipeline funnel counts. Empty stages are
represented by readable empty JSONL files.

`AutonomousRunArtifacts.export` writes atomically, records every artifact hash
and JSONL record count, and then reopens the bundle with
`AutonomousRunArtifacts.verify`. Status becomes `READY_FOR_AUDIT` only after
all required files exist, hashes match, and every JSONL record parses. A
verification error records `FAILED` and raises. A consumer in a later process
can call `AutonomousRunArtifacts.verify(run_directory)` before trusting it.
After that verification succeeds, export atomically publishes the run ID,
commit, status, and registration time in `<root>/runs_registry.json`. A later
process that knows only the storage root can call `AutonomousRunArtifacts.latest()`
to discover and reverify the newest registered bundle. Verification rejects a
`READY_FOR_AUDIT` manifest if its required inventory, any required file, any
SHA256, or a JSONL record/count is missing or invalid.

The production command requires `--data-manifest`; its default artifact root is
the canonical path:

```bash
multihorizon-research --data-root READ_ONLY_DATA --memory-root MEMORY \
  --cycles 1 --data-manifest DATA_MANIFEST --run-id RUN_ID
```

The manifest binds the bundle to the Git commit and external read-only data
inventory without copying or reading source candles. Calendar year 2025 remains
explicitly marked unaccessed. Export serialization and ordering are canonical,
so the same memory, commit, data manifest, seed, and run ID produce identical
artifact bytes and strategy/ranking order.
