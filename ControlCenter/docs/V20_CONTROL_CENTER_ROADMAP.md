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
| CC-02 | Строгий независимый контракт и ручной приём из CC-owned NTFS файлов | PASS: физические Intel READONLY-снимки 3/3, ручной refresh увеличивает реальные циклы на 8502 (27.10.2026); постоянный непривилегированный запуск панели отдельно не принят |
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


## CC-02 real V20-08 readonly integration — 27.10.2026 (Draft, no Intel acceptance)

- V20 PR #567 handoff confirms Task Running / Kill Switch HALTED / HALTED_NO_NEW_ENTRIES on all three V20 workers. Their real live-m15.jsonl logs have utc/robot/state; a check-only operator is pinned at Git blob 6f539f9c421efb56d492f1c903b998b4e8f4a9ca.
- New deployment/v20_live_export.py is a manually invoked, isolated READONLY collector: it validates and invokes only V20-08 operator -mode check -robot all, verifies fixed per-robot logs and kill switches, and creates up to 10 real dated events per robot. No FINAM API, tokens, SQLite or trading/task mutation; no separate publisher inside Streamlit.
- The operator check may exit nonzero with HEALTH_PARTIAL during intentional HALTED. The exporter compares task, switch, newest cycle UTC and monotonic log counts instead of treating HALTED as a dead worker. Actual positions, stops and unresolved broker reconciliation remain unknown (null).
- On explicit --publish the operator tool writes only sanitized CC-owned JSON. Its default mode only PREVIEWs on stdout, without writing. The installed CC-02 policy is deliberately absent pending owner/SID/NTFS/root file ID verification on Intel.
- Pure CC journal contract adds observation result classifications PENDING, HALTED and UNKNOWN alongside PASS/FAULT, never changing a V20 trading rule. Last-cycle timestamp is taken from worker log, not UI refresh time.
- Control buttons remain disabled. V20-08 start/restart may ARM; V20-08 stop HALTs entries while keeping workers running. STOP Windows Task requires separate flat/protection rule. No LIVE activation, merge, or Windows Task changes performed.
- Current status: CC-02 source prepared for native Windows CI and physical readonly acceptance; CC-06/07 LIVE not authorized; CC-08 runtime acceptance pending.

## CC-07 live control semantics — 27.10.2026: OFFLINE policy, no execution

Intel CC-02 physical output: Shallow 3272, OBV 3221, Inside 3276 worker
attempts; 10 recent authentic JSONL events each; `cc02_receiver=PASS_3_OF_3`.
Every Task was RUNNING, each Kill Switch HALTED. No ARM or Task mutation.

The source-backed operator V20-08.5 is **unchanged**. Defined future actions:

- **PAUSE** = stock V20 `-mode stop`: HALT *new entries*, workers continue
  managing existing positions and their protective SLTP. Flat proof not required.
- **STOP** = HALT new entries, then stop a worker Task **only after** current
  independent broker GET-only confirmation of zero positions and zero active
  orders, and an identity/Task verification. Never abandon a live position.
- **START** = stock V20 `-mode start`: can start the worker and then **ARM**.
  This is trading authorization, never a harmless button self-test.
- **RESTART** = stock V20 `-mode restart`: broker FLAT prerequisite and
  **ARM** afterwards. Never restart while protection is active.

The new `controller/v20_live_policy.py` and tests are *pure OFFLINE*
semantic/preflight checks only. They never call PowerShell, FINAM or Task
APIs and return `REFUSED_NO_LIVE_ADAPTER` even when all checks pass.
Actual OS identity, audit, trusted broker source, execution binding and
physical approval remain separate. Existing 12 UI buttons stay disabled.
The user requested: monitoring then control acceptance, then ARMED, not
an immediate ARM. Do not touch V20/H1/IntradayLab modules or active robots.

## CC-02 manual refresh of genuine V20 worker source — 27.10.2026

