# Kimi R1.2 — глубокая передача V20 R088, первоисточники и экзамен

**Срез:** 20.11.2026. **Статус:** `SOURCE_MAP_PREPARED / KIMI_NOT_TESTED / LIVE_NOT_VERIFIED`. Это документация для GPT/Codex и Kimi AI/Kimi Code, не разрешение на установку, торговлю или отправку FINAM-заявок.

**MAIN:** [market-pattern-discovery](https://github.com/alkospacer123/market-pattern-discovery), проверенный до этой документации `main=f15d565755b996252081ed49ed5a094ee1e8d820` после PR #579. **ARCHIVE:** [market-pattern-archive](https://github.com/alkospacer123/market-pattern-archive), после #4 `main=8d4027c8d53625dfe7780cb7ccfdc354d51b25ba`; 19 оригинальных файлов с Git blob MATCH — **частичный** архив. **DATA:** market-pattern-data отдельно.

## 1. Обязательная последовательность чтения

1. [Общая инструкция проекта](PROJECT_INSTRUCTIONS_CURRENT_2026-11-20.md), [карта шести каталогов](KIMI_REPOSITORY_BOUNDARIES_2026-11-20.md), [R1.1 список источников](KIMI_R1_1_VERIFIED_SOURCE_INDEX_2026-11-20.md).
2. [Текущий паспорт R088](../V20_TradingSystem_M15/V20-08/LIVE_RELEASE_R088_20261120_RU.md), **Git blob** `d61b0ac5b30ff706534f4b5c65e523705aa04d3b`.
3. [Windows CI workflow](../.github/workflows/v20-08-live-windows.yml), **Git blob** `889db248b943105dd598fbbe248d277a5e1b7e67`, шаг `R088 all-robots pre-POST orphan recovery (offline only)`, строки 879–916 (в данной редакции).
4. Исходники и тесты в `V20_TradingSystem_M15/v20_runtime/`. Обязательно найти импортируемые модули `TradingSystemLab.stage8_robot` и `IntradayLab.core` в том же рабочем GitHub. **Исторические H1/M15 отключены**, но общие Python-модули используются V20.
5. Лишь после этого смотреть ранние V20-01…07, старые исторические PR и материалы TRL; они не могут переопределять релиз R088.

## 2. Замороженные торговые правила и доказательные границы

- **ACTIVE V20:** Shallow / OBV / Inside, три раздельных FINAM-счёта; N4 = USDRUBF/CNYRUBF/GLDRUBF/IMOEXF; M15, `Market NEXT_OPEN`, первоначальный `SL=2×ATR14 Wilder`, риск `1,5%/trade` и `6%/account`.
- **Принятая конфигурация:** капитал-модель `60/30/45` тыс. ₽, `TP6 (+6R)`, `Protect3` (+3R после закрытой M15 → SL +1R с не ранее следующей M15), `HOLD5`: пять *наблюдаемых торговых сессий*, включая сессию входа; если SL/TP не сработали, выход на первом доступном Open шестой сессии. **EXT2 OFF** (в репозитории есть только неиспользуемые кандидаты EXT2).
- `60/30/45` — **решение о модели капитала**, а не доказательство текущих фактических остатков на счетах; никакого перевода денег без оператора.
- **INSTALLED:** согласно паспорту 20.11, R088 со всеми исправлениями установлен 3/3; установленный `finam_live.py` имеет Git blob `5d30270d3936fb52f58a61aa3abbf070d7df6b57`, установленный `finam_execution.py` — `0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f`. Это **исторические физические свидетельства**, не сегодняшняя автоматическая проверка.
- **LIVE:** последнее представленное безопасное наблюдение 20.11: `Task=Running`, `Kill Switch=HALTED` у всех трёх, `HALTED_NO_NEW_ENTRIES`. Последующие ARMED, текущие позиции, новые сделки, SLTP и работа Protect3 на новом реальном входе **UNKNOWN / NOT_VERIFIED**. GitHub CI и HTTP 200 панели этого не подтверждают.
- Исторические инциденты: PRE-POST orphan intent Inside закрыт без повторного broker POST; Shallow Protect3 не перенёс стоп из-за transport identity, fix подготовлен/установлен, но реальное подтверждение новой защиты отсутствует. При неизвестном результате POST — **не повторять**.

## 3. Девять последовательных патчей production stack

**База для patch stack** — [`V20_TradingSystem_M15/v20_runtime/finam_live.py`](../V20_TradingSystem_M15/v20_runtime/finam_live.py), Git blob SHA-1 `b80fb9eb135f7cdcb4c78337e2b808c4d7135195` в указанном MAIN. Workflow перед наложением проверяет `git hash-object` базы, затем делает `git apply --check` и `git apply` каждого патча строго по порядку; запускает `py_compile` и mock-`unittest`.

| № | Patch в `V20_TradingSystem_M15/V20-08/` | Проверенный Git blob SHA-1 |
|---:|---|---|
| 1 | `r070-tp6-one-shot-candidate.patch` | `c1947f59ab68884fd6543c40d64892d6a899f225` |
| 2 | `r070-protect3-flat-cleanup-candidate.patch` | `b7d3eb587e97d4012cc21a593f2d8b605e431611` |
| 3 | `r070-protect3-broker-id-readonly-candidate.patch` | `4d975f8d2d4b701b48205f9ad24c0d49e45c9c4e` |
| 4 | `r070-protect3-live-trigger-candidate.patch` | `0e378d0197815556cdd99ac8e1d6c20d1c05a056` |
| 5 | `r070-protect3-night-monitor-candidate.patch` | `05dffdaaaed6359b0a78116adac9364dd2bdcc34` |
| 6 | `r070-finam-get-incomplete-read-candidate.patch` | `fabfa58e9d84553fe0c51833530cb90d89412e85` |
| 7 | `r088-hold5-after-r070-combined-candidate.patch` | `0c73f8265a1c7f75a1bc8f4b849e5970fe274bc4` |
| 8 | `r088-inside-prepost-orphan-20261119.patch` | `0b6b23e46b1e63a0afafe88d91cec52d7e19efb9` |
| 9 | `r088-protect3-main-identity-20261120.patch` | `56f03cf0be39a357c2e22ba0ecd5bdc0861e7589` |

**Критично:** установленный итоговый `finam_live.py` не должен совпадать с Git-базой по blob SHA. Имя патча «inside» историческое; его текущая проверка относится ко всем трём роботам. В production stack **нет** `r070-ext2-pre-intent-candidate.patch` и `r088-ext2-live-source-after-combined-candidate.patch`.

## 4. Исходники, связанные модули и offline-проверки

| Исходник | Git blob SHA-1 MAIN / что проверять |
|---|---|
| `v20_runtime/finam_live.py` | `b80fb9eb135f7cdcb4c78337e2b808c4d7135195`; базовый код до патчей, импорты `TradingSystemLab.stage8_robot` |
| `v20_runtime/m15_runner.py` | `41c17be3469fd371d0288db78914ecc492197464`; импорты `IntradayLab.core.execution`, `IntradayLab.core.models` и `TradingSystemLab.stage8_robot` |
| `v20_runtime/finam_execution.py` | `6b600451178b42bd4f8b2037995e7db3a9ad27c8`; Git-база отдельно от установленной версии |
| `v20_runtime/r088_hold5.py` | `f0b9058707230299464f1f6fb5245653a022ec31`; сессии HOLD5 |
| `.github/workflows/v20-08-live-windows.yml` | `889db248b943105dd598fbbe248d277a5e1b7e67`; offline применение patch stack и тесты |

**Доступные тесты по исходникам:** `V20_TradingSystem_M15.v20_runtime.tests.test_r088_prepost_all3`, `test_r088_protect3_identity`, `test_r088_hold5_offline`, а также другие `v20_runtime/tests/` (не считать их автоматически пройденными). В workflow 879–916 после patch apply выполняется `python -m py_compile` и `python -m unittest -q` первых двух модулей. Реальный Windows CI [run 44705275684](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44705275684) завершён `success` 20.11.2026, **HEAD `aa708de2cc94b4220f655cb2fc0e392262f8b06f`**; это свидетельство для **того CI HEAD**, а не автоматический PASS нового MAIN или текущего FINAM.

Для Kimi Code: использовать отдельный *изолированный checkout* проверенного commit SHA, без FINAM credentials/DPAPI, без Windows Tasks, без broker connectivity, без папок `C:\V20Lab` и `C:\Control Center`. Проверить read-only blob SHA, затем локально воспроизвести patch apply и offline unit tests в CI-подобном sandbox. Не выполнять patch apply в рабочей установленной директории. `git apply` изменяет checkout; это допустимо только в специально созданной временной копии при разрешённой безопасной задаче.

## 5. Экзамен R1.2 — вопросы без прав на LIVE

Kimi должен **самостоятельно**, со ссылками и SHA:
1. Назвать точную актуальную конфигурацию R088; доказать, почему EXT2 OFF, а HOLD5 — это не пять календарных суток.
2. Найти все девять патчей и workflow, доказать их порядок и исходный blob базы; объяснить отличие `MAIN` от `INSTALLED`.
3. Указать минимум по два действующих импорта из исторических H1/M15 каталогов и объяснить, почему их нельзя удалять целиком.
4. Объяснить, чем `Task Running` отличается от `ARMED`, а успешный GitHub CI — от FINAM broker PASS/подтверждения активного SLTP.
5. Назвать зарегистрированные ограничения двух инцидентов: orphan intent Inside и Protect3 transport identity у Shallow, включая неопределённость результата реального Protect3 после исправления.
6. При наличии разрешённого изолированного окружения выполнить offline patch/test procedure и предоставить stdout, exit codes, точный HEAD, версии Python и SHA итоговых файлов; не использовать LIVE.
7. Получить от GPT безопасную незавершённую задачу, подготовить отдельную ветку и PR без Merge, выполнить контрольную передачу GPT на review.

**PASS R1.2** только после независимого фактического выполнения Kimi с проверяемыми ссылками, SHA, тестами/пробелами, правильными запретами и объяснением источников. До этого: `R1_2_PREPARED_NOT_EXAMINED`. R1.5 общий экзамен и R1.6 handoff отдельно, автоматическое Merge запрещено.

## 6. Что остаётся не подтверждено

Текущий установленный ARMED/broker protection; независимый весь Git mirror/PR Issues CI; доступ и лимиты Kimi Code; возможность выполнить тесты вне Intel; полные бинарные исходники TRL; полный cold restore. Эти пробелы нельзя заполнять предположениями. По Roadmap после R1 → R2 → R3 затем итоговый R5 backup и R6 cold restore; перед **любым удалением** требуется независимый checkpoint и разрешение оператора.
