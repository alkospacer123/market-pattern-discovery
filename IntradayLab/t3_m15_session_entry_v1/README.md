# T3/M15 Session Entry v1

GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. 2023–2024 development-exposed.

Exactly CONTROL, T1 CORE_HOURS_ENTRY (10:00 inclusive to 18:00 exclusive MSK),
T2 SKIP_FIRST_BAR_AFTER_GAP (>15 minutes between observed completed M15 closes;
missing previous close blocks separately). Each independently replays BASELINE
trailing 3.0 ATR and OPTIMIZED trailing 3.5 ATR. Initial Stop remains 2 ATR.
No combined rules, parameter search, changed indicators, exits, or session flattening.

`EXPERIMENT_SPECS.json` and executable code are committed before any T1/T2 results.
Preflight must reproduce all common #490/#495 fields, 1442 CLOSED +2 terminal OPEN,
and pass causal tests. Only then can `research.py` run variants.

```bash
export PYTHONDONTWRITEBYTECODE=1
python IntradayLab/t3_m15_session_entry_v1/verify.py --data-root /workspace/market-pattern-data --preflight
python IntradayLab/t3_m15_session_entry_v1/research.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_session_entry_v1/audit.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_session_entry_v1/verify.py --data-root /workspace/market-pattern-data
```

Outputs: `results/REPORT.md`, full CONTROL/T1/T2 trades, per-signal entry decisions,
per-exposed-bar Stop decisions, every observed gap, monthly/yearly/instrument/direction
reports, period-end OPEN snapshots, closed-R equity, winner lineage/new losses,
chronology changes, duration/frequency/overnight gap diagnostics, hourly T1 rejects.
All raw data and existing files are read-only. Only this new directory may change.

`audit.py` is a separate standard-library computational implementation, including
recursive indicators and slice-based replay; it does not import the experiment engine
or reporting code. Same author; external reviewer independence remains pending.
Two fresh full runs are compared byte by byte, including all reporting outputs.
Historical signal-Close fills are assumptions, not proven real execution.

One Draft PR only; no merge or auto-merge. STOP for external audit and user decision.
