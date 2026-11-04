> **Актуальный результат Codex Cloud, 23.10.2026:** V20-04.2 — **PASS в offline-scope** (18 новых N4 сигналов + 6 USD ранее, границы M15/session/gap/roll); V20-04.3 — **минимальный H1-контракт PASS только с fake broker**, production остаётся PARTIAL. **55 тестов PASS / 0 FAIL / 0 SKIP** в финальном запуске. Ниже сохранена история прежних PARTIAL/NOT RUN; её заменяет итоговый раздел в конце. [Машинная проверка](FROZEN_EXECUTION_OFFLINE_VERIFICATION.json).

# V20-04.2 — начат адресный frozen parity после закрытия карточки

Историческая карточка закрыта коммитом `29089f1502d58e586d20d0114b688c97a855e40f`, 77 runtime-тестов PASS на этом SHA. Исследования карточки не продолжаются.

Возврат к действующему 04.2: `completed_signal` сопоставлен с опубликованными RAW_SIGNAL V20-03 на шести заранее выбранных первых USD-сигналах 2024 года: по long/short для каждой стратегии, без отбора по admission/PnL/horizon. Вход — только префикс исходных SHA-проверенных M15 до signal_bar_dt, без чтения чисел 2025. Проверены side, strategy, symbol, момент NEXT_OPEN и исходный ATR14. DataFrame не изменяется.

| Стратегия | Side | Бар сигнала МСК |
|---|---:|---|
| INSIDE_DAY_RELEASE | -1 | 2024-02-28 13:15:00 |
| INSIDE_DAY_RELEASE | 1 | 2024-01-18 16:30:00 |
| OBV_PRESSURE | -1 | 2024-01-11 10:00:00 |
| OBV_PRESSURE | 1 | 2024-01-18 16:30:00 |
| SHALLOW_PULLBACK | -1 | 2024-01-09 12:15:00 |
| SHALLOW_PULLBACK | 1 | 2024-01-03 12:00:00 |

Дополнительно проверены незавершённый бар/неправильный NEXT_OPEN, дубли timestamp и размещение/удаление временных CSV вне checkout. Найденное нарушение пути исправлено **только в V20 runtime adapter**: изолированный экземпляр locked helper получает внешний scratch parent. Frozen AST, BASE, сигнальные формулы и исходные файлы не редактируются.

**PASS:** 8 фактически выполненных адресных тестов; затем полный текущий runtime suite — **85 тестов PASS** (77 прежних + 8 новых). Зависимости уже присутствовали: numpy 2.3.5, pandas 2.2.3; новых зависимостей не добавлено. При отсутствии внешних котировок эти data-dependent тесты явно SKIP, не PASS; текущий прогон был без SKIP.

**04.2 остаётся PARTIAL:** это шесть сигналов одного N4-символа, не полная реплика ledger 1589 и не production M15/feed parity. Пограничные overnight/session/roll/feed-recovery сценарии и вся исполнительная часть 04.3 — ещё не приняты. Никакой parity по приказам брокера/SLTP/fill здесь не заявляется.

**Следующая работа в существующем roadmap:** закончить 04.2 frozen/feed parity на репрезентативном N4, затем 04.3 — H1 orders/SLTP/reconciliation/recovery для трёх изолированных роботов. Карточка не участвует в решении о сигнале или риске. H1/M15/FINAM/N4/стопы/риск/счета не менялись, LIVE OFF, roadmap 8/24 без новых подэтапов.

Файлы: `v20_runtime/frozen_adapter.py`, `v20_runtime/tests/test_frozen_adapter.py`, этот статус и tracker/README. Команда:

```sh
python -m unittest discover -s V20_TradingSystem_M15/v20_runtime/tests -v
```

## Продолжение 23.10.2026 — проверка на оставшихся трёх N4

