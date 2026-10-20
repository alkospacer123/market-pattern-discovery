# CC-03 / #550: независимый источник H1 — NO_SAFE_SOURCE

Проверено 20.10.2026 по фактическому GitHub `main`
`c3695b1304aef1acdd889264b3451184f7332bf7` и
[последнему заданию #550](https://github.com/alkospacer123/market-pattern-discovery/issues/550#issuecomment-6286945101).
Вердикт для дополнительных полей: **NOT_AUTHORIZED / NO_SAFE_SOURCE**.
Это результат проверки доступных исходников и контрактов, не утверждение об
отсутствии любых частных источников на Intel. Intel в этой работе не опрашивался.

Принятый Task-only путь #558 сохраняется: физический PASS оператора относится к
`WINDOWS_OS_ONLY / TASK_RUNNING / CURRENT`, не к HEALTHY или брокерским данным.
Повторная установка, новый exporter и изменение runtime для этого результата
не нужны. Изменения поставки — документация, независимый механический аудит и
тесты; app/cc/observer/exporter и deployment entrypoints побайтово прежние.

## Что проверено

Исходники читались как текст; production-модули не импортировались и не запускались.
Точные Git blob и SHA-256 закреплены в
[evidence](CC03_H1_SOURCE_EVIDENCE.json).

| Кандидат | Фактический контракт | Почему не является разрешённым источником CC |
| --- | --- | --- |
| `stage8-537-post-arm-readonly.py/.ps1` | `local_state()` читает live heartbeat и kill switch; `ledger()` открывает production SQLite `mode=ro`, включая WAL; `verify()` выполняет session/account/orders/schedule/bars запросы. Wrapper расшифровывает отдельный REAL_READONLY DPAPI credential | READONLY означает отсутствие торговых команд, но не отсутствие конфликтующих file handles. Всё это исключено последним ТЗ. Historical PASS 16.10 не является текущим разрешённым CC feed. Stdout не имеет полного immutable CC publication/provenance контракта |
| `stage8_493_post_isolation_broker_readonly.py`, broker-flat wrappers | Операторский stopped/HALTED gate, live JSON и FINAM account/orders | Неприменим к принятому running H1; нельзя убрать gate, использовать старый commit или вызвать из панели |
| `stage8_493_n4_financial_readonly.py` | Создаёт отдельный private JSON с `open('x')`, исходными observation start/end, account hash, release/spec, перечнем запросов; до этого local gate и FINAM | Ближайший существующий create-only отчёт, но HALTED/flat-only, старый release, нет принятого CC root/ACL/source binding/TTL; актуальный файл не supplied. Fees/cashflows/realized basis прямо NOT_VERIFIED. Не запускать заново |
| `stage8_493_finam_readonly_observation.py` | Нормализует переданные account/orders/trades; `READONLY_REST_RESPONSE_NORMALIZATION_ONLY`, freshness не доказана | Чистая обработка не создаёт authenticated source. Входа, разрешённого внешнего producer и provenance нет; raw IDs требуют очистки до CC. Production imports в CC не добавляются |
| `stage8_493_capital_pnl_readonly.py` | Чистый classifier уже независимо собранного private snapshot | Не собирает данные, не доказывает broker statement facts; не источник heartbeat/signals/positions |
| `finam_fill_price_readonly.py` / `run-finam-fill-price-readonly.ps1` | Историческая immutable ACK-ledger copy (`mode=ro&immutable=1`, без WAL), bounded FINAM account/trades, create-only report с `observed_at` | Ближайший historical fill contract без live DB; новый запуск требует DPAPI/FINAM и запрещён этим заданием. Уже созданный trusted report можно отдельно предоставить на offline review; current positions/health/signals/stop coverage из historical fill не следуют |
| `independent_uploaded_finam_evidence_audit_20261013.json` | Tracked исторический аудит хешей/структуры supplied reports; observation 12.10, `real_broker_calls=NONE_BY_THIS_AUDIT`, `production_ready=NO` | Это настоящее историческое свидетельство проверки, но не сами authenticated current account/orders/events и не свежий источник H1. Его можно читать как документ, не переносить цену/нулевые значения в live view |
| `run-stage8-493-sltp-local-readonly-precheck.ps1` | NO_FINAM/NO_SQLITE, но Get-Content live heartbeat/kill switch и Task checks | Запрещённые producer paths; explicit LOCAL_ONLY/NOT_BROKER_ACCEPTANCE. Readonly в названии не устраняет Windows conflict |
| `readonly_supervisor.py` / `deploy/windows/run-readonly.ps1` | Continuous REAL_READONLY observer, FINAM, собственная SQLite operational state и heartbeat | Не immutable one-shot feed; запуск запрещён, собственная health не равна production H1 health; отдельная readonly Task исторически Disabled |
| `production_safety_gate.py`, `trading_safety_gate.py` | Live JSON publication через replacement | Нативные Windows regressions подтверждают WinError 5 даже для metadata. `read_source()` и default `collect()` остаются заблокированы до I/O |
| `production_runtime.py`, `production_service.py`, `state.py` | Сигналы/pending/last-evaluated, positions/intents/fills и H1 history в runtime/SQLite | Нет отдельного принятого полного immutable export. Нет безопасного NO SIGNAL/rejection stream; пересчитывать стратегию или читать production DB нельзя |
| `tsl-h1-01-check.ps1` | Tracked файла нет, sanitized исходник не supplied | Невозможно проверить imports, opens, API, timestamp/completeness и права. Существование Intel private script не предполагается |
| `ControlCenter/exporter/snapshot.py` / `h1_export.py` | Закрытые уникальные completed JSON в CC root; pinned native receiver, digest/schema/source/account/TTL checks | Это транспорт, не независимый источник. `collect(..., reader=None)` → `CC03_LIVE_SOURCE_COMPATIBILITY_BLOCKED`; `Start-Exporter.ps1 -Execute` → `CC03_SINGLE_CCPANEL_EXPORTER_DISABLED`. Injected reader используется только тестовыми fixtures |

## Поле → authority и точный блокер

| Поле | Допустимая authority / существующий источник | Фактическая доступность и минимальный недостающий input |
| --- | --- | --- |
| Task / optional pinned process | Windows Scheduler/CIM, canonical XML/principal + approved process epoch/owner pins | Принятый WINDOWS_OS_ONLY; это OS observation. Process только при отдельном полном binding; Task alone не доказывает процесс |
| Health / completed cycle / last FINAM contact | Engine-observed production heartbeat | UNKNOWN: legacy source исключён; нужен уже разрешённый внешний immutable engine observation с оригинальными cycle/contact timestamps и release/account binding |
| Signals / rejection reasons / NO SIGNAL | Реально опубликованные decision events, N4 bar close + event sequence + completeness | UNKNOWN: безопасный независимый event source отсутствует. Отсутствие строки не NO SIGNAL; broker snapshot не доказывает решение робота |
| Positions / fills / orders | Authenticated account snapshot/trade history; local ledger authority отдельно | UNKNOWN: supplied immutable complete broker evidence отсутствует. Task/пустой список/старый flat report не нулевая позиция и не fill. Нужна также доказанная принадлежность H1, а не только общий account |
| Stops / protection | Broker active order status + side/quantity/position ownership linkage | UNKNOWN: нет свежего complete evidence. Intent, heartbeat counter и ACK не доказывают ACTIVE SLTP и исполнение |
| Reconciliation / unresolved | Согласованный local+broker observation, оба watermark и completeness | UNKNOWN: #537 требует исключённые live JSON/SQLite/FINAM. Одного брокерского account snapshot недостаточно |
| Equity / PnL / fees / cashflows / margin | Authenticated finance history и отдельные период/валюта/coverage/evidence | UNKNOWN: #493 classifier не source; create-only private report не supplied/не принят. Ни исторические числа, ни balance differences не переносятся как текущий PnL |
| H1 bars / risk | Engine/data history и календарь / реальные risk decisions | UNKNOWN: отсутствует безопасный source, current calendar/TTL/completeness contract; пересчёта нет |

## Кратчайший безопасный следующий шаг

1. Передать на **offline review** sanitized исходник уже существующего внешнего
   producer (например, `tsl-h1-01-check.ps1`, если он действительно существует)
   и один его уже созданный закрытый immutable результат с provenance. Не запускать
   #537/#493 заново, не копировать live heartbeat/SQLite, не читать Intel из CC.
   Нужны полный call graph, точные paths/API и Windows principal/authority;
   никакие credential/token/raw account/order IDs в материал CC не входят.
2. Подтвердить, что producer уже независимо разрешён и не открывает исключённые
   production paths. Для брокерского результата нужны trusted provenance вне
   самодекларации JSON и independently verified account mapping. Для health/signals
   нужен engine evidence: broker evidence его не заменяет. Если такого producer
   нет, текущий scope заканчивается этим блокером; новая source activation требует
   отдельного решения оператора и technical acceptance, не снятия reader guard.
3. Для supplied evidence сначала сделать только offline parser/fixture. Разделить
   producer release и установленный robot commit, source_id/robot/spec/account binding,
   source event/observation/generated/receipt timestamps, completeness и explicit TTL.
   Исторический результат остаётся историческим; импорт не освежает source clock.
   SHA-256 не подтверждает producer identity. Текущий partial live schema не несёт
   positions/stops/finance; его нельзя расширять или переименовывать fixture authority
   до точного input contract и review. Нужна узкая schema/ingestion доработка CC.
4. После review — отдельно авторизовать one-shot публикацию **только** в CC-owned
   pinned NTFS export root: close/fsync → уникальный completed name, admin-owned
   receiver policy, независимые writer/reader ACL, bounded size/capacity. Существующие
   primitive publication/receiver и manual gate использовать повторно. Панель не
   запускает producer/FINAM/PowerShell произвольной команды и не получает его token.

Это кратчайший путь к реальным полезным positions/signals: сначала существующее
внешнее доказательство, затем минимальный parser. Создание нового dashboard или
правдоподобного fixture вместо недостающего evidence не устраняет блокер.

## Проверки и ограничения результата

Новые тесты отделяют OFFLINE_FIXTURE от реального receiving schema, проверяют
подмену producer/spec/release/account/time и отсутствие побочных вызовов при
заблокированном collection. Native ETW тест выполняет один gated read уже
закрытого CC-only snapshot параллельно 500+ legacy producer replacements,
учитывает parent/worker PIDs, включая venv interpreter descendants по kernel
ProcessStart, требует canary opens до/после и zero lost ETW events,
ноль legacy opens и producer errors. Это проверяет **отсутствие доступа**, не
совместимость чтения legacy. Положительные HALTED/HEALTHY inputs в тестах synthetic,
не реальная H1 authority. Существующий полный Windows security/policy/gate/standard
SID/Streamlit click regression выполняется прежним hosted workflow.

[Независимый механический аудит](../ci/source_feasibility_audit.py) отдельным
процессом сравнивает Git runtime trees и deployment entrypoints с actual main,
запускает прежний outside-ControlCenter tree audit и проверяет manifest. Это
автоматический независимый контроль; авторский source review не выдаётся за
новый внешний reviewer approval. Точные head/run/artifact hashes и результаты
публикуются в Draft PR после фактического CI, вне manifest self-reference.

Нет новых runtime schema/fixtures/ingestion: безопасный реальный вход не выявлен,
а существующий offline fixture и transport уже позволяют проверить границу.
Десять trading controls остаются disabled, M15 — NOT_DEPLOYED. Scope только CC-03.
Phone/VPN access не входит в эту поставку.

Первый native run [39396318488](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/39396318488)
сохранён как FAIL: новый ETW тест не подтвердил CC reader PID (`CC_READER_NOT_OBSERVED`),
хотя сам gated probe, 500+ replacements и canary bracket прошли. Full suite:
515 PASS / 1 FAIL / 15 POSIX SKIP; security/standard-SID и настоящий Streamlit click
PASS. В тест добавлен kernel ProcessStart graph для real interpreter descendants
Windows venv redirector, отдельно от producer tree; assertion чтения CC snapshot
и запрет H1 opens сохранены. Production reader не менялся. Точный итоговый native
run и evidence публикуются в Draft PR после проверки, не выводятся из этого FAIL.

## Операторский checkpoint: NO INSTALL / NO SOURCE ACTIVATION

Практический порядок после отдельного source/package review приведён в
[отдельной инструкции](CC03_H1_SOURCE_OPERATOR_CHECKPOINT.md).
Текущий Draft PR не требуется устанавливать ради Task-only наблюдения.
Merge, Intel install/restart, Task/ACL/account/FINAM/SQLite и robot изменения
не выполняются. NO_SAFE_SOURCE не исчезает от успешного hosted CI.
