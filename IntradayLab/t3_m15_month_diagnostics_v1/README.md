# T3/M15 Month Diagnostics v1

**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. 2023–2024 DEVELOPMENT_EXPOSED.**

[Русский отчёт](results/REPORT.md) отвечает на восемь вопросов задачи. [Все 24 месяца, инструменты и стороны](results/MONTHLY_DETAIL.md), [месячный график](results/monthly_gross_R.svg).

Диагноз: PF падает из-за меньшей доли успешных принятых входов и крупных выигрышей, а не роста среднего убытка. Общее исчезновение трендов свечами не подтверждено. A6 не разделяет слабый апрель–июнь T1+S1 и отсеял бы исходный вход крупнейшего июньского победителя; последствия новой занятости неизвестны; убедительного единственного улучшения для календарной регулярности не найдено. Новый торговый вариант не запускался.

Источник неизменного replay: `../t3_m15_t1_s1_v1/`, OPTIMIZED/COMBINED. Primary импортирует его immutable dataframe engine; independent audit использует его отдельную scalar реализацию и новые independently written scalar diagnostic aggregates. Старые файлы не изменяются и не создают bytecode. [Протокол](PROTOCOL.md) описывает причинные признаки, будущую диагностику, цензурирование, DD и одинаковое покрытие. Внешнее человеческое ревью PENDING; алгоритмическая сверка одним автором не подменяет его.

Все числа отчёта исходят из проверенных CSV/JSON в `results/`: replay trade/Stop/entry/gap/OPEN, 24 месяца, годы, исходы и entry feature distributions, fixed causal cuts, H1 state, каждый Donchian-пробой/его future-window diagnostics, instruments/directions, matched dates/coverage, исторический A6 и крупные победители. Свечные файлы источников не копируются. [Источники/SHA](results/SOURCE_MANIFEST.json), [исходные контрольные точки](results/CHECKPOINTS.json), [независимый аудит](audit/AUDIT_RESULT.json), [сверка Markdown](audit/PRESENTATION_AUDIT.json), [повторы](REPEATABILITY.json), [изоляция](SCOPE_CHECK.json), [полный SHA inventory](ARTIFACT_SHA256.json).

Запуск из корня репозитория с `requirements.txt` (Python 3.12; точный runtime записан в манифесте):

```sh
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR="$PWD/IntradayLab/t3_m15_month_diagnostics_v1/work/mplconfig"
python IntradayLab/t3_m15_month_diagnostics_v1/test_causality.py
python IntradayLab/t3_m15_t1_s1_v1/test_causal.py
python IntradayLab/t3_m15_t1_s1_v1/test_combination.py
python IntradayLab/t3_m15_month_diagnostics_v1/diagnose.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_month_diagnostics_v1/audit.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_month_diagnostics_v1/render_report.py
python IntradayLab/t3_m15_month_diagnostics_v1/audit_presentation.py
python IntradayLab/t3_m15_month_diagnostics_v1/verify_repeats.py /workspace/market-pattern-data
```

Тестовые файлы #500 запускаются read-only; их вывод сохраняется только в новой папке. Два дополнительных свежих процесса полностью повторяют replay, диагностику, scalar audit, русский Markdown, SVG и presentation audit. Все результаты сравниваются напрямую по байтам и SHA256.

Исторический signal-Close fill не подтверждён; реальные costs/funding/slippage, tick-grid, sizing/капитал и MTM не проверены. Диагностические подвыборки/исключение ноября/top-winners не являются новым causal replay. Никаких изменений TradingSystemLab, ROADMAP, прошлых исследований или raw data; никаких новых стадий, Optimization, Robustness, Walk Forward, TRUE OOS, LIVE.

**Один Draft PR. Auto-Merge выключен, Merge запрещён. STOP после создания и проверки.**

Перед подачей main изменился внешним docs-only PR #502; неизменность всего IntradayLab и фактический SHA подтверждены в [FINAL_MAIN_CHECK](FINAL_MAIN_CHECK.md). Исходный main в отчёте относится к началу исследования.