В дополнение к шести уже подтверждённым USD-примерам добавлен только адресный тест `v20_runtime/tests/test_frozen_n4_parity.py`. Он сверяет первые опубликованные `RAW_SIGNAL` 2024 года по каждой стратегии и доступному направлению на `CNYRUBF`, `GLDRUBF`, `IMOEXF` с исходным frozen `completed_signal`; сравнивает момент, сторону, ATR14, отсутствие изменений input-DataFrame. Выбор **без отбора по будущему PnL**. Проверяет SHA внешних M15 и исходного RAW CSV, читает OHLCV только до свечи сигнала. Сессионные/dedup/reset проверки уже выполненного USD-теста не повторяются.

**Текущий статус: TEST ADDED / EXECUTION NOT VERIFIED, V20-04.2 по-прежнему PARTIAL.** В данном GitHub-сеансе нет внешних SHA-pinned котировок `/workspace/market-pattern-data/forever/`; без них тест сообщает **SKIP, не PASS**. Нельзя утверждать parity других трёх символов до фактического прогона в исходной исследовательской среде. Даже его PASS подтверждает только адресные сигналы, не полную 1 589-trade parity и не feed/session/recovery acceptance.

Команда в среде, где доступны исходные CSV и зависимости:

```sh
python -m unittest V20_TradingSystem_M15.v20_runtime.tests.test_frozen_n4_parity -v
```

Затем завершить оставшиеся реальные границы M15/session/roll/feed для всех N4 и только после подтверждения 04.2 перейти к 04.3 H1 execution. Никаких изменений frozen сигналов/риска/N4, H1/M15/FINAM/LIVE.

## Входные котировки подтверждены 23.10.2026

Получен от владельца `Si+Mix_2012-2018.zip` (фактическое содержимое до декабря 2022). Локальная проверка ZIP: **88 квартальных CSV / 299 998 M15 строк / CRC PASS**, **SHA256 `9b253772c6533235b1db0893b6b42472be86dff0862b6af390089608ac561fa2`**. Совпадает с уже опубликованным `V20_2012_2022_SOURCE_AUDIT.json` и не требует повторного replay. Прежние ранние ограничения tick/OPEN/Si-exit остаются.

Подтверждено наличие всех 4 N4 M15 в **отдельном** GitHub-репозитории `alkospacer123/market-pattern-data`, каталог `forever/<SYMBOL>/<SYMBOL>_M15.csv`; подготовку закреплять за коммитом `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, **не** за изменяемым `main`. Не путать его с кодовым `market-pattern-discovery`.

Чтобы избежать ручного переноса котировок, добавлен **один** read-only helper `v20_runtime/prepare_n4_quotes.py`, использующий публичные GitHub raw ссылки и точные **SHA256 уже утверждённого `SOURCE_SHA256`**. Он создаёт **только** данные во внешнем каталоге, не затрагивает исходные файлы/репозитории и не используется торговым runtime; если SHA скачанного файла не соответствует эталону — FAIL без публикации источника. Никаких новых зависимостей или FINAM. Для research/Codex shell с доступом к GitHub:

```sh
python -m V20_TradingSystem_M15.v20_runtime.prepare_n4_quotes --output /tmp/v20-n4/forever
V20_N4_QUOTES_ROOT=/tmp/v20-n4/forever python -m unittest V20_TradingSystem_M15.v20_runtime.tests.test_frozen_n4_parity -v
```

Имеющийся источник `/workspace/market-pattern-data/forever` также поддерживается без скачивания; для другого пути задать `V20_N4_QUOTES_ROOT`. В Windows PowerShell перед запуском теста использовать `$env:V20_N4_QUOTES_ROOT='<external-folder>'` вместо bash-переменной.

**Проверено здесь:** идентичность приложенного архивного ZIP и наличие путей modern N4 в pinned GitHub. **Ещё не подтверждено:** SHA *содержимого* modern N4 в текущем окружении (GitHub connector не выдал содержимое файлов >2MB), исполнение адресного frozen parity и все feed/session/restart случаи. Для отсутствия доступа к GitHub/source нужен честный BLOCKED/SKIP; не заявлять нового PASS.

## Фактически выполнено в Codex Cloud — 23.10.2026

На старте main `6f352acfac7ebdfabba73e143c4dfea3a6e48507`, head PR #567 `90946dcf5aff1ac89f4deaaa73116e2a366b156c`; fast-forward сохранил все изменения владельца. Исследования карточки/архива не повторялись.

`prepare_n4_quotes.py` самостоятельно скачал все 4 CSV из `alkospacer123/market-pattern-data`, commit `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, во внешний `/workspace/work/v20-n4-parity-f8486b4`. SHA256 4/4 PASS. Исходники/ZIP в Git не добавлялись. Шесть прежних сигналов USDRUBF не пересчитывались.

