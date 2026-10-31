# TRL-00.2 — первичная инвентаризация исследовательских ресурсов

**Дата:** 2026-10-31  
**Статус:** PARTIAL — инвентаризация начата, наличие основных ресурсов подтверждено; полный реестр V1–V24 и сквозная проверка котировок не завершены.  
**Режим:** только GitHub GET/read; торговая логика, FINAM, LIVE-данные и настройки не менялись.

## 1. Контрольные версии проверенных репозиториев

| Репозиторий | Ветка | Проверенный SHA | Назначение | Ограничение |
|---|---|---|---|---|
| [market-pattern-discovery](https://github.com/alkospacer123/market-pattern-discovery) | main | `6f352acfac7ebdfabba73e143c4dfea3a6e48507` | Исследовательские библиотеки, IntradayLab, TradingSystemLab, V20 | `main` содержит исторические исследовательские документы; он **не** подтверждает текущий статус LIVE |
| [market-pattern-data](https://github.com/alkospacer123/market-pattern-data) | main | `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8` | Сохранённые рыночные CSV | Периоды, полнота, тик-сетки и происхождение всех серий ещё не переаудированы |
| `market-pattern-autonomous-engine` (private) | main | `dae6dd4612194937f296cd3634cc84e1deb654bd` | Старый автономный прототип поиска | Архивный опыт; **не** основа будущего универсального AI |

Доступ к трём репозиториям подтверждён через подключённый GitHub. Ничего не клонировалось и не копировалось в LIVE.

## 2. Подтверждённые котировки

**2.1.** [`market-pattern-data/forever/`](https://github.com/alkospacer123/market-pattern-data/tree/main/forever): в каталогах **CNYRUBF, GLDRUBF, IMOEXF, USDRUBF** физически присутствуют **M5, M15, M30, H1** — всего **16 CSV**. Один файл `CNYRUBF_H1.csv` проверен построчно в начале: заголовок `Ticker;Datetime;Open;High;Low;Close;Volume`, первая запись 2022-04-26. Полный диапазон и качество остальных файлов пока **NOT VERIFIED**.

**2.2.** [`market-pattern-data/futures_quarterly/`](https://github.com/alkospacer123/market-pattern-data/tree/main/futures_quarterly): каталоги **BR, CNY, GD, MIX, NG, Si**, у каждого обнаружены **H1 и M30** — всего **12 CSV**. Отдельно не проверены охват и непрерывность каждого ряда.

**2.3.** [`market-pattern-data/2026/`](https://github.com/alkospacer123/market-pattern-data/tree/main/2026): каталоги **CNY и Si**; обнаружены квартальные файлы M1, M5, M15, M30, H1 с именами 2023_Q1–2026_Q2 (не все кварталы присутствуют), а также D1_2023_2026. Имя файла не доказывает фактический временной охват.

**2.4.** История 2018–2022 V20 имеет **существенные ограничения**. [`V20-03/DATA_AUDIT_SUMMARY.json`](https://github.com/alkospacer123/market-pattern-discovery/blob/main/V20_TradingSystem_M15/V20-03/DATA_AUDIT_SUMMARY.json) описывает 43 квартальные M15-серии: CNY только с 2022, MIX/Si — с 2018; GLD отсутствует. [`ACCEPTANCE_V20_03.json`](https://github.com/alkospacer123/market-pattern-discovery/blob/main/V20_TradingSystem_M15/V20-03/ACCEPTANCE_V20_03.json) фиксирует `PARTIAL/HOLD`, `independent_OOS=false`, `full_N4=false`. Это сведения из опубликованного аудита, **не новый аудит исходных CSV**.

## 3. Подтверждённые исследовательские результаты и код

| Группа | Путь / материалы | Что реально подтверждено |
|---|---|---|
| V20 frozen source | [`V20_TradingSystem_M15/research_original_v20/`](https://github.com/alkospacer123/market-pattern-discovery/tree/main/V20_TradingSystem_M15/research_original_v20) | `base.py`, `run.py`, `PROTOCOL_RU.md`, `legacy_v4/`; источник трёх сигналов |
| V20 lineage | [`V20_TradingSystem_M15/docs/RESEARCH_LINEAGE.json`](https://github.com/alkospacer123/market-pattern-discovery/blob/main/V20_TradingSystem_M15/docs/RESEARCH_LINEAGE.json) | Опубликованы SHA256 frozen-кода, оригинальных торговых таблиц и исходных ZIP |
| V20 независимая сверка | [`V20-02_AUDIT/`](https://github.com/alkospacer123/market-pattern-discovery/tree/main/V20_TradingSystem_M15/V20-02_AUDIT) | `replay_independent.py`, `SIGNAL_AUDIT.csv`, `PARITY_SUMMARY.csv`, `ACCEPTANCE_V20_02.json`; в отчёте — соответствие 1 589 эталонных сделок |
| V20 исторический стресс | [`V20-03/`](https://github.com/alkospacer123/market-pattern-discovery/tree/main/V20_TradingSystem_M15/V20-03) | `offline/stress_v20_03.py`, тест причинности, результаты и отчёты; опубликованный статус `PARTIAL/HOLD` |
| V20 диагностика | [`V20-03/comparison/`](https://github.com/alkospacer123/market-pattern-discovery/tree/main/V20_TradingSystem_M15/V20-03/comparison) | `DIAGNOSTIC_REPLAY_TRADES.csv`, `YEARLY_STABILITY.csv`, `TRADE_DISTRIBUTION.csv`, `build_diagnostics.py`, `quote_diagnostics.py` |
| IntradayLab | [`IntradayLab/tools/`](https://github.com/alkospacer123/market-pattern-discovery/tree/main/IntradayLab/tools), [`strategies/`](https://github.com/alkospacer123/market-pattern-discovery/tree/main/IntradayLab/strategies) | Реальные аудиторские и исследовательские скрипты, стратегии: squeeze, retest, breakout, pullback и др.; есть отчёты и optimization registry |
| TradingSystemLab | [`TradingSystemLab/`](https://github.com/alkospacer123/market-pattern-discovery/tree/main/TradingSystemLab) | Существующие исследовательские entry points, walk-forward, robustness, OOS, портфельные инструменты |
| Общий test/validation | [`src/market_pattern_discovery/backtest/`](https://github.com/alkospacer123/market-pattern-discovery/tree/main/src/market_pattern_discovery/backtest), [`validation/`](https://github.com/alkospacer123/market-pattern-discovery/tree/main/src/market_pattern_discovery/validation) | `engine.py`, `costs.py`, валидаторы и тесты; исполнимость с текущими данными **не проверялась** |
| Старый autonomous Research | [`docs/marketai_reality_audit.md`](https://github.com/alkospacer123/market-pattern-discovery/blob/main/docs/marketai_reality_audit.md) | Исторический аудит обнаружил, что KNOWN/UNKNOWN production handlers фактически не выполняли полноценный поиск; **не возобновлять этот проект** |

**Важная методологическая деталь.** Корневой [`AGENTS.md`](https://github.com/alkospacer123/market-pattern-discovery/blob/main/AGENTS.md) содержит особый режим `2025 locked TRUE OOS` для раннего исследовательского движка. В V20 2025 и другие годы уже исследовались. Нельзя механически переносить OOS-метки между разными ветками исследования.

## 4. Пробелы и ограничения

1. **V1–V24:** не найден подтверждённый единый каталог со всеми 24 сериями и их окончательными результатами. Поиск кода по `V23/V24` не дал результатов; это **не доказательство отсутствия** архивов (история PR, старые ZIP, внешние каталоги, неиндексированные ветки). Не восстанавливать результаты по памяти или догадкам.
2. **Исходные архивы:** документация V20 содержит SHA256 `search_v20_complete.zip`, `newtrend_v4_complete.zip`, журналов и `2018-2022.zip`, но полные архивы не подтверждены в репозитории. В `README_RUN_RU.md` прямо указано, что оригинальные ZIP и perpetual-входы остаются вне Git.
3. **Котировки:** наличие CSV подтверждено, но ещё не проведены сквозные проверки диапазонов, разрывов, дубликатов, времени, тик-сеток, роллов и актуальности.
4. **Исполнимость:** скрипты и тесты найдены, но ни один replay/tester в рамках TRL-00 не запускался.
5. **V20 READONLY:** известен принцип безопасного выгрузочного контура; актуальный источник для ежемесячной аналитики и его схема ещё не проверены по независимому рабочему снимку. Пункт 00.5 остаётся открытым. Доступ к production SQLite, FINAM и токенам не нужен и не разрешён.

## 5. Решения TRL-00

- **00.1 — PASS (документы):** рамки и исследовательская методика утверждены в `TRL_Project_Instructions.md` и `TRL_Roadmap_1_0.md`.
- **00.2 — PARTIAL:** базовые репозитории, источники, код и отчёты физически установлены; требуется восстановить реестр V1–V24, проверить охват CSV и работоспособность выбранных тестеров.
- **00.3 / 00.4 / 00.5 — OPEN:** структура, шаблоны и READONLY-контракт — следующие пункты TRL-00.
- Никаких новых стратегий/тестеров/монитора не создавать до закрытия инвентаризации.
- Изменения LIVE: **0**.

## 6. Следующие действия (в рамках TRL)

1. Проверить архивные ветки/PR и отчёты, восстановить максимально возможный реестр V1–V24 (идентификатор, идея, источник, итог, путь, ограничения).
2. Сделать выборочный аудит заголовков и временных границ CSV, собрать таблицу фактического покрытия и пробелов; не дублировать исходные данные.
3. Составить таблицу `тестер → входные файлы → назначение → версия → воспроизводимость`. Проверка запуска — отдельно, без LIVE.
4. На этапе 00.5 подтвердить существующий безопасный READONLY-экспорт V20 и согласовать поля месячной карточки.

**Статус TRL-00 в целом: IN PROGRESS.**
