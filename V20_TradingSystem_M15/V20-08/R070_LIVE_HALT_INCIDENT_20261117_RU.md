# V20 — инцидент трёх HALTED, 17.11.2026 (по реальной выгрузке Intel)

Источник: локальный архив оператора `v20-halt-all3-20261117T131141Z.zip` (архив содержит торговые данные и **не загружается в публичный GitHub**). Подтверждены целостность ZIP (26 объектов), штатный SQLite online backup 3/3, три оригинальных журнала worker и три FINAM READONLY-файла. Никаких реальных торговых операций при расследовании.

## Состояние на момент снимка ~16:11 МСК

| Робот | Task | Kill Switch | FINAM positions | FINAM active orders | SQLite risk reservations | SQLite execution_halt | Closed historical entries |
|---|---|---|---:|---:|---:|---|---:|
| V20-Shallow | Running | HALTED | 0 | 0 | 0 | null | 8 / 8 |
| V20-OBV | Running | HALTED | 0 | 0 | 0 | null | 6 / 6 |
| V20-Inside | Running | HALTED | 0 | 0 | 0 | null | 4 / 4 |

`finam_all_three_flat=PASS`; `sqlite_backup=PASS`. Временные данные нельзя трактовать как гарантию будущего состояния брокера. В SQLite `flat_cleanup` имеется для каждого historical ENTRY; идентификаторы счетов/ордеров не публикуются.

## Фактические причины последних HALT

- **Shallow**, 14:42:41 и 14:43:02 МСК — `FAULT_FINAM_READ_AUTH_HTTP_401_UNVERIFIED`; 14:43:22 — `HALT_FINAM_READ_AUTH_HTTP_401_PERSISTENT`; Kill Switch HALTED с 14:43:49 МСК.
- **Inside**, 14:42:36 и 14:43:08 МСК — `FAULT_FINAM_READ_AUTH_HTTP_401_UNVERIFIED`; 14:43:39 и 14:44:01 — `HALT_FINAM_READ_AUTH_HTTP_401_PERSISTENT`; Kill Switch HALTED с 14:43:58 МСК.
- **OBV**, 15:00:23 МСК — `HALT_IncompleteRead`; Kill Switch HALTED с 15:00:54 МСК.

Ранее 12:07–12:24 МСК присутствовали массовые `FAULT_FinamTimeout` по всем трём роботам, а также единичные сбои 401. Это подтверждает проблемы чтения/авторизации FINAM API, но нельзя доказать по JSONL, работал ли сбой у сервера FINAM, у локальной сети или на промежуточном узле.

Строка `HALTED_NO_NEW_ENTRIES` после остановки — состояние, не первопричина. Подсчёт старых `HALT_STAGE8_12_4_ORDER_REQUEST_INVALID` за весь срок логов не является текущим событием и не требует повторного исследования.

## Инженерное решение

1. **Не ослаблять защиту от устойчивого HTTP 401.** Существующий код `V20FinamAPI` преобразует неподтверждённый read-only 401 в временный `V20FinamSnapshotReadRetry`; после трёх повторов `run()` сознательно ставит `HALT_FINAM_READ_AUTH_HTTP_401_PERSISTENT`. Штатная ручная проверка и восстановление только после нового FINAM GET-only broker state. Открытые позиции и неизвестные заявки при восстановлении обрабатываются по обычной строгой процедуре.
2. **Точечный кодовый дефект OBV:** `http.client.IncompleteRead` из FINAM GET не классифицируется и попадает в общий обработчик нетранзитных исключений, вызывая аварийный HALT. Кандидатный патч `r070-finam-get-incomplete-read-candidate.patch` обрабатывает исключение **только для GET** как `V20FinamSnapshotReadRetry('FINAM_GET_INCOMPLETE_READ')`; вся частичная запись отбрасывается, новый полный снимок получается в следующем цикле, никаких order POST/DELETE не повторяется. На POST, SLTP POST и DELETE поведение остаётся строгим HALT.
3. **R070 EXT2 + TP6/Protect3** остаётся отдельным кандидатным обновлением в Draft PR #574. Физическая проверка M15 всё ещё `HOLD_FINAM_M15_SEQUENCE_OR_TIME`, USD/GLD имеют недоказанные исторические пропуски. Не устанавливать неподтверждённые элементы R070 по одному только PASS CI.

## Установка / откат

Патч пока только в GitHub Draft, **не установлен на Intel**. Прежние frozen LIVE module SHA и H1 остаются неизменны. По одобрении конкретного release — согласованный backup SQLite 3/3, FINAM GET-only независимая проверка flat/owned SLTP, pin-проверка оригинала, атомарная замена только V20 LIVE-модуля под отключёнными новыми входами, затем проверка затронутого GET пути и операторское ARMED отдельно. Откат — оригинальный закреплённый SHA при HALTED, без изменения SQLite/SLTP. Не перезапускать работающие процессы в момент неизвестных позиций и не выдавать CI за физическую установку.
