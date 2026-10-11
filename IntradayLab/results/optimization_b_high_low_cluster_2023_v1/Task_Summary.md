# Optimization B High/Low Cluster 2023 — Task Summary

**NO QUALIFYING OPTIMIZATION CANDIDATE**. Полный замороженный поиск **585/585**. Статус относится только к 2023 development; внешняя независимая проверка пользователя ещё требуется.

Проверенный актуальный base/main: `0aa3851b754705145b3c64af9781e93f553e4a09` (Merge #480). Полный pre-P&L freeze: `a7d894ba934ff89f8188e2c3574fdb86b9f2b922`. Final head публикуется в описании Draft PR: документ не может содержать собственный commit SHA.

315 уникальных конфигураций: основная 252 и дополнительная Stop-проверка 63. USD N4–9: 270 оценок; CNY N4–10: 315. USD N10 исключён до P&L (исторические 34 CLOSED), GLD/IMOEX исключены. N5/N6/N8/N9 — новые варианты, не исторические Baseline. Сетка, алгоритмы и критерии после первого исторического P&L не менялись.

Граница всего greedy episode envelope и последнего N-bar окна задаётся шириной 2/3 dated ticks. SHORT использует High, LONG Low; minimum width 1, точные boundary touches 2/3. Первый сформированный кластер потребляет эпизод, включая CLOSE_AT_BOUNDARY и отказ admission. Два валидных направления отклоняются. Все resets каузальны; future H/L/C не входят в admission.

Неизменённый общий Backtester: NEXT_OPEN/V2, Stop-first, entry-bar Take=false, C1 один dated tick на сторону, hold 120 календарных минут, исходные сессии/мартовский обед/праздники/session-flat. Structural Stop ±buffer 1/2 от внешней границы, без перемещения; actual Open risk 3–12 ticks и favorable rebound≤4. FULL_NET_C1_R Take 2–10: distance=R×(risk+planned C1)+planned C1, outward grid. Gross/C1/net, initial gross-risk Net R, planned net/net и realized net/net публикуются раздельно.

## Результаты по инструментам

**Все 585 настроек имеют отрицательное Net expectancy после C1.** Кандидатов нет, ранги пустые.

Замороженные критерии: минимум 100 CLOSED /40 уникальных MSK entry dates /6 активных CLOSED entry months; PF R и price ≥2, Net expectancy >0, минимум 9 положительных календарных exit months из12 (12/12 отмечено отдельно), conditional CLOSED-only DD ≤20R, largest winner ≤25% всей положительной прибыли R, largest positive month ≤50% суммы положительных месяцев R. Минимум два реально включённых непосредственных соседа по одному соседнему шагу N/width/touches/buffer/Take: 100 CLOSED, expectancy >0, PF R ≥1.5. USD N10 не является соседом. Только полностью прошедшие настройки ранжируются по месяцам, min(PFs), DD, CLOSED, затем ID; критерии не ослаблялись.

| Инструмент | Оценок | Sample 100/40/6 | Оба PF≥2 | Sample +оба PF | Месяцев≥9 | Все базовые критерии | Все критерии |
|---|---|---|---|---|---|---|---|
| USDRUBF | 270 | 144 | 0 | 0 | 0 | 0 | 0 |
| CNYRUBF | 315 | 315 | 0 | 0 | 0 | 0 | 0 |

**USDRUBF: NO QUALIFYING OPTIMIZATION CANDIDATE**. Все прошедшие ID: нет; ранги пустые.
Количество оценок с отказом по каждому критерию (причины пересекаются): `{"PF_R": 270, "PF_price": 270, "conditional_DD": 249, "month_concentration": 221, "months": 270, "neighbors": 270, "positive_expectancy": 270, "sample": 126, "trade_concentration": 87}`.
CLOSED по отдельным настройкам: 15–657; SKIP 0–4; EXCLUDED 0–9. Это диапазоны зависимых конфигураций, не объединённая независимая выборка.

**CNYRUBF: NO QUALIFYING OPTIMIZATION CANDIDATE**. Все прошедшие ID: нет; ранги пустые.
Количество оценок с отказом по каждому критерию (причины пересекаются): `{"PF_R": 315, "PF_price": 315, "conditional_DD": 315, "month_concentration": 293, "months": 315, "neighbors": 315, "positive_expectancy": 315, "sample": 0, "trade_concentration": 6}`.
CLOSED по отдельным настройкам: 112–380; SKIP 5–37; EXCLUDED 67–146. Это диапазоны зависимых конфигураций, не объединённая независимая выборка.

## Контрольные W3 /TOUCH2 /BUFFER1 /TAKE3 и прежние Baseline

USDRUBF B4: общих CLOSED **549**, дополнительных V2 CLOSED **2**, прежних CLOSED вне новой версии **0**; per-ID различий классификации/occupancy **50**. Missing entry теперь SKIP и снимает legacy дневной latch; неизвестный filled path становится отдельным EXCLUDED. Старые ledger не изменены.

USDRUBF B7: общих CLOSED **123**, дополнительных V2 CLOSED **1**, прежних CLOSED вне новой версии **0**; per-ID различий классификации/occupancy **5**. Missing entry теперь SKIP и снимает legacy дневной latch; неизвестный filled path становится отдельным EXCLUDED. Старые ledger не изменены.

CNYRUBF B4: общих CLOSED **319**, дополнительных V2 CLOSED **12**, прежних CLOSED вне новой версии **0**; per-ID различий классификации/occupancy **773**. Missing entry теперь SKIP и снимает legacy дневной latch; неизвестный filled path становится отдельным EXCLUDED. Старые ledger не изменены.

CNYRUBF B7: общих CLOSED **217**, дополнительных V2 CLOSED **8**, прежних CLOSED вне новой версии **0**; per-ID различий классификации/occupancy **474**. Missing entry теперь SKIP и снимает legacy дневной latch; неизвестный filled path становится отдельным EXCLUDED. Старые ledger не изменены.

CNYRUBF B10: общих CLOSED **164**, дополнительных V2 CLOSED **4**, прежних CLOSED вне новой версии **0**; per-ID различий классификации/occupancy **305**. Missing entry теперь SKIP и снимает legacy дневной latch; неизвестный filled path становится отдельным EXCLUDED. Старые ledger не изменены.

| Control | Instrument | Old CLOSED | V2 CLOSED | SKIP | EXCLUDED | PF R | PF price | E[R] | +months | Net R | Conditional DD R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B4 | USDRUBF | 549 | 551 | 2 | 8 | 0.554737 | 0.556763 | -0.517090 | 1 | -284.916667 | 300.450000 |
| B7 | USDRUBF | 123 | 124 | 1 | 2 | 0.482008 | 0.457447 | -0.617204 | 3 | -76.533333 | 78.366667 |
| B4 | CNYRUBF | 319 | 331 | 23 | 111 | 0.422731 | 0.360471 | -0.558812 | 0 | -184.966667 | 188.466667 |
| B7 | CNYRUBF | 217 | 225 | 21 | 106 | 0.443571 | 0.439333 | -0.445926 | 1 | -100.333333 | 100.333333 |
| B10 | CNYRUBF | 164 | 168 | 18 | 92 | 0.385942 | 0.351939 | -0.508730 | 1 | -85.466667 | 87.566667 |

USD B10: прежние 34 CLOSED /30 entry dates, INSUFFICIENT_TRADES. Проверен только существующий frozen ledger и его SHA-256; новой USD N10 Optimization-оценки или raw replay нет. Independent legacy comparator проверил сигналы/admission/пути всех пяти включённых исторических пар. Общие CLOSED совпадают точно по entry, Stop, Take, risk, exit и Net R. Каждый signal ID и изменение V2 — comparator_gap_policy.csv.

## Проверки и детерминизм

До исторического P&L: **607 tests PASS** (556 существующих, 20 неизменённых Optimization A, 31 новых B). Новые subtests проверяют все 315 конфигураций в обоих направлениях, CNY tick change, envelope/touches/buffers, consumption, future-candle запрет, admission, Take, Stop-first/gap, missing entry/exposure/deadline, same-day block/conditional FLAT, соседей и missing freeze dependency. Дополнительно 12 независимых V2 fixtures с двумя побайтными повторами. Full synthetic pipeline 585 PASS без исторических свечей.
Существующий документированный in-memory metadata adapter одного архивного A_v1 synthetic audit сообщает текущие hashes трёх расширенных core-файлов; исходные файлы и assertions сохранены. Адаптеры полного synthetic pipeline раскрыты в его receipt и log; они не применялись к историческому запуску.

Отдельный standard-library-only auditor: **PASS, 107,063,481 полей/ID сверок** в каждом из трёх 585-прогонов; strategy, Backtester, execution, loader, metrics и selector не импортируются. Raw episodes/envelope/границы/touches, signals/consumption, NEXT_OPEN/Stop/Take/C1/holding, все trading ledgers, exclusions, coverage, 7020 месячных и 1170 directional строк, diagnostics, neighbors и selection проверены. Exact comparisons: нет epsilon, округления для устранения ошибок или изменения условий.
Canonical 585 плюс **два независимых по запуску повтора по 585**: **7,032 детерминированных артефактов** каждого повтора (включая audit.json/comparator/episode audits) побайтно совпали. Это одна фиксированная сетка, не дополнительные trials. Логи всех runner/auditor процессов и content-hidden syscall traces опубликованы в logs/; hashes в validation.json/artifact_hashes.json.

Accepted ID set равен disjoint CLOSED∪EXCLUDED в каждой оценке. Обычный trades.csv содержит только CLOSED. SKIP без входа/P&L; EXCLUDED сохраняет entry и не имеет вымышленного выхода/P&L.

## Источник, реальные bytes и protected scope

Pinned read-only источник `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Каждый runner и auditor прочитал ровно **81938 свечных строк /4554620 bytes**; шесть чтений = **491628 строк /27327720 bytes**, повторение тех же префиксов. Независимые Linux syscall receipts и Python receipts подтверждают ограничения; **0 bytes свечей 2024+**. Development `[2023-01-01,2024-01-01)` по MSK.

| Source | Rows | Bytes | Git blob | SHA-256 prefix |
|---|---|---|---|---|
| CNYRUBF | 39362 | 2212189 | 01d667868daaa5610cc8794bf90fe0f276e33686 | 42e30caf28909da46226cd2e163739f1c97d00a3a80780d0f2550a05884c9bc9 |
| USDRUBF | 42576 | 2342431 | 2b621e1c0aa9a84838d95d4c139257889b6f825e | 047de8fbc74fbe98028cd236b67bf11823b4e6b9f79a6488113a1d0f43947e1d |

**5 236 preexisting файлов (1 933 IntradayLab +3 303 вне него)** побайтно сохранены. Изменения — только additions внутри IntradayLab. Все завершённые исследования, Master Strategy Registry, Optimization A, TradingSystemLab/стратегии/результаты/config/LIVE/broker/production и read-only market-pattern-data защищены. Отдельный Draft #472 остаётся OPEN/DRAFT с head `82ec9ffe61e18a43cd7510e398f6913b25f045e1`. Freeze 37 dependencies +commitments проверены через GitHub API до первого исторического чтения.

## Ограничения и артефакты

USDRUBF B4: EXCLUDED 8/559 accepted (1.4311%); conditional FLAT CLOSED 520/551.

USDRUBF B7: EXCLUDED 2/126 accepted (1.5873%); conditional FLAT CLOSED 119/124.

CNYRUBF B4: EXCLUDED 111/442 accepted (25.1131%); conditional FLAT CLOSED 330/331.

CNYRUBF B7: EXCLUDED 106/331 accepted (32.0242%); conditional FLAT CLOSED 225/225.

CNYRUBF B10: EXCLUDED 92/260 accepted (35.3846%); conditional FLAT CLOSED 168/168.

USD имеет 30 неполных из 254 исследовательских дней; CNY 172 из 254. CNY неполнота, EXCLUDED и последующие conditional FLAT означают возможный selection bias. Conditional CLOSED-only PF/Net/DD не доказывают полной годовой доходности, continuous equity или broker Max DD. Price P&L инструментов не суммируется; B4/B7/B10 и соседние длительности не объединяются как независимые наблюдения. Внутренний algorithm audit не заменяет внешний независимый аудит пользователя.

[Полный отчёт](Optimization_Report.md) · [Все 585 кандидатов и все причины отказа](all_candidates.csv) · [Все 12 месяцев каждой оценки](monthly_results.csv) · [LONG/SHORT](direction_results.csv) · [Execution funnel](execution_funnel.csv) · [Соседи](parameter_neighborhood.csv) · [Selection](selection_report.json) · [Per-ID Baseline comparison](comparator_gap_policy.csv) · [Audit](audit.json) · [Validation/hashes](validation.json) · [Source provenance](input_provenance.json) · [Freeze](freeze_manifest.json) · [Syscall receipts](syscall_read_receipts.json) · [Protected scope](protected_scope.json). Все detailed ledgers, episodes и width/touches/ROUND_NEAR/ORDINARY_FAR diagnostics: evaluations/<ID>/<instrument>/.

```bash
python -m IntradayLab.optimization_b_high_low_cluster_2023_v1.validate --data-root /workspace/market-pattern-data --output IntradayLab/work/fresh_optimization_b_validation
```

**Ровно один Draft PR. No Merge/auto-merge. STOP.** Robustness, Walk Forward 2024, TRUE OOS 2025+, Optimization C, другие семейства и LIVE не начинались.
