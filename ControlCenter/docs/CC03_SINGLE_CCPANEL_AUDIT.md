# CC-03: независимый аудит single-ccpanel preflight (#548)

Дата: 18.10.2026 MSK. Scope — только ControlCenter, отдельная ветка от проверенного #547; никакого merge/deploy или Intel execution. Текущая operator authority — [#524, comment 6241614427](https://github.com/alkospacer123/market-pattern-discovery/issues/524#issuecomment-6241614427). H1 LIVE ARMED/RUNNING не проверялся и не затрагивался.

## Проверенные исходники и прежние доказательства

GitHub API и git fetch независимо подтвердили main `9067ad87ff35fa6c657e1610013095ad66da7a45`, #547 `e27d40c4784b119493a4c68705ab5088bb1d97b0`, его интеграционную ветку `cc03/single-ccpanel-deployment-20261018`. Diff #547 относительно этого main: 25 файлов, все ControlCenter. Проверены runtime, deployment/ACL, observer, receiver trust и изменённые тесты/документы; main ref не равен устаревшей локальной ветке main и для сравнения использован проверенный origin/main.

Просмотрен реальный job log Windows run [39076988750](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/39076988750), job 117526075756: SUCCESS, 408 PASS, 15 POSIX-only SKIP; manifest 98 файлов, 8 effective ACL probes, стандартный SID/loopback HTTP 200, exporter rejected, Task before/after unchanged, uninstall data retained. Это прежний HEAD #547, не доказательство новой ветки и не Intel acceptance.

Draft #545 проверен на HEAD `1e5bee0e664a3e8ce16e8f9e31faaf8149d9a80e`: его решение — process-scoped Bypass только readiness helper. В данной ветке оно учтено с новым single-SID payload, а тот же ограниченный режим установлен для fixed Task helper. Исходный #545 не меняется.

## Матрица A/B/C и найденные несогласованности

| Участок | До аудита | Исправление / граница |
| --- | --- | --- |
| A policy/readiness | Два SID; null exporter даёт NOT_PROVISIONED даже при существующем ccpanel | v2 с одним cc_panel_sid; безопасный in-memory v1 adapter только для null exporter |
| A observer | Отдельно pinned SID/elevation + Administrators, без назначения по имени | Observer остаётся независимым; limited/привилегированный/impersonated token отклоняется; никаких auto grants |
| A Task | Running допустим; exact XML/principal bracket работает независимо от B | Сохранено. Нельзя объявлять A сломанным из-за отсутствующего exporter |
| B account | SID translation A не проверяла имя/Enabled; B пропускала account validation в CI sandbox | Общий existing-account validator; реальный одноразовый локальный ccpanel в CI; Enabled/SID/privileged membership отрицательные случаи |
| B ACL | Protected DACL, trusted owner, panel private denial, export readonly | Сохранено; A явно cc_acl=NOT_VERIFIED; roots existence не равно ACL PASS |
| PowerShell | Ambient ExecutionPolicy могла запретить helper | Только process-scoped Bypass для двух exact helper; GPO/WDAC/ошибки fail closed; глобальная policy неизменна |
| Manual refresh | Один клик вызывает один provider, lock только внутри процесса | Дополнительный nonblocking Global mutex на Windows между сессиями/процессами; отказ не вызывает provider и не повторяется |
| Кеш | CURRENT у OS rows фиксировался во время чтения и мог пережить TTL | Консервативный общий expiry по envelope/наблюдениям, при rerender данные становятся STALE/UNKNOWN без I/O и без переписывания source/receipt timestamps |
| C | Старый producer заблокирован, реального принятого источника нет | Без изменений: H1 health, broker/account, positions/fills/SLTP/finance UNKNOWN; источник C не утверждён |

## Ограничения безопасности

