# TRAIL_375 — Walk Forward 2025

Один неизменный кандидат, четыре инструмента, весь календарный 2025. 2026 TRUE OOS закрыт. Решение и все результаты публикуются после полного CONTROL; внешнее ревью PENDING. Протокол: PROTOCOL.md; точные границы/параметры: SPEC.json; отдельное разрешение: USER_AUTHORIZATION.json.

Воспроизведение из этого каталога с Python 3.12 и requirements.txt:

```bash
python -m unittest test_execution test_wf -v
python pipeline.py --output /workspace/work/verification/results
python audit.py --primary /workspace/work/verification/results --output /workspace/work/verification/audit
```

Исторические результаты и код не менять. Полные expanding replay сохраняют исходное состояние без квартального reset. Фиксированные diagnostics не меняют стратегию. При любом нарушении протокола STOP.

Итог: results/W4/CONCLUSIONS_RU.md; основные таблицы: results/W4/REPORT_RU.md; полные: results/W4/DETAILS.md, CSV и TABLES.json; квартальные seals: results/W1..W4/SEAL.json; CONTROL: results/CONTROL; независимый аудит: audit/AUDIT_RESULT.json; повторяемость: REPEATABILITY.json. Все timestamps Europe/Moscow. Сумма R — не доходность капитала.

DEVELOPMENT_2023_2024_EXPOSED / WF_2025_AUTHORIZED / TRUE_OOS_2026_LOCKED / GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. NO MERGE / NO AUTO-MERGE / NO TRUE OOS / NO LIVE.
