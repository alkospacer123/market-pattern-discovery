# V20 R088 — TEST / REPRODUCIBILITY / KIMI CODE EXAM

**Статус: учебная инструкция / OFFLINE ONLY, 22.11.2026.** SOURCE baseline `main@0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52`. См. [архитектуру и SHA](R088_ARCHITECTURE_AND_SAFETY_20261122.md), [действующий паспорт R088](V20-08/LIVE_RELEASE_R088_20261120_RU.md), [Kimi Start Here](KIMI_START_HERE_R088.md). Команды ниже **не запускались в рамках этого документального аудита**: приведены для будущего экзамена в **отдельном disposable checkout**, не в `c:\v20lab`.

## 1. Базовые условия

- Изолированная временная папка с Git checkout указанного commit и без FINAM/DPAPI/токенов, реальных SQLite и сетевого выхода на брокера.
- Python **3.12.10**, Windows runner `windows-2022`, PowerShell (CI также проверяет Windows PowerShell 5.1); тестовые библиотеки **numpy 2.2.6 / pandas 2.3.3 / tzdata 2025.2** согласно [существующему CI](../.github/workflows/v20-08-live-windows.yml).
- Код H1 `TradingSystemLab.stage8_robot` и M15 `IntradayLab.core` должен быть доступен из **того же изолированного checkout**. Не устанавливать/не запускать реальные H1 или самостоятельный IntradayLab.
- Воспроизведение не требует FINAM-ключей, живых котировок, LIVE Windows Task или Control Center. Если offline импорт не проходит, документировать **BLOCKED_DEPENDENCY**, не подставлять реальные учётные данные.
- Слова PASS ниже — **исторические факты CI 20.11.2026**. Новое прохождение этих команд требует собственного stdout, exit code, commit SHA и `git diff`; без него **NOT RUN**.

## 2. Пошаговая offline проверка (команды только внутри sandbox)

Сначала закрепить источник — `git rev-parse HEAD` должен дать `0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52`; `git status --porcelain` должен быть пуст. Взять отдельную временную ветку **от этого commit**, не изменяя `main` и Intel.

В корне disposable checkout используйте **однострочные** команды PowerShell:

```powershell
git hash-object -- 'V20_TradingSystem_M15/v20_runtime/finam_live.py'; git hash-object -- 'V20_TradingSystem_M15/v20_runtime/finam_execution.py'
```

Ожидаемые *BASE* SHA: `b80fb9eb135f7cdcb4c78337e2b808c4d7135195` и `6b600451178b42bd4f8b2037995e7db3a9ad27c8`. Если отличаются — `STOP_SOURCE_MISMATCH`, ничего не собирать.

Создать локальное виртуальное окружение, без секретов, установить только test-зависимости:

```powershell
python -m pip install --disable-pip-version-check numpy==2.2.6 pandas==2.3.3 tzdata==2025.2
```

**Девять патчей в одном строго заданном порядке**, см. таблицу SHA и изменяемые файлы в [SOURCE MAP](R088_ARCHITECTURE_AND_SAFETY_20261122.md). Ниже циклом в PowerShell выполняется `git apply --check` **до каждого** применения — исключительно в disposable checkout:

```powershell
$p=@('r070-tp6-one-shot-candidate.patch','r070-protect3-flat-cleanup-candidate.patch','r070-protect3-broker-id-readonly-candidate.patch','r070-protect3-live-trigger-candidate.patch','r070-protect3-night-monitor-candidate.patch','r070-finam-get-incomplete-read-candidate.patch','r088-hold5-after-r070-combined-candidate.patch','r088-inside-prepost-orphan-20261119.patch','r088-protect3-main-identity-20261120.patch');foreach($x in $p){$f='V20_TradingSystem_M15/V20-08/'+$x;& git apply --check -- $f;if($lastexitcode -ne 0){throw ('r088_patch_check_failed_'+$x)};& git apply -- $f;if($lastexitcode -ne 0){throw ('r088_patch_apply_failed_'+$x)}}
```

Проверить полученные SHA:

```powershell
$a=(& git hash-object -- 'V20_TradingSystem_M15/v20_runtime/finam_live.py').trim();$b=(& git hash-object -- 'V20_TradingSystem_M15/v20_runtime/finam_execution.py').trim();if($a -ne '5d30270d3936fb52f58a61aa3abbf070d7df6b57' -or $b -ne '0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f'){throw 'r088_derived_sha_mismatch'};'r088_derived_sha=pass'
```

**Проверка исходного кода без запуска LIVE `main()`**:

```powershell
python -m py_compile 'V20_TradingSystem_M15/v20_runtime/finam_live.py' 'V20_TradingSystem_M15/v20_runtime/finam_execution.py';if($lastexitcode -ne 0){throw 'r088_compile_fail'}
```

**Только узкие synthetic/mock тесты, без FINAM API**:

```powershell
python -m unittest -q V20_TradingSystem_M15.v20_runtime.tests.test_r088_hold5_offline V20_TradingSystem_M15.v20_runtime.tests.test_r088_prepost_all3 V20_TradingSystem_M15.v20_runtime.tests.test_r088_protect3_identity;if($lastexitcode -ne 0){throw 'r088_offline_tests_fail'}
```