Intel 8502 monitoring initial physical PASS: `cc02_export=PUBLISHED_CC_OWNED`,
`cc02_receiver=PASS_3_OF_3`, exact per-robot running/HALTED,
real 10 JSONL events each; no live ARM. Single published snapshots do
**not** automatically refresh in the installed Streamlit process.

To make the operator's existing manual `Обновить данные` button fetch
**new** telemetry, add `cc/v20_manual_export.py`. Only on a deliberate
button click under the existing cross-process gate, launch the approved
immutable CC-only `deployment/v20_live_export.py --publish` via a fixed
Python path. Its sole external V20 operation is the existing immutable
`-mode check`; it may return intentional `HEALTH_PARTIAL`. The UI then
reads through the unchanged native NTFS policy/pinned-root receiver.
No background polling, Task mutations, FINAM API, SQLite trading state,
or live-control calls. Source hash/availability/timeout/export failures
fail closed and never assert fresh heartbeat.

Code and hosted CI are **not physical Intel acceptance**. Validate that
clicking Refresh advances source cycle timestamps on the installed 8502
process without touching H1/V20. Separate CC-07 adapter and command
authorization are still required before any START/PAUSE/STOP/RESTART,
and explicit owner ARM comes last.

## CC-02 физическая приёмка живого обновления — 27.10.2026

Владелец подтвердил в браузере `127.0.0.1:8502` отображение всех трёх V20
карточек и изменение реальных номеров циклов **после** кнопки «Обновить
данные». Подтверждённый Intel операторский READONLY-экспорт:
`cc02_export=PUBLISHED_CC_OWNED`, `cc02_no_finam_no_task_mutation_no_arm=YES`.
Из настоящего приёмника для каждого робота:
`status=HALTED reason=LOCAL_REPORT`; последние циклы при публикации
Shallow=3415, OBV=3364, Inside=3420, у каждого десять наблюдений.

Проверено физически: TCP 127.0.0.1:8502 `LISTEN`, HTTP
`/_stcore/health=200`, новый PID 11200, после принудительного
перезапуска прежнего PID 15104. GitHub Windows CI #40545027017 —
`completed/success` на точном PR head `b5136254586f21e373ae47665cc87b6c999572bf`.
Это **PASS приёма данных и ручного refresh**, а не CC-07 LIVE controller
acceptance и не разрешение ARM.

Незакрытый операционный вопрос: установленный `C:\\Control Center\\venv`
доступен из повышенного PowerShell, но пользователь `alkos` без повышения
получает ACCESS_DENIED. Текущий работоспособный процесс 8502 запущен
с повышенными правами/неверифицированной сервисной идентичностью; его
**не использовать для исполнительного управления**. До CC-07 acceptance
требуется утверждённый непривилегированный сервисный SID и отдельный
аудируемый исполнитель, не переносить токены/торговые полномочия в UI.
Управляющие START, PAUSE, STOP, RESTART по-прежнему `disabled=True`.

Выполненные тесты, проверки и изменения относятся исключительно к
`ControlCenter/`. Ни `TradingSystemLab`, ни `IntradayLab`, ни
`V20_TradingSystem_M15` и их runtime/Task/FINAM не изменены.


## CC-07A: independent Windows operator — staged 27.10.2026

Owner approved development exclusively inside ControlCenter. This is **source-stage only**, not deployed Intel CC-07 or LIVE ARM approval.

