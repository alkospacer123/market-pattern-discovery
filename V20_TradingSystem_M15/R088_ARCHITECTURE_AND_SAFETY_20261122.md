# V20 R088 — ARCHITECTURE / SOURCE MAP / STRATEGY & RISK / OPERATOR SAFETY

**Проверенный исходный срез:** `market-pattern-discovery/main@0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52`, 22.11.2026. GitHub source/documentation audit ONLY. Не свидетельство о текущем Intel/FINAM. Основной [R088 release](V20-08/LIVE_RELEASE_R088_20261120_RU.md), [точка входа](KIMI_START_HERE_R088.md), [offline exam](R088_OFFLINE_EXAM_20261122.md).

## 1. Архитектура: что реально исполняется

```text
V20-08/v20-08-live-operator.ps1 (owner-scoped check/start/stop/restart/backup)
  → V20-08/v20-08-live-launch.ps1 (DPAPI + approved SHA + scope)
    → python -m V20_TradingSystem_M15.v20_runtime.finam_live
      ├─ V20LiveJournal: отдельный SQLite/состояние/lock каждого робота
      ├─ V20FinamReadAdapter: FINAM account, positions, orders, M15 GET
      ├─ V20LiveTransport: H1-based intents, entry, linked broker SLTP, one-shot exit
      ├─ frozen_adapter / offline_planner: Shallow, OBV, Inside signals unchanged
      ├─ account_risk: R15, cap 6%, cash/GO/биржевой тик
      ├─ r070_linked_sltp + tp6_protect3: TP6, +3R review, +1R broker stop
      └─ r088_hold5: sixth OBSERVED session open
  → robots/{shallow,obv,inside}/ (three independent accounts)
      ├─ state/v20-real-intents.sqlite3 (durable state/fills/intents, not in Git)
      ├─ safety/stage8-trading-kill-switch.json
      ├─ logs/live-m15.jsonl
      └─ secrets/ (DPAPI per SID, NEVER read or commit)
```

**`m15_runner.py` не LIVE исполнитель.** `V20_TradingSystem_M15/v20_runtime/m15_runner.py` (blob `41c17be3469fd371d0288db78914ecc492197464`) содержит отдельный OFFLINE/FakeBroker контур с историческим TIME3 `THIRD_OBSERVED_SESSION_EXIT`. Не подменять им `python -m ...finam_live`. Исторический V20-04 `SOURCE_MAP.md` — происхождение интерфейсов на дату 22.10, а не описание полной установленной R088.

## 2. Карта кода и доказательства

| Механизм | Source (Git `main`, base blob) | Дополняющий слой / offline тест |
|---|---|---|
| Три стратегии, completed M15, проверка причинной истории | `v20_runtime/frozen_adapter.py` `71d50f3f1227a00c8831e9a7f738dcf0d19ea49e` | `offline_planner.py`, `tests/test_frozen_n4_parity.py`, `test_frozen_adapter.py` |
| Реальные циклы, ownership, Kill Switch, ночной режим, no duplicate POST | `v20_runtime/finam_live.py` **BASE** `b80fb9eb135f7cdcb4c78337e2b808c4d7135195` | Патчи №3–6, 7–9; `test_r088_prepost_all3.py`, `test_r088_protect3_identity.py` |
| FINAM GET/M15, SQLite durable intents/fills, one-shot entry/exit | `v20_runtime/finam_execution.py` **BASE** `6b600451178b42bd4f8b2037995e7db3a9ad27c8` | Патчи №1–2, №7; `test_finam_execution.py`, `test_finam_journal.py`, `test_finam_frozen_exit.py` |
| Риск, ГО, tick grid, 1,5%/6% | `v20_runtime/account_risk.py` `50d0a924b0eccef45746c0111fa0df4803aed125` | `tests/test_account_risk.py`, H1 `stage8_robot.margin/risk/execution_grid` |
| TP6, Protect3 pure math/closed M15 | `v20_runtime/tp6_protect3.py` `a578cac629350f2c9fe3409121ac085c8a41eb63` | `r070_linked_sltp.py` `864d03d8fe467138adf73c6e6216a88fc81e8c21`; `test_tp6_protect3.py`, `test_r070_v20_protection_handoff.py` |
| HOLD5 observed-session counter / missed-open fail-closed | `v20_runtime/r088_hold5.py` `f0b9058707230299464f1f6fb5245653a022ec31` | Патч №7; `tests/test_r088_hold5_offline.py` |
| Windows Task / DPAPI / operator | `V20-08/v20-08-live-launch.ps1` `4e7498d2eacf0930d0ee1bbf6343883735f3aefb`; `v20-08-live-operator.ps1` `b06957ea7833daeda65296eb372890951860c008` | `.github/workflows/v20-08-live-windows.yml` (repo root) `889db248b943105dd598fbbe248d277a5e1b7e67`; операторский [runbook](V20-08/RUNBOOK_08_5_RU.md) |
| Фикс неоправданного HALT до FINAM POST | Patch №8 `r088-inside-prepost-orphan-20261119.patch` `0b6b23e46b1e63a0afafe88d91cec52d7e19efb9` | Общая проверка для всех трёх; при UNKNOWN POST сохраняется строгий HALT |
| Фикс двойной загрузки `python -m` | Patch №9 `r088-protect3-main-identity-20261120.patch` `56f03cf0be39a357c2e22ba0ecd5bdc0861e7589` | `test_r088_protect3_identity.py` проверяет класс в `__main__` vs canonical import |

