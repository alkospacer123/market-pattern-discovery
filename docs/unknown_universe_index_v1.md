# UNKNOWN universe manifest and rank index v1

Normal UNKNOWN research reads `config/unknown_universe_v1/manifest.json` and
the four referenced little-endian unsigned-32-bit rank permutations. Missing,
truncated, corrupt, stale, or contract-incompatible artifacts fail closed. A
normal run never creates or repairs these release artifacts.

The manifest binds the iterator schema, semantic-ID schema, method order,
scheduler seed, full execution-contract digest, scope order and counts, state
domains, condition blocks, targets, contrasts, family fields, and contract
signatures. It records the SHA-256 digest of the ordered sequence of full
32-byte semantic IDs. Its uniqueness statement is emitted only after all full
IDs have been inserted into one SQLite table with the full ID as its primary
key; it is not a probabilistic or truncated-hash check.

Each rank file is an exact per-scope permutation of logical ordinals ordered by
the legacy key `(deterministic_hash({"seed": seed, "id": pattern_cell_id}),
per_scope_ordinal)`. Normal planning walks that order only until its bounded
budget has enough cells not present in `ResearchMemory`, then reconstructs
those cells through `PatternSearchSpace`.

## Explicit release/audit commands

Generation is intentionally slow and separate from research:

```console
python scripts/build_unknown_universe_index.py \
  --data-root /read-only/development-data \
  --output config/unknown_universe_v1
```

Validate an existing artifact against freshly derived development state
domains and contracts without regenerating it:

```console
python scripts/build_unknown_universe_index.py \
  --data-root /read-only/development-data \
  --output config/unknown_universe_v1 \
  --validate-only
```

These commands use portable Python, SQLite, and ordinary files. They do not use
CUDA, multiprocessing, memory mapping, or source-data copies. Calendar year
2025 remains prohibited input.