- New `controller/cc07-v20-operator.ps1` is a separate PowerShell executor. Streamlit cannot import/invoke it. Existing twelve UI controls remain disabled pending Intel acceptance.
- Exact pinned V20 operator blob `6f539f9c421efb56d492f1c903b998b4e8f4a9ca`, launcher blob `93fc1ce4aded6c40453da14deb4846e10da1b14f`. Frozen V20 files and Tasks are unchanged.
- Default `preview` mode is check-only and distinguishes intentional HALTED from broker failure.
- `execute` checks Intel host, pinned stock operator, Windows Task principal SID and operator SID, admin authorization, worker freshness <=90 sec, exact console confirmation, unique request id, exclusive mutex and durable CC-only audit with fsync before/after.
- `PAUSE` invokes stock V20 `stop` meaning HALT new entries. If already HALTED, audit no-op without touching the Task, positions or stop protection.
- `START` and `RESTART` require separate per-request admin-owned release (<=5 minutes), FINAM GET-only FLAT and zero active orders. They both ARM. No release file is created or installed in this stage.
- `STOP` is not V20 `stop`: first prove broker FLAT, then HALT entries, confirm FINAM FLAT again, only then stop selected Windows Task. Unknown or inconsistent broker evidence refuses action.
- Audit directory and release are not created in this stage; a missing protected audit directory blocks every execution. Preview does not mutate live state.
- Follow-up physical acceptance: separately install the protected CC-only executor + audit directory, verify operator SID and source pins, test preview and already-HALTED PAUSE no-op. Do not execute ARM/restart/Task stop without a new explicit approval.
- Critical isolation blocker: the V20 panel on 8502 was manually restored with elevated identity. Before any command bridge from Streamlit, run it under dedicated non-admin SID and establish authenticated narrow IPC. Never give the UI FINAM tokens, admin rights or V20 Task privileges.
- Native Windows syntax/authority regression in CI does NOT establish physical Intel acceptance. PR #568 remains Draft, no merge.

### CC-07A Intel Preview incident and fix — 27.10.2026

- First physically invoked `cc07-preview-intel-20261027.ps1` aborted on Shallow: Windows PowerShell 5.1 promoted the native stock CHECK's expected `V20_08_5_HEALTH_PARTIAL` stderr into a terminating `NativeCommandError` under `ErrorActionPreference=Stop`. It did not call any V20 start/stop/restart or ARM mode.
- Independent V20 READONLY snapshot operator had already proven three deliberately HALTED running Tasks with fresh `HALTED_NO_NEW_ENTRIES`; no evidence this was a trading failure.
- Fix changes only ControlCenter `controller/cc07-v20-operator.ps1` proof parsing: check-only child is captured with temporary `ErrorActionPreference=Continue`, original setting is restored; full fixed README banner, single fresh task/switch/cycle proof, exact nonzero `HEALTH_PARTIAL` and `HALTED_NO_NEW_ENTRIES` are required before treating intentional HALTED as a valid preview.
- `ARMED` still requires zero stock exit and PASS/PENDING; unexpected nonzero, stale cycle or bad Task fail closed. Added native Windows mock regression for all cases. Recheck new CI exact head before any new Intel preview.
- Explicit owner consent for button tests and ARM is recorded. Under this project's immutable LIVE-robot boundary, CC-07 work remains only CC-owned development and non-mutating preview; no V20 live command can be dispatched from this development stage. Installing release authority, enabling ARM or STOP Task is a separate production change outside authorized ControlCenter file scope.

## CC-07B Intel physical 12/12 preview + isolated installer — 27.10.2026

- User-run `cc07-check-12-readonly-20261027.ps1` returned exactly twelve `*_pass_no_execution` receipts, all three robots × START/PAUSE/STOP/RESTART; `cc07_intel_preview=pass_12_of_12` and `cc07_no_orders_no_task_changes_no_arm=yes`. This is physical PREVIEW acceptance only, not live action-button acceptance.
- Windows CI #40561610161 `completed/success` for fixed CC07A head `668001c874329c9d458317c93270291b2aa58914`.
- CC07B adds a separate `deployment/cc07-install-operator.ps1` installer. It downloads the exact approved CC-07 operator blob into a NEW protected CC-only folder, creates an independent protected CC-owned audit directory, never touches the V20 trading tree, FINAM tokens or Windows Tasks, and never creates a LIVE release token.
- Installer is two-mode (`check` / `install`) and refuses to overwrite existing files or directories. Exact blob, owner and ACL validation are mandatory. Native Windows parser test guards syntax before physical use.
- Next physical step: install only under elevated, explicitly operator-approved Intel session, verify `cc07_install=pass_cc_owned`; only then connect the non-admin 8502 UI to a tightly scoped IPC endpoint. Do not turn Streamlit into an administrator or perform direct shell commands on UI clicks.
- Owner explicitly authorized subsequent tests of all buttons and ARM; live trade-enabling actions still need independent broker-flat evidence and a matching narrowly-scoped audit release. Running this installer is **not** an ARM event.

