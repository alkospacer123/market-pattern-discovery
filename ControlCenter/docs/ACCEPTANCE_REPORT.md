# Фактическая приёмка CC-00 / CC-01

## Исправление независимого аудита PR #529 — 15.10.2026

**AUDIT_FIX_PASS по проверкам автора; повторный независимый аудит и решение оператора ожидаются.**
Основание: [замечание 6199585665](https://github.com/alkospacer123/market-pattern-discovery/pull/529#issuecomment-6199585665).
Перед исправлением непосредственно проверены GitHub refs и PR: main
`15e96cea2c252a2dfac1b61a070e8505c97c4d77`, исходный HEAD
`7e69d2d019ad3790ca1d46de4ed391952371fcdf`, ветка
`codex/controlcenter-cc00-cc01`, Draft=true, auto_merge=null, merged_at=null.
Новый HEAD SHA фиксируется в описании существующего PR после commit этого отчёта
(включение собственного полного SHA в содержимое commit изменило бы сам SHA).

Единственная правка прикладного runtime: `read_safely()` использует `except Exception`
вместо перечисления трёх типов. `BaseException` не перехватывается. Возвращается
существующий пустой RobotSnapshot с отсутствующим observed_at и фиксированным кодом
`SYNTHETIC: SNAPSHOT_INVALID_OR_UNAVAILABLE`; display_state становится UNKNOWN.
Контекст HALTED/NOT_DEPLOYED сохраняется согласно прежнему контракту, торговое разрешение
False. Не сохраняются прошлые HEALTHY, heartbeat, цены, капитал, позиции и заявки.
Исходное исключение не форматируется, не логируется и не включается в снимок.
Модели, стратегия, execution contracts, источники и UI-архитектура не менялись.

Изменены только четыре **существующих** файла:

- `ControlCenter/cc/providers/synthetic.py` — ordinary Exception boundary.
- `ControlCenter/tests/test_scenarios.py` — 8 регрессий ошибок/изоляции/system exceptions.
- `ControlCenter/tests/test_ui.py` — 4 регрессии рендеринга ошибок через Streamlit AppTest.
- `ControlCenter/docs/ACCEPTANCE_REPORT.md` — этот отчёт.

Результаты фактических повторных проверок:

| Проверка | Результат |
| --- | --- |
| Воспроизведение до fix | 4 регрессии с RuntimeError/DatabaseError и отказом H1/M15 завершались FAILED; 4 проверки KeyboardInterrupt/SystemExit уже PASS |
| Полный pytest | **115 PASS (3.28s)**, ранее 103; 12 boundary + 37 contract + 42 scenario + 24 AppTest |
| Автономная копия только ControlCenter, очищенное окружение | **115 PASS (3.56s)**; торговых каталогов и production-ресурсов в копии нет |
| RuntimeError / sqlite3.DatabaseError | Оба типа изолируются для каждого робота; реальная БД не открывалась, DatabaseError только конструируется в тесте |
| Санитарная обработка | SECRET_TRADING_TOKEN_123 / SENSITIVE_ACCOUNT_DATA отсутствуют в результате, stdout/stderr/logs, UI и отображаемом журнале; код ошибки фиксированный |
| Изоляция и восстановление | Сбой H1 не меняет M15; сбой M15 не меняет HEALTHY H1; прежние снимки неизменны; после ошибки новый пустой UNKNOWN; после восстановления возвращается исходный снимок |
| Системные исключения | KeyboardInterrupt и SystemExit проходят наружу для H1/M15, проверена идентичность исключения |
| Streamlit AppTest | Все 7 разделов и новые сбои без UI exception; прежний HEALTHY исчезает у отказавшего H1; соседний монитор сохраняет состояние; в журнале только санитарный код |
| Защитные границы | 10 кнопок остаются disabled без callbacks; HALTED/NOT_DEPLOYED, все прежние сценарии, determinism и side-effect guards PASS |
| Импорты | AST runtime allowlist PASS: FINAM/SQLite/trading/OS-process capability не добавлена; sqlite3 импортируется только тестами |
| Зависимости | pip check: No broken requirements found; зависимости не менялись |
| Git | diff --check PASS; correction diff — только 4 modified ControlCenter файла; новых файлов нет |
| Защищённые файлы | SHA-256 всех 17627 исходных tracked files main: 0 несовпадений; Git trees main / исходный HEAD / индекс совпадают |

Защищённые trees: TradingSystemLab
`7ccc7a838707dd8dc2776a0e0300fc72e57edf15`, IntradayLab
`c4f6e652ba442a575ad5711cb3f55841f860f484`. Полный PR diff относительно main
по-прежнему содержит только 32 добавленных пути ControlCenter; файлы других проектов,
конфигурация, данные, авторизация и roadmap не изменены.

Это узкая повторная приёмка исключений с AppTest; браузерные скриншоты ниже относятся
к первоначальному HEAD и не заявляются как заново снятые. Физического доступа к Intel,
FINAM, SQLite или Windows Tasks не было. Новый PR не создаётся; обновляется Draft #529.
Merge / auto-merge / CC-02 / Intel deployment не выполняются. **STOP для повторного аудита.**

## Первоначальная приёмка — история HEAD 7e69d2d (103 теста)

**Технический результат: PASS для автономного SYNTHETIC / DEMO MVP.**
Внешняя независимая проверка PR и решение оператора ожидаются. Работа выполнена
15.10.2026; browser-проверка финального кода около **21:33 MSK / 18:33 UTC**.
Merge, auto-merge, deployment Intel и реальное управление не выполнялись.

## GitHub и база

- До начала реализации: Issue #524 и оба комментария прочитаны; roadmap v1.0 подтверждён.
- Начальный актуальный main: `d1c74ab284dc5d734a453c44fc41b9912f93a27c` (после #526),
  а не ранее указанный в задании `5bf1fe0…`.
- Во время реализации main продвинулся документационным #527. Прочитан документ
  выбранного будущего M15; до первого commit ветка обновлена fast-forward до
  **`15e96cea2c252a2dfac1b61a070e8505c97c4d77`**. Это итоговая база поставки.
- Перед обновлением базы SHA-256 всех 17626 начальных tracked files совпали.
  Четыре изменения IntradayLab из #527 принадлежат main, не diff ControlCenter.
- Проверен список открытых PR: отдельный Draft #515 (Stage8 stop-grid), не затрагивался;
  существующего ControlCenter PR не было. Для этой поставки создаётся один Draft PR.
- Ветка: `codex/controlcenter-cc00-cc01`. Итоговый commit указан в описании PR;
  он содержит этот отчёт и не может быть встроен в самого себя без изменения hash.

## Среда и команды

Linux, Python **3.12.14**, отдельный venv без system-site-packages,
Streamlit **1.50.0**, Plotly **6.3.1**, pytest **8.4.2**.
`pip check`: No broken requirements found.

```text
python -m venv <отдельный-vеnv>
<venv>/bin/python -m pip install -r ControlCenter/requirements-dev.txt
<venv>/bin/python -m pytest -c ControlCenter/pytest.ini ControlCenter/tests
# Результат: 103 passed (3.03s на контрольном прогоне)
```

Из копии **только ControlCenter/** вне дерева репозитория:

```text
env -i PATH=<venv>/bin:/usr/bin:/bin LANG=C.UTF-8 <venv>/bin/python -m pytest -c pytest.ini
# Результат: 103 passed (3.53s)
env -i PATH=<venv>/bin:/usr/bin:/bin LANG=C.UTF-8 <venv>/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
# Chromium открыл http://127.0.0.1:8501; dashboard работает.
```

Соседние TradingSystemLab/IntradayLab/market data в автономную копию не включались;
окружение процесса очищено от передаваемых токенов и project paths.
Это тестовый локальный Streamlit-процесс, не production runtime/Windows Task.

## Проверки и доказательства

| Проверка | Фактический результат |
| --- | --- |
| Загрузка / навигация | AppTest: все 7 разделов без exception; Chromium: переходы по всем разделам |
| Два независимых робота | HALTED H1 / NOT_DEPLOYED M15; смена/ошибка одного сценария не меняет второй |
| UNKNOWN ≠ 0 | Missing fields / unavailable / malformed → UNKNOWN, без прежнего HEALTHY или нулей |
| Свежесть | STALE, missing heartbeat, future clock skew, отдельные observed_at/received_at; stale child provenance не обновляется чужим timestamp |
| Контракты | Типы, enum, aware timestamps, OHLC, invalid NaN/Inf, fill/stop evidence, account mismatch, atomic provenance |
| M15 | Production identity/heartbeat/финансы/risk UNKNOWN; NOT_DEPLOYED сохраняется; план #527 только справочный |
| Финансы | DEMO equity / net PnL / commissions / PF / DD согласованы с H1 ledger; месяцы MSK; M15 не наследует суммы |
| Исполнение | Все 6 уровней фактов; ACK/REQUESTED/observed position не принимают fill fields; FILL_CONFIRMED требует evidence |
| Графики | Chromium: candle/line/entry/exit traces; AppTest: symbol/period; OPEN_POSITION: отдельный DEMO stop |
| Журнал | MSK date range, робот, инструмент, тип, текстовый поиск; отдельный account/source; пустая выборка работает |
| Управление | AppTest и Chromium: 10 disabled buttons, без callbacks/обработчиков |
| Побочные действия | AST allowlist runtime; запрет OS/process/DB/network imports, динамического исполнения/файловых writes; monkeypatch guards при выполнении сценариев |
| Детерминированность | Два одинаковых входа `(robot,scenario,now)` дают одинаковые модели и canonical JSON для всех сценариев обоих роботов |
| Автообновление | Browser: source time 18:33:26 → 18:33:30 UTC за 4,5s при interval=2; без внешнего источника |
| Мобильный браузер | Chromium viewport 390×844: document horizontal overflow false; карточки складываются в одну колонку |
| Ошибки браузера | pageerror: [] на контрольном прогоне |

[Машиночитаемый browser report](browser-check.json).
Скриншоты финальной копии приложения:

- [Обзор двух роботов](screenshots/overview.png)
- [H1 и демонстрационный график](screenshots/h1-monitor.png)
- [Отключённое управление](screenshots/controls.png)
- [Мобильный вид](screenshots/mobile.png)

## Независимые способы проверки неизменности репозитория

**Не утверждается независимость внешнего рецензента:** проверку выполнял автор
реализации, двумя разными вычислительными способами. Внешний аудит Draft PR ожидается.

1. До/после реализации: SHA-256 содержимого **всех 17627 исходных tracked files**
   итоговой базы. Несовпадений **0**.
2. Отдельное вычисление native Git blob SHA-1 (`blob <length>\0<content>`) каждого
   исходного файла и сравнение с `git ls-tree` base. Несовпадений **0**.
3. Staged/final diff проверен: только новые `ControlCenter/` files; нет modified/deleted
   protected paths, новых внешних data/config/authorization files или root roadmap changes.
4. Protected Git tree IDs до/после commit должны совпадать:

| Дерево | Файлов | Git tree ID базы |
| --- | ---: | --- |
| TradingSystemLab | 3056 | `7ccc7a838707dd8dc2776a0e0300fc72e57edf15` |
| IntradayLab | 14213 | `c4f6e652ba442a575ad5711cb3f55841f860f484` |

[Машиночитаемый integrity report](INTEGRITY_REPORT.json), digest полного SHA-256 manifest:
`897501c78383a2534094e9a309e41dd2a1c81771ca83f130ddab0ad09e91e25a`.
Исходный workspace checkout остался чистым на `63835174…`; работа велась в отдельном
worktree. `market-pattern-data`: tracked diff отсутствует; рыночные CSV не читались
и не использовались. Все защищённые code/config/result файлы репозитория неизменны
относительно **итоговой базы**. Физические production SQLite/Task/hash на Intel не
проверялись и не заявляются как проверенные: доступа к production не было.

## Ограничения и следующий шаг

- Нет живой телеметрии, FINAM, SQLite-reader, trading credential, task/control handler.
- SOURCE_INVENTORY доказывает код/схемы и документированный план, не наличие live файлов.
- У M15 есть документационный выбор #527, но runtime/spec/account authority для LIVE не установлена.
- DEMO-линия не T3 indicator; сигналы/причины/сделки/защита только иллюстрации.
- Финансовые метрики — по пяти synthetic закрытым H1 сделкам; не broker performance.
- Прямые зависимости pinned; полный offline-набор wheels нужно готовить на matching Windows/Python.
- Физический Windows smoke, phone device, Intel ACL/нагрузка/развёртывание не проверены;
  проверена эмуляция мобильного viewport в Chromium Linux.
- Auth/RBAC, TLS, remote access, реальные alerts/retention/control plane отсутствуют.
- Следующий **CC-02**: отдельный read-only H1 exported-snapshot adapter с allowlist,
  source authority/TTL/identity/account и fault tests; без торговли/production изменений.

**STOP после одного Draft PR. Не выполнять merge/auto-merge, Intel installation или CC-02.**
