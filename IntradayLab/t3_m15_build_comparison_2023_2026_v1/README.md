# T3/M15: сравнение замороженных сборок, 2023–2026 YTD

Ретроспективное сравнение ранее разработанных правил: **POST_HOC_COMPARISON / GROSS_ONLY / NOT_LIVE_READY**. Код исполнения и независимых scalar-реализаций импортируется read-only из исторических каталогов main. Изменяется только разрешённый горизонт чтения в памяти; новые сочетания фильтров и режимов не создаются. PR #513 используется только по `c17709a748f6247e8bd6bf85c9b4f20fac14a4dd` в отдельном detached checkout.

Сначала обязательный полный canonical CONTROL TRAIL_375 за 2023–2026, затем 51 уникальная конфигурация, полные причинные replay и независимая арифметика. SIGNAL_CLOSE — идеализированный вход по известному Close. NEXT_OPEN — отдельно, с пропуском отсутствующей смежной свечи, Stop-first и переносом состояния. Портфельные составы — арифметические descriptive pooled Gross R, без общей модели капитала/ГО.

Данные: отдельный read-only checkout `market-pattern-data` на `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Чтение завершений M15 строго до `2026-10-13T00:00:00+03:00`. Исходные котировки не копируются.

```bash
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_build_comparison_2023_2026_v1/run.py \
  --data-root /workspace/market-pattern-data \
  --pr513-root /workspace/work/t3m15-pr513-source \
  --output /workspace/work/comparison-new-run --jobs 3
```

Для побайтных повторов каждый запуск использует новый output. `journals/` содержит полный торговый/Stop/сигнальный журнал каждой сборки, детерминированный gzip (`mtime=0`). `group_audits/` фиксирует поля независимого replay, причинность и контроль исторических сделок. `audit_metrics.py` не импортирует primary metrics/reporting; независимо проверяет все таблицы по журналам.

Первый полный запуск и два полных повтора обязательны. Вычислительная независимость — отдельные реализации, автор один; внешний аудит ChatGPT/пользователя остаётся PENDING. Изменения только в новом каталоге IntradayLab. Один Draft PR, без merge/auto-merge, затем STOP.