## CC-07B Intel physical install PASS — 27.10.2026

- User-provided actual elevated Intel PowerShell completed the pinned CC-only installer with `cc07_install=pass_cc_owned`, controller blob `91a83e388978ded33525357397716d5fd509fc2a`, `cc07_audit=protected`, `cc07_release=not_created`, `cc07_actions=not_executed`, `cc07_no_arm_no_task_no_broker_mutation=yes`.
- Source CI run #40568367681 on exact PR commit `65bc9d2dd4daa5600f5ab57f6923b7fb8b00634f`: `completed/success`. Repo `main` unchanged.
- Installed CC-only executor: `C:\Control Center\cc07-operator\cc07-v20-operator.ps1`; installed CC-only audit directory: `C:\Control Center\data\control-audit`. Installation did not run any V20 command and did not activate/start/pause/stop/restart any worker.
- Next acceptance: invoke installed executor `-mode preview` per robot and verify exact pinned blob and audit ACL, READONLY only. This is distinct from the earlier preview acceptance of a downloaded copy.
- UI 8502 control buttons remain disabled; no production IPC bridge, non-admin Streamlit deployment or live release is installed. No ARM executed. A separate controller IPC step is required before any GUI control.
- Operator permissions for future tests and ARM do not remove the independent current protection: no action can proceed without the required verified state and protected release. Never claim a trade action has occurred without a physical, post-action witness.


## CC-07C: buttons → independent command mailbox (source stage 27.10.2026)

- Physical Intel installed operator acceptance by owner: `cc07_operator=installed_pinned`, `cc07_audit=protected`, three installed `-mode preview` calls `PASS`, Tasks RUNNING with switches HALTED. No orders, Task mutations or ARM.
- The 8502 panel is still the earlier deployed preview. This code is staged in Draft PR #568 ONLY, NOT yet deployed to port 8502.
- New GUI `v20_command_channel.py` (V20-only, intentionally outside readonly `cc/`) accepts only whitelisted V20 robots and START, PAUSE, STOP, RESTART. It requires exact typed `cc07 <action> <robot>`, a fresh admin-ACL-attested worker heartbeat (<=15 s) and writes one bounded, unique request to the CC-owned inbox. Return `QUEUED_NOT_EXECUTED` never claims execution. Receipts are read from admin-owned CC public source only on user manual refresh. No FINAM/order/Task libraries in Streamlit.
- With absent/invalid/stale gateway heartbeat, all twelve buttons remain disabled. This preserves the installed physical panel behavior until separately accepted gateway setup.
- New separately privileged `controller/cc07_command_worker.py`: `--mode check` is inert; `--mode serve` can run only under matching verified elevated operator SID, admin-only policy, admin-owned pinned installed operator, isolated NTFS ACL-protected request/public/private roots and exact panel SID. It uses an fsync-before-dispatch journal and persistent replay latch. Requests older than 30 s, reused IDs, unknown identity or unsafe root fail closed. All real actions still pass through existing frozen V20 stock operator checks, FINAM-flat policy and CC-side durable audit.
- New `deployment/cc07-install-channel.ps1` installs only CC-owned worker and narrow-ACL mailbox/public/private roots. It writes `approved=false`; the worker remains OFF and NO release, no ARM, no Task action occurs. This does not modify V20 or H1/M15.
- Acceptance still needed: Windows native CI on exact PR SHA; installation of new channel (inactive), then run panel 8502 as dedicated non-admin `ccpanel`, release/enable gateway under separate authorized operator process, verify request replay/receipt consistency and real action behavior with FINAM proof. In particular, do not claim that GUI control works while gateway remains INACTIVE.
- Critical Windows-specific boundary: the currently running 8502 panel was restored with elevated identity. Do NOT enable the privileged command gateway while the GUI remains elevated. Switch panel to dedicated non-admin SID first. Privileged worker MUST NOT be the Streamlit process.
- ARM remains an explicit, separately gated trading-state action; this source PR makes no change to V20 robots/strategies/results/configurations/Tasks, FINAM or any currently active robot.

