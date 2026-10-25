# Control Center — переход на V20, CC-00–CC-08

Основа: actual GitHub main `6f352acfac7ebdfabba73e143c4dfea3a6e48507`; V20 roadmap `V20-01–V20-08`, V20-04 OFFLINE.
Целевой проект **один**: `V20_TradingSystem_M15`. Три робота/FINAM-счёта: `V20_SHALLOW`, `V20_OBV`, `V20_INSIDE`.

## Короткое решение
- Старые TradingSystemLab H1 и IntradayLab M15 **не менять и не останавливать**. Старый Streamlit `app.py` и текущую Intel-панель не трогать.
- Новый **изолированный** entrypoint `v20_app.py` в том же ControlCenter. **Без боковой панели**: три верхние вкладки **Главная / Журнал / Управление**, справа сверху одна кнопка «Обновить данные». Вкладки переключаются на клиенте без запроса данных, все три представления используют один и тот же session-local снимок. Нет свечей, графиков, сделок, PF/PnL (их показывает FINAM).
- Одна ручная кнопка refresh. Рядом с ней дата/время **последней ручной проверки панели** в МСК (`—` до первого нажатия); это не метка свежести данных торговых роботов, а также не гарантия удачного ответа источника. Ни автоматического опроса, ни запросов FINAM или торговых команд из панели. На CC-04 вручную допускается только закреплённый READONLY `operator-check` существующего V20-07 (без изменения Task); CC-05 исторический FINAM-снимок был отдельно принят, но из текущей панели по решению владельца удалено даже его чтение.
- **Главная показывает только работоспособность:** единый статус HEALTHY/HALTED/FAULT/UNKNOWN/STALE/НЕ ПОДКЛЮЧЁН, Windows Task, kill switch, **Heartbeat HEALTHY/UNHEALTHY/НЕТ ДАННЫХ** (экранная проекция технических `HEALTHY/STALE/UNKNOWN`, проверка свежести независима от общего HEALTHY; отсутствие источника никогда не отображается как UNHEALTHY), и последнюю ошибку, причём текущие поля скрываются при STALE/UNKNOWN/нет источника. Цикл, локальные позиции и стопы убраны с главной; торговые позиции/стопы и статистика остаются в FINAM, реальные циклы — в «Журнале». Отсутствие источника не превращается в «ошибок нет» или «robot healthy».
- Все не подключённые V20 состояния **НЕ ПОДКЛЮЧЁН** (не HEALTHY и не нули); Stale/Failed коротко видны. Все команда START/STOP/PAUSE/RESTART пока только текст и **не исполняются**.

## Вехи CC
| CC | Цель | Статус |
|---|---|---|
| CC-00 | Три идентичности V20 + изоляция от H1/M15 | OFFLINE PASS: три уникальных robot ID/файла, тесты и три Intel-карточки; diff PR #568 только ControlCenter, H1/M15 не менялись |
| CC-01 | Компактный экран + Журнал + Управление (без торговых кнопок) | PASS: компактная Главная и переход в Журнал физически проверены Intel 24.10.2026 16:20 МСК |
| CC-02 | Строгий независимый контракт и ручной приём из CC-owned NTFS файлов | Draft реализация; физическая policy НЕ ОДОБРЕНА |
| CC-03 | Установка V20-экрана на Intel без замены работающего приложения | PASS: изолированная preview-панель 8502 (24.10.2026); исходная 8501 не заменена |
| CC-04 | READONLY-наблюдение V20-07 staging; позднее runtime при наличии доказательств | PASS: код/Windows CI + физический ручной refresh трёх карточек Intel 8502 (24.10.2026); LIVE не подключён |
| CC-05 | Три FINAM READONLY источника (без токенов в Streamlit) | PASS: обезличенный экспорт, ACL/CI, три исторические FINAM-строки на Intel 8502 (24.10.2026); LIVE-брокер не подключён |
| CC-06 | Независимый изолированный controller | PASS (OFFLINE-контракт): CI SUCCESS + 12/12 отказов на Intel; три Windows Tasks неизменны и отключены. Реального контроллера исполнения пока нет |
| CC-07 | Авторизованные операторские команды на Intel | PASS только OFFLINE UI: 12 отключённых кнопок показаны на Intel 8502, Windows CI #40117395472 SUCCESS; реальное исполнение отдельно НЕ разрешено |
| CC-08 | Отчёт о приёмке, свежесть, инциденты и обслуживание | OFFLINE документация + FINAM-free Журнал PASS на Intel 24.10.2026; реальные LIVE-циклы, инциденты и эксплуатация НЕ приняты |

