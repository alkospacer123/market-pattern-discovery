# АЛОР OpenAPI: вариант Б — сеть заблокирована, загрузчик подготовлен

Продолжение существующего Draft PR #556 от HEAD `5bc2c7f071cdb715f25741e7579a05a7b1fb7335`. Дата: **19.10.2026, Europe/Moscow**. Новый PR не создаётся. **SOURCE_DATA_BLOCKED_M15** сохраняется; экономических результатов нет.

## Один фактически выполненный GET

Время: **18:18:34.989887 UTC / 21:18:34.989887 МСК**.

```text
GET https://api.alor.ru/md/v2/history?symbol=Si&exchange=MOEX&tf=900&from=1788246000&to=1788249600&untraded=true&splitAdjust=false&format=Simple
```

Интервал запроса: 01.09.2026 07:00–08:00 UTC / 10:00–11:00 МСК. Базовый `Si` использован **только для проверки доступа к production endpoint**; конкретный контракт не подтверждён. Авторизация отсутствовала. Других запросов к api.alor.ru из Codex не было.

| Наблюдение | Результат |
|---|---|
| Прокси | используется унаследованный прокси среды |
| CONNECT | **403 Forbidden** |
| DNS/TCP до поставщика | отдельно не наблюдаемы за прокси; не проверялись обходным маршрутом |
| TLS к поставщику | NOT_ESTABLISHED |
| HTTP-код АЛОР | **null**, ответа поставщика нет |
| JSON АЛОР | NOT_RECEIVED |
| Полученные исходные байты | 0 |
| Число свечей из ответа | null — ответ не получен |
| SHA256 котировок | null — котировок нет |

Ошибка: `<urlopen error Tunnel connection failed: 403 Forbidden>`. Полный безопасный receipt: [ALOR_NETWORK_PROBE.json](ALOR_NETWORK_PROBE.json). Это сетевой отказ исполнителя, **не** 401/403 АЛОР, не 400 параметров, не 404 контракта и не HTTP200 с пустой историей. Архив АЛОР не объявляется недоступным или удалённым. Не использовались внешние прокси, туннели, Actions, подмена домена или test/apidev для котировок.

## Проверенная документация и предел её доказательности