### CC-07C native CI remediation — 27.10.2026

- Native Windows run #40574823506 failed only 3 new-source regressions (730 PASS / 3 FAIL / 15 SKIP): writable V20 intent module unexpectedly under immutable H1 readonly `cc/` test boundary, Streamlit AppTest `session_state.get` unsupported accessor, and H1 write-surface guard correctly rejected new write-capable module. No physical install or ARM in this run.
- Fixed by MOVING only the V20 GUI intent client to top-level `ControlCenter/v20_command_channel.py` outside frozen H1 `cc/` runtime; no loosening of H1 boundary/fault-injection regressions. Updated `v20_app.py` and client tests to import dedicated module. AppTest uses membership check instead of `session_state.get` for absent key.
- Changes remain ControlCenter-only; repo main, installed Intel CC07B executor, V20/H1 runtime/Tasks and FINAM untouched. Reverify exact new Windows CI before installing the CC07C command channel.

### CC-07C Intel channel installation preflight conflict — 28.10.2026

- Owner ran the pinned installer from CI #40636884053 SUCCESS on physical Intel, and received **cc07_channel_target_exists** from the no-overwrite preflight. This failure occurred before network download, mkdir, ACL mutations, policy creation, worker startup or ARM. The prior CC-07B executor remains installed and accepted.
- Root cause in source: old installer required `C:\\Control Center\\data\\private` to be absent even though it is a shared Control Center protected directory and may already exist. The old error did not identify which of four target paths existed; actual physical colliding path is NOT YET proven.
- Revised CC-only installer explicitly refuses overwrites of new `cc07_command_worker.py`, `cc07-inbox`, `cc07-public`, `cc07-gateway-policy.json`; but *if* shared private directory already exists, reuses it only when it is a real directory (not reparse), SYSTEM/Administrators-owned, non-inheriting ACL with no untrusted write grants. Does not reset or overwrite the existing private directory/contents. Distinct preflight error names allow diagnosis.
- Physical READONLY path and ACL witness and new exact-SHA Windows CI acceptance must precede re-running installer. Do not remove existing directories or bypass the ACL preflight. Gateway policy remains approved=false; UI 8502 and V20 robots unchanged.

### CC-07D: isolated non-admin panel staging (28.10.2026)

