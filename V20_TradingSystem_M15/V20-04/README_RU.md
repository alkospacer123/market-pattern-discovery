# V20-04 — общий каркас трёх роботов: начата offline-разработка

**Утверждённые подэтапы V20-04.1–04.6** восстановлены в [docs/ROADMAP_DETAILED_RU.md](../docs/ROADMAP_DETAILED_RU.md); оперативные статусы — в [docs/TASK_TRACKER.csv](../docs/TASK_TRACKER.csv). Draft PR — это начало интеграции, а не PASS этапа 04.6.

**Основание:** решение владельца `docs/DECISION_V20_03_CLOSE_20261021_RU.md`; merge V20-03 `6f352acfac7ebdfabba73e143c4dfea3a6e48507`. Roadmap 8 этапов, V20-04 = разработка. **LIVE OFF**.

**Дополнение 22.10.2026:** [карточка пригодности рынка](MARKET_SUITABILITY_CARD_RU.md) реализована как независимая READONLY-диагностика в 04.2. Нужны проверка фактического Python-запуска, подключения к валидированным завершённым FINAM M15 и V20-05.1 offline causality/parity. Ни она, ни рост отдельных метрик НЕ фильтруют сделки и не меняют frozen V20.

**Проверка карточки v2, 22.10.2026:** [отчёт и таблицы](MARKET_CARD_RESEARCH_V2_RU.md), [машинные результаты/SHA256](MARKET_CARD_RESEARCH_V2.json). Исправлены CLV×Volume и строгий Inside, общий расчёт пяти групп используется CLI и историческим адаптером. Проверены исходы всех 4 986 опубликованных raw-сигналов; новые причинные сопоставления вне locked 2025 — 1 604. **61 offline unittest PASS**, классификация не доказана — реальные статусы `НЕ ОЦЕНЕНО`. Это не приёмка всего V20-04/V20-05.

## Что реализовано в этом Draft PR

- `v20_runtime/robots.json`: 3 независимые конфигурации Shallow, OBV, Inside для N4; отдельные root состояния и Windows Task names, отсутствие токенов и account IDs, режим `OFFLINE_ONLY`.
- `v20_runtime/frozen_adapter.py`: использование исходных frozen AST функций через существующий `V20-03/offline/stress_v20_03.py`, не переписывая формулы сигналов; требование завершённого M15 и немедленного `NEXT_OPEN`. Временный CSV-адаптер годится **только** для offline parity, не для LIVE.
- `v20_runtime/offline_planner.py`: три независимых процесса могут иметь один сигнал по одному инструменту; ограничения одной позиции/инструмент, одного нового входа/инструмент/сессию и двух входов/сессию. Шаг и округление стопа берутся из неизменённого H1 `TradingSystemLab/stage8_robot/execution_grid.py`, первоначальная база риска — из `risk.py`, ГО-ограничение — из `margin.py`. Дополнительно резервируется явный бюджет комиссии/проскальзывания. Режим `OFFLINE_REFERENCE_NOT_ORDER`.
- `v20_runtime/tests/test_offline_planner.py`: новые локальные тесты входа, сетки, ограничения риска и независимости.
- `V20-04/SOURCE_MAP.md`: **V20-04.1 SOURCE MAP PASS**; точные main / M15 pinned commits, Git blob SHA, H1 #493 transport/SLTP/state/GO и границы изоляции. Эта проверка документальная, а не runtime PASS.
- `v20_runtime/market_suitability.py`: детерминированная 20-сессионная универсальная READONLY-карточка любого корректного фьючерсного символа на подтверждённых завершённых M15 (N4, BR, серебро и т.д.), ATR Wilder / нормированная волатильность, directional efficiency, continuation, объём/неизвестные broker costs, наблюдаемая полнота и по одному диагностическому набору для всех трёх роботов. Только `НЕ ОЦЕНЕНО` или `НЕДОСТАТОЧНО ДАННЫХ` до отдельного подтверждения правила.
- `v20_runtime/market_suitability_cli.py`: разовый READONLY CLI с компактным текстом по умолчанию; числа через `--details` или `--format json`, без службы, токена, FINAM, SQLite или торговой логики.
- `v20_runtime/tests/test_market_suitability.py`: синтетические случаи для двух направлений изменения наблюдаемых метрик, 20-сессионного окна, bar/session causality, дыр в расписании и отсутствующих брокерских цен. **Исполнены в общей offline-проверке v2; PASS относится только к протестированным случаям.**

