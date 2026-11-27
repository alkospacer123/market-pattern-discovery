# V20 Trading System M15 — паспорт

**ACTIVE trading system.** V20 — три независимых робота Shallow / OBV / Inside на отдельных FINAM-счетах; N4: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF. Каталог `V20_TradingSystem_M15/`, зависимости `TradingSystemLab.stage8_robot`, `IntradayLab.core` сохраняются.

## Канонические источники по задаче

- [STATUS](../V20_TradingSystem_M15/STATUS.md) и [JOURNAL](../V20_TradingSystem_M15/JOURNAL.md) — текущий срез, решения и ссылки на доказательства.
- [V20 AGENTS](../V20_TradingSystem_M15/AGENTS.md) и [R088 release](../V20_TradingSystem_M15/V20-08/LIVE_RELEASE_R088_20261120_RU.md) — действующий торговый контракт и эксплуатационные инварианты; не дублировать параметры здесь.
- [Start Here / карта](../V20_TradingSystem_M15/KIMI_START_HERE_R088.md) и [архитектура](../V20_TradingSystem_M15/R088_ARCHITECTURE_AND_SAFETY_20261122.md) — BASE→ordered patches→DERIVED, source paths, risk/safety и зависимости.
- [COC](CRITICAL_OPERATIONS_CONTRACT.md) — критические операции; [общий AGENTS](../AGENTS.md) — Git, полномочия; [HANDOFF](kimi/EXAM_AND_HANDOFF.md) — передача.

MAIN/SOURCE, DERIVED, INSTALLED и LIVE различаются; старый installed hash не является новым доказательством. HALTED не подтверждает broker FLAT. Не изменять торговые правила, запуск, FINAM, риск или LIVE без отдельного разрешения и действующих gates. Оба ИИ работают по одному контракту.

**C3.2 candidate 27.11.2026:** историческая [предыдущая редакция паспорта](https://github.com/alkospacer123/market-pattern-discovery/blob/2ac85eb5bcdd8757144898b5a27369329f4d125c/recovery/PROJECT_PASSPORT_V20.md) сохраняет решения 26.11, dated installed evidence и прежний exam scope. Актуальные статусы — только STATUS; ранее принятые испытания не повторять. Fallback/Skill migration ещё не приняты.
