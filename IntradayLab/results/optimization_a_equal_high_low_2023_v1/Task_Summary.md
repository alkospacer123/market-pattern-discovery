# Optimization A / Equal High-Low / 2023 — полный Summary

**NO QUALIFYING OPTIMIZATION CANDIDATE** для USDRUBF и CNYRUBF. Все 144/144 оценки выполнены. Все 144 имеют отрицательное Net expectancy после C1; ранги пустые. Критерии не ослаблялись.

| Инструмент | Проверено | Объём 100/40/6 | Оба PF ≥2 | Месяцев ≥9 | Полные критерии |
| --- | ---: | ---: | ---: | ---: | ---: |
| USDRUBF | 72 | 36 | 0 | 0 | 0 |
| CNYRUBF | 72 | 63 | 0 | 0 | 0 |

Недостаточный объём: USD 36/72, CNY 9/72. Достаточный объём не означает экономический PASS. Ни одна настройка не прошла базовые study-specific критерии или соседей. Никакие непрошедшие настройки не ранжируются. Все отрицательные, нулевые и NOT_AVAILABLE значения сохранены.

## Идентичность и freeze

- Проверенный фактический GitHub main / base: `ce89458b063f3af2451f8c4c162107207973c53b`; совпадает с SHA задания. PR #474–479 MERGED.
- Полный pre-P&L freeze v2: `2b6735a3ba459adc59f386620937315d21a060a1` — опубликован до первого чтения реальных свечей для Optimization.
- Изначальная публикация `76692d0bd89af2501ea04b52c0792b25cd7cab18` не содержала GRID.csv из-за существующего глобального `*.csv` ignore. Guard остановил проверку до source read/P&L. GRID явно добавлен; история сохранена, поправка раскрыта в PRE_PNL_FREEZE_COMPLETION.md.
- Финальный commit SHA фиксируется в описании Draft PR и сообщении передачи; файл не может содержать SHA собственного commit.
- После начала P&L ни один код, параметр, grid, критерий или зависимость полного freeze не менялись.

## Ограниченный поиск

72 ID `A_OPT2023_T{2..5}_SB{1..2}_TP{2..10}` × два инструмента. Отдельная версия стратегии параметризует исходное семейство A. Остальные параметры и исходный common Backtester сохранены: M5, tolerance 0, minimum risk 3, maximum risk 12, rebound ≤4 ticks, FULL_NET_C1_R, hold ≤120 calendar minutes, NEXT_OPEN, V2, C1 один исторический tick на сторону, entry-bar Take выключен. Исходные сессии, March lunch, holidays, session-flat и Stop-first сохранены.

Полный фиксированный перебор; без early stop, random/Bayesian/ML search, новых сигналов, фильтров, LONG/SHORT отбора или подбора по будущим данным. Local parameter-neighborhood — диагностика на 2023, не Robustness.

Выборка: ≥100 CLOSED / ≥40 MSK entry dates / ≥6 CLOSED entry months. Экономика: два PF ≥2, expectancy >0, ≥9 положительных exit months, conditional CLOSED-only DD ≤20R, largest winner ≤25%, largest positive month ≤50%; ≥2 соседей с 100 CLOSED, expectancy >0, PF R ≥1.5. Идеал 12/12 опубликован отдельно. PF без убытков — NOT_AVAILABLE.

Take distance = R × (initial gross risk + planned round-trip C1) + planned round-trip C1, с наружным округлением. Реализованный Net R делится на initial gross stop risk; плановый и реализованный net/net R имеют отдельные столбцы. C1 использует датированные ticks entry/exit. Price P&L разных инструментов не суммируется.

## Контрольный comparator T3/SB1/TP3

| Инструмент | CLOSED | Entry dates/months | SKIP | EXCLUDED | Net R | PF R | PF price | Положительных месяцев | Conditional DD R |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| USDRUBF | 235 | 149/12 | 2 | 2 | -81.066667 | 0.699345 | 0.708374 | 4 | 92.466667 |
| CNYRUBF | 260 | 142/12 | 71 | 72 | -168.433333 | 0.410969 | 0.261199 | 2 | 184.833333 |

Independent legacy replay совпал с неизменённым A_v1 по сигналам, admissions, trade paths и экономике. USD сохраняет все 235 исходных CLOSED, новых CLOSED нет. CNY сохраняет все 234 исходных CLOSED и получает 26 дополнительных CLOSED: снятие legacy day latch после отсутствующего entry Open допускает 35 новых fills, из них 26 CLOSED и 9 EXCLUDED. Старые 63 filled UNKNOWN CNY остаются отдельно как EXCLUDED новой версии; 48 старых неизвестных entry attempts и 23 ранее blocked attempts становятся 71 SKIP. Исходные UNKNOWN Baseline не переименовываются и не перезаписываются.