## CC-02: минимальный контракт источника
Один JSON на робота, фиксированные **CC-owned** имена `v20-shallow.json`, `v20-obv.json`, `v20-inside.json` в отдельном `C:\Control Center\data\v20-readonly`. Контракт `cc.v20.readonly.v1`: `schema_id`, `robot_id`, `account_alias`, `observed_at`, `heartbeat_at`, `engine_state`, `task_state`, `kill_switch`, `cycle`, `positions_local`, `stops_local`, `unresolved_local`, `last_error_code`, `events` (до 10), `payload_sha256` (канонический SHA256 без поля хеша). Допустимые статусы `HEALTHY/HALTED/FAULT/UNKNOWN`, bounded identifiers и error codes. **Никаких** токенов, истинных номеров счетов, строк broker orders, произвольных путей, команд или стратегических параметров.

Единый администраторский `deployment/v20-readonly-policy.json` намеренно **не поставляется и не включается**. На V20-07 требуется отдельно утвердить root file-ID `[volume, file_index_high, file_index_low]`, изолированные `account_aliases`, ownership и NTFS ACL: право WRITE только Administrators/SYSTEM, `ccpanel` READ ONLY. `deployment/v20-readonly-policy.example.json` с `approved=false`/root_id=null **не активирует** источник. Нативный `read_windows` повторно проверяет NTFS/reparse/ACL, pin root и bounded access. Файлы публикации V20 внутри торговых корней **не читаются**; будущий отдельный publisher должна предоставить разработка/развёртывание V20, без модификации frozen роботов. Пока policy не активирована, один click возвращает три NOT_CONNECTED.

TTL фиксирован 300 с; просроченный подтверждённый heartbeat на Главной обозначается UNHEALTHY, отсутствие подтверждённого heartbeat — НЕТ ДАННЫХ (не UNHEALTHY). Внутреннее состояние STALE сохраняется, просрочка блокирует актуальные метрики, а historical события остаются отмеченными STALE. Timestamp принятия UI не подменяет observed_at. Кросс-процессный one-shot gate — прежний `cc.manual_gate.export_gate`.

### Важная граница
В PR выполнена физическая установка **только** V20 preview 8502; legacy `app.py`/8501 не заменены. Это не разрешение модификаций Task, LIVE, FINAM, V20, H1/M15, токенов или брокерских действий. Нет merge без решения владельца. Runtime-публикатор V20 для CC-owned JSON не реализован и не считается готовым.


## CC-04: V20-07 staging (24.10.2026)
Фактическая Intel-приёмка V20-07.4 дала `PASS_4_OF_4_STAGING_LIVE_OFF`, три Windows Tasks Disabled, LIVE OFF, worker count=0 по доступным процессам. Исходник check: `V20_TradingSystem_M15/V20-07/Operator-V20.ps1`, принятый Git blob `6905945c34bb14da119f6a1f7a6e3e79edf46be0`. Это **не** работающий торговый runtime.

CC-04 использует только новый `cc/v20_staging.py` внутри ControlCenter. На ручное нажатие он проверяет фиксированный controller Git blob и точную обёртку для каждого `v20-*-check.ps1`, затем исполняет **только check** по фиксированному пути, под текущим Windows SID панели. `start`, `restart`, `stop`, FINAM, торговые библиотеки и Task mutation запрещены. Результат принимается лишь при полном согласовании ROBOT/SHA/SID_PASS/Task Disabled/LIVE OFF/BLOCKED_PLACEHOLDER/kill NOT_CONFIGURED_STAGING/reconciliation NOT_AVAILABLE_STAGING/отсутствие идентифицированных workers. Вне Windows или при отсутствии файлов/прав результат остаётся неподключённым.

Отдельная метка `STAGING · LIVE OFF` на Главной **не равна HEALTHY**: Windows Task DISABLED, исполнение заблокировано; Heartbeat, Kill switch и reconciliation — **НЕТ ДАННЫХ**. Неподтверждённые работники — НЕТ ДАННЫХ (не 0). Снимок старше 300 секунд переходит в STALE. Ошибка SID не обходится, а сообщается отдельно. Старая Streamlit 8501 и действующие H1/M15 неизменны.

Развёртывание только в изолированную V20 preview 8502, с резервным копированием целевых файлов, сравнением SHA256 и откатом при ошибке. Подключение самого Intel Streamlit-сервиса требует текущего процесса под совместимым с V20-07 SID; проверяется физическим READONLY-кликом и не объявляется PASS до такого клика. Этот документ не меняет V20 roadmap, не даёт разрешения на LIVE или Merge.