Код **прямо импортирует** библиотеки `TradingSystemLab.stage8_robot` (FINAM API, broker state, risk/margin, SLTP, SQLite/H1) и `IntradayLab.core` (M15 бар/каузальность, прежде всего в offline коде). Удаление H1/M15 каталогов ради «чистоты» нарушает существующие зависимости. Самостоятельные H1/IntradayLab не должны активироваться.

## 3. MAIN base ≠ установленный production

**R088 production состоит из ДВУХ изменяемых при сборке модулей**, не одного `finam_live.py`. Исходные base blobs: `finam_live.py=b80fb9eb135f7cdcb4c78337e2b808c4d7135195`; `finam_execution.py=6b600451178b42bd4f8b2037995e7db3a9ad27c8`.

Девять `V20-08/*.patch` из [release manifest](V20-08/LIVE_RELEASE_R088_20261120_RU.md), в том же порядке, что и в Windows CI:

| № | Patch (Git blob SHA) | Файл, который меняет |
|---:|---|---|
| 1 | `r070-tp6-one-shot-candidate.patch` `c1947f59ab68884fd6543c40d64892d6a899f225` | execution |
| 2 | `r070-protect3-flat-cleanup-candidate.patch` `b7d3eb587e97d4012cc21a593f2d8b605e431611` | execution |
| 3 | `r070-protect3-broker-id-readonly-candidate.patch` `4d975f8d2d4b701b48205f9ad24c0d49e45c9c4e` | live |
| 4 | `r070-protect3-live-trigger-candidate.patch` `0e378d0197815556cdd99ac8e1d6c20d1c05a056` | live |
| 5 | `r070-protect3-night-monitor-candidate.patch` `05dffdaaaed6359b0a78116adac9364dd2bdcc34` | live |
| 6 | `r070-finam-get-incomplete-read-candidate.patch` `fabfa58e9d84553fe0c51833530cb90d89412e85` | live |
| 7 | `r088-hold5-after-r070-combined-candidate.patch` `0c73f8265a1c7f75a1bc8f4b849e5970fe274bc4` | **execution + live** |
| 8 | `r088-inside-prepost-orphan-20261119.patch` `0b6b23e46b1e63a0afafe88d91cec52d7e19efb9` | live (all three robots despite filename) |
| 9 | `r088-protect3-main-identity-20261120.patch` `56f03cf0be39a357c2e22ba0ecd5bdc0861e7589` | live |

Результат Windows CI #44705275684 **(20.11, SUCCESS)**: после первых семи `live=54ae8e1262482f4ecc80d202c6e9063cf0d6e402`, `execution=0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f`. После девяти `live=5d30270d3936fb52f58a61aa3abbf070d7df6b57`, `execution` остаётся `0fc4c454…`. Шаги no-EXT2, PREPOST, Protect3 identity, HOLD5, compiler и installer syntax — PASS, временные патчи возвращены к базовым blobs. Этот **исторический CI** доказывает offline построение на своём Git ref, но новый checkout после документационных изменений повторно не проверялся.

**Датированное Intel свидетельство 20.11**: `V20_ALL3_PREPOST_PROTECT3_FIX=PASS_3_RUNNING_HALTED_FRESH_CYCLES`, подготовлены backup/rollback, workers Running / switches HALTED. Это **не** доказательство ARMED на 22.11 или исполнения Protect3 на следующей позиции. Текущий LIVE = `UNKNOWN`.

## 4. Замороженный STRATEGY & RISK CONTRACT

