# IntradayLab — A6+S1 trailing 2.75/3.00/3.25/3.50/3.75

GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. 2023–2024 DEVELOPMENT_EXPOSED.

[Спецификация](SPEC.json), [предрегистрация](PROTOCOL.md), [русский отчёт](results/REPORT.md), [решение](CONCLUSIONS.md), [24 месяца × instruments × LONG/SHORT](results/MONTHLY_DETAIL.md).

```bash
python IntradayLab/t3_m15_a6_s1_trail_optimization_v1/test_causal.py
python IntradayLab/t3_m15_a6_s1_trail_optimization_v1/run.py --controls-only --output /workspace/work/trail_controls
python IntradayLab/t3_m15_a6_s1_trail_optimization_v1/run.py
python IntradayLab/t3_m15_a6_s1_trail_optimization_v1/audit_v1_1.py
python IntradayLab/t3_m15_a6_s1_trail_optimization_v1/repeat_v1_1.py
```

Python dependencies pinned in requirements.txt. Read-only source root defaults to `/workspace/market-pattern-data`, exact data commit required. Repeat directories must be fresh. No historical results can be computed without FREEZE.json and both #504 raw-journal control gates. Run only the registered five C1/NEXT_OPEN configurations. All prior research and TradingSystemLab untouched. Один Draft PR; NO MERGE / NO AUTO-MERGE.

Оригинальные frozen audit.py/repeat.py сохранены; display-only ревизия описана в [AUDIT_REVISION_1_1](AUDIT_REVISION_1_1.md).
