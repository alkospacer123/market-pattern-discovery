# V20-04 — общий каркас трёх роботов: начата offline-разработка

**Утверждённые подэтапы V20-04.1–04.6** восстановлены в [docs/ROADMAP_DETAILED_RU.md](../docs/ROADMAP_DETAILED_RU.md); оперативные статусы — в [docs/TASK_TRACKER.csv](../docs/TASK_TRACKER.csv). Draft PR — это начало интеграции, а не PASS этапа 04.6.

**Основание:** решение владельца `docs/DECISION_V20_03_CLOSE_20261021_RU.md`; merge V20-03 `6f352acfac7ebdfabba73e143c4dfea3a6e48507`. Roadmap 8 этапов, V20-04 = разработка. **LIVE OFF**.

**Дополнение 22.10.2026:** [карточка пригодности рынка](MARKET_SUITABILITY_CARD_RU.md) реализована как независимая READONLY-диагностика в 04.2. Нужны проверка фактического Python-запуска, подключения к валидированным завершённым FINAM M15 и V20-05.1 offline causality/parity. Ни она, ни рост отдельных метрик НЕ фильтруют сделки и не меняют frozen V20.

## Что реализовано в этом Draft PR

- `v20_runtime/robots.json`: 3 независимые конфигурации Shallow, OBV, Inside для N4; отдельные root состояния и Windows Task names, отсутствие токенов и account IDs, режим `OFFLINE_ONLY`.
- `v20_runtime/frozen_adapter.py`: использование исходных frozen AST функций через существующий `V20-03/offline/stress_v20_03.py`, не переписывая формулы сигналов; требование завершённого M15 и немедленного `NEXT_OPEN`. Временный CSV-адаптер годится **только** для offline parity, не для LIVE.
- `v20_runtime/offline_planner.py`: три независимых процесса могут иметь один сигнал по одному инструменту; ограничения одной позиции/инструмент, одного нового входа/инструмент/сессию и двух входов/сессию. Шаг и округление стопа берутся из неизменённого H1 `TradingSystemLab/stage8_robot/execution_grid.py`, первоначальная база риска — из `risk.py`, ГО-ограничение — из `margin.py`. Дополнительно резервируется явный бюджет комиссии/проскальзывания. Режим `OFFLINE_REFERENCE_NOT_ORDER`.
- `v20_runtime/tests/test_offline_planner.py`: новые локальные тесты входа, сетки, ограничения риска и независимости.
- `V20-04/SOURCE_MAP.md`: **V20-04.1 SOURCE MAP PASS**; точные main / M15 pinned commits, Git blob SHA, H1 #493 transport/SLTP/state/GO и границы изоляции. Эта проверка документальная, а не runtime PASS.
- `v20_runtime/market_suitability.py`: детерминированная 20-сессионная карточка N4 на подтверждённых завершённых M15, ATR Wilder / нормированная волатильность, directional efficiency, continuation, объём/неизвестные broker costs, наблюдаемая полнота и по одному диагностическому набору для всех трёх роботов. Только `НЕ ОЦЕНЕНО` или `НЕДОСТАТОЧНО ДАННЫХ` до отдельного подтверждения правила.
- `v20_runtime/market_suitability_cli.py`: разовый READONLY CLI для JSON/текста, без службы, токена, FINAM, SQLite или торговой логики.
- `v20_runtime/tests/test_market_suitability.py`: синтетические случаи для двух направлений изменения наблюдаемых метрик, 20-сессионного окна, bar/session causality, дыр в расписании и отсутствующих брокерских цен. **Добавлены, но пока не исполнены в Python.**

### Одноразовый offline-вызов карточки

```sh
python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --input V20_closed_sessions.json --format json
python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --input V20_closed_sessions.json --format text
python -m unittest V20_TradingSystem_M15.v20_runtime.tests.test_market_suitability -v
```

JSON snapshot содержит: `symbol`, `as_of_msk`, `completed_sessions` (массив с `day`, `closed_at`, `expected_opens`, `bars`), каждый bar: `open_time,open,high,low,close,volume`. Все времена — московские naive ISO, Open-labelled M15. `closed_at` и `expected_opens` **уже подтверждены внешней достоверной сессионной authority**; CLI не умеет их доказать и не обращается к брокеру. Опциональные поля `execution_readonly`: `price_step`, `tick_value_rub`, `roundtrip_cost_rub`, `spread_price`, `initial_margin_rub`. Без них значения остаются неизвестными. Поставляемый CLI выводит результат в stdout; интеграция с реальным state/log — часть оставшегося 04.2/04.5. Последние 20 подтверждённых сессий вытесняют предыдущие автоматически, прежняя карточка подаётся `--previous` и используется **только** для дельт, не для оценки пригодности.

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
