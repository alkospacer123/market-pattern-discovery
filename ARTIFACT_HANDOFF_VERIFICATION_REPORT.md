# Artifact Handoff Verification Report v2

## Verdict

**PERSISTENT STORAGE VERIFIED** for independent OS processes sharing the current
`/workspace` filesystem.

- ✅ Process A created artifact
- ✅ Process B found artifact after Process A termination
- ✅ Manifest verified
- ✅ Hashes verified
- ✅ JSONL readable
- ✅ Byte identical export confirmed

No pipeline, research cycle, smoke run, backtest, validation, strategy
construction, market data, or TRUE OOS 2025 data was used. All six JSONL files
are deliberately empty (zero records); this test created no hypothesis,
strategy, signal, backtest result, validation result, or ranking.

## 1. Storage location and initial state

The canonical memory root is `/workspace/market-pattern-artifacts/`. Before this
test, it did not exist. Neither `/workspace/autonomous_runs/` nor
`/tmp/marketai_executable_signal_smoke_001` existed. The complete pre-test
inventory is recorded in `CURRENT_ARTIFACT_STORAGE_STATUS.md`.

The test produced these bundles:

| Bundle | Files | Apparent bytes | Readable |
|---|---:|---:|---:|
| `/workspace/market-pattern-artifacts/persistence_test_20260911_v2/` | 10 | 1,590 | all files |
| `/workspace/market-pattern-artifacts/persistence_test_20260911_v2_byte_identical_copy/` | 10 | 1,590 | all files |

The storage registry is
`/workspace/market-pattern-artifacts/runs_registry.json` (211 bytes, readable).
Only the primary, verified bundle is registered; the second directory is a
comparison export, not a distinct run.

## 2. Persistence mechanism answers

1. **Where is permanent memory stored?** In the configured filesystem root
   `/workspace/market-pattern-artifacts`, one child directory per `run_id`, with
   an atomic root-level `runs_registry.json`.
2. **Does it survive process termination?** Yes. Process A exited before Process
   B started, and Process B read and verified the bytes from disk.
3. **Can a new process/task open an old run?** A new process can: it needs only
   the storage root and calls the registry-backed latest-run discovery, not a
   pre-known bundle path. A future Codex task can do the same **provided the task
   platform mounts the same `/workspace` volume**. The initial absence of the
   earlier smoke bundle proves that a plain absolute path alone cannot guarantee
   retention across newly provisioned containers or discarded workspaces.
4. **Is there a registry?** Yes after this change. Each successful production
   export atomically publishes `run_id`, source commit, status, and UTC
   registration time only after verification succeeds.

## 3. Synthetic Process A

Process A created `persistence_test_20260911_v2` with exactly the requested core
handoff files:

- `manifest.json` — 1,263 bytes
- `source_commit.txt` — 41 bytes
- `data_manifest.sha256` — 65 bytes
- `audit_metadata.json` — 221 bytes
- `hypotheses.jsonl`, `strategies.jsonl`, `signals.jsonl`, `backtests.jsonl`,
  `validations.jsonl`, and `rankings.jsonl` — zero bytes each and valid empty
  JSONL streams

Its checks returned `CREATE PASS`, `MANIFEST PASS`, `HASH PASS`, and
`JSONL READ PASS`. Audit metadata explicitly records synthetic input, no market
input, no TRUE OOS access, and zero record counts. The manifest records the
source commit, synthetic state digest, per-file SHA256, and JSONL counts.

## 4. Independent Process B

After Process A terminated, Process B was launched by a separate Python
invocation. It was given `/workspace/market-pattern-artifacts` only. It read
`runs_registry.json`, selected the latest registered `run_id`, opened its
manifest, checked the manifest commit against `source_commit.txt`, checked the
state digest against `data_manifest.sha256`, recomputed every artifact SHA256,
parsed every JSONL line, and compared all record counts. It returned:

```text
FOUND /workspace/market-pattern-artifacts/persistence_test_20260911_v2
MANIFEST PASS
HASH PASS
JSONL READ PASS
PERSISTENCE TEST PASS
```

## 5. Byte-identical export

Process A wrote the same in-memory synthetic byte map to
`persistence_test_20260911_v2_byte_identical_copy`. A byte comparison covered
`manifest.json`, `audit_metadata.json`, both lineage files, and all six JSONL
files. Every file was identical, and therefore every SHA256 was identical:
`BYTE IDENTICAL`.

The registry timestamp is intentionally outside the bundle and is not part of
the reproducibility comparison.

## 6. False `READY_FOR_AUDIT` protection

Verification now fails closed unless all of the following hold:

- `manifest.json` exists and parses;
- status is exactly `READY_FOR_AUDIT`;
- the artifact inventory exists and contains all mandatory core files;
- source commit and data-manifest digest are present;
- every inventoried file exists and its SHA256 matches;
- every JSONL stream parses and its count matches the manifest.

During export, a failed verification rewrites manifest status to `FAILED` and
raises; only a successfully verified run is published to the registry. A
regression test confirms that a forged `READY_FOR_AUDIT` with an empty artifact
inventory is rejected.

## 7. Forensic-audit availability and loss prevention

A future audit can inspect the manifest, source commit, input-state digest,
audit metadata, hypotheses, strategies, signals, backtests, validations, and
rankings. Production exports may additionally contain direction-bias and
horizon diagnostic reports. Integrity is established by canonical deterministic
serialization, atomic file replacement, manifest SHA256 values, JSONL parsing,
record-count checks, and registry publication after verification.

To avoid another lost smoke bundle:

1. mount `/workspace/market-pattern-artifacts` as a durable volume shared by all
   Codex tasks, or configure the root to an externally durable artifact store;
2. never rely on `/tmp` for a handoff;
3. require the run to appear in `runs_registry.json` before reporting success;
4. run registry-based discovery plus full verification from a separate process;
5. upload/archive the verified bundle and registry before the task workspace is
   destroyed.

The code can verify process-boundary persistence, corruption detection, and
later discovery. Infrastructure outside this repository must guarantee volume
retention across independently provisioned Codex task containers.
