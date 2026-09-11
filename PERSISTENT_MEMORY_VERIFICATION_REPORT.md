# Persistent Memory Verification Report v1

## Scope and safety

Verification was performed on **2026-09-11 UTC** and was limited to synthetic
persistence artifacts. No market data was read or copied, and no research
pipeline, `run_multihorizon_research.py`, backtest, strategy generation,
parameter search, optimization, smoke run, 20-cycle validation, or forensic
audit was run. In particular, locked TRUE OOS 2025 data was not accessed.

## 1. Storage

Permanent autonomous-run memory is stored at:

`/workspace/market-pattern-artifacts/<run_id>/`

Initial inspection found `/workspace/market-pattern-artifacts/` absent. Process
A created it and the synthetic run
`persistence_test_20260911_v1`. The final storage inventory was:

| Location | State | Read access | Detail |
|---|---|---|---|
| `/workspace/market-pattern-artifacts/` | exists | available | 36 KiB allocated |
| `/workspace/market-pattern-artifacts/persistence_test_20260911_v1/` | exists | available | 2,832 bytes apparent bundle size |
| `/tmp/marketai_executable_signal_smoke_001` | absent | not applicable | no old temporary run |
| `/workspace/autonomous_runs/` | absent | not applicable | no old autonomous-run storage |

Available run IDs after the test: `persistence_test_20260911_v1`. Every file in
the bundle was individually readable.

## 2. Persistence

**YES.** Process A created and verified the bundle, then exited completely. A
separate Python interpreter (Process B), without Process A's Python memory,
variables, or temporary files, discovered the run from the persistent storage
root and verified its on-disk contents.

Process A result:

```text
PROCESS A:
CREATE PASS
MANIFEST PASS
HASH PASS
STATUS READY_FOR_AUDIT
```

## 3. Cross-session access

**YES.** An independent process can discover the run by scanning the stable
storage root, open `manifest.json`, and perform a new audit without rerunning
research. This also makes the bundle addressable by a later Codex task as long
as the task uses the same persistent `/workspace` volume.

Process B result:

```text
PROCESS B:
DISCOVERED_RUN_ID persistence_test_20260911_v1
BUNDLE PASS
COMMIT PASS
SHA PASS
JSONL PASS
RECORD_COUNTS PASS
CROSS-SESSION ACCESS PASS
```

## Process A lineage and inventory

- Run ID: `persistence_test_20260911_v1`
- Source commit: `5b27b4bff02b465f62965b76fe7aa5e27fd35a07`
- Synthetic data-manifest SHA256:
  `30adc8895c23e3d0618b93892ae27c197726adfda8be6ca5827942c66a09b441`
- Saved status: `READY_FOR_AUDIT`
- Safety metadata: `zero_look_ahead=true`,
  `true_oos_2025_accessed=false`

| Artifact | Records | SHA256 |
|---|---:|---|
| `audit_metadata.json` | n/a | `709d6412ecf5615703ecc94dc033f450df525ed45897e5ffbf37e97a16907748` |
| `backtests.jsonl` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `data_manifest.sha256` | n/a | `1e080ff0e56e6778722096b7e76b8f4c8c2dea8154ee91ea8b1e29ed500e3e87` |
| `direction_bias_report.json` | n/a | `fcf204efe33db93d807557c0eb738b4e5da6ce0472bd2749221e30b564616f0c` |
| `horizon_report.json` | n/a | `11cdd0c04b1672594589376f7843f1a22dbcea77ec3eb09cfd42f23d79b3936f` |
| `hypotheses.jsonl` | 1 | `1df97dfe5357d3b59ea7c8b3d376966bd70213f007091ce606913a5a528bb2cf` |
| `rankings.jsonl` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `signals.jsonl` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `source_commit.txt` | n/a | `fb8d816236719d8719434c5f24947a0c240c70fbd4279bd7471722002cda0986` |
| `strategies.jsonl` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `validations.jsonl` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The single hypothesis is an explicitly synthetic persistence fixture. Empty
strategy, signal, backtest, validation, and ranking streams confirm that the
test did not create trading output.

## 4. Integrity table

| Проверка | Результат |
|---|---|
| manifest найден | **PASS** |
| artifact bundle полный | **PASS** — all 12 required files present |
| JSONL читаются | **PASS** — every line parsed as JSON |
| SHA совпадает | **PASS** — all artifact digests, source commit, and data-manifest digest matched |
| повторный экспорт идентичен | **PASS — BYTE IDENTICAL** |

The deterministic re-export used the same synthetic state, run ID, seed,
repository commit, and synthetic manifest bytes. All bundle bytes before and
after export compared equal, including byte-identical `manifest.json`; hence
all first-export and second-export artifact hashes were identical.

## 5. Final verdict

# PERSISTENCE VERIFIED

This verdict authorizes only the requested conclusion. No smoke run, 20-cycle
validation, or full forensic audit was started as part of this task.
