# T3/M15 Initial Stop v1

**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY**. Full available 2023–2024,
all four perpetual instruments; both years development-exposed. One bounded
standalone package: CONTROL / I1 / I2 / I3 × trailing 3.0 / 3.5 ATR.
No parameter search, combinations, new filters, costs, sizing or live work.

[Frozen specification](EXPERIMENT_SPECS.json) precedes outcomes in a separate
commit. Source `market-pattern-data` is read-only at
`f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; base main is
`8513203e6e6d9f6995d9464ecd29bb75775400d3` (#497).

[Report](results/REPORT.md), [objective](results/OBJECTIVE_ASSESSMENT.json),
[CONTROL field gate](results/CONTROL_REPRODUCTION.json),
[second implementation audit](AUDIT_RESULTS.json),
[two full byte repeats](REPEATABILITY.json), [scope](SCOPE_CHECK.json),
[artifact hashes](ARTIFACT_SHA256.json).

Reproduce from repository root with Python 3.11+, versions in requirements.txt:

```sh
python IntradayLab/t3_m15_initial_stop_v1/verify.py --data-root /workspace/market-pattern-data --preflight
python IntradayLab/t3_m15_initial_stop_v1/research.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_initial_stop_v1/audit.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_initial_stop_v1/verify.py --data-root /workspace/market-pattern-data
```

Fresh repeat directories are required; remove only this study's ignored work/
if rerunning verification. Never alter frozen references or the data checkout.
The primary engine reads the frozen #490 indicator oracle; the auditor independently
derives signals with recursive stdlib arithmetic and reconstructs each trade path.
Algorithmic independence is same-author validation, not an external reviewer audit.

Signal-Close entry remains an **unverified execution assumption**. Stop and trailing
are not rounded onto the exchange grid. Narrow-stop, gap and 2×ATR diagnostics
never filter trades. All negative outcomes are retained. No live/economic PASS,
no automatic winner selection. One Draft PR, no Merge/Auto-Merge, STOP for external audit.
