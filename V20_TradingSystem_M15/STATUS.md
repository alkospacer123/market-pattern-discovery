# V20 Trading System — рабочий статус

[Паспорт](../recovery/PROJECT_PASSPORT_V20.md) · [SOURCE map](KIMI_START_HERE_R088.md) · [R088 release](V20-08/LIVE_RELEASE_R088_20261120_RU.md) · [Журнал](JOURNAL.md) · [AGENTS](AGENTS.md) · [COC](../recovery/CRITICAL_OPERATIONS_CONTRACT.md)

**27.11.2026 — Post-G9, профильная диагностика NEXT.** Владелец 27.11.2026 утвердил `FULL_PARITY_OWNER_ADMITTED` для V20/CC/TRL; этап II принят в документированных пределах. [Roadmap](../ROADMAP.md), [Recovery STATUS](../recovery/STATUS.md), [KDR](../recovery/kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md). #614 MERGED; итоговый документационный closeout — #615. Допуск не является разрешением на конкретные критические операции.

Исторический профильный HANDOFF C3.2: MAIN при сверке `2ac85eb5bcdd8757144898b5a27369329f4d125c`; исходный [Draft #608](https://github.com/alkospacer123/market-pattern-discovery/pull/608) HEAD `f6c28ad4027fdc1fdfc8c279671f5c3001f3bd1e`.

- SOURCE: R088 Shallow/OBV/Inside, N4, M15 Market NEXT_OPEN, SL 2×ATR14 Wilder, риск 1,5%/6%, модель капитала 60/30/45 тыс. ₽, TP6 + Protect3 (+3R M15 → SL +1R) + HOLD5 (выход на первом подтверждённом Open шестой наблюдаемой сессии), EXT2 OFF.
- DERIVED: BASE+9, исторические blobs `finam_live.py=5d30270d3936fb52f58a61aa3abbf070d7df6b57`, `finam_execution.py=0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f`; не пересобирались.
- INSTALLED: историческое операторское свидетельство 20.11 `V20_ALL3_PREPOST_PROTECT3_FIX=PASS_3_RUNNING_HALTED_FRESH_CYCLES`. Текущие bytes/launcher/deps NOT_VERIFIED.
- LIVE: последнее известное HALTED 3/3 (REPORTED_ONLY, решение владельца не ARM до адаптации); Tasks, FINAM positions/orders/SLTP, остатки и CC сейчас UNKNOWN. HALTED не доказывает FLAT.
- [#601](https://github.com/alkospacer123/market-pattern-discovery/pull/601) MERGED `d6f21355d33b22d35a98a1539f2bae2154f20b94`: диагностический SOURCE fix `protect3_reason` в JSONL, не доказан INSTALLED; причина отказа 20.11 UNKNOWN. Торговые gates не изменены.
- Далее: самостоятельно диагностировать Shallow/OBV/Inside силами Kimi Code в `C:\V20Lab` по отдельно согласованному READONLY scope. Сверить SOURCE/DERIVED/INSTALLED и ранее сообщённое расхождение launcher (причина UNKNOWN); подготовить единый all-three пакет #601 с offline checks, SHA, backup/rollback и READONLY postflight. Оценить HOLD5 и альтернативы без необязательной задержки запуска. Market входы сохраняются; лимитные обсуждать после 1–2 месяцев статистики. Deploy/ARM/LIVE только отдельно.

Не свежая проверка Intel/FINAM; статус не передаёт полномочия.