**Разделение аналитики и торговли:** `market_suitability.py`/CLI не читают `robots.json` и не выбирают состав N4. Любой новый символ допускается только к **аналитическому расчёту**, если переданы достоверные сессии; добавление инструмента к трём роботам требует отдельного решения и проверки. Вывод содержит `trading_instrument_authority=OPERATOR_ONLY` и всегда `affects_signals_or_risk=false`. До валидированных критериев пригодности статус — `НЕ ОЦЕНЕНО`. Новый сервис и торговый автоматический фильтр не создаются.

**Обновление:** зафиксирован [SHA-проверенный описательный эталон 2023–2026 YTD](MARKET_REFERENCE_2023_2026_RU.md): 3 423 причинно завершённых 20-сессионных окна по N4, медианы по годам. **Это не готовое доказательство пригодности по сделкам.** Добавлены `v20_runtime/market_verdict.py` и `tests/test_market_verdict.py` для трёх статусов **ДОПУСТИМО/НЕЙТРАЛЬНО/НЕДОПУСТИМО**, с отдельными `НЕ ОЦЕНЕНО` и `НЕДОСТАТОЧНО ДАННЫХ`. Эти статусы может выдавать лишь явно предоставленный и внешне проверенный causal/holdout профиль, обязательно со списком проверенных инструментов; **такого одобренного профиля сейчас нет**, поэтому реальные карточки остаются «НЕ ОЦЕНЕНО». 8 локальных автономных unittest проверок именно алгоритма меток — PASS; GitHub/Windows прогон общего проекта и каузальная проверка по frozen ledger пока не проведены. Профиль заявляет свою проверку через метаданные и требует фактической операторской сверки доказательств, не является самодоказательным. Никакой автоматической блокировки/изменения торгового списка.

### Одноразовый offline-вызов карточки

```sh
python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --input V20_closed_sessions.json --format json
python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --input V20_closed_sessions.json
python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --input V20_closed_sessions.json --details
python -m unittest V20_TradingSystem_M15.v20_runtime.tests.test_market_suitability -v
```

JSON snapshot содержит: `symbol`, `as_of_msk`, `completed_sessions` (массив с `day`, `closed_at`, `expected_opens`, `bars`), каждый bar: `open_time,open,high,low,close,volume`. Все времена — московские naive ISO, Open-labelled M15. `closed_at` и `expected_opens` **уже подтверждены внешней достоверной сессионной authority**; CLI не умеет их доказать и не обращается к брокеру. Дополнительный список `expected_session_days` из проверенного календаря позволяет выявить целиком пропущенные сессии; без него caller обязан подтвердить отсутствие пропусков, это явно отмечается в отчёте. Предыдущая карточка должна иметь ту же `metric_schema` v2. Опциональные поля `execution_readonly`: `price_step`, `tick_value_rub`, `lot_size`, `roundtrip_cost_rub`, `spread_price`, `initial_margin_rub`. Без них значения остаются неизвестными. Поставляемый CLI выводит результат в stdout; интеграция с реальным state/log — часть оставшегося 04.2/04.5. Последние 20 подтверждённых сессий вытесняют предыдущие автоматически, прежняя карточка подаётся `--previous` и используется **только** для дельт, не для оценки пригодности.

## V20-04.2 — исторический эталон и доказательная пригодность

- `MARKET_REFERENCE_2023_2026_RU.md`: зафиксирована фактическая характеристика 3 423 двадцатисессионных окон по SHA-verified frozen M15 всех N4 за 2023–2026 YTD. **Только описательная статистика, не пороги пригодности.**
- `MARKET_OUTCOME_EXPLORATORY_RU.md`: результаты причинной привязки признаков по 20 завершённым сессиям до входа к 957 сделкам из усечённого журнала 997 из 1 589. Не доказано, что больший ATR / направленность обеспечивают лучшее математическое ожидание; границы не выбирались.
- `v20_runtime/market_reference_descriptive.py`: автономный offline расчёт рынка с проверкой замороженных SHA256, без FINAM и торговых команд. Стандартной библиотеки Python достаточно; v2 исключает locked 2025 и сохраняет неполные дни в окнах. Используйте:

```sh
python -m V20_TradingSystem_M15.v20_runtime.market_reference_descriptive --data-dir <folder_with_N4_M15_csv> --output market_descriptive.json
```

