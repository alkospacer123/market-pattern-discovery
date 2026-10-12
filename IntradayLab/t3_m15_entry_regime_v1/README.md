# T3/M15 Entry & Regime v1 — Gross-only research

Семь одиночных заранее фиксированных механизмов, каждый на двух неизменных контролях: BASELINE ATR trailing 3.0 и OPTIMIZED ATR trailing 3.5. Все прочие параметры и сигналы исходной T3 сохранены. `COSTS_DEFERRED / GROSS_ONLY / NOT_LIVE_READY`.

Фактический `main` перед началом: `758a0ac1deda8bfa7aa1bc99d8a97a33a9357f02`, объединённый PR #494. Данные: `alkospacer123/market-pattern-data` @ `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Только полный доступный 2023–2024 M15 prefix, реальные поздние старты GLDRUBF и IMOEXF. Рыночные CSV не копируются. Источники #490, #491 и ROADMAP доступны только для чтения.

Спецификация [EXPERIMENT_SPECS.json](EXPERIMENT_SPECS.json) заморожена до расчёта вариантов. A2 использует пользовательское уточнение: любые две последовательные неправильные свечи **только среди первых четырёх завершённых M15 после входа**; правильная свеча сбрасывает счётчик; после четвёртой проверка отключена. Длину окна не перебирали.

Главный результат и выводы — [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md). Контроль — `results/CONTROL_REPRODUCTION.json`, `results/control_gross_trades.csv` и `results/CONTROL_OPEN_POSITIONS.json`. Журналы `results/trades_CONTROL.csv`, `trades_A1.csv` … `trades_A7.csv` содержат обе конфигурации с явно указанной версией. Общий журнал — `results/trades.csv`; незакрытые позиции отдельно в `results/OPEN_POSITIONS.json`. `entry_opportunities.csv` и `exit_decisions.csv` сохраняют решения и доступность, включая занятость позиции и новые входы.

Отчёты `overall_report`, `yearly_report`, `monthly_report`, `instrument_report`, `direction_report`, `baseline_comparison`, `november_dependence`, `trade_lineage`, `winner_loss_changes`, `large_winners` находятся в `results/`. Положительные/отрицательные/нулевые месяцы включают все фактически доступные месяцы инструмента; до реальной первой даты инструмента месяцев нет. Год относится к исторической метке выхода, а не входа. Незакрытые позиции — **терминальные** на конце полного периода, сгруппированы по году входа, не снимки на конце каждого года. Gross R суммы четырёх инструментов — учётная сумма, не доходность реального портфеля; просадка — последовательность закрытых сделок, не портфельная mark-to-market просадка.

Исходная модель входит по Close сигнальной свечи: это исторический oracle, физическая исполнимость заявки по этому Close не подтверждена. Stop непрерывный, без изменения сетки, с исходной активацией trailing только на следующей свече. Protective exit сохраняет историческую метку Close свечи: точный intrabar timestamp неизвестен. Новый выход имеет известный timestamp следующего фактического Open. Приоритет Stop и gap на этом Open; последующий intrabar Low/High не может отменить уже исполненный Open-выход. Никаких искусственных свечей, цен или терминальной ликвидации. Подробнее — [CAUSALITY_REPORT.md](CAUSALITY_REPORT.md).

Все Gross R = `direction * (exit_price - entry_price) / abs(entry_price - initial_stop)`. Расходы вообще не вычисляются и не вычитаются: нет C1, комиссий, проскальзывания, funding. Старый CSV с C1 читается только для сравнения механики и Gross R; исходные результаты не изменяются. Полный SHA-256 исходного файла — непрозрачная операция над байтами; парсер останавливается после timestamp первой строки 2025+, **до** её OHLC.

Запуск из корня checkout (Python 3.12.14, pandas 2.2.3, numpy 2.3.5):

```bash
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_entry_regime_v1/research.py --data-root /workspace/market-pattern-data --output IntradayLab/t3_m15_entry_regime_v1/work/control --controls-only
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s IntradayLab/t3_m15_entry_regime_v1 -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_entry_regime_v1/research.py --data-root /workspace/market-pattern-data
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_entry_regime_v1/audit.py --data-root /workspace/market-pattern-data
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_entry_regime_v1/render_report.py
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_entry_regime_v1/verify_repeatability.py --data-root /workspace/market-pattern-data
```

Для независимого повтора `research.py --output` направляется только внутрь нового каталога, в `work/`. Independent Audit — отдельная реализация рекурсивных признаков и последовательности событий на стандартной библиотеке; это независимость реализации тем же автором, **не независимый внешний аудитор**. [INDEPENDENT_AUDIT.md](INDEPENDENT_AUDIT.md), `AUDIT_RESULTS.json`, `REPEATABILITY.json`, `SCOPE_CHECK.json` и `ARTIFACT_SHA256.json` фиксируют границы и проверки. Каталог `work/` не входит в PR.

2023–2024 уже исследованы и не являются новым независимым Walk Forward. OHLC 2025+ не читаются и не используются для выбора или проверки. Комбинации, подбор порогов, Optimization, новая Robustness/WF/TRUE OOS, работа с роботом и брокерскими endpoint не запускались. PF ≥2 — исследовательская цель, не PASS-критерий. Внешний аудит и решение пользователя остаются PENDING. Завершение: отдельный Draft PR без Merge и Auto-Merge, без автоматического следующего пакета.
