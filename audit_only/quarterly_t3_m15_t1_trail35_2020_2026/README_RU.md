# Изолированная проверка T3/M15 T1, 2020–2026

**SOURCE_DATA_BLOCKED_M15.** [Отчёт](REPORT_RU.md), [пилот](DATA_ACQUISITION_PILOT.md), [источники](DATA_ACQUISITION_REPORT.md), [требования к данным](DATA_REQUIREMENTS_RU.md). Стратегия не исполнялась; статистических/торговых CSV нет.

Offline-проверка файлов (Python 3, только stdlib; data checkout должен быть чистым на закреплённом commit):

```bash
cd audit_only/quarterly_t3_m15_t1_trail35_2020_2026
python preflight.py --data /workspace/market-pattern-data --out /workspace/work/m15_preflight_repeat
M15_AUDIT_DATA=/workspace/market-pattern-data python -m unittest -v test_preflight
```

`preflight.py` не скачивает данные и не содержит торгового движка. Проверяет исходные Git blobs/SHA256, различает вечные тикеры в legacy-файлах, сохраняет NO_DATA/null. Новые M15 требуют нового аудита источника и пилота.

Только после настройки законного сетевого доступа и проверки политики можно явно выполнить discovery-пробы, с внешним cache:

```bash
python probe_network.py --private-cache /workspace/work/quarterly_m15_private/discovery_cache
```

Это **не массовый downloader** и не подтверждение доступности M15. Успешные discovery-ответы сохраняются с SHA256 вне репозитория; cached receipts повторно не запрашиваются, отказы не ретраятся. При изменении доступа старый cache сохранять как evidence, для нового наблюдения использовать новый каталог.

`reproducibility.json` содержит SHA256 артефактов и двух **source-gate**, не replay, прогонов. `independent_audit.json` сообщает COMPUTATIONAL_AUDIT=NOT_RUN. Один автор; внешнего человеческого аудита ещё нет. PR только Draft; merge/auto-merge запрещены.

Проверка опубликованного пакета: `python verify_artifacts.py`.