- `v20_runtime/market_verdict.py` и `tests/test_market_verdict.py`: поддержка статусов **ДОПУСТИМО / НЕЙТРАЛЬНО / НЕДОПУСТИМО** при наличии **независимо подтверждённого** причинного эталона. Сейчас такого профиля нет, поэтому корректный результат — **НЕ ОЦЕНЕНО**. Отсутствие достаточной истории — **НЕДОСТАТОЧНО ДАННЫХ**. Модуль не читает `robots.json` и не вызывает торговые API.
- В текущем checkout 61 runtime offline test **PASS**, включая синтетическую проверку статусов/хронологии; экономическая пригодность, Windows и FINAM не подтверждены.
- Стопы, сигналы и frozen N4 роботов не менялись; карточка — независимое средство аналитика.

## V20-04.3 — начата прямая интеграция H1 StateStore (OFFLINE ONLY)

- `v20_runtime/h1_state_journal.py` импортирует без переписывания проверенные H1 `StateStore` и `InstanceLock`. Использует отдельные `V20Lab/shallow|obv|inside/state/v20-offline-reference.sqlite3` с точной robot/account-hash identity; защищённые каталоги H1/M15 и чужая SQLite запрещены; reference-планы записываются атомарно и переживают перезапуск. Записи **не являются** `persist_intent` для реальной заявки; broker intents/fills намеренно не создаются.
- `v20_runtime/tests/test_h1_state_journal.py`: синтетические offline проверки трёх независимых счетов, восстановления, двойного экземпляра и 2/1 session caps; 10 существующих тестов PASS в текущем checkout, без приёмки реальной интеграции.
- `ProductionService` и `ProductionRuntime` H1 жестко привязаны к H1/T3 identity и `DecisionCore`, поэтому прямой вызов с M15 не работает. Следующий обязательный шаг в этом же 04.3 — тонкий V20-адаптер к H1 FINAM order/SLTP/fill/reconciliation контрактам, без изменений `TradingSystemLab/`. Защита фактических частичных исполнений и restart остаётся НЕ РЕАЛИЗОВАНА. **04.3 PARTIAL / НЕ ГОТОВО К LIVE**.

Проверки нового офлайн-слоя (из корня репозитория, без токенов):

```sh
python -m unittest V20_TradingSystem_M15.v20_runtime.tests.test_h1_state_journal -v
```

## Проверенная база повторного использования из актуального GitHub main

| Назначение | Существующий источник |
|---|---|
| FINAM/auth/bars | `TradingSystemLab/stage8_robot/finam_api.py`, `instrument_resolver.py`, `market_data.py` |
| Order/SLTP и broker fill | `live_execution.py`, `protective_stop_contract.py`, `production_broker_state.py`, `production_service.py` |
| Stop tick grid | `execution_grid.py` — `initial_projection` / `project_stop` |
| Quantity/R15/ГО | `risk.py` — `size_position`; `margin.py` — `cap_r15_by_margin` |
| State/ledger/restart/kill-switch | `state.py`, `production_runtime.py`, `reconciliation.py`, `operations.py`, `production_safety_gate.py` |
| M15 completed/window | `IntradayLab/core/m15_bars.py`, `calendar.py`, `execution.py` |
| Frozen V20 signals | `V20_TradingSystem_M15/research_original_v20/base.py`, `run.py`, `legacy_v4/study_v4.py` |

H1 production runtime содержит H1/T3-специфический `DecisionCore`. Нельзя просто переключить таймфрейм и считать это готовым V20. Дальнейшая минимальная адаптация — заменить только источник сигналов/порядок M15, сохранив рабочие транспорт, SLTP, ledger/recovery и safeguards после доказанного интерфейсного соответствия.

## Не завершено

1. Offline signal-by-signal parity с 1589 frozen trade reference и N4 feed (выполнить из исходного файла, без изменения стратегии); отсутствие look-ahead после рестарта и свечных разрывов.
2. Реальное позиционное state-machine после FINAM fills, поправка стопа к фактической цене исполнения, защита 100%, комиссии/ГО/сквозная экспозиция трёх счетов.
3. Три независимых исполняемых процесса и persistence, recovery, защитные stop/exit; В20-05 offline acceptance, В20-06 READONLY, В20-07 Intel и В20-08 разрешённый LIVE.

Текущий код — **не запускоспособный торговый робот** и не допуск к V20-05. Никакие ордера, FINAM токены, настоящие Windows Tasks, production H1/IntradayLab не трогались.