## CC-04: фактическая приёмка Intel (24.10.2026, 15:14 МСК)

- GitHub PR #568 exact deployed head `1138a32c4426fc4c4b5938b107556713ded90459`; native CI #40092111444 `completed/success`. Установка из проверенных SHA256: `cc04_install=pass`, резервная копия `C:\Control Center\cc04-install-1138a32c\backup`.
- READONLY диагностика Intel подтвердила `cc04_panel_8502=running` и `cc04_sid_match=True` для Task `v20-shallow` (тот же SID). В публичных отчётах не приводить полный SID.
- Владелец прислал фактический скриншот `127.0.0.1:8502` после ручного нажатия, последняя проверка **24.10.2026 15:14:55 МСК**. На трёх карточках **Shallow, OBV, Inside**: `STAGING · LIVE OFF`, Windows Task `DISABLED`, LIVE `OFF`, worker `0`, исполнение заблокировано, heartbeat / kill switch / reconciliation **НЕТ ДАННЫХ**.
- Итог: **CC-04 STAGING PHYSICAL PASS**. Это доказывает работающую UI-интеграцию check-only, не HEALTHY торгового runtime, не текущие брокерские остатки/позиции/SLTP и не разрешение запускать задачи. Streamlit 8501, H1/M15, V20 файлы и Windows Tasks не менялись. PR остаётся Draft, merge не выполнялся.

## CC-05: минимальный следующий шаг по существующему roadmap

