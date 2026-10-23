# Control Center — переход на V20, CC-00–CC-08

Основа: actual GitHub main `6f352acfac7ebdfabba73e143c4dfea3a6e48507`; V20 roadmap `V20-01–V20-08`, V20-04 OFFLINE.
Целевой проект **один**: `V20_TradingSystem_M15`. Три робота/FINAM-счёта: `V20_SHALLOW`, `V20_OBV`, `V20_INSIDE`.

## Короткое решение
- Старые TradingSystemLab H1 и IntradayLab M15 **не менять и не останавливать**. Старый Streamlit `app.py` и текущую Intel-панель не трогать.
- Новый **изолированный** entrypoint `v20_app.py` в том же ControlCenter. Только три страницы: **Главная / Журнал / Управление**. Нет свечей, графиков, сделок, PF/PnL (их показывает FINAM).
- Одна ручная кнопка refresh. Ни автоматического опроса, ни запросов FINAM, ни shell/Task/счетов из панели.
- **Главная показывает только работоспособность:** единый статус HEALTHY/HALTED/FAULT/UNKNOWN/STALE/НЕ ПОДКЛЮЧЁН, Windows Task, kill switch, heartbeat и последнюю ошибку, причём текущие поля скрываются при STALE/UNKNOWN/нет источника. Цикл, локальные позиции и стопы убраны с главной; торговые позиции/стопы и статистика остаются в FINAM, реальные циклы — в «Журнале». Отсутствие источника не превращается в «ошибок нет» или «robot healthy».
- Все не подключённые V20 состояния **НЕ ПОДКЛЮЧЁН** (не HEALTHY и не нули); Stale/Failed коротко видны. Все команда START/STOP/PAUSE/RESTART пока только текст и **не исполняются**.

## Вехи CC
| CC | Цель | Статус |
|---|---|---|
| CC-00 | Три идентичности V20 + изоляция от H1/M15 | Draft реализация |
| CC-01 | Компактный экран + Журнал + Управление (без торговых кнопок) | Draft реализация |
| CC-02 | Строгий независимый контракт и ручной приём из CC-owned NTFS файлов | Draft реализация; физическая policy НЕ ОДОБРЕНА |
| CC-03 | Установка V20-экранa на Intel без замены работающего приложения | NOT EXECUTED |
| CC-04 | Runtime источники всех трёх роботов | После V20-07 |
| CC-05 | Три FINAM READONLY источника (без токенов в Streamlit) | После V20-06 |
| CC-06 | Независимый изолированный controller | Не начат |
| CC-07 | Авторизованные операторские команды на Intel | После V20-07 и отдельного разрешения |
| CC-08 | Отчёт о приёмке, свежесть, инциденты и обслуживание | Не начат |

## CC-02: минимальный контракт источника
Один JSON на робота, фиксированные **CC-owned** имена `v20-shallow.json`, `v20-obv.json`, `v20-inside.json` в отдельном `C:\Control Center\data\v20-readonly`. Контракт `cc.v20.readonly.v1`: `schema_id`, `robot_id`, `account_alias`, `observed_at`, `heartbeat_at`, `engine_state`, `task_state`, `kill_switch`, `cycle`, `positions_local`, `stops_local`, `unresolved_local`, `last_error_code`, `events` (до 10), `payload_sha256` (канонический SHA256 без поля хеша). Допустимые статусы `HEALTHY/HALTED/FAULT/UNKNOWN`, bounded identifiers и error codes. **Никаких** токенов, истинных номеров счетов, строк broker orders, произвольных путей, команд или стратегических параметров.

Единый администраторский `deployment/v20-readonly-policy.json` намеренно **не поставляется и не включается**. На V20-07 требуется отдельно утвердить root file-ID `[volume, file_index_high, file_index_low]`, изолированные `account_aliases`, ownership и NTFS ACL: право WRITE только Administrators/SYSTEM, `ccpanel` READ ONLY. `deployment/v20-readonly-policy.example.json` с `approved=false`/root_id=null **не активирует** источник. Нативный `read_windows` повторно проверяет NTFS/reparse/ACL, pin root и bounded access. Файлы публикации V20 внутри торговых корней **не читаются**; будущий отдельный publisher должна предоставить разработка/развёртывание V20, без модификации frozen роботов. Пока policy не активирована, один click возвращает три NOT_CONNECTED.

TTL фиксирован 300 с; просрочка блокирует актуальные метрики, а historical события остаются отмеченными STALE. Timestamp принятия UI не подменяет observed_at. Кросс-процессный one-shot gate — прежний `cc.manual_gate.export_gate`.

### Важная граница
Этот PR является **OFFLINE-only code**. Никаких установок Intel/переноса приложения в `app.py`, изменений Task, LIVE, FINAM, V20, H1/M15, токенов или брокерских действий. Нет merge без решения владельца. Источник-продуцент не реализован и не считается готовым.
