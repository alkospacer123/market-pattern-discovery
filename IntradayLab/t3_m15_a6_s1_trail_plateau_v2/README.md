# T3/M15 A6+S1 — Trailing Plateau Verification v2

2023–2024 **DEVELOPMENT_EXPOSED**. **GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.**

Ровно три новых trailing ATR 3.625, 3.875, 4.000; существующий контроль3.500 и замороженный лидер3.750. Все остальные правила и исходные журналы read-only. Никакого расширения сетки.

Протокол: [PROTOCOL.md](PROTOCOL.md), настройки: [SPEC.json](SPEC.json), Git freeze: [FREEZE.json](FREEZE.json), источники: [SOURCE_ORIGIN.json](SOURCE_ORIGIN.json).

Команды из каталога исследования:

```sh
python test_causal.py
python run.py --controls-only
python run.py
python audit.py
python repeat.py
python seal.py
```

Primary: pandas/object; независимый аудит: stdlib streaming/dict/scalar. Автор один, внешнее ревью PENDING. Source/data pins и frozen code guard обязательны; no OHLC2025+. Полные журналы сохраняются в results/replay и control*/; полные таблицы в CSV и TABLES.json, отчёты REPORT.md/MONTHLY_DETAIL.md. После результатов — CONCLUSIONS.md и DECISION.json.

Один Draft PR, NO MERGE / NO AUTO-MERGE, STOP после создания PR. Не запускать следующие исследования/этапы.