Все 3072 raw comparator события сопоставлены по ID; 746 различий классификации/occupancy раскрыты в comparator_gap_policy.csv. На общих CLOSED цены, Stop/Take, risk, выход и Net R совпадают точно. Эти изменения объясняются V2, а не объявляются автоматически регрессией.

## Проверки и воспроизводимость

- До P&L: **576 tests PASS** — 556 существующих и 20 новых. Новые subtests охватывают всю сетку для обеих сторон, оба ticks CNY, causality, admission, stop/take, deadline/session-flat, skips/exclusions, blocking/conditional FLAT и corruption detection. Существующий документированный in-memory metadata adapter старого synthetic A audit сохранён; исходные тесты/assertions не изменены.
- Дополнительно: 12 существующих независимо проверенных V2 synthetic cases с двумя побайтными повторами каждой.
- Canonical 144 + **два полных повтора по 144**: **1 161 deterministic artifacts** в каждом повторе побайтно идентичны. Repeats не являются новыми параметрическими trials.
- Отдельный standard-library-only auditor, без импортов strategy/Backtester/execution/loader/metrics/selection: **PASS, 19,086,789 checked fields/ID checks**; все 144, raw signals/paths/C1, coverage, 1 728 месячных строк, 288 directional строк, neighbors, критерии и ранги.
- Accepted signal IDs = disjoint CLOSED + EXCLUDED IDs для каждой оценки. CLOSED-only trade ledger; SKIP/EXCLUDED без вымышленного P&L.
- **4 042 исходных файла побайтно проверены**: 739 IntradayLab + 3 303 вне него. Baselines A/B/C/прочие, Master Registry, TradingSystemLab, robot/LIVE/broker/production неизменны.

## Источник и реальные чтения

Pinned read-only source: `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Research interval 2023-01-01 inclusive — 2024-01-01 exclusive, MSK. Ни GLDRUBF, ни IMOEXF не оцениваются.

| Source | Rows | Bytes | Git blob | SHA-256 prefix |
| --- | ---: | ---: | --- | --- |
| CNYRUBF | 39362 | 2212189 | `01d667868daaa5610cc8794bf90fe0f276e33686` | `42e30caf28909da46226cd2e163739f1c97d00a3a80780d0f2550a05884c9bc9` |
| USDRUBF | 42576 | 2342431 | `2b621e1c0aa9a84838d95d4c139257889b6f825e` | `047de8fbc74fbe98028cd236b67bf11823b4e6b9f79a6488113a1d0f43947e1d` |

Каждый из трёх запусков и независимый auditor читает ровно 81 938 свечных строк / 4 554 620 bytes. Итого четыре читателя: 327 752 строки / 18 218 480 bytes, повторное чтение тех же prefixes. Python guard и фактические Linux syscalls подтверждают byte ceilings, SHA-256 и source blobs. **Zero 2024+ candle reads**. Датированный CNY tick .01 до 2023-09-27 19:00 MSK, затем .001.

## Ограничения и передача

На comparator неполных дней: USD 30/254, CNY 172/254. Доля EXCLUDED среди accepted entries: USD 2/237 (0.8439%), CNY 72/332 (21.6867%). Все CNY comparator CLOSED используют conditional FLAT после предыдущего исключения. Выборка может иметь selection bias. SKIP и EXCLUDED не входят в Net/PF/expectancy/DD; их количество, доли и entry evidence опубликованы отдельно.

Нет доказанного complete annual PF, полной годовой доходности, continuous equity, брокерского Max DD или портфельной доходности. Internal algorithm audit не заменяет внешний независимый review Draft PR.

Артефакты: [Optimization_Report.md](Optimization_Report.md), [all_candidates.csv](all_candidates.csv), [monthly_results.csv](monthly_results.csv), [direction_results.csv](direction_results.csv), [execution_funnel.csv](execution_funnel.csv), [parameter_neighborhood.csv](parameter_neighborhood.csv), [selection_report.json](selection_report.json), [freeze_manifest.json](freeze_manifest.json), [input_provenance.json](input_provenance.json), [audit.json](audit.json), [validation.json](validation.json), [syscall_read_receipts.json](syscall_read_receipts.json), [comparator_gap_policy.csv](comparator_gap_policy.csv), все детальные журналы в evaluations/<ID>/<instrument>/. Полный отчёт содержит все 12 месяцев для каждой из 144 оценок.

```bash
python -m IntradayLab.optimization_a_2023_v1.validate --data-root /workspace/market-pattern-data --output IntradayLab/work/fresh_optimization_a_validation
```

**Один Draft PR. Без Merge и auto-merge. STOP после создания Draft PR.** B, C, Robustness, Walk Forward, TRUE OOS, LIVE и новые стадии не начинались. Draft #472 не изменён.
