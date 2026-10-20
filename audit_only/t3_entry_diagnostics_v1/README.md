# T3 ENTRY DIAGNOSTICS V1

Start with [REPORT_RU.md](REPORT_RU.md), then [HYPOTHESES.md](HYPOTHESES.md)
and [PROTOCOL_RU.md](PROTOCOL_RU.md). Schemas: [DATA_DICTIONARY_RU.md](DATA_DICTIONARY_RU.md).

Read-only, audit-only diagnostic continuation of PR560. Unchanged H1/M15
CONTROL, FULL N4, R15, initial/trailing and execution. No candidate/filter
backtest, no ML/parameter search. Development 2023–2024 only; complete frozen
period processed solely by isolated mandatory CONTROL gate. No new OOS claim.

Requires Python 3.11+, numpy 2.3.5, pandas 2.2.3, matplotlib 3.10.8 (actual
runtime versions recorded), git and the pinned repository objects. Data stays
outside this repository at `/workspace/market-pattern-data` (clean pinned M15
checkout; H1 read from its pinned git blob). No broker/robot/SQLite imports.

From repository root:

```bash
python audit_only/t3_entry_diagnostics_v1/run.py --output audit_only/t3_entry_diagnostics_v1/work/fresh_manual
python audit_only/t3_entry_diagnostics_v1/repeat.py
```

Output and scratch run directory must be fresh; use a new basename per run.
`repeat.py` does three complete fresh processes after CODE_FREEZE and compares
every generated artifact by direct bytes and SHA256; publishes the first set
only after all comparisons pass. It never repairs the frozen CONTROL.
SHA256SUMS covers all delivered files except itself and ignored work/.

Independent verification means a separate scalar algorithm, with fresh source
reads and separate CSV arithmetic, written by the same author. External human
and separate-agent signoff are **not performed**; AUDIT explicitly marks this.
Draft research only; no merge/auto-merge, no deployment.