Runtime не запускает Task/CIM/FINAM: UI импортирует только receiver и читает из отдельного CC export лишь по кнопке. Нет timers/retry/poll/background READONLY; переключение страниц не вызывает источники. Один provider-вызов может включать ограниченное чтение protected receiver policy и одного completed CC snapshot (не одно физическое ReadFile всего процесса). На Windows каждое чтение ограничено worker timeout/размером и root/ACL/digest checks. При конфликте mutex — ноль provider вызовов. Mutex занят/недоступен/подменён → отказ, не повышение прав. ОС освобождает mutex при завершении владельца. POSIX development flock использует существующий файл модуля readonly, без lock-файлов/записей; его scope — текущий checkout, целевой Windows mutex общий между checkout/сессиями. Это не блокировка внешнего H1 producer и не решение legacy os.replace.

Кеш не обновляет страницу по таймеру: на неподвижной странице остаётся датированное прошлое наблюдение; при следующем ручном UI rerender TTL пересчитывается без обращения к источнику. Ошибка новой попытки очищает текущий cached result до UNKNOWN. SYNTHETIC/OFFLINE_FIXTURE имеют видимую тестовую provenance; M15 остаётся NOT_DEPLOYED и отдельным контуром. Все десять торговых controls disabled.

ccpanel не получает app/venv/policy/export write и data/private read. Preflight A policy — отдельная protected review-копия, доступна лишь отдельно одобренному standard SID; это не раздача private source policy интерфейсу. Source/receiver approval false в шаблонах; реальные SID/секреты/production paths в GitHub не добавлялись. Старый Start-Exporter -Execute отклоняется до policy/source I/O.

## Воспроизводимые проверки

Локально: `python -m pytest -q` из ControlCenter и `python deployment/manifest.py --check`. На одноразовом GitHub-hosted Windows Server 2022: существующий pinned workflow, Python 3.12.10 x64, exact hashed wheel lock, ci/windows_acceptance.py. Полный suite выполняется нативно; Windows SKIP считается незавершённой проверкой. Новые тесты не используют SKIP/XFAIL для сокрытия дефектов.

Проверяются: ccpanel Enabled/absent/Disabled/wrong SID/Administrators, restricted deny-only Administrators token и elevated observer; реальные Task Running XML/principal/drift/denial; отсутствие exporter SID; чтение private запрещено под реальным low token; один клик/навигация/ошибка/межпроцессный mutex и смерть владельца; TTL кеша; отсутствие production JSON opens; активный Task/process observer при 500 sandbox producer replacements; expected-conflict legacy regressions честно остаются NOT_PASSED, не выдаются за noninterference acceptance. Rehearsal проверяет ACL, install, listener SID/127.0.0.1:8501, exporter rejection, Task до/после и сохранность CC data при stop/uninstall. Никакие production SQLite/WAL/FINAM/settings не открываются; noninterference для них устанавливается отсутствием capability/I/O, а не чтением реальных hashes.

Новый HEAD, Draft PR, полные файлы, итоговые counts, run URL и SHA-256 пакета/manifest публикуются в PR/issue после CI; они не вставляются самоссылкой в hashed source. Ранние FAIL, если возникнут, перечисляются отдельно; evidence одного HEAD не переносится на другой.

## Оставшиеся блокеры и STOP

CC03_INTEL_PHYSICAL_NOT_EXECUTED: состояние/Enabled/token существующего ccpanel, фактические owners/DACL/effective rights и единственный loopback listener на Intel здесь не подтверждены. Нельзя включать/переименовывать/удалять серверные аккаунты или расширять ACL. CC03_H1_SOURCE_BLOCKED: точный безопасный one-shot источник, независимая authority/binding и Windows noninterference ещё требуют review; legacy H1 JSON/metadata os.replace несовместимы. Источник не подключается из UI независимо от ручного режима.

Следующий шаг строго CC-03: аудит отдельного Draft и его hosted evidence оператором; затем только отдельно разрешённая подготовка/физическая B и независимая C приёмка по #524. Ни эта ветка, ни CI не разрешают merge, установку или переход CC-04/05. STOP.
