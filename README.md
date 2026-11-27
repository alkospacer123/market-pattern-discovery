# Trading Systems — V20 / Control Center / Trading Research Lab

**27.11.2026 — FULL_PARITY_OWNER_ADMITTED:** этап II принят владельцем ([Roadmap](ROADMAP.md), [Recovery STATUS](recovery/STATUS.md), [#615 MERGED](https://github.com/alkospacer123/market-pattern-discovery/pull/615)). GPT и Kimi — равноправные инженерные агенты; полномочия конкретной операции определяются AGENTS/COC и отдельными разрешениями. Штатные области Code — V20 `C:\V20Lab` и CC `C:\Control Center`, TRL — `TradingResearchLab/` без постоянного локального корня; [Windows policy](recovery/kimi/WINDOWS_WORKSPACE_AND_ACCESS.md). Учебная копия не штатная зависимость, не OS sandbox; не обновлять и не удалять без отдельного решения. LIVE UNKNOWN.


> **Единый рабочий GitHub трёх проектов.** H1/M15 сохранены как необходимые V20-зависимости и источник исследований, а не новые LIVE-проекты. Контрольный GitHub-срез после этапа I: `main=41d0b48c1d33db29bc1b19497d558748b3db8fb4` (22.11.2026, Merge #589). Это **датированный pin**, а не обещание неизменности HEAD. Перед любой новой операцией повторно сверять GitHub SHA.

## Проекты — начинать здесь

| Область | Назначение | Канонический паспорт / рабочий контекст |
| --- | --- | --- |
| `V20_TradingSystem_M15/` | Shallow, OBV, Inside: код, R088, тесты, замороженные правила | [V20](recovery/PROJECT_PASSPORT_V20.md) · [STATUS](V20_TradingSystem_M15/STATUS.md) · [JOURNAL](V20_TradingSystem_M15/JOURNAL.md) |
| `ControlCenter/` | V20-панель, мониторинг, CC-07 и операторские команды | [Control Center](recovery/PROJECT_PASSPORT_CONTROL_CENTER.md) · [STATUS](ControlCenter/STATUS.md) · [JOURNAL](ControlCenter/JOURNAL.md) |
| `TradingResearchLab/` | Research, Evolution, Journal и воспроизводимость исследований | [TRL](recovery/PROJECT_PASSPORT_TRL.md) · [STATUS](TradingResearchLab/STATUS.md) · [journal/](TradingResearchLab/journal/) |

[**Сохранённые исследования и audit_only: точная классификация (22.11)**](recovery/RETAINED_RESEARCH_CLASSIFICATION_2026-11-22.md) — история H1/M15 отдельно от текущих инструкций.

**Порядок документов и правила устаревших источников:** [реестр полномочий документации](recovery/DOCUMENTATION_AUTHORITY_2026-11-22.md).

**Общие источники:** [AGENTS.md](AGENTS.md) — действующие правила обоих ИИ; [состояние GitHub](recovery/REPOSITORY_CURRENT_STATE.md); [Roadmap](ROADMAP.md); [база знаний](recovery/README.md).

## Исторические комплексы — сохранять до доказательства ненужности

- `TradingSystemLab/` — исторический H1 и рабочие библиотеки `TradingSystemLab.stage8_robot` для V20. Сотни тестов и тысячи результатов — не основание удалять исходные исследования.
- `IntradayLab/` — исторический M15 и необходимые V20 модули `IntradayLab.core`; множество `t3_m15_*` — воспроизводимая история, не новые LIVE-роботы.
- Старая корневая платформа Market Pattern Discovery (`src/`, `tests/`, `docs/`, `research/`, `schemas/`, `scripts/`, `config/`, `results/`, `evidence/` и шесть root reports) **удалена из `main` после [Merge #586](https://github.com/alkospacer123/market-pattern-discovery/pull/586)**: 233 удалённых path, 6 изменений и 4 добавления, только в проверенном scope. Все старые оригиналы доступны в [Git commit `09bca564…`](https://github.com/alkospacer123/market-pattern-discovery/tree/09bca5641cb5bb367e84505ebfc6f8c7f35e2620) и protected branch `archive/pre-root-legacy-20261122`. `audit_only/` **сохранён как необходимая H1 исследовательская зависимость** после выявленных прямых чтений в `signal_execution_diagnostic.py` и `tests/replay_stop_tick_grid.py`; [final audit / #590 BLOCKED](recovery/R7_STAGE_I_FINAL_ACCEPTANCE_20261122.md); [research_domains.md](research_domains.md) — архивный указатель для H1. [Состояние](recovery/REPOSITORY_CURRENT_STATE.md), [свидетельства приёмки](recovery/R7_ROOT_LEGACY_EXTRACTION_GATE_2026-11-22.md). История Git **не** является самостоятельной резервной копией.

**Почему старые корневые файлы не уничтожены?** [Ревизия docs / research / schemas / scripts / Smoke Run](recovery/ROOT_LEGACY_AUDIT_2026-11-21.md) — не текущие проекты, но пока важны для provenance и воспроизводимости старой платформы.

## Критические ограничения

- Для V20 последний задокументированный релиз — **60/30/45 + TP6 + Protect3 + HOLD5 без EXT2**, R088, N4/M15, NEXT_OPEN, SL 2×ATR14, риск 1,5% и cap 6%. Git хранит базу и **девять патчей**, установленный код может отличаться. Датированное наблюдение Running/HALTED от 20.11 **не означает** свежий ARMED/FINAM PASS.
- ZERO LOOK-AHEAD, причинное время доступности свечей, явные комиссии и проскальзывание, ликвидность, детерминизм и защита от оптимизации по OOS — обязательны.
- Старый корневой контракт «2025 locked TRUE OOS» относится к замороженным историческим исследованиям Market Pattern Discovery/H1/M15. Для V20/TRL 2018–2026 уже изучались; не запрещать исследования 2025 и не выдавать эту историю за untouched TRUE OOS.
- MAIN ≠ INSTALLED ≠ LIVE ≠ RESEARCH ≠ ARCHIVE. Только владелец разрешает Merge, торговлю, LIVE, риск, управление FINAM, перенос денег и удаление. Не публиковать токены/DPAPI, счета, секреты, личные журналы и SQLite.

## GitHub и Kimi

- [PR #583](https://github.com/alkospacer123/market-pattern-discovery/pull/583) удалил 11 594 исторических A/B/C+BBW файла с сохранением Git history, **но не провёл полного выноса старых исследований в отдельный архив**.
- [market-pattern-data](https://github.com/alkospacer123/market-pattern-data) — отдельные данные; [market-pattern-archive](https://github.com/alkospacer123/market-pattern-archive) — дополнительный публичный архив (по проверке в его main 26 файлов), **не требуется для ежедневной работы трёх систем** и не является независимым полным Recovery. До решения о сохранности не удалять.
- [Три проекта знаний Kimi](recovery/kimi/README.md), [KDR](recovery/kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md) и [Recovery STATUS](recovery/STATUS.md): обучение и квалификация приняты в документированных пределах, KDR 11/11; не повторять экзамены.
- Kimi Chat — общение и знания, Kimi Code — основной технический исполнитель, Work — резерв. [HANDOFF](recovery/kimi/EXAM_AND_HANDOFF.md): независимый контроль, один writer на scope, STOP/DEFER и безопасный runner обязательны. Допуск не доказывает полный GPT-outage, OS isolation или непроверенные remote controls.
- Финальный автономный backup + реальный cold restore V20, CC и TRL вне Intel/GitHub/обоих ИИ — после возвращения V20 к штатной работе и ≥7 последовательных календарных суток безаварийной эксплуатации всех трёх, по [Roadmap](ROADMAP.md).

**Порядок работы:** актуальный MAIN/рабочий ref, [AGENTS](AGENTS.md), профильный STATUS и последние релевантные JOURNAL → паспорт/применимый COC/первоисточники. После существенного результата обновить STATUS/JOURNAL в разрешённой ветке. Не читать весь репозиторий; исторические документы — свидетельства, не текущие инструкции.