V20-06 завершён физическим `PASS_READONLY_3_OF_3` для трёх счетов после пополнения (обезличенные результаты опубликованы в Draft PR #567). Готовые локальные отчёты `ACCOUNT_STATE_REPORT_FUNDED.json` и `BROKER_READONLY_REPORT_FUNDED.json` **исторические**: это не непрерывный FINAM monitoring и не источник текущей финансовой власти.

В CC-05 только ControlCenter должен показывать по каждому роботу отдельное **подтверждённое время/статус последней READONLY-проверки в Журнале**, не загружая Главную. Не повторять FINAM API, не получать токены в Streamlit, не считать старые квитанции свежими, не читать документы/секреты V20 торгового корня напрямую из UI. Разделить внешний операторский обезличенный экспорт и проверяемый CC-owned вход; policy/ACL и физическая приёмка остаются самостоятельными явными условиями. Без LIVE, заявок, раздачи прав Task, изменения V20/H1/M15.

## CC-05 — операторский HISTORICAL READONLY экспорт (24.10.2026)

Источник — уже полученная фактическая V20-06 квитанция `C:\V20Lab\readonly-06\BROKER_READONLY_REPORT_FUNDED.json`, зафиксированное наблюдение `2026-10-24T06:07:32.065908+00:00` (09:07:32 МСК), 3/3 `PASS_READONLY`, `MONEY=PASS`, `POSITIONS=0`, `ACTIVE_ORDERS=0`. Это **исторический** отчёт, не broker live/poll и не разрешение торговли.

Только **отдельно запускаемый оператором**, а не Streamlit, `deployment/export_v20_finam.py` читает фиксированный funded JSON **без** FINAM API и токена, проверяет три уникальные идентичности SHA256, `entry_authorized=false`, отсутствие диагностических заявок/SLTP-подтверждений и три PASS. Он создаёт **только один** (exclusive, без перезаписи) очищенный JSON `C:\Control Center\data\v20-finam\finam-funded-readonly.json` с короткими робот-именами, булевым статусом, нулём на момент проверки, временем исходного наблюдения/экспорта и SHA256 исходного отчёта. Финансовые суммы, account_id/hash и торговые/READONLY токены в CC-файл **не копируются**. Папка должна быть заранее выделена оператором с ACL/owner, принимаемыми существующим нативным `read_windows(admin_policy=True)`. Сам Python не создаёт папку и не выдаёт разрешений.

При однократном ручном refresh Streamlit вызывает `cc.v20_finam.acquire`: нативное READONLY-чтение только CC-owned пути, строгая схема, ROBOT 3/3, старые timestamp сохраняются. При отсутствии файла, неверном ACL, чужих/дублированных идентичностях, PARTIAL/подмене данных возвращает **НЕТ ИСТОЧНИКА**. Если источник подтверждён: под каждой робо-карточкой только `FINAM READONLY · ИСТОРИЧЕСКИЙ PASS · <дата исходного наблюдения>` и пояснение `Не текущий статус брокера`. Текущие STAGING/LIVE OFF, Task, heartbeat и kill switch **не меняются**. При повторном показе старый снимок никогда не становится сегодняшней свежестью.

Эти критерии физической приёмки CC-05 подтверждены установщиком, выводом Intel, Windows CI и скриншотом трёх карточек; исторический снимок не является текущим брокерским наблюдением. Никаких изменений V20/H1/IntradayLab/Windows Task, брокерских запросов или автоматического опроса; merge только с отдельным разрешением владельца.

## CC-05: фактическая физическая приёмка и компактный экран (24.10.2026, 15:49 МСК)

- Исходная FINAM READONLY квитанция содержит 3/3 PASS, MONEY=PASS, POSITIONS=0, ACTIVE_ORDERS=0 на **24.10.2026 09:07:32 МСК**. При ручном обновлении новых запросов FINAM не выполнялось.
- Оператор Intel создал `C:\Control Center\data\v20-finam` с owner Administrators, ACL: SYSTEM/Administrators full, панель `alkos` read+execute; исходный protected `C:\Control Center\data` без изменения. Новая папка используется только для обезличенного CC-owned JSON.
- Exact SHA развернутой версии `1ac589d2309d0a9e55684cd95250dc446b5d4b01`, GitHub Windows CI #40094211554 **SUCCESS**. Установщик: `cc05_install=pass`, `cc05_export=pass_historical_only`; резервная копия `C:\Control Center\cc05-install-1ac589d2\backup`. `cc05_runtime_accepted=no` — флаг самого установщика (не тестировал браузер).
- Владелец передал скриншот реальной Intel-панели 8502 **24.10.2026 15:49 МСК**: три независимые карточки Shallow, OBV, Inside показывали `STAGING · LIVE OFF`, Task DISABLED, worker 0, heartbeat/kill/reconciliation = нет данных, FINAM READONLY **ИСТОРИЧЕСКИЙ PASS 09:07:32 МСК** и предупреждение, что текущее состояние брокера не подтверждено.
- Итог: **CC-05 PHYSICAL PASS** для отображения исторического обезличенного FINAM READONLY по трём роботам. Это не приёмка FINAM live monitoring, не торговая авторизация и не подтверждение актуальных позиций/финансов после момента наблюдения.
- По замечанию владельца тот же день упрощён экран **Главная**: по каждому роботу только статус + Heartbeat + Windows Task + Kill switch и последняя ошибка **только если она реально есть**. Из карточек убраны worker count, reconciliation, пояснения и исторический FINAM; они сохранены во вкладке **Журнал**, внутри уже существующих раскрывающихся блоков роботов. Отдельной четвёртой вкладки/автоматического опроса нет. Отдельный UI-коммит затем прошёл Windows CI и физическую Intel-проверку 24.10.2026 16:20 МСК; ранее подтверждённый CC-05 PASS остаётся действительным.

## CC-01/CC-05 компактный экран — физическая приёмка Intel (24.10.2026, 16:20 МСК)

- Установщик `cc_compact_install=pass`, установленный UI commit `ef66aa9911d7f686308580a87ef34053221007cc`, GitHub Windows CI #40096623795 `completed/success`; резервная копия `C:\Control Center\cc05-compact-ef66aa99\backup`. H1, IntradayLab, V20 и Tasks не изменены.
- Оператор передал два скриншота панели `127.0.0.1:8502`, время последнего refresh 24.10.2026 **16:20:12 МСК**. На Главной Shallow/OBV/Inside каждая имеет **только название, статус STAGING · LIVE OFF, Heartbeat НЕТ ДАННЫХ, Windows Task DISABLED, Kill switch НЕТ ДАННЫХ**; Worker, Reconciliation и исторический FINAM отсутствуют на Главной. Нет ложного HEALTHY.
- Вкладка **Журнал** открывается, три независимых раскрывающихся заголовка показаны. Содержимое раскрытых секций на этих двух кадрах **не проверено**; ранее исторический FINAM READONLY был принят на Главной до переноса.
- Итог: **COMPACT UI PHYSICAL PASS**, функционал три робота и исторический CC-05 PASS не отозваны; это не приёмка нового LIVE контроллера.

## CC-06: независимый controller — начат как OFFLINE-only

Источник только `ControlCenter/controller/v20_control.py` — отдельный CLI, **не импортируется из Streamlit**, не получает PowerShell, Task, broker, токены, V20 и файловые пути. Проверяет строго три ID `v20-shallow/v20-obv/v20-inside`, четыре действия `start/pause/stop/restart`, короткий безопасный `request_id`; для каждого валидного запроса возвращает машинно-читаемое `REFUSED_NOT_AUTHORIZED`, `executed=false`, `task_mutated=false`, `finam_contacted=false`, `live_authorized=false`, с exit code 3. Запросы с неизвестными роботами/командами и path-подобными ID отклоняются.

Данный **CC-06 Draft scaffold** — это проверяемый контракт разделения UI и будущего исполнителя, **не готовое реальное управление**. Команда `pause` пока отсутствует в V20-07 operator-скрипте, а `start/restart` намеренно запрещены V20-07 при LIVE OFF. Никаких Task-мутаций и кнопок в UI. Физическая OFFLINE-приёмка 24.10.2026 пройдена: это только контракт отказов. CC-07 (реальные действия) — после отдельной авторизации владельца и доказательства совместимости с V20 release. Не менять защищённые проекты.

## CC-06: фактическая Intel OFFLINE-приёмка (24.10.2026)

- Исходный код: SHA `922ed4f1a0bbebff57d6a8daf028c74f06d95c8e`, контроллер `controller/v20_control.py` SHA256 `6ebfa76af3f3bb9d378b60ff34c3ca04ceefbb93795d2fadc45f94a9b76dafa3`. Windows CI #40115884660: `completed/success`.
- Вывод запуска `cc06-offline-922ed4f1.ps1` на Intel: `cc06_refusals=12_of_12_pass`; `cc06_windows_tasks=unchanged_disabled_3_of_3`; `cc06_no_finam_no_token_no_live_no_orders=yes`; `cc06_physical_offline_contract=pass`.
- **CC-06 OFFLINE-контракт — PHYSICAL PASS**: три ID × четыре команды распознаны и безопасно отклонены; это не установка полномочного сервиса контроллера и не разрешение управлять Windows Tasks. Никакие V20/H1/M15 источники, Windows Tasks, токены, FINAM и робот не менялись.
- Следующий CC-07: сначала независимый **неактивный интерфейс управления** и негативные тесты без доступа к Windows Task; реальное исполнение `start/stop/restart` и определение семантики `pause` требуют отдельной авторизации, совместимости с версией V20 на Intel и готовности торгового runtime. Не обойти V20-07 LIVE OFF. До этого на Intel не запускать команды управления.

## CC-07: предварительный интерфейс команд (OFFLINE, без права исполнения)

В отдельной вкладке `Управление` на V20 preview 8502 представлены три независимых набора `START/PAUSE/STOP/RESTART`. Все **12 кнопок навсегда disabled в данной ревизии**, без `on_click`, без импорта `controller/v20_control.py`, без Task/PowerShell/FINAM вызовов. Используются стабильные ключи `cc07-v20-*-*`. Кнопка ручного READONLY обновления остаётся единственной активной.

Код прошёл Windows CI #40117395472 (SUCCESS). Физическая установка на Intel выполнена штатным установщиком, в том числе с резервной копией, и экран вкладки подтверждён скриншотом оператора 24.10.2026 21:51 МСК. Здесь не снимаются ограничения V20-07: `start/restart` по-прежнему запрещены для LIVE OFF, `pause` в операторе нет, `stop` не вызывается. Реальное управление будет оцениваться отдельно и **только после прямого разрешения владельца**. Никаких изменений торговых проектов, Windows Tasks, FINAM, токенов, текущей панели 8501 или живого H1/M15.

## CC-07: физическая приёмка OFFLINE UI (24.10.2026, 21:51 МСК)

- Проверенный commit и развернутый код: `9bb7e2ba5bc1f9fe2a423700ee1af829c558ee2e`; GitHub Windows CI #40117395472 `completed/success`; изменения только в `ControlCenter/`, PR #568 остаётся Draft, GitHub `main` без изменений.
- Установщик на Intel вывел `cc07_disabled_ui_install=pass`, `cc07_buttons=12_disabled_no_handlers`, `cc07_only_preview_8502_ui_changed=yes`, `cc07_no_task_no_finam_no_live_no_orders_no_h1_no_m15_no_v20_mutation=yes`; backup: `C:\Control Center\cc07-disabled-ui-9bb7e2ba\backup`. `cc07_runtime_accepted=no` означало, что установщик не проверял браузер.
- Оператор передал скриншот браузера на `127.0.0.1:8502` от **24.10.2026 21:51 МСК**. Видна вкладка «Управление»: три секции Shallow/OBV/Inside, по четыре визуально отключённые кнопки START/PAUSE/STOP/RESTART в каждой, предупреждение «команды не авторизованы» и пояснение отсутствия управляющих обработчиков. Ручная проверка ещё не запускалась в данной сессии (`Последняя проверка: —`), это ожидаемо.
- **CC-07 OFFLINE UI PHYSICAL PASS**, но **CC-07 LIVE CONTROL NOT AUTHORIZED/NOT TESTED**: не было включения Windows Tasks, проверки настоящего `START/STOP/PAUSE/RESTART` или режима торговли. Штатный V20 оператор по-прежнему не поддерживает `pause` и отказывает `start/restart` при LIVE OFF. Нельзя переименовывать этот PASS в приёмку настоящего управления.
- CC-08 — независимо от LIVE: оформить доказательства CC-03..07, расписать свежесть/отказы/реакцию оператора и процедуры поддержки; поддерживать ручное чтение, отдельную панель 8502, не подменять «нет данных» успешной проверкой, не изменять торговые проекты.

## CC-08: приёмка трёх раскрытых секций Журнала (24.10.2026 21:57 МСК)

- Оператор передал два изображения `127.0.0.1:8502` после ручного «Обновить данные» (метка `24.10.2026 21:57:30 МСК`); все три раздела Shallow/OBV/Inside раскрыты.
- Во всех трёх: STAGING LIVE OFF, Worker 0, исполнение заблокировано, подтверждённых событий нет; Reconciliation и последняя ошибка «НЕТ ДАННЫХ». Отображение этих сообщений **не доказывает торговый runtime**.
- FINAM READONLY в каждой секции остаётся историческим PASS от **24.10.2026 09:07:32 МСК**; текст корректно предупреждает, что текущий статус брокера неизвестен. Время нажатия refresh не стало новым FINAM timestamp.
- **CC-08 JOURNAL DISPLAY PHYSICAL PASS**. Весь CC-08 как эксплуатационная система (инциденты, реальные циклы, LIVE свежесть) не принят. Нет Task/FINAM/токенов/торговых действий.
- Процедуры и границы наблюдения: `docs/V20_CC08_OPERATIONS.md`.

## CC-08: упрощение Журнала по решению владельца (24.10.2026)

- В рабочем интерфейсе `v20_app.py` отключено чтение исторической FINAM READONLY-квитанции; строк `FINAM READONLY` и `Деньги PASS` больше нет. Вся историческая информация CC-05 сохранена в `docs/V20_CC08_OPERATIONS.md` и прежнем защищённом обезличенном экспорте, **без** актуализации времени, брокерских запросов и удаления доказательств.
- В трёх независимых раскрывающихся Журналах выводятся `Время / Цикл / Результат / Причина`, максимум **10 подтверждённых событий** на робота, новые сверху. Контракт проверяет `events` (не более 10, хронологический порядок, `PASS/FAULT`), но ещё **нет подключённого V20-публикатора последних десяти завершённых циклов**. До отдельной приёмки реального источника нельзя гарантировать наличие 10 реальных циклов — STAGING может корректно показывать «Подтверждённых событий пока нет».
- Компактная «Главная», ручное обновление и 12 отключённых кнопок CC-07 не изменены. Вся правка только `ControlCenter/`; frozen V20/H1/M15, Tasks, FINAM и панель 8501 не затронуты.
- Статус: **PHYSICAL PASS обновлённого FINAM-free Журнала на Intel 8502** (скриншот владельца 24.10.2026 22:22 МСК, подтверждённый ручной refresh 22:22:22 МСК); Windows CI #40124087130 для установленного SHA `0d180922c12deb2612b99bab4b23ef9f99dbba53` — SUCCESS. Это OFFLINE UI PASS, не приёмка LIVE-циклов.

## CC-08: физическая приёмка Журнала без FINAM (24.10.2026, 22:22 МСК)

- Проверенный код интерфейса `v20_app.py` — SHA `0d180922c12deb2612b99bab4b23ef9f99dbba53`, GitHub Windows CI #40124087130 `completed/success`. На Intel: `cc08_journal_install=pass`, `cc08_finam_ui=removed_no_read`, `cc08_journal=last_10_completed_cycles_newest_first_when_source_available`, `cc08_controls=12_disabled`; backup `C:\control center\cc08-journal-0d180922\backup`. Установщик изменил только UI 8502, не тронув TradingSystemLab/IntradayLab/V20, FINAM и Windows Tasks.
- Владелец прислал **скриншот работающего** `127.0.0.1:8502` от 24.10.2026 **22:22 МСК**. Все три раздела Журнала (Shallow, OBV, Inside) раскрыты, в них отображается `STAGING · LIVE OFF`, `Worker: 0`, отсутствие подтверждённых событий, `Reconciliation` и `Последняя ошибка` — «НЕТ ДАННЫХ». Ранее отображавшиеся строки `FINAM READONLY` / `Деньги PASS` **отсутствуют**. Время ручной попытки `Последняя проверка: 24.10.2026 22:22:22 МСК` не является временем последнего цикла робота.
- **CC-08 FINAM-FREE JOURNAL OFFLINE UI PHYSICAL PASS**. Таблица «последние 10 циклов, новые сверху» подтверждена Windows UI-тестом на синтетических данных; реальных событий пока нет, поскольку V20 STAGING и runtime publisher не подключён. Не выдавать эту проверку за приёмку live telemetry, выполнение сделок или актуальное состояние брокера. Полный CC-08 (реальные инциденты/свежесть runtime) остаётся открытым.

## Итоговый OFFLINE-аудит по CC-00–CC-08 (25.10.2026)

Основание: фактический GitHub `main=6f352acfac7ebdfabba73e143c4dfea3a6e48507`; Draft PR #568 (до оформления данного отчёта) `6573f0a0484ac6a67a6549bcd947e37d497b6413`; точный Windows CI #40125233302 `completed/success`. В проверенном diff **19 файлов, все только под `ControlCenter/`**. Роботы, торговые стратегии, результаты, конфигурации и Windows Tasks не изменялись.

- **CC-00 OFFLINE PASS:** три строго заданных ID `V20_SHALLOW/V20_OBV/V20_INSIDE`, уникальные JSON-имена и алиасы, fail-closed тесты разделения; на Intel три отдельные карточки и вкладки, сохранён legacy H1 8501. Это проверка разделения в CC, не проверка LIVE идентичности publisher для V20.
- **CC-01, CC-03, CC-04 OFFLINE/STAGING PASS:** компактный интерфейс 8502, ручной refresh, три независимых STAGING `LIVE OFF` и Task `DISABLED`; ни один робот не был запущен ради панели.
- **CC-05 HISTORICAL PASS:** очищенный отдельный FINAM READONLY-отчёт ранее был проверен 3/3. По решению владельца сведения о деньгах и историческая квитанция не читаются/не отображаются в текущем интерфейсе. Доказательства остаются в offline-документации.
- **CC-06 OFFLINE CONTRACT PASS:** 12/12 отказов на Intel, Tasks не изменились; реального диспетчера действий нет.
- **CC-07 OFFLINE UI PASS:** 12 отключённых кнопок без обработчиков; `start/restart` при LIVE OFF запрещены V20-07, `pause` не реализован в V20-07. Реальное управление не принято.
- **CC-08 OFFLINE PLAYBOOK + JOURNAL UI PASS:** описаны источники, TTL, реакции на сбои и резервные копии; на Intel 24.10 22:22 приняты три раскрытых FINAM-free журнала. Контракт и UI тестируют до 10 событий, последние сверху. **Никаких подтверждённых LIVE циклов V20 пока нет**.
- **CC-02 НЕ ЗАКРЫТ для production:** строгий receiver присутствует, но `deployment/v20-readonly-policy.json` сознательно отсутствует, пример `approved=false`; отсутствует одобренный CC-owned publisher реальных циклов и физически подтверждённая policy/ACL связка. Не подменять STAGING наблюдения этим источником.

Остаток работы **без добавления новых этапов**: (1) отдельное решение владельца по merge только OFFLINE-кода PR #568; (2) после готовности V20 и отдельной авторизации — согласовать read-only publisher и CC-02 policy, получить реальные до 10 циклов и heartbeat; (3) отдельно согласовать команды/права/аудит CC-06/07 и семантику PAUSE; (4) принять CC-08 на реальном runtime и инцидентах. До этих решений **не включать Tasks, LIVE и кнопки, не повышать права панели**. Текущий Intel UI 8502 не требует переустановки ради данного документа.

## CC-06/07: самостоятельный OFFLINE preflight команд (25.10.2026; CI и Intel НЕ приняты)

Следующий шаг существующего CC-06/07 **без новой фазы**: `controller/v20_rehearsal.py` — отдельный от Streamlit **чистый** симулятор предпосылок управляющих команд. `RehearsalFacts` получает только недоверенные *тестовые* признаки: роль/подтверждённую личность, доверие и свежесть источника, Task state, число открытых позиций, reconciliation и наличие отдельного LIVE release. Любое отсутствие подтверждения, нетипизированный вход, дубликат `request_id`, неизвестный Task state и открытая позиция формируют причины отказа. `start` требует `DISABLED`, `stop/restart` требуют `RUNNING`, `pause` всегда отмечен `PAUSE_SEMANTICS_NOT_APPROVED`.

**Любая** комбинация входов, включая искусственно положительные факты, завершается `REFUSED_OFFLINE` + `NO_APPROVED_EXECUTION_ADAPTER`, `executed=false`, `task_mutated=false`, `finam_contacted=false`, `live_authorized=false`. Формируется сериализуемая **заготовка audit receipt**, но **журнал на диск пока не записывается** (`audit_persisted=false`), непрерывной защиты от повторов между процессами нет. Такой контракт не может превратиться в кнопку с настоящими полномочиями просто сменой аргумента. Сервис аутентификации, доверенные снимки, атомарный реальный audit trail, исполнитель штатных V20-команд, защита открытых позиций и PAUSE требуют отдельной последующей разработки и приёмки в рамках CC-06/07; сам V20 оператор/стратегии не меняем.

В тестах запланированы матрица 3 робота × 4 команды, полный набор отказов, контроль Task state, неизвестных/просроченных показаний, позиций, дубликатов и статический запрет I/O/исполнения. Данный Draft **не развёрнут на Intel 8502**, не изменяет 12 отключённых кнопок и никаким образом не разрешает запуск V20, FINAM, Windows Tasks или merge. После точного Windows CI потребуется отделить PASS нового симулятора от ранее физически принятого CC-06-контракта; не объявлять это приёмкой полномочного контроллера.

## CC-06/07: durable OFFLINE command intake (25.10.2026)

- Added `controller/v20_offline_journal.py` without changing existing `v20_rehearsal.py`. All three robots and four commands are permanently refused: no Task, FINAM, shell, Streamlit, execution adapter, LIVE toggle, or trading-directory access.
- Operator alias allowlist and role/freshness checks are **simulated preflight only**, NOT production Windows SID authentication. True OS identity, ACL checks, and live authorization remain unimplemented and require a distinct approved change.
- CC-owned SQLite database records refusals with UTC time, alias, robot, command, request ID, blockers, and hypothetical before/after state. Unique IDs survive journal re-opening; duplicates are refused and audited. SQLite exclusive write lock protects concurrent intake; lock/audit failure refuses, never executes.
- The optional post-check compares two *simulated* snapshots. It never claims a real Windows Task or FINAM postcondition; absent snapshot is `NOT_OBSERVED_NO_EXECUTION`.
- Added autonomous OFFLINE tests: 12/12 refused commands, durable duplicate detection after restart, operator/source gating, post-check mismatch, contending writer, malformed inputs, forbidden symlink, static no-executor import check.
- This is an incremental CC-06/07 OFFLINE development result, **not CC-07 LIVE acceptance**. Panel buttons remain disabled; no Intel install/merge/Task mutation was performed. CC-02 authenticated real telemetry and PAUSE/STOP semantics are still open.

## CC-06/07: Intel OFFLINE acceptance — пункт 6 закрыт (25.10.2026)

Оператор выполнил `cc07-offline-intel-check-25-10-2026.ps1` на Intel Windows. Переданный им фактический вывод:

```text
CC07_OFFLINE_12_OF_12=PASS; DUPLICATE_REPLAY=PASS; AUDIT=PASS; LIVE_EXECUTION=NO; FINAM=NO; WINDOWS_TASK_CALLS=NO
CC07_INTEL_OFFLINE_ACCEPTANCE=PASS
```

Версия проверенного пакета контроллера: PR #568 head `b5fab2a5f3379b2bb8d14034d5a9663a1983fb53`, native Windows CI #40217839469 `completed/success`. Это **представленное оператором свидетельство физической OFFLINE-проверки**, не независимая проверка текущих Windows Tasks и не проверка реального исполнения. Контроллер остаётся без полномочий, журнал и допуск оператора пока только OFFLINE. Принят: **CC-06/07 автономная Intel OFFLINE-проверка / пункт 6 PASS**. Не приняты: LIVE-управление CC-07, реальный CC-02 publisher/Heartbeat/циклы и LIVE-эксплуатация CC-08.

По согласованному плану **работы Control Center до запуска V20 на этом завершены**. Не создавать искусственные циклы или альтернативные источники, не включать Tasks и не менять роботов. После **отдельно разрешённого запуска V20** продолжить CC-02: оценить реальные `status.json` / `m15.jsonl`, одобрить CC-owned READONLY-источник и policy/ACL, затем принять подлинные Heartbeat/до 10 завершённых циклов на Intel и CC-08. Реальные команды CC-07 — позже, только по отдельной авторизации. PR #568 остаётся Draft; merge не разрешён.
