# Control Center — переход на V20, CC-00–CC-08

Основа: actual GitHub main `6f352acfac7ebdfabba73e143c4dfea3a6e48507`; V20 roadmap `V20-01–V20-08`, V20-04 OFFLINE.
Целевой проект **один**: `V20_TradingSystem_M15`. Три робота/FINAM-счёта: `V20_SHALLOW`, `V20_OBV`, `V20_INSIDE`.

## Короткое решение
- Старые TradingSystemLab H1 и IntradayLab M15 **не менять и не останавливать**. Старый Streamlit `app.py` и текущую Intel-панель не трогать.
- Новый **изолированный** entrypoint `v20_app.py` в том же ControlCenter. **Без боковой панели**: три верхние вкладки **Главная / Журнал / Управление**, справа сверху одна кнопка «Обновить данные». Вкладки переключаются на клиенте без запроса данных, все три представления используют один и тот же session-local снимок. Нет свечей, графиков, сделок, PF/PnL (их показывает FINAM).
- Одна ручная кнопка refresh. Рядом с ней дата/время **последней ручной проверки панели** в МСК (`—` до первого нажатия); это не метка свежести данных торговых роботов, а также не гарантия удачного ответа источника. Ни автоматического опроса, ни запросов FINAM или торговых команд из панели. На CC-04 вручную допускается только закреплённый READONLY `operator-check` существующего V20-07 (без изменения Task).
- **Главная показывает только работоспособность:** единый статус HEALTHY/HALTED/FAULT/UNKNOWN/STALE/НЕ ПОДКЛЮЧЁН, Windows Task, kill switch, **Heartbeat HEALTHY/UNHEALTHY/НЕТ ДАННЫХ** (экранная проекция технических `HEALTHY/STALE/UNKNOWN`, проверка свежести независима от общего HEALTHY; отсутствие источника никогда не отображается как UNHEALTHY), и последнюю ошибку, причём текущие поля скрываются при STALE/UNKNOWN/нет источника. Цикл, локальные позиции и стопы убраны с главной; торговые позиции/стопы и статистика остаются в FINAM, реальные циклы — в «Журнале». Отсутствие источника не превращается в «ошибок нет» или «robot healthy».
- Все не подключённые V20 состояния **НЕ ПОДКЛЮЧЁН** (не HEALTHY и не нули); Stale/Failed коротко видны. Все команда START/STOP/PAUSE/RESTART пока только текст и **не исполняются**.

## Вехи CC
| CC | Цель | Статус |
|---|---|---|
| CC-00 | Три идентичности V20 + изоляция от H1/M15 | Draft реализация |
| CC-01 | Компактный экран + Журнал + Управление (без торговых кнопок) | Draft реализация |
| CC-02 | Строгий независимый контракт и ручной приём из CC-owned NTFS файлов | Draft реализация; физическая policy НЕ ОДОБРЕНА |
| CC-03 | Установка V20-экрана на Intel без замены работающего приложения | PASS: изолированная preview-панель 8502 (24.10.2026); исходная 8501 не заменена |
| CC-04 | READONLY-наблюдение V20-07 staging; позднее runtime при наличии доказательств | PASS: код/Windows CI + физический ручной refresh трёх карточек Intel 8502 (24.10.2026); LIVE не подключён |
| CC-05 | Три FINAM READONLY источника (без токенов в Streamlit) | V20-06 PASS READONLY 3/3; подключение обезличенного CC-источника ещё не принято |
| CC-06 | Независимый изолированный controller | Не начат |
| CC-07 | Авторизованные операторские команды на Intel | После V20-07 и отдельного разрешения |
| CC-08 | Отчёт о приёмке, свежесть, инциденты и обслуживание | Не начат |

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

В CC-05 только ControlCenter должен показывать по каждому роботу отдельное **подтверждённое время/статус последней READONLY-проверки**. Не повторять FINAM API, не получать токены в Streamlit, не считать старые квитанции свежими, не читать документы/секреты V20 торгового корня напрямую из UI. Разделить внешний операторский обезличенный экспорт и проверяемый CC-owned вход; policy/ACL и физическая приёмка остаются самостоятельными явными условиями. Без LIVE, заявок, раздачи прав Task, изменения V20/H1/M15.
