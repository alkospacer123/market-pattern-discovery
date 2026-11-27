# V20 Control Center — data/telemetry, security, test gates

## 27.11.2026 — C3.2: текущий CI и дополнительные диагностические регрессии

[#602](https://github.com/alkospacer123/market-pattern-discovery/pull/602) принят в MAIN, #603 разделил исторический frozen CC-03 и active V20 SOURCE CI, [#609](https://github.com/alkospacer123/market-pattern-discovery/pull/609) допускает точный C3 документационный scope. Старый отказ #592 ниже — исторический, не текущий CI. На исходном HEAD #608 `86a5731f64e039c52c8c296a9dffedab44e161d1` CC docs/Main Admission SUCCESS, Windows native на docs-only не выполнялся. Это не installed/FINAM/LIVE acceptance.

При целевой диагностике сохраняй symptom/robot/session/observed_at/attempt time и исходное evidence; трассируй конкретное поле UI → session/cache/render → receiver/validation → publisher/exporter → фактический source. Не повторяй refresh/rerun, пока не установлены side effects. Дополнительные синтетические regression classes из профильного Skill:

- failed publisher → acquire того же старого snapshot: не считать новой публикацией; отдельно проверить attempt time vs observed_at, TTL после acquire, отсутствие воскрешения прежних положительных полей.
- clock rollback / будущие и naive timestamps: STALE не возвращается в свежий PASS без нового валидного source; проверить отдельно heartbeat и ARMED-cycle в LOCAL_REPORT/UNKNOWN, не только общий health.
- Streamlit startup, navigation, dialog, rerun, session/robot isolation: отсутствие неразрешённых source I/O/dispatch, повторного submit, сохранения cached positives после UNKNOWN; для зависимостей различать DECLARED / RESOLVED / IMPORTED / RUNTIME_LOADED, lockfile не подтверждает installed env.

Это требования к будущим целевым проверкам, **NOT_RUN**, не новые доказанные LIVE-инциденты. Для действий — COC, CC-07 и CC-08. Не повторять экзамен или запускать реальную команду ради regression.
**CURRENT CODE SOURCE, 22.11.2026:** `main=0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52`. Это не доказательство физического Intel/LIVE. [START HERE](V20_START_HERE_SOURCE_MAP.md), [CC-07](V20_CC07_COMMAND_CONTRACT.md).

## Источник каждого наблюдения

| Поле UI/контракта | Provenance | Чего НЕ доказывает |
|---|---|---|
| «Последняя проверка» | `v20_app.py`: время явного refresh, включая ошибку | Свежесть источника / FINAM |
| Task, kill switch, cycle/code | Pinned V20 `-mode check`, экспорт в CC-owned JSON | Фактические позиции, заявки, SLTP |
| Heartbeat | Дата последнего завершённого локального события `live-m15.jsonl`, а не timestamp UI | Broker HEALTHY, real protective stop |
| События Журнала | До 10 локальных worker attempts, newest first | Полнота брокерских fills и executions |
| `positions_local`, `stops_local`, `unresolved_local` | В текущем `deployment/v20_live_export.py` все **None** | FLAT, нуль позиций/риска, действующий SL |
| FINAM | Только независимая утверждённая broker READONLY-проверка | Нельзя выводить из HTTP 200, Task Running или старых квитанций |

`cc.v20.readonly.v1` из `cc/v20_contract.py` содержит `schema_id,robot_id,account_alias,observed_at,heartbeat_at,engine_state,task_state,kill_switch,cycle,positions_local,stops_local,unresolved_local,last_error_code,events,payload_sha256`. Строго проверяются имена трёх роботов, account aliases, SHA-256 digest, typed values, max 32 KiB и до 10 событий. `cc/v20_receiver.py` требует утверждённую NTFS policy, root file-ID, проверку owner/ACL/identity; policy.example **не активирует** источник.

TTL наблюдения — **300 секунд**. Просроченный/будущий/невалидный source → `STALE` / `UNKNOWN` / `NOT_CONNECTED` и сокрытие недостоверных текущих метрик; clock rollback не оживляет старый PASS. `HEALTHY` локального контракта требует свежести, Running, ARMED, локальный `unresolved_local=0`, а также заполненные `positions_local` и `stops_local` без противоречия «FLAT при ненулевых стопах». Свежая комбинация `positions_local>0`, `stops_local=0` даёт `FAULT / LOCAL_POSITION_WITHOUT_STOPS` независимо от заявленного `engine_state`; неполные exposure-поля при претензии на HEALTHY дают `UNKNOWN / LOCAL_EXPOSURE_DATA_MISSING`. `status_reason` — производное поле результата `parse()`, оно **не добавляется** в подписанную wire-схему. Текущий exporter не имеет независимых данных о positions/stops/unresolved (None), поэтому успешная публикация сама по себе не гарантирует HEALTHY. Даже согласованные counts не доказывают полноту quantity coverage или брокерские SLTP. `HALTED`, `STALE`, `FAULT` и отсутствие данных — разные состояния. Подробности: [инцидент HEALTHY/exposure](V20_HEALTH_EXPOSURE_FIX_20261126.md).

## Security и доверие
- STREAMLIT: исторический локальный адрес `127.0.0.1:8502`, реальный listener/bind/venv/ACL требуется проверить на Intel. Localhost сам по себе не авторизует управление.
- READONLY refresh и CC-07 execute — разные capabilities. Установленный админ-адаптер проверяет host, admin, pinned PS и отключённость альтернативного gateway; PS защищён точным blob, SID, ACL, release, stock check и broker-flat gate. Никаких обходов HALTED или изменения V20 ради панели.
- Не читать FINAM token/DPAPI, приватные SQLite/WAL, реальные account IDs; не публиковать сырые broker logs в GitHub/архив/Kimi. SHA доказывает байтовое совпадение SOURCE, а не результат торговли.
- Непрошедшая policy/ACL/PIN/schema/timeout → отказ/UNKNOWN, не запрашивать дополнительные привилегии автоматически. Физическое исправление/установка панели — только отдельный допуск с backup, hash parity, rollback и READONLY acceptance.
- `docs/SECURITY_BOUNDARY.md` описывает **исторический CC-03/H1 8501**, а не действующий CC-07/8502. Старые операторские панели и тесты сохранять как source evidence.

## Тестовый контракт и точная CI provenance

Изолированные synthetic tests: `tests/test_cc07_admin_control.py`, `test_cc07_command_channel.py`, `test_cc07_operator_stage.py`, `test_v20_controller.py`, `test_v20_live_export.py`, `test_v20_control_center.py`. Тесты запускать **только** в disposable environment с fixture/mock, без живых Windows Tasks, FINAM и Intel 8502. При отсутствии среды: `NOT RUN`.

- [PR #568](https://github.com/alkospacer123/market-pattern-discovery/pull/568) **MERGED** 20.11, merge commit `66093575312010ea2ecd92b5cddef063f1340488`. Финальный PR head `0fa36b4529efeaaf5526dd8521d54159cbbcaf6a`, его [Windows CI run #44716628573](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44716628573) `completed/success`. Ранний run [#44711373064](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44711373064) — `757 PASS / 15 SKIP` для **другого** exact head `b9da21b3b5e530460ed54100add999fa5afcf131`. Не переносить число тестов на другой SHA.
- `.github/workflows/controlcenter-cc03-windows-native.yml` — замороженная CC-03 Windows suite. Исходный `ci/scope_audit.py` выдаёт исторически ожидаемый **exit 1** для изменившегося общего корня. Workflow проверяет frozen source и явно распознаёт это исключение, **не исправляет его**; остальные native/JUnit gates отдельно. «Зелёный CI» здесь не `CC03_FULL_SCOPE_PASS` и не Intel/LIVE acceptance.
- По MAIN `0e569be…` GitHub Main Admission SUCCESS, специализированные проверки CC-03 были SKIPPED. Это не новый результат pytest CC07.
- В документационной ревизии 22.11 физические pytest/Windows PowerShell/real Streamlit click были **NOT RUN**; это историческая запись, не результат текущей ветки.
- 26.11.2026 для исправления HEALTHY/exposure в изолированном Linux disposable environment выполнен полный `pytest -q -p no:cacheprovider tests`: **729 passed, 57 skipped, 0 failed**. Целевые BASE-проверки до исправления: **14 failed**; после исправления: **14 passed**. Streamlit-проверки используют `AppTest`, а не физический браузер/Intel. Все 57 пропусков — Windows PowerShell/native/NTFS/transport; они остаются **NOT_VERIFIED**, а не PASS. Exact head SHA и provenance фиксируются в Draft PR; см. [отчёт исправления](V20_HEALTH_EXPOSURE_FIX_20261126.md).

## Known issues / UNKNOWN / NOT_VERIFIED

| Вопрос | Статус на 22.11 | Следующая безопасная проверка |
|---|---|---|
| Побайтовый installed UI/adapter/operator на Intel сейчас | **NOT_VERIFIED**; есть датированное свидетельство 20.11 | Отдельная READONLY SHA-сверка с разрешением доступа |
| Текущие ARMED/FLAT, реальные заявки/SLTP FINAM | **UNKNOWN** | Независимые свежие Task/switch/FINAM READONLY, не UI heartbeat |
| STOP/RESTART на каждом из трёх роботов | **NOT_VERIFIED** полностью | Только естественный разрешённый операторский сценарий; не останавливать ради теста |
| Успешный RECOVER при реальном HALT | **NOT_VERIFIED**; защитный отказ проверялся | Не инициировать искусственный HALT; ждать отдельного безопасного события и допуска |
| Полная установка/активность альтернативного gateway | **NOT_VERIFIED** | Сверить installed channel-policy и imports READONLY, не запускать второй канал |
| Новый docs-only PR и frozen CC-03 CI | **BLOCKED:** workflow `controlcenter-cc03-windows-native.yml` требует неизменный `HEAD:ControlCenter`. PR #592 исходный head `bd0817b19f2837e48b8c33bc298f4d2a92a06691` → run [45002006316](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/45002006316) **FAIL** в identity guard: `CC_FROZEN_ORIGIN_CHANGED:HEAD:ControlCenter`; Windows tests **NOT RUN** | Нужен отдельный утверждённый review CI owner/общего проекта: безопасно разделить immutable CC03 baseline и docs-only проверки. Нельзя обходить gate или менять `.github/workflows` в этом ТЗ |
| Полная Windows pytest и физическая приёмка этого docs PR | **NOT RUN** | CI по точному PR HEAD; физические действия отдельным решением |
| Независимый полный Recovery/cold restore | **NOT_TESTED** | Общий финальный этап после Kimi |

**Операторская процедура при инциденте:** сохранить время, робот/действие/request_id, локальный результат и audit; при неизвестном исходе не повторять POST/команду и не менять switch; провести независимую READONLY сверку. Для отказа панели — отдельно разрешённый rollback **только Control Center** из точного backup после SHA/ACL review, без пересоздания Task или token.

## Ограничения физической приёмки и восстановление
Операторский `cc07_install=pass` и `already_current` на 20.11, некоторые START/PAUSE/STOP/RESTART — датированное INSTALLED свидетельство. Не проверены **сейчас** ARMED, FINAM positions/orders/SLTP, все STOP/RESTART и успешный RECOVER на естественном аварийном HALT. R5 final backup/R6 cold restore — в конце общего проекта, изолированно. При `FAILED_UNKNOWN` никакого автоматического повтора, только независимая проверка.

[Реестр документов](V20_DOCUMENT_REGISTER_20261122.md) · [Экзамен Kimi](V20_KIMI_EXAM.md).
