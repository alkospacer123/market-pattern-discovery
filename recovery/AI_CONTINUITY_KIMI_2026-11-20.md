# GPT ↔ Kimi — адаптация и проверяемая преемственность

**Обновлённая инструкция проекта:** [PROJECT_INSTRUCTIONS_CURRENT_2026-11-20.md](PROJECT_INSTRUCTIONS_CURRENT_2026-11-20.md). Три проекта Kimi используют один действующий `market-pattern-discovery` и отдельный исторический архив с 8 отчётами, а не отдельные три рабочих GitHub. Доступ Kimi и экзамены пока не PASS.

**Актуальный каталог:** [Kimi R1.1 — проверяемые первоисточники](KIMI_R1_1_VERIFIED_SOURCE_INDEX_2026-11-20.md) и [состояние после исторического закрытия](RECOVERY_STATE_POST_CLOSURE_2026-11-20.md). Десять исторических Draft теперь закрыты без Merge; они ARCHIVE и не должны смешиваться с рабочим кодом трёх проектов.

**Целевое состояние, ещё НЕ PASS.** После R7 создать три отдельных проекта Kimi Chat и изолированный Kimi Code, **но все три используют один рабочий GitHub `market-pattern-discovery`**. [Обязательная карта шести каталогов и legacy-зависимостей](KIMI_REPOSITORY_BOUNDARIES_2026-11-20.md). `market-pattern-archive` — дополнительный публичный архив, `market-pattern-data` — отдельные данные. До R7 допустима подготовка read-only документов.

| Проект | Глубокая передача знаний | Экзамен |
|---|---|---|
| V20 Trading System | Shallow/OBV/Inside, N4/M15, NEXT_OPEN, FINAM, SLTP, риск, R088, 9-patch stack, Protect3/HOLD5, инциденты | Отличить MAIN, INSTALLED и LIVE, показать patch stack, не принять HALTED за ARMED |
| Control Center | Панель 8502, exporter, CC-07, Windows, operator gates, интерфейс против broker truth | Найти установленную версию, объяснить ограничения UI/Task и readonly диагностику |
| Trading Research Lab | Research/Evolution/Journal, R060/R086/R089/R097/R098, исторические и отрицательные результаты | Найти ZIP/XLSX и их SHA; объяснить выбор 60/30/45 при исследовательском лидере 75/30/30 по Net/PF |

**R1.1** фундамент и каталог источников; **R1.2** V20 deep dive; **R1.3** CC deep dive; **R1.4** TRL deep dive; **R1.5** экзамен по первоисточникам; **R1.6** передача незавершённой задачи GPT ↔ Kimi.

**R2:** Kimi Chat не заменяет Kimi Code; нужны отдельные права/аудит, GitHub branch/commit/PR/CI, повторный вход, изолированные рабочие копии. **R3:** независимое review и безопасная совместная задача без торговых полномочий.

Оператор единственный, кто разрешает merge, установку и LIVE. Запрещено разглашать FINAM/DPAPI, реальные идентификаторы счетов и приватные журналы. Данные в чатах не заменяют Git и независимый Recovery.
