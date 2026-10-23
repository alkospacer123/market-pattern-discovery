# V20-06.1 — привязка трёх FINAM-счетов, только READONLY

Статус: **PREPARED / REAL FINAM NOT RUN**. Следующий подэтап после подтверждённой V20-05.5 (Intel Windows 10 Pro, FakeBroker 64/64 PASS).

- Повторно используется **неизменённый H1** `TradingSystemLab/stage8_robot/finam_fill_price_readonly.py` из отдельного закреплённого каталога `C:\V20Lab\source-raw`. Его `ReadonlyFillAPI` разрешает только POST создания/проверки сессии и чтение одного строго указанного счёта/истории; POST заявок, SLTP и DELETE запрещены на уровне запросов.
- `verify_bindings.py --self-test` проверяет локально запрет POST/DELETE, запрет чужого счёта, отказ в доступе при `readonly=false`. Сеть FINAM не используется.
- `verify_bindings.py --connect` **интерактивно на Intel**, а не в переписке, получает отдельно для Shallow/OBV/Inside `account_id` и READONLY-токен. Проверяет `session_details.readonly=true` и точную принадлежность `account_id`; три ID и три токена должны различаться. Никаких заявок или отмен. Токены не сохраняются и не выводятся.
- Только после **3/3** успешных привязок создаёт локальный `C:\V20Lab\readonly-06\ACCOUNT_BINDING_REPORT.json`: хеши ID, статусы и формы запросов, **без** токенов, самих account_id или финансовых данных. Никаких записей в каталог H1/M15. Этот отчёт относится только к **06.1**, не к FINAM-спецификациям/сверке 06.2–06.4.
- Если V20-счета или отдельные READONLY-токены не открыты — **BLOCKED**, не PASS. Не использовать токен H1. Если привязка не совпала — **FAIL/CLOSED**, без подбора альтернативного счёта.
- В GitHub публиковать только обезличенные статусы. **Никакого LIVE**, Windows Tasks и модификации frozen V20.

Исходный V20-05.5 локальный отчёт `C:\V20Lab\acceptance-raw\WINDOWS_ACCEPTANCE_REPORT.json` не загружен в GitHub.
