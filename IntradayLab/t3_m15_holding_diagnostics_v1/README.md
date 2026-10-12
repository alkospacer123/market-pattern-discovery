# T3 M15 Holding & Entry Diagnostics v1

Диагностика завершённого PR #490. Главный результат и ограничения: [REPORT.md](REPORT.md). Проверены фактический discovery/main `d963b783b9de31fc0f2c965f6dfb11ab9cd90f5b` и read-only data/main `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Никакие стратегии/исходные результаты не меняются. Только две фиксированные версии, четыре инструмента, 2023–2024.

## Воспроизведение

Python 3.12.14; зависимости в requirements.txt. Из корня discovery checkout:

```bash
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_holding_diagnostics_v1/diagnose.py --data-root /path/to/market-pattern-data
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_holding_diagnostics_v1/render_report.py
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/t3_m15_holding_diagnostics_v1/verify.py --data-root /path/to/market-pattern-data
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s IntradayLab/t3_m15_holding_diagnostics_v1 -p 'test_*.py' -v
```

Для отдельных повторов передать каждому скрипту `--output IntradayLab/t3_m15_holding_diagnostics_v1/work/repeat_a` (и второй каталог repeat_b). Все выходы принудительно ограничены новым каталогом. Не запускать исходный research.py/audit.py с их output по умолчанию: завершённый Baseline здесь используется исключительно read-only.

diagnose.py читает закреплённые исходные OHLC через исторический prefix parser engine.py PR #490 и не меняет файлы. Проверяет blob/hash и прекращает парсинг до OHLC первой строки 2025+. Использует исходные индикаторы и original execute только для сверки зафиксированных сделок. Затем восстанавливает оригинальную Stop-траекторию отдельно для каждой исходной сделки. Не исполняет новые exits/signals. verify.py независимо рассчитывает рекурсивные признаки и Stop стандартной библиотекой, опираясь на исходный независимый oracle audit.py. Исполняемых импортов TradingSystemLab нет. `PYTHONDONTWRITEBYTECODE=1` обязателен для предотвращения записи cache в исходный каталог.

## Файлы и определения

| Файл | Содержание |
|---|---|
| REPORT.md, holding_summary.svg | Проверенные факты, гипотезы, ограничения и три следующих эксперимента |
| trade_diagnostics.csv | 1 442 исходные сделки и entry/holding/Stop/excursion/economic признаки |
| stop_trajectory.csv | 28 541 строка entry/survived/exit включая две OPEN_TERMINAL траектории |
| first_candles.csv, first_candles_summary.csv | 1/2/4 завершённые свечи: фиксированные горизонты и отдельно completed_before_exit |
| entry_features_by_outcome.csv | Предвходовые EMA/H1/ADX/ATR и breakout признаки, mean/median по исходу |
| instrument_year.csv | Год × инструмент × фиксированная версия |
| holding_by_year.csv, holding_by_direction.csv, holding_by_bars.csv | Продолжительность в календарных минутах и фактических барах |
| carry_by_year.csv, carry_by_direction.csv, holding_carry_direction.csv | Фактическая календарная полночь, направление, длительность |
| carry_kind.csv, entry_hour.csv | Отдельно gaps ночного перерыва и час входа |
| monthly.csv, monthly_carry.csv | Месяц фактического московского выхода; детализация direction/carry |
| stop_by_year.csv, outcome_by_year.csv | Тип исходного Stop и исход сделки |
| pooled_bookkeeping.csv, pooled_year.csv | Суммы условных R четырёх инструментов; не портфель/капитал |
| fixed_version_entry_pairs.csv | Только общие зафиксированные входы двух исходных версий |
| open_position_diagnostics.json | Незавершённые IMOEXF позиции без выдуманного закрытия/Net |
| MANIFEST.json, ARTIFACT_SHA256.json | Pins, исходные хеши, параметры, runtime, детерминированные хеши |
| AUDIT_RESULTS.json, REPEATABILITY.json, SCOPE_CHECK.json | Независимая сверка, два свежих процесса, неизменность исходников/данных |

Включены группы с наблюдаемыми закрытыми сделками; отсутствующая строка после старта инструмента означает 0 сделок/0R, PF и средние не определены. До старта инструмента нет истории. Для маленьких ячеек нет статистических выводов; PF без отрицательных R пустой, это не подтверждённая бесконечная доходность.

MAE/MFE сохранены из исходной stop-first модели, Stop-свеча исключена из исходного MFE. Lower/upper favorable bounds отделяют известный Open/fill от неизвестного внутрисвечного порядка High/Low. `available` у первых свечей означает наличие свечи в историческом диапазоне; `completed_before_exit` строго раньше exit-свечи. Цена после выхода не является движением открытой сделки.

DD — последовательность закрытых R, не капитал/маржа/переоценка. Top5 удаляет только положительных победителей. `extra_cost_break_even_*` — математический запас после C1, не реальный тариф/funding. funding, дивидендные поправки и полная экономика — UNRESOLVED_NOT_ZERO.

Новая Optimization, Robustness, Walk Forward, TRUE OOS, подбор фильтров, TRAIL1/ONE_BAR/LOCK1/SESSION не проводились. Период не объявляется новой OOS-выборкой. Реализационная независимость проверена тем же автором; внешний аудит остаётся PENDING. Draft PR не merge и не auto-merge; после создания — остановка для внешнего аудита.
