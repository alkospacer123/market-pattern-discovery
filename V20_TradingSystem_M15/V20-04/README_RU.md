# V20-04 — общий каркас трёх роботов: начата offline-разработка

**Утверждённые подэтапы V20-04.1–04.6** восстановлены в [docs/ROADMAP_DETAILED_RU.md](../docs/ROADMAP_DETAILED_RU.md); оперативные статусы — в [docs/TASK_TRACKER.csv](../docs/TASK_TRACKER.csv). Draft PR — это начало интеграции, а не PASS этапа 04.6.

**Основание:** решение владельца `docs/DECISION_V20_03_CLOSE_20261021_RU.md`; merge V20-03 `6f352acfac7ebdfabba73e143c4dfea3a6e48507`. Roadmap 8 этапов, V20-04 = разработка. **LIVE OFF**.

**Дополнение 22.10.2026 (пока только требование, не реализованная функция):** добавить компактную информационную [карточку пригодности рынка](MARKET_SUITABILITY_CARD_RU.md) по нескольким метрикам, ежедневный пересчёт на завершённых сессиях и наблюдение восстановления благоприятного режима. Входит в 04.2 / 05.1, НЕ является торговым фильтром; не менять frozen V20 и не вводить новую службу.

## Что реализовано в этом Draft PR

- `v20_runtime/robots.json`: 3 независимые конфигурации Shallow, OBV, Inside для N4; отдельные root состояния и Windows Task names, отсутствие токенов и account IDs, режим `OFFLINE_ONLY`.
- `v20_runtime/frozen_adapter.py`: использование исходных frozen AST функций через существующий `V20-03/offline/stress_v20_03.py`, не переписывая формулы сигналов; требование завершённого M15 и немедленного `NEXT_OPEN`. Временный CSV-адаптер годится **только** для offline parity, не для LIVE.
- `v20_runtime/offline_planner.py`: три независимых процесса могут иметь один сигнал по одному инструменту; ограничения одной позиции/инструмент, одного нового входа/инструмент/сессию и двух входов/сессию. Шаг и округление стопа берутся из неизменённого H1 `TradingSystemLab/stage8_robot/execution_grid.py`, первоначальная база риска — из `risk.py`, ГО-ограничение — из `margin.py`. Дополнительно резервируется явный бюджет комиссии/проскальзывания. Режим `OFFLINE_REFERENCE_NOT_ORDER`.
- `v20_runtime/tests/test_offline_planner.py`: новые локальные тесты входа, сетки, ограничения риска и независимости.

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
