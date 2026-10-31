# TRL-00.2 — карта повторного использования исследовательских тестеров

**Дата:** 2026-10-31  
**Метод:** GitHub file/tree inspection. Никакой скрипт не исполнялся и ни одно исследование не запускалось.

| Назначение | Найденный модуль | Источники / необходимые входы | Ограничение и пригодность |
|---|---|---|---|
| V20: воспроизведение трёх замороженных стратегий | `V20_TradingSystem_M15/research_original_v20/{base.py,run.py}` | Исходные M15 в `marketdata_m15` + конфигурация источника | **SOURCE CONFIRMED**; код фиксирует исходные правила, не менять |
| V20: независимый replay | `V20_TradingSystem_M15/V20-02_AUDIT/replay_independent.py` | Полный пакет `V20_Autonomous` рядом с аудиторским каталогом (явно проверяется в коде), включая marketdata/inside signals | **SOURCE CONFIRMED / INPUT PACKAGE UNVERIFIED**; публикация аудита есть, чистый checkout сам по себе недостаточен |
| V20: ранний stress 2018–2022 | `V20_TradingSystem_M15/V20-03/offline/stress_v20_03.py` | 43 M15 квартальных ряда + сохранённый frozen code, pandas/numpy; roll rules | **SOURCE CONFIRMED / OOS PARTIAL/HOLD**; данные не полный N4; не переносить критерии без оговорок |
| V20: поздняя диагностика и сравнение | `V20_TradingSystem_M15/V20-03/comparison/{build_diagnostics.py,quote_diagnostics.py}` | `market-pattern-data/forever`, оригинальный `2018-2022.zip`, внешний `--work`, публикуемые manifest/checksum | **SOURCE CONFIRMED / EXTERNAL ZIP UNVERIFIED**; строит сравнение, не даёт самостоятельный новый OOS |
| IntradayLab: независимая проверка сделок | `IntradayLab/tools/audit_canonical_baseline.py` | `IntradayLab/config/orb_a_base_2023_canonical_v1.json`, raw M5/M15 и ledger | **SOURCE CONFIRMED / EXECUTION NOT TESTED**; специализированный аудитор, не универсальный тестер |
| IntradayLab: историческая исследовательская база | `IntradayLab/tools/run_*baseline.py`, `audit_*.py`, `strategies/*.py` | Ранее согласованные конфигурации, M5/M15 и связанные отчёты | **MANY EXISTING MODULES**; выбрать конкретный тестер по стратегии и проверить исполнение отдельно |
| TradingSystemLab: системный H1 WF | `TradingSystemLab/run_t3_walk_forward.py` | `market-pattern-data/2026/{CNY,Si}/*_H1_2023/2024_Q*.csv`, T3 frozen config; из кода видно исключение 2025+ | **SOURCE CONFIRMED**; ранний OOS-контракт для этого исследования, не общий TRL-OOS 2026 |
| TradingSystemLab: портфель/robustness | `TradingSystemLab/portfolio/`, `robustness/`, `run_phase6_portfolio.py`, `run_t3_parameter_robustness.py` | Утверждённые правила T2/T3, конфигурации и соответствующая история | **SOURCE CONFIRMED / EXECUTION NOT TESTED** |
| General: backtest engine | `src/market_pattern_discovery/backtest/{engine.py,costs.py}` | Готовые `StrategyCandidate`, `ExecutableSignalDefinition`, подготовленные данные | **SOURCE CONFIRMED**; движок оценивает заранее определённые сигналы, не открывает рынок самостоятельно |
| General: validation | `src/market_pattern_discovery/validation/` | Результат и frozen кандидат + исторические входы | **SOURCE CONFIRMED**, методологические контракты сверять отдельно |
| Старый автономный генератор | `scripts/run_multihorizon_research.py`, `market-pattern-autonomous-engine/` | Старый план автономной архитектуры | **NOT ADOPTED**: `docs/marketai_reality_audit.md` зафиксировал фиктивную UNKNOWN/KNOWN обработку; TRL не возобновляет этот подход |

Все пути относительно `alkospacer123/market-pattern-discovery`, кроме явно указанного другого репозитория. При чтении использован `main@6f352acfac7ebdfabba73e143c4dfea3a6e48507`. Ветка TRL сама содержит только документы.

## Правила выбора существующего тестера

1. Одна гипотеза → один подходящий существующий тестер; не создавать «единый движок» ради всех стратегий.
2. Перед повторным использованием проверять точную конфигурацию, календарь, правила NEXT_OPEN, SL, издержки, таймфрейм и источники.
3. Выполнять исследовательские запуски только в отдельном offline checkout с разрешёнными данными; никаких путей в production/V20 LIVE.
4. Если тестер зависит от отсутствующего ZIP, **BLOCKED INPUT**, а не фиктивный PASS и не переписывание frozen источника.
5. Пригодность программ пока только `SOURCE CONFIRMED`, а не `RUNTIME PASS`.

## Итог

Готовые тестеры, валидаторы, отчёты, механизмы риска и стратегии в репозитории действительно существуют. Изобретать новый тестер в TRL-00 нельзя и не нужно. Для полного `TRL-00.2 PASS` требуется подтвердить входные пакеты и хотя бы одну воспроизводимую безопасную цепочку запуска на выбранных source/data, плюс документировать судьбу недостающих архивов V1–V24.
