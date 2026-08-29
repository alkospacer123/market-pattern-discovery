# Top-5 V4 engine readiness report

Status: **ENGINE_READY_FOR_DEV**.

This status means the V4 specification/engine is internally consistent and ready for the guarded DEV workflow. It is **not** a profitability, validation, TRUE-OOS, or live-trading claim.

## Frozen research surface

- Machine contract: `config/top5_v4/strategy_contract.json` (single V4 source of semantic truth).
- Candidate registry: `config/top5_v4/candidate_registry.json`.
- Canonical candidates: **142**.
- DEV selection-eligible candidates: **136**.
- Single-leg candidate identity excludes instrument; CNYRUBF and USDRUBF are executions of the same parameter candidate.
- Per-family decision clocks are frozen: Structural/Trend/Bollinger/Gerchik use causal closed M5; ORB uses closed M1; PAIRS uses exact common closed M1.
- 2025 is locked TRUE OOS.

## Integrity and causality controls

The V4 engine freezes exact executable formulas, integer-tick comparisons, causal M5 composition and pivot availability, immutable structural snapshots, bounded state-machine lifetimes, actual-next-open R targets, STOP_FIRST/gap rules, pair alignment/convergence semantics, friction scenarios, pooled normalized metrics, deterministic selection, and Validation pre-read reproduction gates.

DEV market availability is bounded by `open_time >= start AND close_time < end`; a bar closing exactly at a period boundary is excluded from the earlier period.

Validation A/B is classified as preregistered frozen forward validation nested inside the repository 2026 DISCOVERY period, not repository-level INTERNAL_CONFIRMATION and not pristine dataset-wide OOS.

## Verification completed without market data

- Python compilation: PASS.
- V4 synthetic/state-machine/governance tests: **74/74 PASS**.
- Machine contract/registry audit: PASS.
- Audit verified **142 / 136** registry counts and reported `market_data_accessed: false`.
- Runner audit succeeds with a deliberately nonexistent market-data root, proving audit does not require/read OHLCV.
- Local Git engine/artifact gate test: PASS. A result-only child commit is accepted for later validation, while `--dev-full` is refused after V4 result artifacts become tracked.

## Not executed in this repair

- `--dev-full`: NOT RUN.
- `--validate`: NOT RUN.
- Validation A/B OHLCV: NOT MATERIALIZED.
- 2025 TRUE OOS: NOT ACCESSED.
- Real-data smoke/performance gate: NOT RUN in this environment because `/workspace/market-pattern-data` is not available here.

The next permitted research step is the guarded DEV smoke/profile/full-grid sequence on the environment that contains the frozen market-data files. Validation remains blocked until the DEV freeze manifest and selected DEV semantic ledger reproduce exactly.
