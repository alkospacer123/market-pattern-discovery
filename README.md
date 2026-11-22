# Trading Systems — V20 / Control Center / Trading Research Lab

> **Единый рабочий GitHub трёх проектов.** H1/M15 сохранены как необходимые V20-зависимости и источник исследований, а не новые LIVE-проекты. Проверенный после R7 `main=4f118ee1cdeced15406136401faabe4fdc3bb847` (22.11.2026). Перед любой новой операцией повторно сверять GitHub SHA.

## Проекты — начинать здесь

| Область | Назначение | Канонический паспорт |
| --- | --- | --- |
| `V20_TradingSystem_M15/` | Shallow, OBV, Inside: код, R088, тесты, замороженные правила | [V20](recovery/PROJECT_PASSPORT_V20.md) |
| `ControlCenter/` | V20-панель, мониторинг, CC-07 и операторские команды | [Control Center](recovery/PROJECT_PASSPORT_CONTROL_CENTER.md) |
| `TradingResearchLab/` | Research, Evolution, Journal и воспроизводимость исследований | [TRL](recovery/PROJECT_PASSPORT_TRL.md) |

**Общие источники:** [AGENTS.md](AGENTS.md) — действующие правила обоих ИИ; [состояние GitHub](recovery/REPOSITORY_CURRENT_STATE.md); [Roadmap](ROADMAP.md); [база знаний](recovery/README.md).

## Исторические комплексы — сохранять до доказательства ненужности

- `TradingSystemLab/` — исторический H1 и рабочие библиотеки `TradingSystemLab.stage8_robot` для V20. Сотни тестов и тысячи результатов — не основание удалять исходные исследования.
- `IntradayLab/` — исторический M15 и необходимые V20 модули `IntradayLab.core`; множество `t3_m15_*` — воспроизводимая история, не новые LIVE-роботы.
- Старая корневая платформа Market Pattern Discovery (`src/`, `tests/`, `docs/`, `research/`, `schemas/`, `scripts/`, `config/`, `results/`, `evidence/` и шесть root reports) **удалена из `main` после [Merge #586](https://github.com/alkospacer123/market-pattern-discovery/pull/586)**: 233 удалённых path, 6 изменений и 4 добавления, только в проверенном scope. Все старые оригиналы доступны в [Git commit `09bca564…`](https://github.com/alkospacer123/market-pattern-discovery/tree/09bca5641cb5bb367e84505ebfc6f8c7f35e2620) и protected branch `archive/pre-root-legacy-20261122`. `audit_only/` сохранён; [research_domains.md](research_domains.md) — архивный указатель для H1. [Состояние](recovery/REPOSITORY_CURRENT_STATE.md), [свидетельства приёмки](recovery/R7_ROOT_LEGACY_EXTRACTION_GATE_2026-11-22.md). История Git **не** является самостоятельной резервной копией.

**Почему старые корневые файлы не уничтожены?** [Ревизия docs / research / schemas / scripts / Smoke Run](recovery/ROOT_LEGACY_AUDIT_2026-11-21.md) — не текущие проекты, но пока важны для provenance и воспроизводимости старой платформы.

## Критические ограничения

- Для V20 последний задокументированный релиз — **60/30/45 + TP6 + Protect3 + HOLD5 без EXT2**, R088, N4/M15, NEXT_OPEN, SL 2×ATR14, риск 1,5% и cap 6%. Git хранит базу и **девять патчей**, установленный код может отличаться. Датированное наблюдение Running/HALTED от 20.11 **не означает** свежий ARMED/FINAM PASS.
- ZERO LOOK-AHEAD, причинное время доступности свечей, явные комиссии и проскальзывание, ликвидность, детерминизм и защита от оптимизации по OOS — обязательны.
- Старый корневой контракт «2025 locked TRUE OOS» относится к замороженным историческим исследованиям Market Pattern Discovery/H1/M15. Для V20/TRL 2018–2026 уже изучались; не запрещать исследования 2025 и не выдавать эту историю за untouched TRUE OOS.
- MAIN ≠ INSTALLED ≠ LIVE ≠ RESEARCH ≠ ARCHIVE. Только владелец разрешает Merge, торговлю, LIVE, риск, управление FINAM, перенос денег и удаление. Не публиковать токены/DPAPI, счета, секреты, личные журналы и SQLite.

## GitHub и Kimi

- [PR #583](https://github.com/alkospacer123/market-pattern-discovery/pull/583) удалил 11 594 исторических A/B/C+BBW файла с сохранением Git history, **но не провёл полного выноса старых исследований в отдельный архив**.
- [market-pattern-data](https://github.com/alkospacer123/market-pattern-data) — отдельные данные; [market-pattern-archive](https://github.com/alkospacer123/market-pattern-archive) — дополнительный публичный архив (по проверке в его main 26 файлов), **не требуется для ежедневной работы трёх систем** и не является независимым полным Recovery. До решения о сохранности не удалять.
- Kimi Chat — три логических проекта знаний из одного GitHub; **Kimi Code отдельно** должен получить проверенные доступы, выполнить практический offline-экзамен и взаимную передачу задач с GPT. Не считать настроенным до теста.
- Финальный автономный backup + реальный cold restore V20, CC и TRL вне Intel/GitHub/обоих ИИ — **после** всех исправлений и адаптации.

**Порядок чтения:** `AGENTS.md` → этот README → один из трёх паспортов → проектный README/исходники/тесты → датированный оригинал. Старые исследовательские README не являются общими операционными инструкциями.
