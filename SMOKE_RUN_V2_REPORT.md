# 5 Cycle Smoke Run v2 — Persistent Artifact Validation

## Финальный verdict

**SMOKE RUN V2 PASS**

Production pipeline завершил все пять ограниченных исследовательских циклов, все
созданные стратегии прошли Signal → Backtest → Validation → Ranking, bundle
сохранён в постоянном хранилище и повторно прочитан независимой проверкой.
Bundle имеет статус `READY_FOR_AUDIT` и готов к следующему этапу — **FORENSIC
AUDIT v1**. Запуск на 20 циклов не выполнялся.

## 1. Run information

| Поле | Значение |
|---|---|
| `run_id` | `smoke-v2-20260911T083829Z-661a3a41` |
| Source commit | `661a3a41d34d173a67ae9573cacb7a12f908d7c8` |
| Data-manifest SHA-256 | `848227c1580034affbcbd0b3ee944edca18426ef5d60468458fa5cbdc0091028` |
| Seed | `35` |
| Cycles / budget | `5 / 1` |
| Pipeline duration | `3776.014749 s` (62 min 56.015 s) |
| Instrumented wall duration | `3825.751140 s` (63 min 45.751 s) |
| Data interval | 2026-01-01…2026-08-31, Europe/Moscow |
| TRUE OOS 2025 | Не использовался; manifest фиксирует `true_oos_2025_accessed=false` |

Перед запуском repository был чистым (`git status --short --branch` показал
только `## work`), commit был зафиксирован, постоянное хранилище отсутствовало и
было создано. Отдельный внешний data manifest был создан в постоянном
хранилище из имён и размеров разрешённых source-файлов; market values не
копировались в repository. Для смешанного D1-архива manifest фиксирует фильтр
разрешённого development-интервала до разбора OHLCV.

Каждый из циклов 0–4 имел `planned=1`, `hypotheses_evaluated=1`, `recorded=1`.

## 2. Persistent memory

Artifact bundle:

`/workspace/market-pattern-artifacts/smoke-v2-20260911T083829Z-661a3a41/`

Проверены все обязательные файлы:

- `manifest.json`
- `source_commit.txt`
- `data_manifest.sha256`
- `audit_metadata.json`
- `direction_bias_report.json`
- `horizon_report.json`
- `hypotheses.jsonl`
- `strategies.jsonl`
- `signals.jsonl`
- `backtests.jsonl`
- `validations.jsonl`
- `rankings.jsonl`

Итог memory validation:

| Проверка | Результат |
|---|---|
| Artifact directory / manifest существуют | PASS |
| Все обязательные файлы существуют | PASS |
| Все JSONL строки читаются как JSON | PASS |
| SHA-256 каждого artifact совпадает с manifest | PASS |
| Record counts совпадают с manifest | PASS |
| `source_commit.txt` совпадает с manifest | PASS |
| `data_manifest.sha256` совпадает с manifest | PASS |
| Manifest status | `READY_FOR_AUDIT` |

## 3. Pipeline funnel

| Стадия | Количество |
|---|---:|
| Research hypotheses | 5 |
| Pattern effects | 2 |
| Trading candidates | 2 |
| Strategy candidates | 54 |
| Executable signals | 54 |
| Backtests | 54 |
| Validation reports | 54 |
| Rankings | 54 |

Pipeline errors: **0**. Persistent pipeline memory содержит по 54 backtest,
validation и ranking records. Полные определения всех 54 стратегий (ID,
symbol, horizon, execution/context timeframes, direction, signal type,
entry/exit, stop loss, take profit и risk/reward) и их индивидуальные trading
metrics сохранены в `audit_metadata.json` внутри bundle.

## 4. Trading results

Ниже — наблюдаемая агрегация всех 54 backtests без оптимизации и без изменения
стратегий или execution settings.

| Метрика | Значение |
|---|---:|
| Strategies / backtests | 54 / 54 |
| Total trades | 346,176 |
| LONG trades | 0 |
| SHORT trades | 346,176 |
| Aggregate win rate | 0.2926546034 (29.2655%) |
| Aggregate gross profit | 6,002.880000 |
| Aggregate gross loss | -6,384.272143 |
| Aggregate profit factor | 0.9402606696 |
| Aggregate net result | -1,073.744143 |
| Per-trade expectancy | -0.0031017290 |
| Maximum individual-strategy drawdown | 34.7600000001 |
| Trade-weighted average holding time | 616.583818 s |

`profit_factor` рассчитан для наблюдения как сумма gross profit / абсолютная
сумма gross loss. Drawdown — максимум среди отдельных strategy backtests, а не
синтетический portfolio drawdown. Production costs остались
`fixed:0.001`, slippage — `fixed_per_fill:0.0005`.

## 5. Direction-bias analysis

| Стадия | LONG | LONG % | SHORT | SHORT % |
|---|---:|---:|---:|---:|
| PatternEffect | 0 | 0% | 2 | 100% |
| TradingCandidate | 0 | 0% | 2 | 100% |
| StrategyCandidate | 0 | 0% | 54 | 100% |
| ExecutableSignal | 0 | 0% | 54 | 100% |
| Backtest trades | 0 | 0% | 346,176 | 100% |

**Наблюдение:** первый видимый SHORT bias возник уже на стадии
`PatternEffect`: оба прошедших scientific gate эффекта отрицательны. Следующие
этапы сохранили, а не создали этот direction bias. Это только диагностика
фактического smoke run; параметры, PF и торговая логика не оптимизировались.

## 6. Horizon analysis

| Horizon | Execution TF | Context TF | Strategies created | Backtests completed | Trades |
|---|---|---|---:|---:|---:|
| SCALPING | M1 | M15 | 54 | 54 | 346,176 |
| SCALPING | M5 | M15 | 0 | 0 | 0 |
| INTRADAY | M5 / M15 / M30 | H1 / D1 | 0 | 0 | 0 |
| MEDIUM TERM | H1 / D1 | H1 / D1 | 0 | 0 | 0 |

В этом ограниченном deterministic run реально участвовали только M1 execution
и causal M15 context. Отсутствие остальных timeframes — наблюдаемый результат
первых пяти scheduler cells, а не ручное изменение research parameters.
`horizon_report.json` сохраняет нулевые counts и для отсутствовавших профилей,
чтобы audit мог отличить «не участвовал» от «данные потеряны».

## 7. Performance observation

| Наблюдение | Значение |
|---|---:|
| Pipeline time | 3776.014749 s |
| End-to-end instrumented wall time | 3825.751140 s |
| Backtests completed | 54 |
| Amortized pipeline time per backtest | 69.926199 s |
| Peak RSS (`ru_maxrss`) | 948,424 KiB (926.20 MiB) |
| Pipeline errors | 0 |
| Artifact bundle size (approximately) | 128.3 MiB, dominated by `backtests.jsonl` |

Amortized time включает research, signal translation, validation, ranking и
serialization, поэтому не является изолированным microbenchmark одного
backtest. Первый запрос `/usr/bin/time -v` не запустил pipeline, потому что
binary отсутствует; фактический запуск был измерен монотонным Python timer,
wall clock и `resource.getrusage`.

## 8. Audit hand-off

Forensic audit должен начинаться с повторного вызова
`AutonomousRunArtifacts.verify` для указанного bundle, проверки source commit и
data-manifest digest, затем анализа `audit_metadata.json`,
`direction_bias_report.json`, `horizon_report.json` и неизменяемых JSONL stage
streams. Bundle прошёл такую process-independent проверку после записи.
