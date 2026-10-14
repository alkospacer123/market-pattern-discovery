# T3/M15 T1+S1 v1 — independent audit and one fixed experiment

GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY

2023–2024: DEVELOPMENT_EXPOSED. Historical signal-Close fills remain unverified.

The external-to-#499 FIRST GATE is documented in [AUDIT_499_PROTOCOL.md](AUDIT_499_PROTOCOL.md), with immutable stdlib `independent.py` / `audit_499.py` and complete independently reproduced journals in `audit_499/`. No prior engine, metric or internal audit is imported. Full audit: 2,580,630 fields, zero discrepancies, CONTROL 1442 CLOSED +2 terminal OPEN; T1/T2 and all reports/diagnostics reproduce.

Only after that PASS, [PREREGISTRATION.md](PREREGISTRATION.md) and [EXPERIMENT_SPECS.json](EXPERIMENT_SPECS.json) define exactly one new mechanism: T1 core-hours entries + S1 trailing after 1 immutable initial R. All executable code and causal fixtures are frozen before any historical COMBINED result. `FREEZE.json` records that Git commit and every code/spec hash. The post-freeze `PRE_COMBINATION_GATE.json` records fresh CONTROL/S1/T1 and independent benchmark matches plus 40 fixtures.

`engine.py` builds dataframe features and object positions; `independent_combination.py` uses separate scalar forward features/positions. `reports.py` computes primary metrics; `verify.py` uses independently computed scalar metrics and diagnostics and compares every common trade/Stop/entry/gap/OPEN/report field within absolute 1e-8. Final complete journal and report artifacts are in `results/` and `independent_results/`.

Reproduction (run from repository root; all output paths must stay inside this package):

```sh
export PYTHONDONTWRITEBYTECODE=1
python IntradayLab/t3_m15_t1_s1_v1/test_causal.py
python IntradayLab/t3_m15_t1_s1_v1/test_combination.py
python IntradayLab/t3_m15_t1_s1_v1/audit_499.py --data-root /workspace/market-pattern-data --output IntradayLab/t3_m15_t1_s1_v1/work/audit_fresh
python IntradayLab/t3_m15_t1_s1_v1/research.py --data-root /workspace/market-pattern-data --output IntradayLab/t3_m15_t1_s1_v1/work/fresh
python IntradayLab/t3_m15_t1_s1_v1/verify.py --data-root /workspace/market-pattern-data --target IntradayLab/t3_m15_t1_s1_v1/work/fresh --output IntradayLab/t3_m15_t1_s1_v1/work/independent_fresh
```

Two fresh complete primary, independent and FIRST GATE byte repeats are recorded in `REPEATABILITY.json`. Generated SHA256 inventories are beside results; root `ARTIFACT_SHA256.json` covers every non-work deliverable except itself (its Git blob and commit provide the non-self-referential seal). No raw market data is copied. Source opaque hashing and timestamp-first historical parsing are separate.

Files are added only inside this new directory. The older local checkout is unchanged; a separate Git index in ignored `work/` assembles commits on verified remote main. `SCOPE_CHECK.json` records hashes, freeze and scope checks. One new branch, one Draft PR, no merge, Auto-Merge off, STOP. No Optimization, Robustness, Walk Forward, TRUE OOS or LIVE.
