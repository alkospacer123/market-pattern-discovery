# Control Center — паспорт и эксплуатационная граница

## Назначение
Панель Streamlit локально на Intel: `C:\control center`, `http://127.0.0.1:8502`, обычный запуск через `C:\control center\venv\scripts\python.exe -m streamlit run v20_app.py --server.address=127.0.0.1 --server.port=8502`. Это **операторская панель**, не торговый алгоритм, не FINAM truth и не централизованный перенос средств/риска.

## Слои
- CC-02: локальный READONLY exporter/наблюдение; вывод может быть STALE/UNKNOWN, если pin, SHA, возраст снимка или источник не соответствуют установленному V20. Ограниченный loopback-only endpoint.
- CC-07: операторские START / PAUSE и отдельно разрешаемые STOP / RESTART / RECOVER с явными safety gates. Команда из UI требует отдельного подтверждения состояния Task/switch/cycle; UI request != завершённое действие.
- Журнал, здоровье, интервалы freshness, проверка export/report, политики доступа. Source health snapshots **не** равны финансовым журналам сделок TRL.
- CC-08 и старые файлы: исторические результаты и отчёты, не достаточное основание для предположения принятого physical functionality.

## История
23–28.10: проект V20-панели отделён от legacy H1 CC, первые CC-02/CC-07 offline trials, deployment и physical START/PAUSE. 29.10 диагностировали двоение loopback/ZeroTier/portproxy, оставлено локальное `127.0.0.1:8502`. 02–06.11 панели понадобились обновления pin/source после V20 фиксов, отдельные состояния Shallow HALTED vs OBV/Inside ARMED. 09.11 по данным другого контекста CC-07 установлен и прошёл preview тесты 12/12; реальные START/PAUSE подтверждались, а реальные STOP/RESTART ожидали отдельной приёмки 14–15.11. RECOVER не должен обходить HALTED-only gate. Не объявлять эти будущие проверки выполненными заранее.

## Разница между версиями
GitHub `ControlCenter/README.md` в `main` содержит раннее CC-03/H1 описание и **не** является актуальной инструкцией для установленного V20 CC-07. Draft PR [#568](https://github.com/alkospacer123/market-pattern-discovery/pull/568) содержит более позднюю V20-панель; installed packages в `C:\control center` могут содержать дополнительные исправления. Физическая приёмка = установленный SHA/pins + LOCAL READONLY witness + поведение UI/Tasks.

## Ограничения
Без проверки pin нельзя повышать красный/UNKNOWN до HEALTHY. Без согласованного источника нельзя отображать несуществующие P&L, позиции, fills, SLTP. STOP/RESTART/RECOVER — не экспериментировать на торгующих счетах без операторского разрешения. Не подключать публичный адрес и не писать FINAM секреты в UI. Не менять H1 или V20 ради доработки панели.