### 18 новых сигналов и сквозная offline-проверка

Отбор тот же: первый опубликованный RAW_SIGNAL 2024 по символу/стратегии/LONG–SHORT без отбора по PnL. Полный префикс OHLCV заканчивается свечой сигнала; её информация доступна через 15 минут. У следующей свечи отдельно читается только Open для проверки NEXT_OPEN, HLCV в признаки не попадают. У каждого примера совпали стратегия, сторона, ATR, время и Open; исходный DataFrame не изменён.

| Инструмент | Стратегия | Сторона | Signal M15 Open (MSK) | Доступен / NEXT_OPEN | ATR14 | Initial stop |
|---|---|---|---|---|---:|---:|
| CNYRUBF | INSIDE_DAY_RELEASE | SHORT | 2024-03-29 10:00:00 | 2024-03-29 10:15:00 | 0.0109431375 | 12.674 |
| CNYRUBF | INSIDE_DAY_RELEASE | LONG | 2024-01-18 12:00:00 | 2024-01-18 12:15:00 | 0.0186483276 | 12.223 |
| CNYRUBF | OBV_PRESSURE | SHORT | 2024-01-09 13:15:00 | 2024-01-09 13:30:00 | 0.0180160976 | 12.608 |
| CNYRUBF | OBV_PRESSURE | LONG | 2024-01-18 16:45:00 | 2024-01-18 17:00:00 | 0.0159792567 | 12.242 |
| CNYRUBF | SHALLOW_PULLBACK | SHORT | 2024-01-09 12:30:00 | 2024-01-09 12:45:00 | 0.01837468 | 12.647 |
| CNYRUBF | SHALLOW_PULLBACK | LONG | 2024-01-24 14:00:00 | 2024-01-24 14:15:00 | 0.0128399721 | 12.276 |
| GLDRUBF | INSIDE_DAY_RELEASE | SHORT | 2024-01-10 11:15:00 | 2024-01-10 11:30:00 | 6.91804194 | 5823.5 |
| GLDRUBF | INSIDE_DAY_RELEASE | LONG | 2024-01-31 12:15:00 | 2024-01-31 12:30:00 | 5.31769189 | 5825.5 |
| GLDRUBF | OBV_PRESSURE | SHORT | 2024-01-05 10:30:00 | 2024-01-05 10:45:00 | 6.14903582 | 5900.5 |
| GLDRUBF | OBV_PRESSURE | LONG | 2024-01-03 13:15:00 | 2024-01-03 13:30:00 | 6.89839489 | 5923.5 |
| GLDRUBF | SHALLOW_PULLBACK | SHORT | 2024-01-05 12:00:00 | 2024-01-05 12:15:00 | 7.10668638 | 5878.3 |
| GLDRUBF | SHALLOW_PULLBACK | LONG | 2024-01-24 16:30:00 | 2024-01-24 16:45:00 | 4.86877436 | 5743.1 |
| IMOEXF | INSIDE_DAY_RELEASE | SHORT | 2024-08-07 11:30:00 | 2024-08-07 11:45:00 | 7.06564536 | 2831.0 |
| IMOEXF | INSIDE_DAY_RELEASE | LONG | 2024-01-10 10:00:00 | 2024-01-10 10:15:00 | 3.69835014 | 3161.0 |
| IMOEXF | OBV_PRESSURE | SHORT | 2024-02-12 11:00:00 | 2024-02-12 11:15:00 | 2.88798629 | 3242.0 |
| IMOEXF | OBV_PRESSURE | LONG | 2024-01-03 10:15:00 | 2024-01-03 10:30:00 | 3.14302097 | 3111.5 |
| IMOEXF | SHALLOW_PULLBACK | SHORT | 2024-01-24 14:00:00 | 2024-01-24 14:15:00 | 3.56591468 | 3169.5 |
| IMOEXF | SHALLOW_PULLBACK | LONG | 2024-01-08 10:00:00 | 2024-01-08 10:15:00 | 8.54123981 | 3132.5 |