| Инвариант | Действующая модель (решение владельца) | Что нельзя делать |
|---|---|---|
| Strategy | Shallow Pullback / OBV Pressure / Inside Day Release | Менять сигнал/фильтр/индикатор; подменять Inside историческим V4 |
| Symbols | USDRUBF / CNYRUBF / GLDRUBF / IMOEXF (N4) | Добавлять инструмент/счёт |
| M15 / Market | completed M15 signal → NEXT_OPEN market, входное окно 10:15–17:15 МСК внутри сессии 10–18 | Delayed market POST после пропущенного Open |
| SL / TP | начальный SL=2×ATR14 Wilder M15; TP=+6R от **фактического VWAP fills**, tick rounding | Выставлять цель от планового Open или отменять stop без процедуры |
| Protect3 | +3R на завершённой M15; план +1R не раньше следующей; подтверждённая котировка и FINAM stop ownership | Считать intrabar touch доказательством переноса; обходить HALT при неизвестной отмене |
| HOLD5 | пять **наблюдаемых** торговых сессий включая вход; exit на первом подтверждённом Open шестой; пропущенная граница fail-closed | Считать календарные дни или закрывать задним числом при пропуске Open |
| Money | риск 1,5% на новую сделку, номинальный cap 6% на **каждый отдельный счёт**; GO/тик/доступные средства обязательны | Делать 6% «общим для трёх счетов», обходить margin guard |
| Portfolio | утверждённое распределение 60/30/45 тыс. ₽ | Считать банковские остатки известными или делать перевод в рамках документации |
| EXT2 | **OFF** в production patch stack | Автоматически подключать `ext2_r060.py`, `r088_ext2_live_source.py` |
| Weekend | новых входов Sat/Sun нет; существующие позиции/SLTP продолжают сопровождаться | Выключать брокерскую защиту на выходные |

`TIME3`, старые V20-04/V20-03 результаты, R070 с EXT2 ON и другие research-кандидаты — **историческая база**, не `MAIN` производственный контракт. 2025–2026 уже использованы для исследования, поэтому это не новый untouched TRUE OOS.

## 5. OPERATOR SAFETY (V20 / CC)

Разрешено в рамках GitHub-аудита: читать, сравнивать Git commit/blob SHA, строить только одноразовый **offline** стенд, анализировать synthetic/mock tests и документы. Нельзя выполнять команды из операционных скриптов на Intel, вызвать FINAM, получить DPAPI/token/account ID, читать приватный SQLite/JSONL, или управлять реальными Task/ARM/HALT/защитными заявками. Merge, deployment, финансовые операции — **только по отдельному разрешению владельца**.

При существующей позиции брокерское доказательство **100%-SLTP** важнее текстового HEALTHY. `HALTED` запрещает новые входы, но не является самостоятельным доказательством нулевой позиции. **UNKNOWN broker POST → никакого повторного POST**. PREPOST patch может закрыть только точно никогда не отправленный intent при отсутствии позиции/активной заявки и при доказательстве локального durable checkpoint. Protect3 cancel-first: нельзя объявить «безразрывная замена SLTP»; отмену старой и подтверждение новой нужно отдельно доказать по брокеру. Partial fills требуют actual VWAP, дозаполнения/переоценки и правильного coverage, не гипотетического расчёта.

**Control Center CC-07/CC-08:** [V20 CC-08 operations](../ControlCenter/docs/V20_CC08_OPERATIONS.md) (Git blob `51781e013f68fc323a4740701ae84e066ef86926`) и [CC README](../ControlCenter/README.md) (`707080ee4daf1b2cf3a754c078a67e78f6612aae`). V20 оператор находится в `c:\v20lab\pretrade-08\live-08\v20-08-live-operator.ps1`, Control Center по `http://127.0.0.1:8502`. CC-07 проверяет разрешения/соответствие SHA и использует отдельный approval/recover flow. В источниках есть датированное сообщение владельца о совместимости после обновления 20.11, но **нет** свежей независимой проверки этого аудита; `CC_COMPAT_LIVE=NOT VERIFIED`. Не запускать кнопки ради документационного теста.

## 6. KNOWN ISSUES / GAPS

- `R070_PROTECT3_LIVE_TRANSPORT_IDENTITY_INVALID` — объяснён двойной загрузкой `python -m`, patch №9 проверен offline; **реальный новый перенос стопа после фикса не наблюдался**.
- Более ранний `R070_PROTECT3_M15_OR_FILL_UNVERIFIED` 20.11 — **внутреннее условие UNKNOWN**, не утверждать, что patch №9 решает его.
- `PREPOST` Inside 19.11: «never sent» orphan отменён после GET-only и нового кода, факт из dated install. Для **неизвестного** POST остаётся HALT.
- Реальные SLTP partial-fill, reset/restart, broker cancel acknowledgment и переход Protect3 при разрыве связи **не доказаны этим GitHub-аудитом**; имеются только mock и прежняя операторская история.
- Текущие ARMED/Task/FINAM, позиции, остатки, фактическая 60/30/45, стопы, CC-07 recovery — **UNKNOWN / NOT VERIFIED**. Cold restore — отдельный этап III, не заявлять PASS.
- В R088 source/patch stack нет EXT2 ON, но исследовательские модули с «EXT2» внутри Git присутствуют сознательно. Наличие кода ≠ его импорт в installed main.
