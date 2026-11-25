# V20 START HERE — GPT / Kimi Chat / Kimi Code (аудит 22.11.2026)

**SOURCE checkpoint**: `market-pattern-discovery/main` = `0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52` (Merge #591, проверен через GitHub API 22.11). Это зафиксированный базовый срез для данного документа, а не вечный HEAD. **Никаких изменений Intel/FINAM/LIVE не выполнялось.**

## Обязательный маршрут чтения (в таком порядке)

1. [Общий AGENTS](../AGENTS.md) → [реестр полномочий документации](../recovery/DOCUMENTATION_AUTHORITY_2026-11-22.md) → [паспорт V20](../recovery/PROJECT_PASSPORT_V20.md). Общие полномочия и границы.
2. [Проектный AGENTS](AGENTS.md) → [R088 LIVE release от 20.11](V20-08/LIVE_RELEASE_R088_20261120_RU.md). Выбранные правила, физическое **датированное** подтверждение, девять patch names и ограничения.
3. [R088 ARCHITECTURE / SOURCE MAP / RISK / SAFETY](R088_ARCHITECTURE_AND_SAFETY_20261122.md). Операционный код, два связанных Git Python-модуля, SQLite/H1/M15, предохранители, CC-07/CC-08.
4. [R088 TEST / REPRODUCIBILITY / EXAM](R088_OFFLINE_EXAM_20261122.md). Offline-only команды, ожидаемые Git blob SHA и отрицательные тесты; экзамен для Kimi Code.
5. [Инвентаризация документации и находки](V20_DOCUMENTATION_AUDIT_20261122.md). Для каждого сохранённого Markdown — `CURRENT`, `HISTORICAL`, `RESEARCH`, `SOURCE_EVIDENCE`, `SUPERSEDED` или `UNKNOWN`. Исторические материалы не переписываются.
6. Только при конкретном вопросе: [операторский runbook V20-08.5](V20-08/RUNBOOK_08_5_RU.md), [исторический этапный Roadmap](docs/ROADMAP_DETAILED_RU.md), [исходный frozen-сигнальный SOURCE_MAP 22.10](V20-04/SOURCE_MAP.md) и датированные R070/R088 исследования. Старые названия `CURRENT`, `Draft`, `TIME3`, `EXT2 ON`, `LIVE OFF` в них **не** задают R088.

## Разделять пять состояний (строго)

| Состояние | Что доказывает | Чего НЕ доказывает |
| --- | --- | --- |
| `MAIN` | Принятый GitHub commit, его базовые файлы, патчи, документы | Что конкретный blob установлен на Intel |
| `INSTALLED` | Подтверждение локального SHA и результата установщика на определённую дату | Текущий ARMED, FINAM баланс, SLTP |
| `LIVE` | **Только свежая** сверка Tasks, kill switches, FINAM позиций/заявок/защит | Не выводится из CI, Git, истории PR или Streamlit heartbeat |
| `RESEARCH` | Описательная/offline проверка на использованной истории | Новый untouched TRUE OOS или торговый допуск |
| `ARCHIVE` | Сохранённый протокол/скрипт/SHA старого этапа | Текущая разрешённая модель или возможность автономного восстановления |

**На момент данного GitHub-only аудита LIVE = UNKNOWN.** Подтверждён лишь исторический результат установки 20.11: `PASS_3_RUNNING_HALTED_FRESH_CYCLES`. Актуальные ARMED/FINAM/SLTP/состояния счетов недоступны; не называть их PASS.

## Утверждённое ядро, в одну строку

**Shallow + OBV + Inside / N4 / M15 / Market NEXT_OPEN / SL 2×ATR14 Wilder / риск 1,5% и номинальный cap 6% на счёт / распределение капитала 60/30/45 / TP6 / Protect3 (+3R → SL +1R после завершённой M15) / HOLD5 (выход на первом подтверждённом Open шестой наблюдаемой сессии) / EXT2 OFF / выходные: новые входы OFF.** Замороженные сигналы не менять. 60/30/45 — утверждённая модель распределения, не свидетельство текущих денежных остатков FINAM.

## Правило для двух Kimi

**Kimi Chat:** читать документацию, находить верные пути/SHA, отличать historical от LIVE, не объявлять статус без источника, не делать Git/LIVE-операций от лица оператора.

**Kimi Code:** только отдельный одноразовый offline checkout с фиксированным SHA, точные Git blob проверки, `git apply --check` до применения в scratch, mock/unit без FINAM, журнал команд/stdout/exit/Git diff, один Draft PR для разрешённых будущих документальных изменений. Не деплоить, не MERGE, не ARM/HALT, не открывать реальные заявки.

**2025–2026 уже исследованы для V20/TRL и не являются untouched TRUE OOS**. Оценки PF из этого периода нельзя выдавать за независимую будущую валидацию. Защита ZERO LOOK-AHEAD остаётся обязательной.

## История GitHub (фактическая, не «Draft» по старому тексту)

PR [#567](https://github.com/alkospacer123/market-pattern-discovery/pull/567), [#574](https://github.com/alkospacer123/market-pattern-discovery/pull/574), [#575](https://github.com/alkospacer123/market-pattern-discovery/pull/575) — **MERGED**, последовательность сохранена; Stage I [#583](https://github.com/alkospacer123/market-pattern-discovery/pull/583), #585–#589, #591 — **MERGED**. [#590](https://github.com/alkospacer123/market-pattern-discovery/pull/590) — **CLOSED without Merge**, H1 audit-only dependency сохранена. Это история принятия источников, не разрешение торговать.

**Перед любыми последующими действиями заново прочитать `main`, перепроверить SHA и не переносить эти статусные выводы на новую дату без доказательств.**

## Critical Operations Contract — обязательный hazard-слой

После source map и R088 release читай [Critical Operations Contract](../recovery/CRITICAL_OPERATIONS_CONTRACT.md). Для ARMED/HALTED, Protect3 и HOLD5 используй его `COC-V20-*` IDs вместе с фактическим BASE + ordered patches. Контракт не заменяет DERIVED/INSTALLED/LIVE проверки и не разрешает операции. Single-trial и основной R088 LIVE path не смешивать.
