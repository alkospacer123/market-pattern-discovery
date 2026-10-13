# T3/M15 Execution Sensitivity v1

**Next Open сохраняет положительные gross результаты всех шести фиксированных конфигураций; ни одна не достигает ежегодного PF ≥1.70 в 2024.** Регулярность неизменна. Полный доступный 2023–2024, четыре инструмента; никакой новой Optimization.

GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. 2023–2024 DEVELOPMENT_EXPOSED.

- [Русский итог, таблица всех шести и семь ответов](CONCLUSIONS.md).
- [Полный отчёт: годы, все 24 месяца, concentration, occupancy, winners, November, инструменты/LONG/SHORT](results/REPORT.md).
- [Пререгистрация](PROTOCOL.md), [точные параметры/source pins](SPEC.json), [initial/corrected freeze](FREEZE.json).
- [CONTROL primary](control/CONTROL_GATE.json), [CONTROL scalar](control_scalar/CONTROL_GATE.json): каждый 2 442 256 fields, 0 differences.
- [Независимый вычислительный аудит](audit/AUDIT_RESULT.json): 6 570 563 fields, 0 differences; внешний human review PENDING.
- [Честное раскрытие audit schema correction](AUDIT_CORRECTION.md), [побайтная идентичность торговых результатов после исправления](POST_CORRECTION_IDENTITY.json).
- [Два свежих побайтных повтора](REPEATABILITY.json), [22 причинных fixtures](results/TEST_RESULTS.txt).
- [Source SHA и границы](results/SOURCE_MANIFEST.json), [прочитанные references](READ_REFERENCES_SHA256.json), [проверка main/scope](FINAL_MAIN_CHECK.json), [полные artifact SHA](ARTIFACT_SHA256.json).

Полные causal journals отдельно в `results/signal_close/` и `results/next_open/`: CLOSED, Stop/entry/gap decisions, terminal/period OPEN. Ни один путь не составлен фильтрацией старых trade CSV. Общие CSV/JSON: comparison, summary, monthly (все инструменты × LONG/SHORT), funnel_occupancy, lineage, winner_retention ≥2R/≥5R, new_entries, entry_price_sensitivity, november, closed_equity, negative_results, missing-adjacent/pending.

Цена Next Open и отмена несмежных сигналов совместно меняют Stop/занятость/повторные входы; отдельный численный вклад каждого эффекта в ΔR не идентифицирован без counterfactual replay. Здесь дополнительные replay не запускались. Next Open не гарантирует fill/queue/latency; costs/sizing/tick-grid/MTM отложены. CLOSED-R DD не равен drawdown капитала.

Воспроизведение из этого каталога с Python 3.11+ и зафиксированными requirements:

```bash
python test_causal.py
python run.py --data-root /workspace/market-pattern-data --output /workspace/work/new_execution_run/results
python audit.py --data-root /workspace/market-pattern-data --primary /workspace/work/new_execution_run/results --output /workspace/work/new_execution_run/audit
```

Read-only data checkout должен быть чистым и pinned на `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Parser timestamp-first останавливается до 2025+ numeric suffix. FREEZE guard проверяет code/spec и соответствующие Git blobs; initial freeze и одно исправление аудита видны в истории PR. `repeat.py` — протокол двух свежих процессов в исходной cloud-сессии; фиксированные scratch-каталоги `/workspace/work/execution_repeat_1/2` должны отсутствовать перед запуском. Direct bytes и SHA256 сравниваются для каждого сгенерированного primary/audit файла.

Новый каталог — единственная область diff. Старый local checkout, прежние IntradayLab, ROADMAP, TradingSystemLab/робот и source data не изменены. Один **Draft PR, NO MERGE / NO AUTO-MERGE**; STOP для независимой проверки. No numerical Optimization / Robustness / Walk Forward / TRUE OOS / LIVE / broker endpoints.