- Physical Intel CC-07C installation accepted: `cc07_channel_install=pass_cc_only`, `cc07_private=trusted_reused_no_acl_change`, pinned worker blob `8ac883f48f79f8b2b5e7b90abd57e13d5cd9b942`; gateway policy INACTIVE, service NOT STARTED, NO ARM/order/Task mutation. Exact GitHub CI #40640466802 SUCCESS; main remains protected.
- Owner's actual READONLY process inspection: port 8502 is Python PID 11200, executable `C:\\Control Center\\runtime\\python312\\python.exe`, current process owner `URIU-PC\\alkos` and NOT `ccpanel`. The `ccpanel` user is enabled and not in Administrators. Existing new `cc07-inbox` and `cc07-public` have explicit SID ACL; `data\\private` correctly has NO `ccpanel` ACE.
- Physical ACL scan: `runtime/python312/python.exe` and `data/v20-readonly` explicitly grant `ccpanel` READ/EXECUTE; deployed legacy `v20-preview-d80f2446` and its `v20_app.py` have no direct `ccpanel` grant; latest `v20_command_channel.py` not yet installed there. The scan checks explicit ACEs only and is not itself a full effective-access test.
- CC-07D staged **only in Draft PR**: `deployment/cc07-stage-ccpanel-ui.ps1` safely downloads 11 exact pinned Git blobs for the existing V20 Streamlit UI and its direct `cc` dependency closure to newly created `C:\\Control Center\\cc07-panel-13ce0973`. Installer rejects preexisting destination, enforces non-admin `ccpanel`, grants only READ/EXECUTE to `ccpanel`, pins file hashes, and has INSTALL/CHECK only. It never touches running 8502, 8501, robot Tasks, FINAM or live gateway, does NOT start Python or ARM.
- Next after exact native CI: physical stage installation, then *independent non-admin* `ccpanel` identity/access/runtime smoke test on a different loopback port (e.g. 8503) **without stopping PID 11200**. Do not enable gateway while 8502 is still elevated. Keep the current approved=false gateway policy.
- **READONLY warning:** currently `cc/v20_manual_export.py` launches a pinned publisher with the panel's effective SID. Changing UI identity to `ccpanel` does not magically authorize the V20 Task principal; legacy publisher may return `READONLY_EXPORT_UNAVAILABLE`. Before cutover of port 8502, provide a separate CC-owned approved READONLY publisher compatible with owner SID, or prove the exact independent snapshot source works under non-admin UI. Do not weaken Task SID checks or fake HEALTHY.

### CC-07 single-admin 8502 decision — 28.10.2026

- Owner explicitly chose the existing **local administrator panel on 127.0.0.1:8502 under URIU-PC\\alkos** instead of a separate `ccpanel` service account. The inactive CC-07C independent queue is NOT started or authorized; the abandoned CC-07D nonadmin staging installer and tests are removed from the Draft PR. The owner requested disabling `ccpanel`; the supplied guarded PowerShell disables the local user only when no processes, scheduled tasks or services use it. Account status on Intel is still unconfirmed until owner sends actual command output.
- The existing locally installed, pinned `cc07-v20-operator.ps1` (Git blob `91a83e388978ded33525357397716d5fd509fc2a`) remains **unchanged** and is the ONLY V20 execution path. New `v20_admin_control.py` is confined to ControlCenter; GUI calls it only after an exact typed `cc07 <action> <robot>` confirmation. Python must run as an elevated URIU-PC administrator and verify the pinned stock operator file. It refuses operation while the separate gateway policy is active.
- `PAUSE` uses stock HALT, preserving position/stop maintenance; `START`/`RESTART` require a per-request admin-owned CC release, a fresh stock cycle/Task/SID check and FINAM FLAT, and then ARM via stock operator. `STOP` requires FINAM FLAT and only then stops the selected Windows Task after HALT. Stock CC-07 owns mutex, replay audit, exact second confirmation and post-check. Any ambiguous result is `FAILED_UNKNOWN`, never auto-retried.
- Localhost-only admin Streamlit is an explicit user-accepted reduction of privilege isolation. It is NOT equivalent to dedicated `ccpanel` sandboxing. No modifications to V20_TradingSystem_M15, TradingSystemLab, IntradayLab, FINAM tokens, robot strategies, broker accounts or running Tasks are authorized by staging code.
- NEXT: exact new native CI SUCCESS, controlled 8502 code deployment with backup and rollback, verify existing manual READONLY refresh and display before any button action; first physical `PAUSE` against an already HALTED robot should be audited no-op; separately observe FINAM FLAT and per-action proof before any ARM/START/RESTART. This source stage does not activate trading by itself.

### CC-07 daily operator UX — 28.10.2026