Во всех 18 примерах проверена цепочка `completed_signal → OfflinePlanner → OfflineH1Executor → FakeBroker fill → 100% SLTP → restart → повтор ключа без POST`. На каждый пример отдельный временный счёт/БД. Капитал 500 000, доступный cash 200 000 и GO 10 000 — **синтетические предпосылки fixture**, не подтверждённые параметры FINAM. ATR и NEXT_OPEN реальные; тик/стоимость шага/символ `@RTSX` прочитаны из неизменённого H1 registry. Это интерфейсная проверка, не новый торговый replay/PF.

### Границы и исправления

- Незавершённая/устаревшая M15, неверный immediate NEXT_OPEN, duplicate/order/timezone, micro/nanosecond отклонения, смешанный `Ticker` и невалидный OHLCV отклоняются до frozen-функции. Добавлена только валидация обвязки; frozen AST не менялся.
- Исходная граница сессии — 09:00 MSK, не полночь. Исходный frozen engine синтетически проверяет третий **наблюдаемый** сеанс, пропуск NEXT_OPEN, входной стоп, gap-through-stop, C1 и независимость лимитов. Его `main`, archive ingestion и полный replay не запускались.
- Причинный LOCKED_V1 roll проверен на синтетических прошлых/будущих сводках: будущая серия/поздно доступная сводка не меняют старый выбор, открытая позиция старой серии удерживает underlying slot. OHLC серий не склеивались. В N4 perpetual нет квартального roll; тест не заявляет новой исторической сертификации Si/MIX.
- Переиспользован `IntradayLab/core/m15_bars.py`: неполная M15 с пропущенной M5 сохраняет только наблюдаемый Open, HLC остаются NaN; вымышленных свечей нет. Для V20 не подставлялся календарь T1.
- Штатная N4 frozen-подготовка сохраняет свои расчёты по наблюдаемым строкам; новый reset индикаторов после gap не добавлялся. Пропущенный immediate NEXT_OPEN не заменяется более поздней ценой.
- Helper подготовки данных теперь запрещает сохранение **в любом месте checkout**, а не только внутри V20.

### V20-04.3 — общий минимальный H1 executor

`v20_runtime/h1_execution.py` использует H1 `RuntimeAction`, чистый `_market_payload`, `percent_position_stop_payload`, `compact_client_order_id`, `order_views`, `position_quantities`, `unique_order_by_client_id`, `reconcile`, Decimal/Fraction stop grid, `StateStore` и `InstanceLock`. H1 `ProductionRuntime/Service` и авторизованный transport не создаются; `RuntimeAction.payload()` с H1 identity не вызывается. Никакой подмены H1 authorization или FINAM-сессии.

На вход разрешён ровно `FakeBroker` с совпадающей identity. В каждом `V20Lab/shallow|obv|inside/state/` создан отдельный `v20-offline-execution.sqlite3`, отличающийся от прежнего reference-only журнала; общий instance lock не разрешает второй процесс того же робота. Intent и резерв session quota сохраняются до обращения к fake. Незавершённый POST после сбоя никогда не повторяется автоматически. ACK не считается fill; нужны непротиворечивые order-linked fills и точная сверка позиции. Частичное исполнение немедленно получает stop-only SLTP на 100% позиции. Исходный 2×ATR проецируется наружу на неизменённый N4 tick; TP/trailing не добавлены.