Прочитаны [официальный history GET](https://alor.dev/docs/api/http/md-v-2-history-get), [публичный поиск инструментов](https://alor.dev/docs/api/http/md-v-2-securities-get), [карточка инструмента](https://alor.dev/docs/api/http/md-v-2-securities-exchange-symbol-get), [контуры](https://alor.dev/docs/api/access/environments), [ограничения](https://alor.dev/docs/api/usage/limits-and-recommendations) и OpenAPI schema из [официального SDK](https://github.com/alor-broker/OpenAPI.SDK/blob/10bd1f814c693c0c4ce136e0ff117ff700b223e3/WarpOpenAPIv2.yml). SHA256 и commit schema закреплены в `ALOR_DOCUMENTATION_RECEIPT.json`; чтение GitHub/schema не является обращением к архиву котировок.

History и общий `/md/v2/Securities` документированы публичными. Exchange-wide каталог с `includeOld` и отдельная карточка документированы приватными; они не используются. Запросы history соответствуют schema: tf=900 секунд, UTC Unix seconds, exact `untraded=true`, `splitAdjust=false`, Simple; `countBack` исключён. Указанные `next`/`prev` — времена соседних свечей, а не произвольные page tokens.

Из документации нельзя вывести доступную глубину 2020–2026, полноту публичного поиска истёкших контрактов или истинную Open-label convention фактических ответов. Эти вопросы остаются открытыми. Примеры по умолчанию могут содержать тестовый контур; в загрузчике endpoint фиксирован production. Заголовки авторизации и токены не поддерживаются.

## Что подготовлено

[`download_quarterly_m15_alor.py`](download_quarterly_m15_alor.py) — один автономный stdlib-файл Python 3.12:

- `--mode probe`, `--mode download`, `--mode verify`, обязательный `--output-dir`;
- discovery через ограниченный публичный поиск с limit/offset, проверкой повторяющихся страниц и жёстким пределом; кандидаты имён не принимаются без метаданных;
- строгие канонические датированные символы, MOEX/FORTS/RFUD, futures type/CFI; perpetual/spot/mini/чужие активы исключены по идентичности; BR/NG проверяются по всем месяцам;
- девять проб Si/GD/CNY с настоящими смежными M15 как обязательным условием, один отдельный повтор положительных проб для стабильности OHLCV;
- загрузка только после успешного probe с тем же кодом/параметрами; частичный допуск не объявляет 2020 подтверждённым;
- диапазоны до семи дней, `[from,to)` внутри программы и `to-1` в запросе, без countBack; строгое уменьшение поддиапазона при neighbor traversal, защита от зацикливания;
- сохранение неизменённых response bytes, URL/time/status/ошибки/SHA256, immutable receipts и chunks, кэш успешных запросов; одна новая попытка сбоя только по явному `--retry-failed`, без перезаписи;
- не чаще одного GET в секунду, бюджет запросов на запуск, Retry-After, обработка HTTP/DNS/TLS/CONNECT, lock от параллельных запусков и сохранение прогресса;
- OHLCV/NaN/finite/price/volume/range/order/duplicates validation, конфликт OHLCV останавливает процесс; никаких clipping/filling/искусственных свечей;
- отдельные контракты и годовой отчёт покрытия без склейки; NO_DATA/null; отсутствующие listing/expiry даты не выдумываются; raw запрещены внутри Git checkout;
- автономная проверка сохранённых байтов и схемы без сети; производные отчёты имеют историю версий.

Даты начала/окончания торгов и экспирации требуют дальнейшей верификации. АЛОР `cancellation` сохраняется как provider completion; неизвестные first/last trade/expiry остаются null. Принята только рабочая гипотеза Open label, явно отмеченная в manifest. Rollover rule отсутствует; Stop/P&L между контрактами не переносится. H1/M30 другого continuous-источника автоматически не сравниваются. Срок хранения неизвестен; пустой ответ его не доказывает.

[`ALOR_WINDOWS_RUNBOOK_RU.md`](ALOR_WINDOWS_RUNBOOK_RU.md) содержит готовые PowerShell-команды: Python, получение и SHA256 файлов, тесты, probe, просмотр результата, download/resume, offline verify, ZIP и возврат в этот чат. Запуск только на отдельном обычном ПК; не на Intel, без Scheduled Tasks. Сырые данные не публиковать в PR #556.

## Проверки и текущие статусы

**31 автономный synthetic test PASS на Python 3.12.14/Linux**, в том числе полный fake probe/cache/gate/download/manifest, границы и пагинация, дедупликация, сохранение/повтор, ошибки и отсутствие Authorization. `ALOR_TESTS.log`. Ещё 6 source-gate tests PASS; два source-gate прогона побайтово совпали. `reproducibility.json` отдельно учитывает их и не подменяет ими replay.

**Windows execution: NOT_RUN. Real ALOR API acceptance: NOT_VERIFIED.** Успешных реальных ответов нет. Не выполнялись массовая загрузка, реальный контрактный пилот, аудит целевых M15, frozen replication, scalar trade audit или исторический replay. Самопроверки не дают COMPUTATIONAL_AUDIT=PASS.

| Статус | Значение |
|---|---|
| DATA_ACQUISITION | BLOCKED |
| SOURCE_INTEGRITY | INCOMPLETE |
| FROZEN_STRATEGY_REPLICATION | NOT_RUN |
| COMPUTATIONAL_AUDIT | NOT_RUN |
| EXPLORATORY_REPLAY | NOT_RUN |
| ROLL_PROVENANCE | UNVERIFIED |
| TRADABLE_QUARTERLY_PERFORMANCE | NOT_VALIDATED |
| ECONOMIC_CONCLUSION | INCONCLUSIVE |

После приёма архива возможно продолжение **той же задачи и PR #556** с аудитом исходных данных. Не менялись T1_NEXT_OPEN_TRAIL_3p5, production H1/M15, Control Center, FINAM, R15, прежние frozen-результаты и PR #555. **STOP для внешнего аудита. Без merge и auto-merge.**
