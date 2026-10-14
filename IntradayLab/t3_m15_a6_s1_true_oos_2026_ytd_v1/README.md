# T3/M15 TRAIL_375 — OOS 2026 YTD, Gross PF

Фактический прогон выполнен в существующем Draft PR #513. **Gross PF 2,062109497; Gross R +118,743507457R; 246 CLOSED / 0 OPEN.** Полный вывод и ограничения — [итоговое ревью](results/supplemental/REVIEW_MEMO_RU.md) и [отчёт с таблицами](results/REPORT_RU.md).

Пользователь разрешил 2026 и GROSS_ONLY. Заморожены T3/M15 A6+S1 NEXT_OPEN TRAIL_375, EMA 75 / slope 5 / ADX 14 >20 / ATRRatio >1 / A6 / shifted Donchian 20 / initial Stop 2 ATR / S1 +1R / trail 3,75. Все USDRUBF, CNYRUBF, GLDRUBF, IMOEXF и LONG/SHORT сохранены. Нет оптимизации или cost-stress; расходы не вычитаются.

Окно OOS_SPEC.json не изменено: **[2026-01-01T00:00:00+03:00, 2026-10-13T00:00:00+03:00)**, только завершения M15 строго до конца. Это **OOS 2026 YTD**, не полный календарный OOS. USDRUBF/CNYRUBF заканчиваются 30.08.2026 19:00 MSK, GLDRUBF/IMOEXF — 16.09.2026 00:00 MSK; август/сентябрь неполные, октябрь NO_COVERAGE.

## Воспроизведение в двух checkout

Исследовательский checkout содержит merged #512, main `d6946056332ce71658a6ca933cefa0740a7570a2`, и эту ветку #513. Данные отдельно, read-only, `market-pattern-data` pin `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Нельзя изменять TradingSystemLab, старые стратегии или исходные данные.

```bash
cd IntradayLab/t3_m15_a6_s1_true_oos_2026_ytd_v1
python -m pip install -r ../t3_m15_a6_s1_walk_forward_2025_v1/requirements.txt
python -m unittest -v test_ytd
python repeat_and_seal.py --data-root /workspace/market-pattern-data --output results_new --end-exclusive 2026-10-13T00:00:00+03:00
python final_validate.py --data-root /workspace/market-pattern-data --results results_new --output results_new/supplemental
```

Результаты публикуются после исторического CONTROL, primary/scalar и свежего независимого scalar-процесса. Первый полный запуск и два повтора в отдельных каталогах включают весь контроль 2023–2025, YTD и аудит. Все CSV/JSON/MD проверяются direct bytes и SHA256; логи отдельных процессов сохраняются отдельно. Существующий output не перезаписывается.

## Проверки и артефакты

- `EXECUTION_FREEZE.json`: code/spec SHA256 и тесты до первого чтения OHLCV 2026; commit 61130e70 опубликован до запуска. `OOS_SPEC.json` сохранён как первоначальная спецификация; его preparatory status/limitation описывают прежнюю среду, фактическое выполнение раскрыто отдельно.
- `FROZEN_TESTS.log`: 43 синтетических теста PASS; `YTD_TESTS.log`: 8 тестов PASS, включая read-spy и poisoned suffix.
- `results/control/`: полный повтор W4 primary/scalar, источник, индикаторы, исторический gate и USDRUBF carry на границе 2026. PF2023 2,207277631; PF2024 1,772133705; PF2025 1,581307595. 2025: 300 CLOSED / +86,876613R / 1 OPEN; cohort 299 CLOSED / 1 OPEN, PF 1,563150474, WF_MIXED.
- `results/primary/` и `results/scalar/`: полные trades / Stops / opportunities / gaps / month-end и terminal OPEN. `indicators.csv`: полный причинный индикаторный replay, без копирования raw CSV.
- `SOURCE_RECEIPTS.json`, `SUMMARY.json`, `monthly.csv`, `slices.csv`, `coverage.csv`, `monthly_instrument_coverage.csv`, `CARRY.json`, `DIAGNOSTICS.json`, новые и перенесённые сделки.
- `AUDIT.json`, `FEATURE_CONTROL.json`, `INDEPENDENT_AUDIT.json`/DIFF, `REPEATABILITY.json`, RUN_1/2/3.log. Независимый аудит не импортирует primary runner, engine или reporting.
- `results/supplemental/`: связь отчёта с независимо проверенной SUMMARY; точное соответствие worktree четырём pinned Git blobs. Полные hashes допустимы здесь только потому, что все четыре источника кончаются до cutoff и EOF уже подтверждён разрешёнными readers. При закрытом suffix полный hash запрещён.
- `SUPPLEMENT_REPEATABILITY.json`, `EXECUTION_STATUS.json`, `SCOPE_CHECK.json`, `FINAL_GITHUB_CHECK.json`: два повтора дополнительного аудита, фактическое исполнение и изоляция.

Результат поддерживает устойчивость на доступном префиксе: 8/9 покрытых месяцев положительны (6/7 января–июля), против 7/12 в 2025. Два последних месяца неполные; IMOEXF LONG отрицателен. Gross PF не доказывает готовность к LIVE. Независимость вычислительная, автор один; внешнее человеческое ревью PENDING.

**STOP для независимой проверки ChatGPT и решения пользователя. Draft PR #513. NO MERGE / NO AUTO-MERGE / NO LIVE.**
