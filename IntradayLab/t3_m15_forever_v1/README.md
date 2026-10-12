# T3 M15 Forever — Independent Baseline v1

Самостоятельный исторический replay двух заранее фиксированных T3/M15 конфигураций на вечных USDRUBF, CNYRUBF, GLDRUBF и IMOEXF. Только 2023–2024; без оптимизации, отбора, новых фильтров и запуска новых Robustness/WF/OOS. **Gate A PASS; Gate B PASS в границах нормализованной C1-модели. Полная положительная экономическая прибыль на четырёх инструментах не доказана.**

Исходный discovery/main: `7927d3d6b465ec1bceae51ec8121def5e7c7e191`; данные закреплены на `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Оригиналы TradingSystemLab используются только как текстовые/CSV references через `git show` закреплённого base; исполняемых импортов и запусков исторических runners нет. CSV котировок сюда не копируются.

Запуск из корня checkout с Python 3.12.14, pandas 2.2.3, numpy 2.3.5 (фактические версии также в manifest):

```bash
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_forever_v1/research.py --data-root /path/to/market-pattern-data
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s IntradayLab/t3_m15_forever_v1 -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_forever_v1/audit.py --data-root /path/to/market-pattern-data
```

Для независимых повторов запускать `research.py` в двух новых каталогах через `--output`, при необходимости задавать `--reference-root` на checkout discovery. У репозитория данных не нужны checkout/изменения: каждый разрешённый локальный файл проверяется против Git blob указанного коммита. Доступ только read-only. Полный SHA-256 считается над непрозрачными байтами; исследовательский парсер прекращает чтение после timestamp первой 2025+ строки, до её OHLC. Никакие OHLC 2025–2026 не загружаются в признаки, сделки или подбор.

Время: московское открытие свечи, доступность `t+15min`; H1 — четыре последовательных завершённых M15 по историческим дневным ordinal-блокам. Индикаторы/Donchian явно пересекают дни, блоки контекста сбрасываются по дате закрытия. Donchian `shift(1)`. Вход по закрытию сигнальной свечи; carried Stop проверяется до trailing, гэп неблагоприятный; разрешён повторный вход на том же закрытии. Это исторические исследовательские допущения, не доказанные LIVE fills.

C1 price unit: Si/CNY `0.001` для точного исторического воспроизведения; GLD `0.1` RUB; IMOEX `0.5` пункта. `Net R = Gross R − 2*unit/initial_risk`. Это только C1, без полного funding, dividend и прочих обязательств. У IMOEXF есть одна незавершённая позиция на версию; закрытая статистика не присваивает ей окончательный net-результат. Подробности — [SPEC_EVIDENCE.json](SPEC_EVIDENCE.json), [OPEN_POSITIONS.json](OPEN_POSITIONS.json), [BASELINE_REPORT.md](BASELINE_REPORT.md).

Артефакты:

- Методология и итоги: `README.md`, `BASELINE_REPORT.md`, `INDEPENDENT_AUDIT.md`.
- Происхождение и контроль: `SOURCE_MANIFEST.json`, `SPEC_EVIDENCE.json`, `BASELINE_CONFIGS.json`, `GATES.json`, `REPRODUCTION_AUDIT.md`, `REPRODUCTION_DETAIL.json`, `REPRODUCTION_DIFF.csv`.
- Сделки и отчёты: `trades.csv`, `yearly_report.csv`, `quarterly_report.csv`, `monthly_report.csv`, `instrument_report.csv`, `direction_report.csv`, `mae_mfe_report.csv`, `exit_diagnostics.csv`, `WF_REFERENCE_COMPARISON.csv`, `OPEN_POSITIONS.json`.
- Проверки: `ARTIFACT_SHA256.json`, `AUDIT_RESULTS.json`, `REPEATABILITY.json`, `SCOPE_CHECK.json`.
- Самостоятельный код: `engine.py`, `research.py`, `audit.py`, `test_research.py`.

`ARTIFACT_SHA256.json` охватывает детерминированные генерируемые исследовательские отчёты и manifests, исключая сам файл хешей и мета-отчёты проверки. `REPEATABILITY.json` документирует два свежих процесса; `audit.py` отдельно считает признаки и replay рекурсивными формулами стандартной библиотеки и сверяет отчёты. Это независимость реализации, **не отдельный внешний аудитор**: внешний аудит и решение пользователя остаются PENDING после Draft PR.

Все новые tracked-файлы должны находиться только здесь. Ни TradingSystemLab, ни существующие IntradayLab исследования, ни LIVE authority/робот/расписание/kill switch, ни Optimization Level Rejection не изменяются. Нет торговых endpoint, merge или auto-merge. После создания Draft PR работа остановлена до внешнего аудита и решения пользователя. Этот Baseline не меняет статусы/периоды прежних исследований; отделение дат не делает период TRUE OOS.