Подтверждены частичные исполнения, потеря entry/stop ACK, definite rejection, сбой до/после принятия заявки, restart, неизвестные/дублированные заявки, несовпадение wire/позиции, неполный/конфликтующий fill history, pending occupancy после смены сессии, отдельные LONG/SHORT и три робота. При frozen time-exit решении вызывающего кода используется H1 market-exit wire; стоп снимается только после подтверждённого flat. Сам планировщик времени/автономный feed loop этим адаптером ещё не реализован.

### Фактические тесты

| Набор | Число tests | Результат |
|---|---:|---|
| `test_frozen_n4_parity` (18 subcases + 18 fake/restart flows) | 1 | PASS |
| `test_m15_boundaries` | 9 | PASS |
| `test_offline_planner` | 11 | PASS |
| `test_h1_state_journal` | 10 | PASS |
| `test_h1_execution` | 24 | PASS |
| **Финальный запуск** | **55** | **PASS, 0 failures/errors/skips** |

В процессе разработки одна проверка wrong-grid сначала завершилась ERROR из-за порядка валидации (ожидала binding error, получала grid error); guard переставлен перед grid, после исправления выполнен указанный финальный запуск. Это не расхождение frozen-сигнала.

**SKIP отдельно от 55 выполненных:** старые 6 USD по прямому указанию; полный 1 589 replay и архив 2012–2022 по неизменённым источникам; FINAM/Windows/Tasks/LIVE вне разрешённой offline-проверки. SHA исходников, всех quotes, тестов и нового кода сохранены в JSON. Diff H1/IntradayLab относительно main пуст; frozen-источники относительно входного PR head не изменились.

### Остаток roadmap и предел PASS

**04.2 offline archive/interface/boundaries PASS** позволяет продолжать **04.3**. Это 24 representative signals с учётом прежних USD, а не новая полная 1 589-trade или физическая FINAM-feed parity. Фактическая OPEN/close label authority и свежесть FINAM M15 остаются обязательной READONLY-проверкой V20-06. Карточка остаётся диагностической и не участвует в ордерах.

**04.3 минимальная fake-broker интеграция PASS, production PARTIAL.** Неподтверждённая защита блокирует входы и требует диагностики; слепого retry или утверждения защищённости нет. История fills в fake полная; физическая пагинация/lag реального брокера пока не приняты.

Следующий технический пункт — **V20-04.4**: фактический fill → денежный риск 1,5%, общий cap 6%, доступный cash/направленный GO и расходы. В текущем адаптере slipped fill получает защиту по фактической цене, но новые входы блокируются `ACTUAL_FILL_RISK_REQUIRES_V20_04_4`; полной приёмки этого расчёта нет. Если VWAP следующих partial fills изменился, прежняя 100% защита сохраняется, дальнейшие входы блокируются; автоматической переустановки/ослабления стопа нет. Затем 04.5/04.6 — общий причинный цикл/три процесса, и V20-05 offline acceptance. Этапы/подэтапы не добавлены, roadmap остаётся 8/24.

```sh
python -m V20_TradingSystem_M15.v20_runtime.prepare_n4_quotes --output /tmp/v20-n4-parity
V20_N4_QUOTES_ROOT=/tmp/v20-n4-parity python -m unittest V20_TradingSystem_M15.v20_runtime.tests.test_frozen_n4_parity V20_TradingSystem_M15.v20_runtime.tests.test_m15_boundaries V20_TradingSystem_M15.v20_runtime.tests.test_offline_planner V20_TradingSystem_M15.v20_runtime.tests.test_h1_state_journal V20_TradingSystem_M15.v20_runtime.tests.test_h1_execution -v
```

**PR #567 остаётся Draft. Merge, FINAM, токены, LIVE, Windows Tasks и работающий H1 не затрагивались.**