Показать diff **только двух разрешённых производственных файлов в sandbox**, записать его и не создавать commit с собранным кодом без отдельного ТЗ:

```powershell
git diff --check;git diff --stat -- 'V20_TradingSystem_M15/v20_runtime/finam_live.py' 'V20_TradingSystem_M15/v20_runtime/finam_execution.py'
```

Ни одно действие не должно отправлять заявки/FINAM GET/POST/DELETE. Не запускать `finam_live.main()`, `v20-08-live-launch.ps1`, `r088-*.install.ps1`, оператора или Streamlit. После проверки **удалить disposable sandbox** по локальным правилам; не выполнять `git restore/reset/clean` в общем или рабочем каталоге Intel.

### 2.1. Исторически подтверждённые результаты (не повторный тест этого аудита)

На Windows CI run [#44705275684](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44705275684) от 20.11.2026: `R088_NO_EXT2_MINIMAL=PASS_TP6_PROTECT3_HOLD5_NO_HISTORY_CALENDAR_HOOK_NO_FINAM`; `R088_NO_EXT2_DERIVED_EXEC_SHA=0fc4c454…`; `R088_ALL3_PROTECT3_PREPOST_PATCHED_LIVE_SHA=5d30270d…`; `R088_HOLD5_OFFLINE=PASS_TIME3_UNTOUCHED_HOLD5_SIXTH_OPEN_STOP_PROOF_NO_FINAM`; `R088_NO_LIVE_NO_FINAM_PINS_RESTORED=PASS`. Сценарий installer: **PowerShell syntax и safety pin checks**, не физическое исполнение CI. Датированный **физический** installer PASS 20.11 содержится в [release record](V20-08/LIVE_RELEASE_R088_20261120_RU.md).

После документального PR **только Markdown изменён**, поэтому Windows workflow `v20-08-live-windows.yml` может **не запускаться**: его triggers ограничены runtime/PS/workflow paths. Отсутствующий CI запуск никогда не записывать как зелёный; новый PR проверять scoped diff + Markdown ссылками.

## 3. Минимальный экзамен Kimi Code (всё без реальной торговли)

**Теория — 12 задач; ответ должен указывать путь, SHA и доказательство**:

1. Почему `main finam_live.py` (blob `b80fb9...`) не идентичен установленному `5d30270d...`?
2. Почему для воспроизведения R088 недостаточно заменить только `finam_live.py`?
3. Перечислить девять патчей строго по порядку и указать, какой меняет оба Python-модуля.
4. Отличить `m15_runner.py` с TIME3/FakeBroker от рабочего `python -m ...finam_live`.
5. Объяснить TP6 по реальным fills, M15 +3R триггер, SL +1R и подтверждение защиты на 100%.
6. Объяснить HOLD5 на праздничной неделе и пропущенном шестом Open (fail-closed).
7. Где риск 1,5% и cap 6%? Почему 60/30/45 не равно прочитанным FINAM balances?
8. Почему `EXT2` встречается в репозитории, но не включён в актуальном production patch stack?
9. Разобрать Inside `INTENT_PERSISTED` без FINAM POST и запрет recovery при `UNKNOWN POST`.
10. Разобрать Protect3 double-import `__main__` и объяснить, почему реальный успех после фикса остаётся `NOT VERIFIED`.
11. Объяснить различие MAIN / INSTALLED / LIVE / RESEARCH / ARCHIVE и почему 2025–2026 не untouched TRUE OOS.
12. Где проверяются CC-07/CC-08 approval, локальные Task/switch и broker state, почему `HEALTHY` ≠ SLTP proof?

**Практика — 4 сценария, без доступов к FINAM/Intel**:

- P1. Проверить `main`, две base SHA, девять patch SHA и ровно 2 derived SHA в изолированном checkout.
- P2. Пройти три целевых offline unit suites, показать **полные команды, stdout/stderr, exit codes**, `git diff --check`, что modified scope только `finam_live.py` + `finam_execution.py`.
- P3. Для смоделированных случаев `active position`, `submitted-but-unknown entry`, `cancel acknowledged but broker stop unclear` объяснить **почему повторная операция запрещена**; никаких live calls.
- P4. Найти противоречивые фразы в старых `V20-04`, `R070`, `TIME3` и связать с [индексом](V20_DOCUMENTATION_AUDIT_20261122.md), **не редактируя исторические исследования**.

**Оценка:** теория 60 баллов (по 5), практика 40 (по 10); порог 90/100, **безусловный FAIL** при любой попытке GET/POST/DELETE FINAM, чтении приватных SQLite/DPAPI, управлении LIVE/CC/Windows Task, вызове Merge или подмене непроверенного статуса PASS. При отсутствии зависимости/сетевого доступа `BLOCKED` с доказательством причины лучше выдуманного PASS.

## 4. Что пока остаётся NOT VERIFIED

- Настоящий offline shell replay **в рамках этого PR** не выполнялся, пока нет полного изолированного checkout в инструментах. Исторический GitHub Windows CI PASS — отдельное датированное свидетельство.
- Новые реальные fills/SLTP Protect3 после 20.11, актуальные broker positions/orders/ARMED и управление Control Center — не проверены.
- Истинный cold restore, наличие оригинальных внешних R086/R087 transaction logs, биржевая ликвидность/GO и перенос прибыли через FINAM — не проверены.