- Intel owner physically confirmed the installed pinned administrative UI under `URIU-PC\\alkos` on `127.0.0.1:8502`: `cc07_admin_ui=installed_pinned`, backup `C:\\Control Center\\cc07-admin-8502-1c885f88`, no robot action. After manually entering `cc07 pause v20-shallow`, the correct **Shallow PAUSE** button became available. This confirms the administrative readiness path and button gate, **not execution** of PAUSE or ARM.
- Explicit owner decision: no recurring typed `cc07 <action> <robot>` phrase in daily operation. New UI is 3 robots × four always-visible buttons when the installed administrative operator is ready. `PAUSE` dispatches on its single click. `START`, `STOP`, `RESTART` require **one click + a clearly labeled Confirm/Cancel** interaction; the first click alone never executes a trade-affecting operation. Refresh cancels pending confirmation; UI rerun does not resend a command. Every request still goes through exact stock CC-07B operator confirmation, actor SID/Task/cycle, per-request release for non-PAUSE, FINAM flat proof for ARM/STOP and durable journal.
- This is a UI-only simplification in ControlCenter and does not change V20 strategy/configuration/FINAM, robot Task definitions, broker tokens, risk semantics or H1/M15 projects. The preexisting administrative Streamlit localhost risk remains explicitly accepted by owner.
- Before physical update: require exact Windows CI SUCCESS; install only the updated Git-pinned `v20_app.py` in the existing `C:\\Control Center\\v20-preview-d80f2446` with backup and rollback, preserve the already pinned `v20_admin_control.py`. Do not restart the process just to force reload unless UI fails to reload. Validate manual READONLY refresh first; first operator action should be a single-click PAUSE on known HALTED robot, then the current FINAM/Task witnesses before any ARM.

### CC-07 first START transient and operator postflight — 28.10.2026

- Owner physically installed one-click UI under existing localhost administrative port 8502, physically tested PAUSE on already HALTED Shallow: panel said `ALREADY_HALTED`; three separate stock readonly probes returned `cc07_preview_exit=0`, Task Running/HALTED/fresh cycles and all three FINAM account-bound FLAT (0 positions, 0 orders).
- On first confirmed Shallow START via UI, panel returned `FAILED_UNKNOWN`, while immediate subsequent **stock READONLY** reported `switch=ARMED`, `cycle=HALTED`, `cycle_code=HALTED_NO_NEW_ENTRIES`, `age_seconds=16`, and `HEALTH_PARTIAL`. User then invoked PAUSE, but has **not yet supplied a post-PAUSE stock switch/FINAM witness**. NO second ARM authorized; OBV/Inside remain untested for START. Do not infer current HALTED solely from the user's description of clicking PAUSE.
- Source diagnosis: original CC-07 operator called strict `proof` immediately after stock START; the switch can flip to ARMED before the next worker cycle. Strict ARMED requires PASS/PENDING with exit 0, so it could produce `unknown_outcome_reconcile_manually` and `FAILED_UNKNOWN` even if ARM already happened. The old same strict preflight can also refuse PAUSE during this brief ARMED/HALTED transition. This is a ControlCenter-only orchestration defect, not permission to change V20 frozen files.
- Draft CC-07 fix: **one** stock action, then at most 12 independent `proof` read-only observations with 5-second bounded waits. Never automatically reissue ARM, task mutation, trade or cancel. Permit exact `ARMED + recent HALTED_NO_NEW_ENTRIES + HEALTH_PARTIAL` only on PAUSE preflight, not successful START. STOP remains FINAM FLAT-gated. Any stale/fault/unexpected switch or timeout fails closed and requires reconciliation.
- Dashboard `UNKNOWN` plus green heartbeat is expected under the independent CC-02 publisher: for ARMED without independently proven broker reconciliation the publisher intentionally publishes `engine_state=UNKNOWN` while a verified recent heartbeat may be HEALTHY. Do not call UNKNOWN a broker fault or equivalent to healthy trading.
- NEXT: obtain fresh physical `switch=HALTED` + FINAM position/order report and CC-07 audit; then new exact native CI SUCCESS and guarded upgrade of the two CC-only installed files with backups. No direct V20 or TradingSystemLab/IntradayLab changes.
