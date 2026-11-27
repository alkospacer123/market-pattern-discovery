# V20 Trading System — рабочий статус

[Паспорт](../recovery/PROJECT_PASSPORT_V20.md) · [SOURCE map](KIMI_START_HERE_R088.md) · [R088 release](V20-08/LIVE_RELEASE_R088_20261120_RU.md) · [Журнал](JOURNAL.md) · [AGENTS](AGENTS.md) · [COC](../recovery/CRITICAL_OPERATIONS_CONTRACT.md)

**27.11.2026 — Post-G9, SOURCE-аудит завершён, техническая readiness не доказана.** Владелец 27.11.2026 утвердил `FULL_PARITY_OWNER_ADMITTED` для V20/CC/TRL; этап II принят в документированных пределах. [Roadmap](../ROADMAP.md), [Recovery STATUS](../recovery/STATUS.md), [KDR](../recovery/kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md). #614 MERGED; итоговый документационный closeout — #615. Допуск не является разрешением на конкретные критические операции.

Исторический профильный HANDOFF C3.2: MAIN при сверке `2ac85eb5bcdd8757144898b5a27369329f4d125c`; исходный [Draft #608](https://github.com/alkospacer123/market-pattern-discovery/pull/608) HEAD `f6c28ad4027fdc1fdfc8c279671f5c3001f3bd1e`.

- SOURCE: R088 Shallow/OBV/Inside, N4, M15 Market NEXT_OPEN, SL 2×ATR14 Wilder, риск 1,5%/6%, модель капитала 60/30/45 тыс. ₽, TP6 + Protect3 (+3R M15 → SL +1R) + HOLD5 (выход на первом подтверждённом Open шестой наблюдаемой сессии), EXT2 OFF.
- DERIVED: BASE+9, исторические blobs `finam_live.py=5d30270d3936fb52f58a61aa3abbf070d7df6b57`, `finam_execution.py=0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f`; не пересобирались.
- INSTALLED: историческое операторское свидетельство 20.11 `V20_ALL3_PREPOST_PROTECT3_FIX=PASS_3_RUNNING_HALTED_FRESH_CYCLES`. Текущие bytes/launcher/deps NOT_VERIFIED.
- LIVE: последнее известное HALTED 3/3 (REPORTED_ONLY, решение владельца не ARM до адаптации); Tasks, FINAM positions/orders/SLTP, остатки и CC сейчас UNKNOWN. HALTED не доказывает FLAT.
- [#601](https://github.com/alkospacer123/market-pattern-discovery/pull/601) MERGED `d6f21355d33b22d35a98a1539f2bae2154f20b94`: диагностический SOURCE fix `protect3_reason` в JSONL, не доказан INSTALLED; причина отказа 20.11 UNKNOWN. Торговые gates не изменены.
- SOURCE-аудит Kimi Chat и независимое статическое ревью GPT завершены на MAIN `a3aa48fee59b0a077794cccc5ae3eef33d62a6c5`; F1/F4 static confirmed, F2 potential, F3 margin mechanism, F5 POST/DELETE transport gate, F6 operator/CC, F7 TP6 validation gap. Подробные доказательства и приоритеты — [JOURNAL](JOURNAL.md). Все открыты до соответствующей проверки/решения; не LIVE-инциденты. #601 diagnostic-only, HOLD5 сохраняем.
- Далее: CC SOURCE-аудит и статическое ревью завершены; F6 связан с CC H01/M01 ([CC Journal](../ControlCenter/JOURNAL.md)), согласованный stock/exporter/controller/UI state machine и pins обязательны для operator readiness. Разовая Evolution V20 завершена, GPT поддержал KEEP_CURRENT_V20 ([TRL Journal](../TradingResearchLab/journal/2026-11-27-trl-knowledge-consolidation.md)); новых торговых изменений не предложено к внедрению. Результаты в едином PR #617, Merge отдельно. После совместного решения Kimi Code — отдельно разрешённая локальная диагностика SOURCE/DERIVED/INSTALLED/launcher и целевые offline regressions F1–F7 по применимости; единый all-three пакет с #601, SHA, backup/rollback и READONLY postflight. Market входы сохраняются; лимитные обсуждать после 1–2 месяцев статистики. Deploy/ARM/LIVE только отдельно.

Не свежая проверка Intel/FINAM; статус не передаёт полномочия.
