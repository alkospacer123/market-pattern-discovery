# T3/M15 — stretched breakout confirmation v1

Один фиксированный causal replay: CONTROL и подтверждение одной M15 только при
исходном выносе >=0.5 ATR. Development 2023–2024. Итог: REPORT_RU.md.
Протокол зафиксирован commit 6cb232e1 до расчёта альтернативы.

Требуется Python 3.11+, pandas 2.2.3, numpy 2.3.5. Никаких production сервисов.
Checkout market-pattern-data должен быть read-only соседним каталогом на
f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8. Source OHLC в git не копировать.
Требуются git objects PR518 d85cf85083d6fea047a1a960c9ead441f7b4a6ed,
PR560 90a0a552c05f9ae280f4f2350fd013ea507ea00f,
PR562 40b59a495936adc8110a60f8c25028bbbc9c2e8d.
Исходники PR518 уже находятся на main, их exact bytes проверяются на каждом run.
Архивы PR560/562 автоматически извлекаются в соседний work/t3_confirmation/,
проверяются git object и SHA256; это результаты, не source OHLC.

Из корня репозитория:

```bash
python audit_only/t3_m15_stretched_breakout_confirmation_v1/test_contract.py
python audit_only/t3_m15_stretched_breakout_confirmation_v1/run.py --output ../work/t3_confirmation/my_fresh_run
python audit_only/t3_m15_stretched_breakout_confirmation_v1/repeat.py
```

Output должен отсутствовать. Каждый полный процесс сначала запускает изолированный
full frozen CONTROL (2023–2026, retrospective reconciliation only), затем обе
development state machines, отдельный scalar verifier и fresh CSV/Decimal audit.
run.py никогда не использует trade CSV как вход симуляции. Архивные CSV читаются
только после свежего соответствующего CONTROL для сверки.

Нормированная чувствительность расходов задаётся явно:
`--round-trip-cost-R` и `--round-trip-slippage-R`, оба >=0, по умолчанию 0.
Она записывается отдельно от Gross, не считается брокерским Net и не влияет
на сигналы/занятость. Параметры альтернативы конфигурировать/подбирать нельзя.

engine.py — ограниченная адаптация frozen PR518 primary replay;
ENGINE_LINEAGE.patch показывает весь delta state machine. Feature builder
CONTROL/CONFIRM один и тот же frozen PR518. verifier.py — отдельный алгоритм
очереди событий; indicators пересчитываются независимым PR518 streaming EWM.
stats_verifier.py не импортирует analysis.py/report.py и перечитывает CSV.
Все реализации одним автором; это не независимое human approval.

См. DATA_DICTIONARY_RU.md для календаря/полей; AUDIT.json, CODE_FREEZE.json,
REPEATABILITY.json, SHA256SUMS — квитанции проверки.

Только один новый audit-каталог и Draft PR. NO MERGE / NO AUTO-MERGE.
