# R099 — contamination and decision ledger

## 1. Pre-freeze доступ

До 2026-11-26T11:37:04Z были доступны:

- канонические TRL-документы, методология, реестры и доступные отчёты R040–R098;
- частичные архивные сведения V1–V24; отсутствующие оригиналы не реконструировались по догадке;
- научные публикации об intraday momentum, включая RUB/USD MICEX;
- pinned raw M5/M15/M30/H1 файлы четырёх инструментов;
- инвентаризация покрытия, NA, duplicates, monotonicity, OHLC и Volume;
- расписание/спецификация контракта и межтаймфреймная структура баров.

**Не вычислялись:** sign returns, correlations, beta, P&L, PF, годовые разрезы, thresholds или optimization. Выбор USDRUBF и 10:00–18:50 выполнен до просмотра результата.

## 2. Frozen object

- ID: `TRL-R-2026-099`.
- Frozen at: `2026-11-26T11:37:04Z`.
- Protocol SHA256: `ea2e066085b016b53be58f947b95e9b37aca99554cc5cdfbeff442f8684ffee0`.
- Один baseline; только заранее перечисленные diagnostics.
- Final implementation SHA256: `56e99cd46a6f63eefe13be4fd2d95296bc1c67116a5cada929fdb52a858a2fdb`.

## 3. Post-freeze exposures

| Порядок | Событие | Что стало известно | Разрешённое действие |
|---:|---|---|---|
| 1 | Первый runtime failure | Ошибка имени колонки bootstrap; исследовательский статистический результат не получен | Техническое исправление |
| 2 | Первый завершённый расчёт | `REJECT`; predictive gate PASS; экономические/yearly/data/concentration gates FAIL | Запрет оптимизации; проверка кода |
| 3 | Code review | Нулевой bootstrap вызван ошибкой merge типов дат; controls не покрывали zero-signal days | Исправление реализации без смены торговых правил |
| 4 | Повторный расчёт | Net C2 −25440 ₽; bootstrap mean −27,592 ₽, CI ниже нуля; исход REJECT сохранён | Фиксация результата |
| 5 | TF inspection | Frozen close witnesses расходятся; в части 2026 fixed 18:45 не отражает фактический конец сессии | Только data-quality disclosure; граница не меняется |
| 6 | Final canonical + clean replay | Шесть аналитических outputs побайтово совпали | Воспроизводимость pinned run |
| 7 | Independent vectorized check | Ledger и statsmodels HAC совпали в floating-point tolerance; Net C2 −25440 ₽ | `REPRODUCIBLE_VERIFIED`; bootstrap/прочие diagnostics не переписаны |

## 4. Историческая contamination

- Весь 2023–2026 классифицирован `RETROSPECTIVE_DEVELOPMENT_NOT_TRUE_OOS`.
- Эти годы ранее использовались TRL; повторный запуск не восстанавливает независимость.
- 2026 — YTD до 30.08.2026 по raw range, не полный календарный год.
- Научные публикации и прошлые TRL-результаты повлияли на постановку гипотезы; это development knowledge, не внешняя валидация.
- Полная новизна среди V1–V24 не доказана из-за недоступных архивов.

## 5. Запрещённые действия после результата

Под тем же ID нельзя:

- переносить 18:20/18:45 или менять определение предыдущего Close;
- выбирать short-only, потому что short-side выглядит лучше long-side;
- менять C после сравнения сценариев или исключать слабые годы;
- добавлять ATR/volume/session/SL/TP/filter;
- называть положительный beta доказанным торговым edge;
- присваивать CANDIDATE/TRUE OOS/INSTALLED/LIVE.

Любая новая конструкция требует нового Research ID, нового frozen protocol и отдельной contamination истории. Даже она останется development на старой истории.

## 6. Отсутствующие независимые данные

`MISSING_DATA` для фактических исторических spread/fees/slippage, order book/queue, partial fills, ГО, export timezone metadata и untouched forward OOS. Отсутствие этих данных не заполнялось предположениями и не подменялось C1/C2/C4.
